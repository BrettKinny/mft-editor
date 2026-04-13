export enum MidiType {
  NOTE = 0,
  CC = 1,
  REL_ENC = 2,
  SWITCH_VEL_CONTROL = 3,
  REL_ENC_MOUSE_DRAG = 4,
  REL_ENC_MOUSE_SCROLL = 5,
}

export enum EncSwActionType {
  CC_HOLD = 0,
  CC_TOGGLE = 1,
  NOTE_HOLD = 2,
  NOTE_TOGGLE = 3,
  RESET_VALUE = 4,
  FINE_ADJUST = 5,
  SHIFT_HOLD = 6,
  SHIFT_TOGGLE = 7,
}

export enum EncMoveType {
  DIRECT = 0,
  RESPONSIVE = 1,
  VELOCITY_SENSITIVE = 2,
}

export enum DisplayType {
  DOT = 0,
  BAR = 1,
  BLENDED_BAR = 2,
  BLENDED_DOT = 3,
}

export enum SideSwAction {
  CC_HOLD = 0,
  CC_TOGGLE = 1,
  NOTE_HOLD = 2,
  NOTE_TOGGLE = 3,
  SHIFT_PAGE_1 = 4,
  SHIFT_PAGE_2 = 5,
  BANK_UP = 6,
  BANK_DOWN = 7,
  BANK_1 = 8,
  BANK_2 = 9,
  BANK_3 = 10,
  BANK_4 = 11,
  CYCLE_BANK = 12,
}
