import {
  DisplayType,
  EncMoveType,
  EncSwActionType,
  MidiType,
  SideSwAction,
} from './enums.js';

export const NUM_ENCODERS = 16;
export const NUM_BANKS = 4;
export const TOTAL_ENCODERS = NUM_ENCODERS * NUM_BANKS;

export const ENC_CFG_SIZE = 15;
export const GLOBAL_CFG_SIZE = 12;

type DefaultColors = readonly [number, number, number];
const DEFAULT_COLORS: Record<number, DefaultColors> = {
  0: [25, 113, 63],
  1: [81, 63, 63],
  2: [25, 100, 63],
  3: [25, 0, 63],
};

export interface EncoderConfig {
  has_detent: number;
  movement: number;
  switch_action_type: number;
  switch_midi_channel: number;
  switch_midi_number: number;
  switch_midi_type: number;
  encoder_midi_channel: number;
  encoder_midi_number: number;
  encoder_midi_type: number;
  active_color: number;
  inactive_color: number;
  detent_color: number;
  indicator_display_type: number;
  is_super_knob: number;
  encoder_shift_midi_channel: number;
}

export function makeDefaultEncoderConfig(): EncoderConfig {
  return {
    has_detent: 0,
    movement: EncMoveType.DIRECT,
    switch_action_type: EncSwActionType.CC_HOLD,
    switch_midi_channel: 1,
    switch_midi_number: 0,
    switch_midi_type: MidiType.CC,
    encoder_midi_channel: 0,
    encoder_midi_number: 0,
    encoder_midi_type: MidiType.CC,
    active_color: 25,
    inactive_color: 113,
    detent_color: 63,
    indicator_display_type: DisplayType.BLENDED_BAR,
    is_super_knob: 0,
    encoder_shift_midi_channel: 4,
  };
}

export function encoderToBytes(cfg: EncoderConfig): number[] {
  return [
    cfg.has_detent,
    cfg.movement,
    cfg.switch_action_type,
    cfg.switch_midi_channel,
    cfg.switch_midi_number,
    cfg.switch_midi_type,
    cfg.encoder_midi_channel,
    cfg.encoder_midi_number,
    cfg.encoder_midi_type,
    cfg.active_color,
    cfg.inactive_color,
    cfg.detent_color,
    cfg.indicator_display_type,
    cfg.is_super_knob,
    cfg.encoder_shift_midi_channel,
  ];
}

export function encoderFromBytes(data: readonly number[]): EncoderConfig {
  return {
    has_detent: data[0]!,
    movement: data[1]!,
    switch_action_type: data[2]!,
    switch_midi_channel: data[3]!,
    switch_midi_number: data[4]!,
    switch_midi_type: data[5]!,
    encoder_midi_channel: data[6]!,
    encoder_midi_number: data[7]!,
    encoder_midi_type: data[8]!,
    active_color: data[9]!,
    inactive_color: data[10]!,
    detent_color: data[11]!,
    indicator_display_type: data[12]!,
    is_super_knob: data[13]!,
    encoder_shift_midi_channel: data[14]!,
  };
}

export interface GlobalConfig {
  midi_channel: number;
  side_is_banked: number;
  side_func_1: number;
  side_func_2: number;
  side_func_3: number;
  side_func_4: number;
  side_func_5: number;
  side_func_6: number;
  super_knob_start: number;
  super_knob_end: number;
  rgb_brightness: number;
  ind_brightness: number;
}

export function makeDefaultGlobalConfig(): GlobalConfig {
  return {
    midi_channel: 3,
    side_is_banked: 1,
    side_func_1: SideSwAction.CC_HOLD,
    side_func_2: SideSwAction.BANK_DOWN,
    side_func_3: SideSwAction.CC_HOLD,
    side_func_4: SideSwAction.CC_HOLD,
    side_func_5: SideSwAction.BANK_UP,
    side_func_6: SideSwAction.CC_HOLD,
    super_knob_start: 63,
    super_knob_end: 127,
    rgb_brightness: 127,
    ind_brightness: 127,
  };
}

export function globalToBytes(cfg: GlobalConfig): number[] {
  return [
    cfg.midi_channel,
    cfg.side_is_banked,
    cfg.side_func_1,
    cfg.side_func_2,
    cfg.side_func_3,
    cfg.side_func_4,
    cfg.side_func_5,
    cfg.side_func_6,
    cfg.super_knob_start,
    cfg.super_knob_end,
    cfg.rgb_brightness,
    cfg.ind_brightness,
  ];
}

export function globalFromBytes(data: readonly number[]): GlobalConfig {
  return {
    midi_channel: data[0]!,
    side_is_banked: data[1]!,
    side_func_1: data[2]!,
    side_func_2: data[3]!,
    side_func_3: data[4]!,
    side_func_4: data[5]!,
    side_func_5: data[6]!,
    side_func_6: data[7]!,
    super_knob_start: data[8]!,
    super_knob_end: data[9]!,
    rgb_brightness: data[10]!,
    ind_brightness: data[11]!,
  };
}

function makeDefaultEncoderForBankIndex(bank: number, index: number): EncoderConfig {
  const [active, inactive, detent] = DEFAULT_COLORS[bank]!;
  const n = index + bank * NUM_ENCODERS;
  return {
    ...makeDefaultEncoderConfig(),
    switch_midi_channel: 1,
    switch_midi_number: n,
    encoder_midi_channel: 0,
    encoder_midi_number: n,
    encoder_shift_midi_channel: 4,
    active_color: active,
    inactive_color: inactive,
    detent_color: detent,
  };
}

export interface DeviceConfig {
  encoders: EncoderConfig[];
  global_config: GlobalConfig;
}

export function makeDefaultDeviceConfig(): DeviceConfig {
  const encoders: EncoderConfig[] = [];
  for (let bank = 0; bank < NUM_BANKS; bank++) {
    for (let enc = 0; enc < NUM_ENCODERS; enc++) {
      encoders.push(makeDefaultEncoderForBankIndex(bank, enc));
    }
  }
  return { encoders, global_config: makeDefaultGlobalConfig() };
}

export function getEncoder(config: DeviceConfig, bank: number, index: number): EncoderConfig {
  return config.encoders[bank * NUM_ENCODERS + index]!;
}

export function setEncoder(
  config: DeviceConfig,
  bank: number,
  index: number,
  cfg: EncoderConfig,
): void {
  config.encoders[bank * NUM_ENCODERS + index] = cfg;
}

export function cloneDeviceConfig(config: DeviceConfig): DeviceConfig {
  return {
    encoders: config.encoders.map((e) => ({ ...e })),
    global_config: { ...config.global_config },
  };
}
