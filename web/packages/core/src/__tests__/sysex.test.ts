import { describe, expect, it } from 'vitest';

import {
  DisplayType,
  EncMoveType,
  EncSwActionType,
  MidiType,
} from '../enums.js';
import {
  makeDefaultEncoderConfig,
  makeDefaultGlobalConfig,
  type EncoderConfig,
  type GlobalConfig,
} from '../model.js';
import {
  BULK_PULL,
  CMD_BULK_XFER,
  CMD_PULL_CONF,
  CMD_PUSH_CONF,
  CMD_SYSTEM,
  SYS_BOOTLOADER,
  SYS_FACTORY_RESET,
  buildBulkPullEncoder,
  buildBulkPushEncoder,
  buildPullGlobal,
  buildPushGlobal,
  buildSystemBootloader,
  buildSystemFactoryReset,
  encoderTag,
  identifyMessage,
  parseEncoderPayload,
  parsePushGlobal,
} from '../sysex.js';

describe('GlobalConfig roundtrip', () => {
  it('default global roundtrip', () => {
    const cfg = makeDefaultGlobalConfig();
    const data = buildPushGlobal(cfg);
    const result = identifyMessage(data);
    expect(result).not.toBeNull();
    expect(result!.command).toBe(CMD_PUSH_CONF);
    const parsed = parsePushGlobal(result!.payload);
    expect(parsed.midi_channel).toBe(cfg.midi_channel);
    expect(parsed.side_is_banked).toBe(cfg.side_is_banked);
    expect(parsed.rgb_brightness).toBe(cfg.rgb_brightness);
    expect(parsed.ind_brightness).toBe(cfg.ind_brightness);
    expect(parsed.super_knob_start).toBe(cfg.super_knob_start);
    expect(parsed.super_knob_end).toBe(cfg.super_knob_end);
  });

  it('custom global roundtrip', () => {
    const cfg: GlobalConfig = {
      midi_channel: 5,
      side_is_banked: 0,
      side_func_1: 3,
      side_func_2: 6,
      side_func_3: 1,
      side_func_4: 2,
      side_func_5: 7,
      side_func_6: 12,
      super_knob_start: 0,
      super_knob_end: 64,
      rgb_brightness: 80,
      ind_brightness: 100,
    };
    const data = buildPushGlobal(cfg);
    const result = identifyMessage(data)!;
    const parsed = parsePushGlobal(result.payload);
    expect(parsed.midi_channel).toBe(5);
    expect(parsed.side_func_2).toBe(6);
    expect(parsed.side_func_6).toBe(12);
    expect(parsed.rgb_brightness).toBe(80);
  });
});

