"""Unit tests for SysEx encode/decode round-trips."""

import pytest
from mft_editor.model.config import EncoderConfig, GlobalConfig, DeviceConfig
from mft_editor.model.enums import DisplayType, EncMoveType, EncSwActionType, MidiType
from mft_editor.midi import sysex


class TestGlobalConfigRoundTrip:
    def test_default_global_roundtrip(self):
        cfg = GlobalConfig()
        data = sysex.build_push_global(cfg)
        result = sysex.identify_message(data)
        assert result is not None
        cmd, payload = result
        assert cmd == sysex.CMD_PUSH_CONF
        parsed = sysex.parse_push_global(payload)
        assert parsed.midi_channel == cfg.midi_channel
        assert parsed.side_is_banked == cfg.side_is_banked
        assert parsed.rgb_brightness == cfg.rgb_brightness
        assert parsed.ind_brightness == cfg.ind_brightness
        assert parsed.super_knob_start == cfg.super_knob_start
        assert parsed.super_knob_end == cfg.super_knob_end

    def test_custom_global_roundtrip(self):
        cfg = GlobalConfig(
            midi_channel=5,
            side_is_banked=0,
            side_func_1=3,
            side_func_2=6,
            side_func_3=1,
            side_func_4=2,
            side_func_5=7,
            side_func_6=12,
            super_knob_start=0,
            super_knob_end=64,
            rgb_brightness=80,
            ind_brightness=100,
        )
        data = sysex.build_push_global(cfg)
        result = sysex.identify_message(data)
        parsed = sysex.parse_push_global(result[1])
        assert parsed.midi_channel == 5
        assert parsed.side_func_2 == 6
        assert parsed.side_func_6 == 12
        assert parsed.rgb_brightness == 80


class TestEncoderConfigRoundTrip:
    def test_default_encoder_roundtrip(self):
        cfg = EncoderConfig()
        msgs = sysex.build_bulk_push_encoder(0, 0, cfg)
        assert len(msgs) >= 1

        # Accumulate all payloads
        payload = []
        for msg in msgs:
            result = sysex.identify_message(msg)
            assert result is not None
            cmd, data = result
            assert cmd == sysex.CMD_BULK_XFER
            size = data[4]
            payload.extend(data[5:5 + size])

        parsed = sysex.parse_encoder_payload(payload)
        assert parsed.has_detent == cfg.has_detent
        assert parsed.movement == cfg.movement
        assert parsed.encoder_midi_type == cfg.encoder_midi_type
        assert parsed.indicator_display_type == cfg.indicator_display_type

    def test_custom_encoder_roundtrip(self):
        cfg = EncoderConfig(
            has_detent=1,
            movement=EncMoveType.RESPONSIVE,
            switch_action_type=EncSwActionType.NOTE_TOGGLE,
            switch_midi_channel=3,
            switch_midi_number=42,
            switch_midi_type=MidiType.NOTE,
            encoder_midi_channel=0,
            encoder_midi_number=7,
            encoder_midi_type=MidiType.CC,
            active_color=64,
            inactive_color=0,
            detent_color=127,
            indicator_display_type=DisplayType.DOT,
            is_super_knob=1,
            encoder_shift_midi_channel=5,
        )
        msgs = sysex.build_bulk_push_encoder(2, 7, cfg)
        payload = []
        for msg in msgs:
            result = sysex.identify_message(msg)
            data = result[1]
            size = data[4]
            payload.extend(data[5:5 + size])

        parsed = sysex.parse_encoder_payload(payload)
        assert parsed.has_detent == 1
        assert parsed.movement == EncMoveType.RESPONSIVE
        assert parsed.switch_action_type == EncSwActionType.NOTE_TOGGLE
        assert parsed.switch_midi_channel == 3
        assert parsed.switch_midi_number == 42
        assert parsed.encoder_midi_channel == 0
        assert parsed.encoder_midi_number == 7
        assert parsed.active_color == 64
        assert parsed.detent_color == 127
        assert parsed.is_super_knob == 1
        assert parsed.encoder_shift_midi_channel == 5

    def test_encoder_tag_calculation(self):
        # Bank 0, Encoder 0 -> tag 1
        assert sysex._encoder_tag(0, 0) == 1
        # Bank 0, Encoder 15 -> tag 16
        assert sysex._encoder_tag(0, 15) == 16
        # Bank 1, Encoder 0 -> tag 17
        assert sysex._encoder_tag(1, 0) == 17
        # Bank 3, Encoder 15 -> tag 64
        assert sysex._encoder_tag(3, 15) == 64

    def test_all_values_7bit(self):
        """Ensure all SysEx data bytes are 7-bit (< 0x80)."""
        cfg = EncoderConfig(
            has_detent=1,
            movement=2,
            switch_midi_channel=15,
            switch_midi_number=127,
            encoder_midi_channel=15,
            encoder_midi_number=127,
            active_color=127,
            inactive_color=127,
            detent_color=127,
            encoder_shift_midi_channel=15,
        )
        msgs = sysex.build_bulk_push_encoder(3, 15, cfg)
        for msg in msgs:
            for byte in msg:
                assert byte <= 0x7F, f"Byte {byte:#x} exceeds 7-bit range"


class TestBulkPullRequest:
    def test_pull_message_format(self):
        msg = sysex.build_bulk_pull_encoder(0, 0)
        result = sysex.identify_message(msg)
        assert result is not None
        cmd, data = result
        assert cmd == sysex.CMD_BULK_XFER
        assert data[0] == sysex.BULK_PULL
        assert data[1] == 1  # tag for bank 0 encoder 0

    def test_pull_various_encoders(self):
        msg = sysex.build_bulk_pull_encoder(2, 5)
        result = sysex.identify_message(msg)
        data = result[1]
        assert data[1] == 2 * 16 + 5 + 1  # tag = 38


class TestSystemCommands:
    def test_factory_reset_format(self):
        msg = sysex.build_system_factory_reset()
        result = sysex.identify_message(msg)
        assert result is not None
        cmd, data = result
        assert cmd == sysex.CMD_SYSTEM
        assert data[0] == sysex.SYS_FACTORY_RESET


class TestPullGlobal:
    def test_pull_global_format(self):
        msg = sysex.build_pull_global()
        result = sysex.identify_message(msg)
        assert result is not None
        cmd, data = result
        assert cmd == sysex.CMD_PULL_CONF
        assert data[0] == 0x00


class TestIdentifyMessage:
    def test_invalid_message(self):
        assert sysex.identify_message([0x01, 0x02]) is None

    def test_wrong_manufacturer(self):
        assert sysex.identify_message([0x00, 0x02, 0x79, 0x01]) is None

    def test_valid_message(self):
        result = sysex.identify_message([0x00, 0x01, 0x79, 0x01, 0x00, 0x05])
        assert result is not None
        assert result[0] == 0x01
