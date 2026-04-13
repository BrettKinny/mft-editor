import {
  ENC_CFG_SIZE,
  TOTAL_ENCODERS,
  encoderFromBytes,
  globalFromBytes,
  makeDefaultDeviceConfig,
  type DeviceConfig,
} from './model.js';
import { ENC_TAG_OFFSET } from './sysex.js';

const FORMAT_TAG = 'mft-editor-v1';

const GLOBAL_TAG_TO_FIELD: ReadonlyMap<number, number> = new Map([
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
  [31, 10],
  [32, 11],
]);

const GLOBAL_CHANNEL_FIELDS: ReadonlySet<number> = new Set([0]);
const ENC_CHANNEL_FIELDS: ReadonlySet<number> = new Set([3, 6, 14]);

export interface PresetJson {
  format: string;
  global: number[];
  encoders: number[][];
}

export function exportConfigJson(config: DeviceConfig): PresetJson {
  return {
    format: FORMAT_TAG,
    global: [
      config.global_config.midi_channel,
      config.global_config.side_is_banked,
      config.global_config.side_func_1,
      config.global_config.side_func_2,
      config.global_config.side_func_3,
      config.global_config.side_func_4,
      config.global_config.side_func_5,
      config.global_config.side_func_6,
      config.global_config.super_knob_start,
      config.global_config.super_knob_end,
      config.global_config.rgb_brightness,
      config.global_config.ind_brightness,
    ],
    encoders: config.encoders.map((e) => [
      e.has_detent,
      e.movement,
      e.switch_action_type,
      e.switch_midi_channel,
      e.switch_midi_number,
      e.switch_midi_type,
      e.encoder_midi_channel,
      e.encoder_midi_number,
      e.encoder_midi_type,
      e.active_color,
      e.inactive_color,
      e.detent_color,
      e.indicator_display_type,
      e.is_super_knob,
      e.encoder_shift_midi_channel,
    ]),
  };
}

export function exportConfigJsonString(config: DeviceConfig): string {
  return JSON.stringify(exportConfigJson(config), null, 2);
}

export function importConfig(raw: Uint8Array): DeviceConfig {
  if (looksLikeJson(raw)) {
    return importJson(raw);
  }
  return importMfs(raw);
}

function looksLikeJson(data: Uint8Array): boolean {
  let i = 0;
  // Skip UTF-8 BOM
  if (data.length >= 3 && data[0] === 0xef && data[1] === 0xbb && data[2] === 0xbf) {
    i = 3;
  }
  for (; i < data.length; i++) {
    const b = data[i]!;
    if (b === 0x20 || b === 0x09 || b === 0x0a || b === 0x0d) continue;
    return b === 0x7b; // '{'
  }
  return false;
}

function importJson(raw: Uint8Array): DeviceConfig {
  const text = new TextDecoder().decode(raw);
  const data = JSON.parse(text) as Partial<PresetJson>;
  const config = makeDefaultDeviceConfig();
  if (data.global) {
    config.global_config = globalFromBytes(data.global);
  }
  if (data.encoders) {
    const limit = Math.min(data.encoders.length, TOTAL_ENCODERS);
    for (let i = 0; i < limit; i++) {
      config.encoders[i] = encoderFromBytes(data.encoders[i]!);
    }
  }
  return config;
}

function importMfs(buf: Uint8Array): DeviceConfig {
  if (buf.length < 2) {
    throw new Error('File too short to be a valid .mfs file');
  }
  let pos = 0;
  // marker byte, then global_data_size
  pos += 1;
  const globalDataSize = buf[pos]!;
  pos += 1;

  const globalValues = new Array<number>(12).fill(0);
  const end = pos + globalDataSize;
  if (end > buf.length) {
    throw new Error('Global data extends past end of file');
  }

  while (pos + 1 < end) {
    const tag = buf[pos]!;
    let val = buf[pos + 1]!;
    pos += 2;
    const fieldIdx = GLOBAL_TAG_TO_FIELD.get(tag);
    if (fieldIdx !== undefined) {
      if (GLOBAL_CHANNEL_FIELDS.has(fieldIdx)) {
        val = Math.max(val - 1, 0);
      }
      globalValues[fieldIdx] = val;
    }
    // encoder tags (10-24) in the global section are ignored
  }

  const config = makeDefaultDeviceConfig();
  config.global_config = globalFromBytes(globalValues);

  pos = end;
  while (pos + 5 <= buf.length) {
    const blockMarker = buf[pos]!;
    if (blockMarker !== 0x00) break;
    const encTag = buf[pos + 1]!;
    // bytes 2-3 are part/total (always 01 00 for single-part)
    const payloadSize = buf[pos + 4]!;
    pos += 5;

    if (pos + payloadSize > buf.length) break;

    const encValues = new Array<number>(ENC_CFG_SIZE).fill(0);
    let p = pos;
    const pEnd = pos + payloadSize;
    while (p + 1 < pEnd) {
      const stag = buf[p]!;
      let sval = buf[p + 1]!;
      p += 2;
      const fieldIdx = stag - ENC_TAG_OFFSET;
      if (fieldIdx >= 0 && fieldIdx < ENC_CFG_SIZE) {
        if (ENC_CHANNEL_FIELDS.has(fieldIdx)) {
          sval = Math.max(sval - 1, 0);
        }
        encValues[fieldIdx] = sval;
      }
    }
    pos = pEnd;

    const flatIdx = encTag - 1;
    if (flatIdx >= 0 && flatIdx < TOTAL_ENCODERS) {
      config.encoders[flatIdx] = encoderFromBytes(encValues);
    }
  }

  return config;
}