describe('EncoderConfig roundtrip', () => {
  it('default encoder roundtrip', () => {
    const cfg = makeDefaultEncoderConfig();
    const msgs = buildBulkPushEncoder(0, 0, cfg);
    expect(msgs.length).toBeGreaterThanOrEqual(1);

    const payload: number[] = [];
    for (const msg of msgs) {
      const result = identifyMessage(msg);
      expect(result).not.toBeNull();
      expect(result!.command).toBe(CMD_BULK_XFER);
      const data = result!.payload;
      const size = data[4]!;
      payload.push(...data.slice(5, 5 + size));
    }

    const parsed = parseEncoderPayload(payload);
    expect(parsed.has_detent).toBe(cfg.has_detent);
    expect(parsed.movement).toBe(cfg.movement);
    expect(parsed.encoder_midi_type).toBe(cfg.encoder_midi_type);
    expect(parsed.indicator_display_type).toBe(cfg.indicator_display_type);
  });

  it('custom encoder roundtrip', () => {
    const cfg: EncoderConfig = {
      has_detent: 1,
      movement: EncMoveType.RESPONSIVE,
      switch_action_type: EncSwActionType.NOTE_TOGGLE,
      switch_midi_channel: 3,
      switch_midi_number: 42,
      switch_midi_type: MidiType.NOTE,
      encoder_midi_channel: 0,
      encoder_midi_number: 7,
      encoder_midi_type: MidiType.CC,
      active_color: 64,
      inactive_color: 0,
      detent_color: 127,
      indicator_display_type: DisplayType.DOT,
      is_super_knob: 1,
      encoder_shift_midi_channel: 5,
    };
    const msgs = buildBulkPushEncoder(2, 7, cfg);
    const payload: number[] = [];
    for (const msg of msgs) {
      const result = identifyMessage(msg)!;
      const data = result.payload;
      const size = data[4]!;
      payload.push(...data.slice(5, 5 + size));
    }

    const parsed = parseEncoderPayload(payload);
    expect(parsed.has_detent).toBe(1);
    expect(parsed.movement).toBe(EncMoveType.RESPONSIVE);
    expect(parsed.switch_action_type).toBe(EncSwActionType.NOTE_TOGGLE);
    expect(parsed.switch_midi_channel).toBe(3);
    expect(parsed.switch_midi_number).toBe(42);
    expect(parsed.encoder_midi_channel).toBe(0);
    expect(parsed.encoder_midi_number).toBe(7);
    expect(parsed.active_color).toBe(64);
    expect(parsed.detent_color).toBe(127);
    expect(parsed.is_super_knob).toBe(1);
    expect(parsed.encoder_shift_midi_channel).toBe(5);
  });

  it('encoder tag calculation', () => {
    expect(encoderTag(0, 0)).toBe(1);
    expect(encoderTag(0, 15)).toBe(16);
    expect(encoderTag(1, 0)).toBe(17);
    expect(encoderTag(3, 15)).toBe(64);
  });

  it('all values are 7-bit safe', () => {
    const cfg: EncoderConfig = {
      ...makeDefaultEncoderConfig(),
      has_detent: 1,
      movement: 2,
      switch_midi_channel: 15,
      switch_midi_number: 127,
      encoder_midi_channel: 15,
      encoder_midi_number: 127,
      active_color: 127,
      inactive_color: 127,
      detent_color: 127,
      encoder_shift_midi_channel: 15,
    };
    const msgs = buildBulkPushEncoder(3, 15, cfg);
    for (const msg of msgs) {
      for (const byte of msg) {
        expect(byte).toBeLessThanOrEqual(0x7f);
      }
    }
  });
});

describe('Bulk pull request', () => {
  it('pull message format', () => {
    const msg = buildBulkPullEncoder(0, 0);
    const result = identifyMessage(msg);
    expect(result).not.toBeNull();
    expect(result!.command).toBe(CMD_BULK_XFER);
    expect(result!.payload[0]).toBe(BULK_PULL);
    expect(result!.payload[1]).toBe(1);
  });

  it('pull various encoders', () => {
    const msg = buildBulkPullEncoder(2, 5);
    const result = identifyMessage(msg)!;
    expect(result.payload[1]).toBe(2 * 16 + 5 + 1);
  });
});

describe('System commands', () => {
  it('factory reset format', () => {
    const msg = buildSystemFactoryReset();
    const result = identifyMessage(msg)!;
    expect(result.command).toBe(CMD_SYSTEM);
    expect(result.payload[0]).toBe(SYS_FACTORY_RESET);
  });

  it('bootloader format', () => {
    const msg = buildSystemBootloader();
    const result = identifyMessage(msg)!;
    expect(result.command).toBe(CMD_SYSTEM);
    expect(result.payload[0]).toBe(SYS_BOOTLOADER);
  });
});

describe('Pull global', () => {
  it('pull global format', () => {
    const msg = buildPullGlobal();
    const result = identifyMessage(msg)!;
    expect(result.command).toBe(CMD_PULL_CONF);
    expect(result.payload[0]).toBe(0x00);
  });
});

describe('identifyMessage', () => {
  it('invalid message', () => {
    expect(identifyMessage([0x01, 0x02])).toBeNull();
  });

  it('wrong manufacturer', () => {
    expect(identifyMessage([0x00, 0x02, 0x79, 0x01])).toBeNull();
  });

  it('valid message', () => {
    const result = identifyMessage([0x00, 0x01, 0x79, 0x01, 0x00, 0x05]);
    expect(result).not.toBeNull();
    expect(result!.command).toBe(0x01);
  });
});
