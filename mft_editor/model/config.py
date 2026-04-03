"""Data classes for MFT device configuration."""

from __future__ import annotations
from dataclasses import dataclass, field
from copy import deepcopy

from .enums import (
    DisplayType,
    EncMoveType,
    EncSwActionType,
    MidiType,
    SideSwAction,
)

NUM_ENCODERS = 16
NUM_BANKS = 4
TOTAL_ENCODERS = NUM_ENCODERS * NUM_BANKS  # 64

# Default colors per bank (from firmware constants.h)
_DEFAULT_COLORS = {
    0: (25, 113, 63),   # Bank 1: active, inactive, detent
    1: (81, 63, 63),    # Bank 2
    2: (25, 100, 63),   # Bank 3
    3: (25, 0, 63),     # Bank 4
}


@dataclass
class EncoderConfig:
    """Configuration for a single encoder (15 fields, matching encoder_config_t)."""
    has_detent: int = 0
    movement: int = EncMoveType.DIRECT
    switch_action_type: int = EncSwActionType.CC_HOLD
    switch_midi_channel: int = 1   # 0-15
    switch_midi_number: int = 0    # 0-127
    switch_midi_type: int = MidiType.CC
    encoder_midi_channel: int = 0  # 0-15
    encoder_midi_number: int = 0   # 0-127
    encoder_midi_type: int = MidiType.CC
    active_color: int = 25
    inactive_color: int = 113
    detent_color: int = 63
    indicator_display_type: int = DisplayType.BLENDED_BAR
    is_super_knob: int = 0
    encoder_shift_midi_channel: int = 4  # 0-15

    def to_bytes(self) -> list[int]:
        """Serialize to 15-byte list matching firmware field order."""
        return [
            self.has_detent,
            self.movement,
            self.switch_action_type,
            self.switch_midi_channel,
            self.switch_midi_number,
            self.switch_midi_type,
            self.encoder_midi_channel,
            self.encoder_midi_number,
            self.encoder_midi_type,
            self.active_color,
            self.inactive_color,
            self.detent_color,
            self.indicator_display_type,
            self.is_super_knob,
            self.encoder_shift_midi_channel,
        ]

    @classmethod
    def from_bytes(cls, data: list[int]) -> EncoderConfig:
        """Deserialize from 15-byte list."""
        return cls(
            has_detent=data[0],
            movement=data[1],
            switch_action_type=data[2],
            switch_midi_channel=data[3],
            switch_midi_number=data[4],
            switch_midi_type=data[5],
            encoder_midi_channel=data[6],
            encoder_midi_number=data[7],
            encoder_midi_type=data[8],
            active_color=data[9],
            inactive_color=data[10],
            detent_color=data[11],
            indicator_display_type=data[12],
            is_super_knob=data[13],
            encoder_shift_midi_channel=data[14],
        )


@dataclass
class GlobalConfig:
    """Global device settings (12 fields, matching global_tvtable_t)."""
    midi_channel: int = 3          # 0-15 (display as 1-16)
    side_is_banked: int = 1
    side_func_1: int = SideSwAction.CC_HOLD
    side_func_2: int = SideSwAction.BANK_DOWN
    side_func_3: int = SideSwAction.CC_HOLD
    side_func_4: int = SideSwAction.CC_HOLD
    side_func_5: int = SideSwAction.BANK_UP
    side_func_6: int = SideSwAction.CC_HOLD
    super_knob_start: int = 63
    super_knob_end: int = 127
    rgb_brightness: int = 127
    ind_brightness: int = 127

    def to_bytes(self) -> list[int]:
        """Serialize to 12-byte list matching firmware field order."""
        return [
            self.midi_channel,
            self.side_is_banked,
            self.side_func_1,
            self.side_func_2,
            self.side_func_3,
            self.side_func_4,
            self.side_func_5,
            self.side_func_6,
            self.super_knob_start,
            self.super_knob_end,
            self.rgb_brightness,
            self.ind_brightness,
        ]

    @classmethod
    def from_bytes(cls, data: list[int]) -> GlobalConfig:
        """Deserialize from 12-byte list."""
        return cls(
            midi_channel=data[0],
            side_is_banked=data[1],
            side_func_1=data[2],
            side_func_2=data[3],
            side_func_3=data[4],
            side_func_4=data[5],
            side_func_5=data[6],
            side_func_6=data[7],
            super_knob_start=data[8],
            super_knob_end=data[9],
            rgb_brightness=data[10],
            ind_brightness=data[11],
        )


def _make_default_encoder(bank: int, index: int) -> EncoderConfig:
    """Create a default encoder config for a given bank and index."""
    active, inactive, detent = _DEFAULT_COLORS[bank]
    return EncoderConfig(
        switch_midi_channel=1,
        switch_midi_number=index + (bank * NUM_ENCODERS),
        encoder_midi_channel=0,
        encoder_midi_number=index + (bank * NUM_ENCODERS),
        encoder_shift_midi_channel=4,
        active_color=active,
        inactive_color=inactive,
        detent_color=detent,
    )


@dataclass
class DeviceConfig:
    """Complete device configuration: 64 encoders + global settings."""
    encoders: list[EncoderConfig] = field(default_factory=list)
    global_config: GlobalConfig = field(default_factory=GlobalConfig)

    def __post_init__(self):
        if not self.encoders:
            self.encoders = [
                _make_default_encoder(bank, enc)
                for bank in range(NUM_BANKS)
                for enc in range(NUM_ENCODERS)
            ]

    def get_encoder(self, bank: int, index: int) -> EncoderConfig:
        """Get encoder config by bank (0-3) and index (0-15)."""
        return self.encoders[bank * NUM_ENCODERS + index]

    def set_encoder(self, bank: int, index: int, config: EncoderConfig):
        """Set encoder config by bank (0-3) and index (0-15)."""
        self.encoders[bank * NUM_ENCODERS + index] = config

    def copy(self) -> DeviceConfig:
        """Return a deep copy."""
        return deepcopy(self)
