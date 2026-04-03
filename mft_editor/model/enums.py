"""Firmware enums matching the MFT protocol."""

from enum import IntEnum


class MidiType(IntEnum):
    """Encoder MIDI output type (midi_type_t)."""
    NOTE = 0
    CC = 1
    REL_ENC = 2            # Relative encoder (3Fh/41h)
    SWITCH_VEL_CONTROL = 3 # CC with velocity control
    REL_ENC_MOUSE_DRAG = 4
    REL_ENC_MOUSE_SCROLL = 5


class EncSwActionType(IntEnum):
    """Encoder switch action (enc_sw_action_type_t)."""
    CC_HOLD = 0
    CC_TOGGLE = 1
    NOTE_HOLD = 2
    NOTE_TOGGLE = 3
    RESET_VALUE = 4
    FINE_ADJUST = 5
    SHIFT_HOLD = 6
    SHIFT_TOGGLE = 7


class EncMoveType(IntEnum):
    """Encoder movement sensitivity (enc_move_type_t)."""
    DIRECT = 0
    RESPONSIVE = 1  # Called EMULATION in firmware
    VELOCITY_SENSITIVE = 2


class DisplayType(IntEnum):
    """Indicator display type (display_type_t)."""
    DOT = 0
    BAR = 1
    BLENDED_BAR = 2
    BLENDED_DOT = 3


class SideSwAction(IntEnum):
    """Side switch action (side_sw_action_t)."""
    CC_HOLD = 0
    CC_TOGGLE = 1
    NOTE_HOLD = 2
    NOTE_TOGGLE = 3
    SHIFT_PAGE_1 = 4
    SHIFT_PAGE_2 = 5
    BANK_UP = 6
    BANK_DOWN = 7
    BANK_1 = 8
    BANK_2 = 9
    BANK_3 = 10
    BANK_4 = 11
    CYCLE_BANK = 12
