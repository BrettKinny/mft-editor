import {
  ENC_CFG_SIZE,
  NUM_ENCODERS,
  type EncoderConfig,
  type GlobalConfig,
  encoderFromBytes,
  encoderToBytes,
  globalFromBytes,
  globalToBytes,
} from './model.js';

export const MFR_ID = [0x00, 0x01, 0x79] as const;

export const CMD_PUSH_CONF = 0x01;
export const CMD_PULL_CONF = 0x02;
export const CMD_SYSTEM = 0x03;
export const CMD_BULK_XFER = 0x04;

export const SYS_FACTORY_RESET = 0x02;

export const BULK_PUSH = 0x00;
export const BULK_PULL = 0x01;

export const ENC_TAG_OFFSET = 10;
export const MAX_BULK_PAYLOAD = 30;

function header(cmd: number): number[] {
  return [...MFR_ID, cmd];
}

// Global field index → SysEx tag. Brightness fields 10/11 map to tags 31/32
// to avoid collision with encoder tag range (10-29).
const GLOBAL_TAG_MAP: ReadonlyArray<readonly [number, number]> = [
  [0, 0],
  [1, 1],
  [2, 2],
  [3, 3],
  [4, 4],
  [5, 5],
  [6, 6],
  [7, 7],
  [8, 8],
  [9, 9],
  [10, 31],
  [11, 32],
];

const GLOBAL_TAG_REVERSE: Map<number, number> = new Map(
  GLOBAL_TAG_MAP.map(([field, tag]) => [tag, field]),
);

export function buildPushGlobal(cfg: GlobalConfig): number[] {
  const data = header(CMD_PUSH_CONF);
  const values = globalToBytes(cfg);
  for (const [fieldIdx, tag] of GLOBAL_TAG_MAP) {
    let val = values[fieldIdx]!;
    if (fieldIdx === 0) {
      // midi_channel: stored 0-15, sent 1-16
      val = val + 1;
    }
    data.push(tag, val & 0x7f);
  }
  return data;
}

export function buildPullGlobal(): number[] {
  return [...header(CMD_PULL_CONF), 0x00];
}

export function parsePushGlobal(data: readonly number[]): GlobalConfig {
  const values = new Array<number>(12).fill(0);
  let i = 0;
  while (i + 1 < data.length) {
    const tag = data[i]!;
    let val = data[i + 1]!;
    const fieldIdx = GLOBAL_TAG_REVERSE.get(tag);
    if (fieldIdx !== undefined) {
      if (fieldIdx === 0) {
        val = val - 1;
      }
      values[fieldIdx] = val;
    }
    i += 2;
  }
  return globalFromBytes(values);
}

// ---------------------------------------------------------------------------
// Encoder config (BULK_XFER)
// ---------------------------------------------------------------------------

const ENC_CHANNEL_FIELDS: ReadonlySet<number> = new Set([3, 6, 14]);

export function encoderTag(bank: number, encoder: number): number {
  return bank * NUM_ENCODERS + encoder + 1;
}

export function buildBulkPushEncoder(
  bank: number,
  encoder: number,
  cfg: EncoderConfig,
): number[][] {
  const tag = encoderTag(bank, encoder);
  const raw = encoderToBytes(cfg);

  const pairs: number[] = [];
  for (let i = 0; i < ENC_CFG_SIZE; i++) {
    const sysexTag = i + ENC_TAG_OFFSET;
    let val = raw[i]!;
    if (ENC_CHANNEL_FIELDS.has(i)) {
      val = val + 1;
    }
    pairs.push(sysexTag, val & 0x7f);
  }

  const messages: number[][] = [];
  const totalParts = Math.ceil(pairs.length / MAX_BULK_PAYLOAD);
  for (let partNum = 0; partNum < totalParts; partNum++) {
    const start = partNum * MAX_BULK_PAYLOAD;
    const chunk = pairs.slice(start, start + MAX_BULK_PAYLOAD);
    const msg = header(CMD_BULK_XFER);
    msg.push(BULK_PUSH, tag, partNum + 1, totalParts, chunk.length);
    msg.push(...chunk);
    messages.push(msg);
  }
  return messages;
}

export function buildBulkPullEncoder(bank: number, encoder: number): number[] {
  const tag = encoderTag(bank, encoder);
  return [...header(CMD_BULK_XFER), BULK_PULL, tag];
}

export interface BulkPushParsed {
  bank: number;
  encoder: number;
  config: EncoderConfig | null;
}

export function parseBulkPushEncoder(data: readonly number[]): BulkPushParsed {
  if (data.length < 5) {
    return { bank: 0, encoder: 0, config: null };
  }
  // const subCmd = data[0]!;
  const tag = data[1]!;
  const part = data[2]!;
  const total = data[3]!;
  const size = data[4]!;
  const payload = data.slice(5, 5 + size);

  const bank = Math.floor((tag - 1) / NUM_ENCODERS);
  const encoder = (tag - 1) % NUM_ENCODERS;

  if (part === total) {
    return { bank, encoder, config: parseEncoderPayload(payload) };
  }
  return { bank, encoder, config: null };
}

export function parseEncoderPayload(payload: readonly number[]): EncoderConfig {
  const values = new Array<number>(ENC_CFG_SIZE).fill(0);
  let i = 0;
  while (i + 1 < payload.length) {
    const sysexTag = payload[i]!;
    let val = payload[i + 1]!;
    const fieldIdx = sysexTag - ENC_TAG_OFFSET;
    if (fieldIdx >= 0 && fieldIdx < ENC_CFG_SIZE) {
      if (ENC_CHANNEL_FIELDS.has(fieldIdx)) {
        val = val - 1;
      }
      values[fieldIdx] = val;
    }
    i += 2;
  }
  return encoderFromBytes(values);
}

// ---------------------------------------------------------------------------
// System commands
// ---------------------------------------------------------------------------

export function buildSystemFactoryReset(): number[] {
  return [...header(CMD_SYSTEM), SYS_FACTORY_RESET];
}

// ---------------------------------------------------------------------------
// Message dispatch
// ---------------------------------------------------------------------------

export interface IdentifiedMessage {
  command: number;
  payload: number[];
}

export function identifyMessage(data: readonly number[]): IdentifiedMessage | null {
  if (data.length < 4) return null;
  if (data[0] !== MFR_ID[0] || data[1] !== MFR_ID[1] || data[2] !== MFR_ID[2]) {
    return null;
  }
  return { command: data[3]!, payload: data.slice(4) };
}
