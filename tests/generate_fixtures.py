"""Generate byte-exact cross-check fixtures for the TypeScript web port.

Writes JSON files under tests/fixtures/ containing:
  - name: fixture identifier
  - preset: mft-editor-v1 JSON export (identical to what export_config writes)
  - sysex.global: byte list of build_push_global(cfg.global_config)
  - sysex.encoders: list of per-encoder {bank, encoder, messages} byte lists

The TypeScript Vitest suite loads these via packages/core/src/__tests__/
fixtures.test.ts and asserts byte-exact equality against its own port of
the SysEx + preset logic. Any protocol drift between editors will fail here.
"""

from __future__ import annotations

import json
from pathlib import Path

from mft_editor.io.preset_file import export_config
from mft_editor.midi import sysex
from mft_editor.model.config import (
    NUM_BANKS,
    NUM_ENCODERS,
    DeviceConfig,
    EncoderConfig,
    GlobalConfig,
)
from mft_editor.model.enums import (
    DisplayType,
    EncMoveType,
    EncSwActionType,
    MidiType,
    SideSwAction,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _encode_full(config: DeviceConfig) -> dict:
    """Return the full SysEx byte stream for a config as nested byte lists."""
    global_bytes = sysex.build_push_global(config.global_config)
    encoders = []
    for bank in range(NUM_BANKS):
        for enc in range(NUM_ENCODERS):
            cfg = config.get_encoder(bank, enc)
            messages = sysex.build_bulk_push_encoder(bank, enc, cfg)
            encoders.append({
                "bank": bank,
                "encoder": enc,
                "messages": messages,
            })
    return {"global": global_bytes, "encoders": encoders}


def _preset_payload(config: DeviceConfig) -> dict:
    """Return the same structure export_config writes to disk."""
    return {
        "format": "mft-editor-v1",
        "global": config.global_config.to_bytes(),
        "encoders": [enc.to_bytes() for enc in config.encoders],
    }


def _fixture(name: str, config: DeviceConfig) -> dict:
    return {
        "name": name,
        "preset": _preset_payload(config),
        "sysex": _encode_full(config),
    }


def _default_config() -> DeviceConfig:
    return DeviceConfig()


def _max_values_config() -> DeviceConfig:
    """All 7-bit fields at 0x7F, all channels at 15 — mirrors test_all_values_7bit."""
    config = DeviceConfig()
    config.global_config = GlobalConfig(
        midi_channel=15,
        side_is_banked=1,
        side_func_1=SideSwAction.CYCLE_BANK,
        side_func_2=SideSwAction.BANK_4,
        side_func_3=SideSwAction.SHIFT_PAGE_2,
        side_func_4=SideSwAction.NOTE_TOGGLE,
        side_func_5=SideSwAction.BANK_UP,
        side_func_6=SideSwAction.CC_TOGGLE,
        super_knob_start=127,
        super_knob_end=127,
        rgb_brightness=127,
        ind_brightness=127,
    )
    for bank in range(NUM_BANKS):
        for enc in range(NUM_ENCODERS):
            config.set_encoder(bank, enc, EncoderConfig(
                has_detent=1,
                movement=EncMoveType.VELOCITY_SENSITIVE,
                switch_action_type=EncSwActionType.SHIFT_TOGGLE,
                switch_midi_channel=15,
                switch_midi_number=127,
                switch_midi_type=MidiType.REL_ENC_MOUSE_SCROLL,
                encoder_midi_channel=15,
                encoder_midi_number=127,
                encoder_midi_type=MidiType.REL_ENC_MOUSE_SCROLL,
                active_color=127,
                inactive_color=127,
                detent_color=127,
                indicator_display_type=DisplayType.BLENDED_DOT,
                is_super_knob=1,
                encoder_shift_midi_channel=15,
            ))
    return config


def _brightness_quirk_config() -> DeviceConfig:
    """Exercise the rgb_brightness != ind_brightness tag-31/32 path."""
    config = DeviceConfig()
    config.global_config.rgb_brightness = 44
    config.global_config.ind_brightness = 100
    config.global_config.midi_channel = 7
    config.global_config.super_knob_start = 10
    config.global_config.super_knob_end = 90
    return config


def _mixed_encoders_config() -> DeviceConfig:
    """A few hand-picked encoder values distributed across banks."""
    config = DeviceConfig()
    config.set_encoder(0, 0, EncoderConfig(
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
    ))
    config.set_encoder(2, 7, EncoderConfig(
        has_detent=0,
        movement=EncMoveType.DIRECT,
        switch_action_type=EncSwActionType.FINE_ADJUST,
        switch_midi_channel=10,
        switch_midi_number=64,
        switch_midi_type=MidiType.CC,
        encoder_midi_channel=11,
        encoder_midi_number=100,
        encoder_midi_type=MidiType.REL_ENC,
        active_color=80,
        inactive_color=20,
        detent_color=50,
        indicator_display_type=DisplayType.BAR,
        is_super_knob=0,
        encoder_shift_midi_channel=12,
    ))
    config.set_encoder(3, 15, EncoderConfig(
        has_detent=1,
        movement=EncMoveType.VELOCITY_SENSITIVE,
        switch_action_type=EncSwActionType.SHIFT_HOLD,
        switch_midi_channel=0,
        switch_midi_number=1,
        switch_midi_type=MidiType.SWITCH_VEL_CONTROL,
        encoder_midi_channel=1,
        encoder_midi_number=2,
        encoder_midi_type=MidiType.REL_ENC_MOUSE_DRAG,
        active_color=1,
        inactive_color=126,
        detent_color=63,
        indicator_display_type=DisplayType.BLENDED_BAR,
        is_super_knob=0,
        encoder_shift_midi_channel=7,
    ))
    return config


FIXTURES: list[tuple[str, DeviceConfig]] = [
    ("default", _default_config()),
    ("max_values", _max_values_config()),
    ("brightness_quirk", _brightness_quirk_config()),
    ("mixed_encoders", _mixed_encoders_config()),
]


def main() -> None:
    FIXTURES_DIR.mkdir(exist_ok=True)
    index: list[str] = []
    for name, config in FIXTURES:
        payload = _fixture(name, config)
        out_path = FIXTURES_DIR / f"{name}.json"
        with open(out_path, "w") as f:
            json.dump(payload, f, indent=2)
        index.append(f"{name}.json")
        print(f"wrote {out_path}")
    with open(FIXTURES_DIR / "index.json", "w") as f:
        json.dump(index, f, indent=2)
    # Also write a round-trip of the default config through export_config
    # to catch any divergence between _preset_payload() and export_config().
    verify_path = FIXTURES_DIR / "_verify_default_preset.json"
    export_config(DeviceConfig(), verify_path)
    with open(verify_path) as f:
        exported = json.load(f)
    if exported != _preset_payload(DeviceConfig()):
        raise RuntimeError(
            "export_config() output diverges from _preset_payload(); "
            "regenerate fixtures after fixing the mismatch."
        )
    verify_path.unlink()


if __name__ == "__main__":
    main()
