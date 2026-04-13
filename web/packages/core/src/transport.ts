import {
  NUM_BANKS,
  NUM_ENCODERS,
  makeDefaultDeviceConfig,
  setEncoder,
  type DeviceConfig,
  type EncoderConfig,
  type GlobalConfig,
} from './model.js';
import {
  BULK_PUSH,
  CMD_BULK_XFER,
  CMD_PUSH_CONF,
  buildBulkPullEncoder,
  buildBulkPushEncoder,
  buildPullGlobal,
  buildPushGlobal,
  encoderTag,
  identifyMessage,
  parseEncoderPayload,
  parsePushGlobal,
} from './sysex.js';

/**
 * Low-level MIDI transport: send raw SysEx payloads (without F0/F7 framing)
 * and subscribe to incoming SysEx messages (also stripped of F0/F7).
 */
export interface Transport {
  readonly name: string;
  readonly connected: boolean;

  send(data: readonly number[]): void;
  onMessage(listener: (data: readonly number[]) => void): () => void;
  close(): void | Promise<void>;
}

// Rate-limit delays (ms) between SysEx sends. Tuned empirically against real
// firmware to avoid buffer overflow. Mirrors mft_editor/midi/device.py:103,114,136,145.
export const DELAY_AFTER_PULL_GLOBAL_MS = 50;
export const DELAY_AFTER_PUSH_GLOBAL_MS = 50;
export const DELAY_BETWEEN_PULL_ENCODER_MS = 20;
export const DELAY_BETWEEN_PUSH_ENCODER_PART_MS = 20;

export const DEFAULT_PULL_TIMEOUT_MS = 500;
export const DEFAULT_ENCODER_PULL_WINDOW_MS = 300;

const sleep = (ms: number): Promise<void> =>
  new Promise((resolve) => setTimeout(resolve, ms));

/**
 * Wait until `collect(msg)` returns a non-null value, or reject on timeout.
 * Subscribes before `send` fires to avoid races.
 */
function waitForMatch<T>(
  transport: Transport,
  collect: (msg: readonly number[]) => T | null,
  timeoutMs: number,
): Promise<T> {
  return new Promise((resolve, reject) => {
    let done = false;
    const finish = (result: T | null, err?: Error) => {
      if (done) return;
      done = true;
      clearTimeout(timer);
      unsubscribe();
      if (err) reject(err);
      else if (result === null) reject(new Error('Timed out waiting for MIDI response'));
      else resolve(result);
    };
    const timer = setTimeout(() => finish(null), timeoutMs);
    const unsubscribe = transport.onMessage((msg) => {
      try {
        const result = collect(msg);
        if (result !== null) finish(result);
      } catch (err) {
        finish(null, err as Error);
      }
    });
  });
}

export async function pullGlobal(
  transport: Transport,
  timeoutMs: number = DEFAULT_PULL_TIMEOUT_MS,
): Promise<GlobalConfig> {
  const promise = waitForMatch<GlobalConfig>(
    transport,
    (msg) => {
      const ident = identifyMessage(msg);
      if (!ident || ident.command !== CMD_PUSH_CONF) return null;
      return parsePushGlobal(ident.payload);
    },
    timeoutMs,
  );
  transport.send(buildPullGlobal());
  return promise;
}

export async function pullEncoder(
  transport: Transport,
  bank: number,
  encoder: number,
  windowMs: number = DEFAULT_ENCODER_PULL_WINDOW_MS,
): Promise<EncoderConfig> {
  const expectedTag = encoderTag(bank, encoder);
  const parts: (number[] | undefined)[] = [];
  let totalParts = 0;

  const promise = waitForMatch<EncoderConfig>(
    transport,
    (msg) => {
      const ident = identifyMessage(msg);
      if (!ident || ident.command !== CMD_BULK_XFER) return null;
      const payload = ident.payload;
      if (payload.length < 5) return null;
      if (payload[0] !== BULK_PUSH) return null;
      if (payload[1] !== expectedTag) return null;
      const part = payload[2]!;
      const total = payload[3]!;
      const size = payload[4]!;
      const chunk = payload.slice(5, 5 + size);
      parts[part - 1] = chunk;
      totalParts = total;
      for (let i = 0; i < totalParts; i++) {
        if (!parts[i]) return null;
      }
      const fullPayload: number[] = [];
      for (let i = 0; i < totalParts; i++) {
        fullPayload.push(...parts[i]!);
      }
      return parseEncoderPayload(fullPayload);
    },
    windowMs,
  );
  transport.send(buildBulkPullEncoder(bank, encoder));
  return promise;
}

export async function pullDeviceConfig(transport: Transport): Promise<DeviceConfig> {
  const config = makeDefaultDeviceConfig();

  try {
    config.global_config = await pullGlobal(transport);
  } catch {
    // leave defaults
  }
  await sleep(DELAY_AFTER_PULL_GLOBAL_MS);

  for (let bank = 0; bank < NUM_BANKS; bank++) {
    for (let enc = 0; enc < NUM_ENCODERS; enc++) {
      try {
        const cfg = await pullEncoder(transport, bank, enc);
        setEncoder(config, bank, enc, cfg);
      } catch {
        // leave defaults for this encoder
      }
      await sleep(DELAY_BETWEEN_PULL_ENCODER_MS);
    }
  }

  return config;
}

export async function pushDeviceConfig(
  transport: Transport,
  config: DeviceConfig,
): Promise<void> {
  transport.send(buildPushGlobal(config.global_config));
  await sleep(DELAY_AFTER_PUSH_GLOBAL_MS);

  for (let bank = 0; bank < NUM_BANKS; bank++) {
    for (let enc = 0; enc < NUM_ENCODERS; enc++) {
      const cfg = config.encoders[bank * NUM_ENCODERS + enc]!;
      const messages = buildBulkPushEncoder(bank, enc, cfg);
      for (const msg of messages) {
        transport.send(msg);
        await sleep(DELAY_BETWEEN_PUSH_ENCODER_PART_MS);
      }
    }
  }
}
