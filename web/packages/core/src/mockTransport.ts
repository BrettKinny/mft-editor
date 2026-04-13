import {
  NUM_ENCODERS,
  getEncoder,
  makeDefaultDeviceConfig,
  setEncoder,
  type DeviceConfig,
} from './model.js';
import {
  BULK_PULL,
  BULK_PUSH,
  CMD_BULK_XFER,
  CMD_PULL_CONF,
  CMD_PUSH_CONF,
  buildBulkPushEncoder,
  buildPushGlobal,
  identifyMessage,
  parseEncoderPayload,
  parsePushGlobal,
} from './sysex.js';
import type { Transport } from './transport.js';

type Listener = (data: readonly number[]) => void;

/**
 * In-memory MFT that responds to SysEx like real hardware. Mirrors
 * mft_editor/midi/mock.py for offline development and testing.
 */
export class MockTransport implements Transport {
  readonly name = 'Mock Midi Fighter Twister';
  connected = true;

  config: DeviceConfig;
  private listeners = new Set<Listener>();
  private bulkAccum = new Map<number, { parts: number[]; seen: number; total: number }>();

  constructor(config?: DeviceConfig) {
    this.config = config ?? makeDefaultDeviceConfig();
  }

  onMessage(listener: Listener): () => void {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  }

  close(): void {
    this.connected = false;
    this.listeners.clear();
    this.bulkAccum.clear();
  }

  send(data: readonly number[]): void {
    const ident = identifyMessage(data);
    if (!ident) return;
    const { command, payload } = ident;

    if (command === CMD_PULL_CONF) {
      this.queue(buildPushGlobal(this.config.global_config));
    } else if (command === CMD_BULK_XFER) {
      this.handleBulk(payload);
    } else if (command === CMD_PUSH_CONF) {
      this.config.global_config = parsePushGlobal(payload);
    }
  }

  private handleBulk(payload: readonly number[]): void {
    if (payload.length < 2) return;
    const subCmd = payload[0]!;
    const tag = payload[1]!;
    const bank = Math.floor((tag - 1) / NUM_ENCODERS);
    const encoder = (tag - 1) % NUM_ENCODERS;

    if (subCmd === BULK_PULL) {
      const cfg = getEncoder(this.config, bank, encoder);
      for (const msg of buildBulkPushEncoder(bank, encoder, cfg)) {
        this.queue(msg);
      }
      return;
    }

    if (subCmd === BULK_PUSH) {
      if (payload.length < 5) return;
      const part = payload[2]!;
      const total = payload[3]!;
      const size = payload[4]!;
      const chunk = payload.slice(5, 5 + size);

      let entry = this.bulkAccum.get(tag);
      if (!entry) {
        entry = { parts: [], seen: 0, total };
        this.bulkAccum.set(tag, entry);
      }
      entry.parts.push(...chunk);
      entry.seen += 1;
      // Suppress unused variable warning; part index preserved for future strict ordering.
      void part;

      if (entry.seen >= entry.total) {
        const cfg = parseEncoderPayload(entry.parts);
        setEncoder(this.config, bank, encoder, cfg);
        this.bulkAccum.delete(tag);
      }
    }
  }

  private queue(data: readonly number[]): void {
    // Emit asynchronously so receive side sees it after the current send returns,
    // matching real-device event delivery semantics.
    queueMicrotask(() => {
      for (const listener of this.listeners) {
        listener(data);
      }
    });
  }
}
