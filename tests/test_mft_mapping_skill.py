"""Behavior tests for the self-contained MFT mapping skill helper."""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from mft_editor.io.preset_file import export_config
from mft_editor.io.preset_file import import_config
from mft_editor.model.config import DeviceConfig
from mft_editor.model.enums import EncMoveType, EncSwActionType, MidiType


SCRIPT_PATH = (
    Path(__file__).parents[1]
    / ".claude"
    / "skills"
    / "mft-mapping"
    / "scripts"
    / "mft_preset.py"
)


def load_helper():
    spec = importlib.util.spec_from_file_location("mft_preset", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_default_preset_matches_canonical_project_export(tmp_path: Path) -> None:
    helper = load_helper()
    expected_path = tmp_path / "canonical.json"
    export_config(DeviceConfig(), expected_path)

    assert helper.Preset.defaults().to_dict() == helper.load_json(expected_path)


def test_validation_requires_a_complete_64_encoder_preset() -> None:
    helper = load_helper()
    data = helper.Preset.defaults().to_dict()
    helper.validate_preset(data)

    data["encoders"].pop()
    with pytest.raises(helper.PresetError, match="exactly 64"):
        helper.validate_preset(data)


def test_validation_applies_field_specific_ranges() -> None:
    helper = load_helper()
    data = helper.Preset.defaults().to_dict()
    data["global"][0] = 16

    with pytest.raises(helper.PresetError, match="global.midi_channel.*0..15"):
        helper.validate_preset(data)


def test_named_encoder_update_targets_one_bank_position() -> None:
    helper = load_helper()
    before = helper.Preset.defaults().to_dict()
    preset = helper.Preset.defaults()

    preset.update_encoder(
        bank=2,
        position=7,
        movement=helper.EncMoveType.RESPONSIVE,
        encoder_midi_number=99,
    )
    after = preset.to_dict()

    changed = [
        index
        for index, (old, new) in enumerate(
            zip(before["encoders"], after["encoders"], strict=True)
        )
        if old != new
    ]
    assert changed == [2 * 16 + 7]
    assert after["encoders"][changed[0]][1] == 1
    assert after["encoders"][changed[0]][7] == 99


def test_grouped_update_maps_explicit_sequences_by_position_order() -> None:
    helper = load_helper()
    preset = helper.Preset.defaults()
    before = preset.to_dict()

    result = preset.update_encoders(
        bank=1,
        positions=range(4),
        per_encoder={
            "switch_midi_number": [60, 61, 62, 63],
            "encoder_midi_number": [40, 41, 42, 43],
        },
        movement=helper.EncMoveType.RESPONSIVE,
        encoder_midi_channel=helper.user_channel(3),
    )
    data = preset.to_dict()
    changed = [
        index
        for index, (old, new) in enumerate(
            zip(before["encoders"], data["encoders"], strict=True)
        )
        if old != new
    ]

    assert result is preset
    assert changed == [16, 17, 18, 19]
    for position in range(4):
        encoder = data["encoders"][16 + position]
        assert encoder[1] == 1
        assert encoder[6] == 2
        assert encoder[4] == 60 + position
        assert encoder[7] == 40 + position
        for field_index in set(range(15)) - {1, 4, 6, 7}:
            assert encoder[field_index] == before["encoders"][16 + position][
                field_index
            ]
    assert all(
        type(value) is int
        for values in [data["global"], *data["encoders"]]
        for value in values
    )
    assert json.loads(json.dumps(data)) == data


@pytest.mark.parametrize(
    ("positions", "values"),
    [
        ([0, 1], [70, 71]),
        ((0, 1), (70, 71)),
        (range(2), range(70, 72)),
    ],
)
def test_grouped_update_accepts_deterministic_sequence_types(
    positions: object,
    values: object,
) -> None:
    helper = load_helper()
    preset = helper.Preset.defaults()

    preset.update_encoders(
        bank=0,
        positions=positions,
        per_encoder={"encoder_midi_number": values},
    )

    assert [encoder[7] for encoder in preset.to_dict()["encoders"][:2]] == [
        70,
        71,
    ]


def test_grouped_sequences_follow_the_explicit_position_order() -> None:
    helper = load_helper()
    preset = helper.Preset.defaults()

    preset.update_encoders(
        bank=2,
        positions=[5, 2, 9],
        per_encoder={"encoder_midi_number": [70, 71, 72]},
    )
    encoders = preset.to_dict()["encoders"]

    assert encoders[2 * 16 + 5][7] == 70
    assert encoders[2 * 16 + 2][7] == 71
    assert encoders[2 * 16 + 9][7] == 72


@pytest.mark.parametrize("values", [[40, 41, 42], [40, 41, 42, 43, 44]])
def test_grouped_update_rejects_mismatched_sequence_lengths_atomically(
    values: list[int],
) -> None:
    helper = load_helper()
    preset = helper.Preset.defaults()
    before = preset.to_dict()

    with pytest.raises(
        helper.PresetError,
        match=r"per_encoder\.encoder_midi_number.*exactly 4 values",
    ):
        preset.update_encoders(
            bank=1,
            positions=range(4),
            per_encoder={"encoder_midi_number": values},
        )

    assert preset.to_dict() == before


@pytest.mark.parametrize(
    ("positions", "message"),
    [
        ([], "at least one"),
        ([0, 0], "unique"),
        ("01", "list, tuple, or range"),
        ({0, 1}, "list, tuple, or range"),
        ((position for position in [0, 1]), "list, tuple, or range"),
        ([0, 16], r"positions\[1\].*0\.\.15"),
        ([0, True], r"positions\[1\].*0\.\.15"),
    ],
)
def test_grouped_update_rejects_invalid_position_sequences_atomically(
    positions: object,
    message: str,
) -> None:
    helper = load_helper()
    preset = helper.Preset.defaults()
    before = preset.to_dict()

    with pytest.raises(helper.PresetError, match=message):
        preset.update_encoders(
            bank=0,
            positions=positions,
            active_color=64,
        )

    assert preset.to_dict() == before


@pytest.mark.parametrize("bank", [-1, 4, True, 1.0])
def test_grouped_update_rejects_invalid_banks_atomically(bank: object) -> None:
    helper = load_helper()
    preset = helper.Preset.defaults()
    before = preset.to_dict()

    with pytest.raises(helper.PresetError, match=r"bank.*0\.\.3"):
        preset.update_encoders(
            bank=bank,
            positions=[0],
            active_color=64,
        )

    assert preset.to_dict() == before


@pytest.mark.parametrize(
    ("per_encoder", "message"),
    [
        ([], "per_encoder must be a mapping"),
        (
            {"active_color": "12"},
            r"per_encoder\.active_color.*list, tuple, or range",
        ),
        (
            {"active_color": {1, 2}},
            r"per_encoder\.active_color.*list, tuple, or range",
        ),
        (
            {"active_color": (value for value in [1, 2])},
            r"per_encoder\.active_color.*list, tuple, or range",
        ),
        (
            {"active_color": 1},
            r"per_encoder\.active_color.*list, tuple, or range",
        ),
    ],
)
def test_grouped_update_rejects_nondeterministic_per_encoder_inputs_atomically(
    per_encoder: object,
    message: str,
) -> None:
    helper = load_helper()
    preset = helper.Preset.defaults()
    before = preset.to_dict()

    with pytest.raises(helper.PresetError, match=message):
        preset.update_encoders(
            bank=0,
            positions=[0, 1],
            per_encoder=per_encoder,
            movement=helper.EncMoveType.RESPONSIVE,
        )

    assert preset.to_dict() == before


@pytest.mark.parametrize(
    ("fields", "message"),
    [
        ({}, "at least one encoder field"),
        (
            {
                "per_encoder": {"active_color": [1]},
                "active_color": 2,
            },
            r"active_color.*both shared and per_encoder",
        ),
        ({"not_a_field": 1}, "unknown encoder field: not_a_field"),
        (
            {"per_encoder": {"not_a_field": [1]}},
            "unknown encoder field: not_a_field",
        ),
    ],
)
def test_grouped_update_rejects_ambiguous_or_unknown_fields_atomically(
    fields: dict[str, object],
    message: str,
) -> None:
    helper = load_helper()
    preset = helper.Preset.defaults()
    before = preset.to_dict()

    with pytest.raises(helper.PresetError, match=message):
        preset.update_encoders(bank=0, positions=[0], **fields)

    assert preset.to_dict() == before


@pytest.mark.parametrize("active_color", [128, True])
def test_grouped_update_rejects_invalid_shared_values_atomically(
    active_color: object,
) -> None:
    helper = load_helper()
    preset = helper.Preset.defaults()
    before = preset.to_dict()

    with pytest.raises(
        helper.PresetError,
        match=r"encoder\.active_color.*0\.\.127",
    ):
        preset.update_encoders(
            bank=0,
            positions=[0, 1],
            active_color=active_color,
        )

    assert preset.to_dict() == before


@pytest.mark.parametrize(
    ("field_name", "value_case", "message"),
    [
        ("active_color", "out-of-range", r"encoder\.active_color.*0\.\.127"),
        ("active_color", "bool", r"encoder\.active_color.*0\.\.127"),
        (
            "encoder_midi_channel",
            "raw-channel",
            r"encoder\.encoder_midi_channel.*user_channel\(1\.\.16\)",
        ),
    ],
)
def test_grouped_update_rejects_invalid_per_encoder_values_atomically(
    field_name: str,
    value_case: str,
    message: str,
) -> None:
    helper = load_helper()
    preset = helper.Preset.defaults()
    before = preset.to_dict()
    values = {
        "out-of-range": [1, 128],
        "bool": [1, True],
        "raw-channel": [helper.user_channel(1), 1],
    }

    with pytest.raises(helper.PresetError, match=message):
        preset.update_encoders(
            bank=0,
            positions=[0, 1],
            per_encoder={field_name: values[value_case]},
            movement=helper.EncMoveType.RESPONSIVE,
        )

    assert preset.to_dict() == before


def test_user_channel_converts_displayed_channels_and_rejects_boundaries() -> None:
    helper = load_helper()
    preset = helper.Preset.defaults()

    preset.update_global(midi_channel=helper.user_channel(1))
    preset.update_encoder(
        bank=0,
        position=0,
        encoder_midi_channel=helper.user_channel(16),
    )
    data = preset.to_dict()

    assert data["global"][0] == 0
    assert data["encoders"][0][6] == 15
    for invalid in (0, 17, True):
        with pytest.raises(helper.PresetError, match="displayed MIDI channel"):
            helper.user_channel(invalid)


@pytest.mark.parametrize(
    ("scope", "field_name"),
    [
        ("global", "midi_channel"),
        ("encoder", "switch_midi_channel"),
        ("encoder", "encoder_midi_channel"),
        ("encoder", "encoder_shift_midi_channel"),
    ],
)
@pytest.mark.parametrize(
    "raw_case",
    ["stored-zero", "stored-middle", "stored-max", "bool", "unrelated-enum"],
)
def test_named_channel_updates_reject_unmarked_values_without_mutating(
    scope: str,
    field_name: str,
    raw_case: str,
) -> None:
    helper = load_helper()
    preset = helper.Preset.defaults()
    before = preset.to_dict()
    raw_values = {
        "stored-zero": 0,
        "stored-middle": 5,
        "stored-max": 15,
        "bool": True,
        "unrelated-enum": helper.MidiType.CC,
    }

    with pytest.raises(
        helper.PresetError,
        match=rf"{scope}\.{field_name}.*user_channel\(1\.\.16\)",
    ):
        if scope == "global":
            preset.update_global(**{field_name: raw_values[raw_case]})
        else:
            preset.update_encoder(
                bank=0,
                position=0,
                **{field_name: raw_values[raw_case]},
            )

    assert preset.to_dict() == before


def test_channel_markers_emit_plain_stored_integers_for_all_channel_fields() -> None:
    helper = load_helper()
    preset = helper.Preset.defaults()

    preset.update_global(midi_channel=helper.user_channel(5))
    preset.update_encoder(
        bank=0,
        position=0,
        switch_midi_channel=helper.user_channel(2),
        encoder_midi_channel=helper.user_channel(10),
        encoder_shift_midi_channel=helper.user_channel(16),
    )
    data = preset.to_dict()
    stored_channels = [
        data["global"][0],
        data["encoders"][0][3],
        data["encoders"][0][6],
        data["encoders"][0][14],
    ]

    assert stored_channels == [4, 1, 9, 15]
    assert all(type(channel) is int for channel in stored_channels)
    roundtripped = json.loads(json.dumps(data))
    roundtripped_channels = [
        roundtripped["global"][0],
        roundtripped["encoders"][0][3],
        roundtripped["encoders"][0][6],
        roundtripped["encoders"][0][14],
    ]
    assert roundtripped_channels == stored_channels
    assert all(type(channel) is int for channel in roundtripped_channels)


@pytest.mark.parametrize("scope", ["global", "encoder"])
def test_channel_errors_are_atomic_with_other_valid_named_updates(
    scope: str,
) -> None:
    helper = load_helper()
    preset = helper.Preset.defaults()
    before = preset.to_dict()

    with pytest.raises(helper.PresetError, match=r"user_channel\(1\.\.16\)"):
        if scope == "global":
            preset.update_global(rgb_brightness=64, midi_channel=5)
        else:
            preset.update_encoder(
                bank=0,
                position=0,
                active_color=64,
                encoder_midi_channel=5,
            )

    assert preset.to_dict() == before


def test_channel_marker_is_rejected_for_a_non_channel_field() -> None:
    helper = load_helper()
    preset = helper.Preset.defaults()
    before = preset.to_dict()

    with pytest.raises(
        helper.PresetError,
        match=r"encoder\.active_color.*integer.*0\.\.127",
    ):
        preset.update_encoder(
            bank=0,
            position=0,
            active_color=helper.user_channel(5),
        )

    assert preset.to_dict() == before


def test_strict_validation_accepts_plain_stored_channel_integers() -> None:
    helper = load_helper()
    data = helper.Preset.defaults().to_dict()
    data["global"][0] = 15
    data["encoders"][0][3] = 0
    data["encoders"][0][6] = 5
    data["encoders"][0][14] = 15

    helper.validate_preset(data)


def test_named_global_update_uses_canonical_fields_and_enums() -> None:
    helper = load_helper()
    preset = helper.Preset.defaults()

    result = preset.update_global(
        midi_channel=helper.user_channel(12),
        side_func_1=helper.SideSwAction.CYCLE_BANK,
        ind_brightness=80,
    )

    assert result is preset
    assert preset.to_dict()["global"] == [
        11,
        1,
        12,
        7,
        0,
        0,
        6,
        0,
        63,
        127,
        127,
        80,
    ]


def test_write_emits_a_valid_complete_preset_atomically(tmp_path: Path) -> None:
    helper = load_helper()
    output = tmp_path / "mapping.json"
    preset = helper.Preset.defaults().update_encoder(
        bank=3,
        position=15,
        encoder_midi_type=helper.MidiType.NOTE,
        encoder_midi_number=120,
    )

    result = preset.write(output)

    assert result == output
    assert helper.load_json(output) == preset.to_dict()
    helper.validate_file(output)
    assert sorted(path.name for path in tmp_path.iterdir()) == ["mapping.json"]


def test_validate_cli_reports_success_and_failure(tmp_path: Path) -> None:
    helper = load_helper()
    valid_path = helper.Preset.defaults().write(tmp_path / "valid.json")
    invalid_path = tmp_path / "invalid.json"
    invalid_path.write_text("{}\n", encoding="utf-8")

    valid = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "validate", str(valid_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    invalid = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "validate", str(invalid_path)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert valid.returncode == 0
    assert "valid mft-editor-v1 preset" in valid.stdout
    assert invalid.returncode == 2
    assert "preset must contain exactly the keys" in invalid.stderr


@pytest.mark.parametrize(
    ("bank", "position"),
    [
        (bank, position)
        for bank in range(4)
        for position in range(16)
    ],
)
def test_every_bank_position_maps_to_exactly_one_flat_encoder(
    bank: int,
    position: int,
) -> None:
    helper = load_helper()
    before = helper.Preset.defaults().to_dict()
    preset = helper.Preset.defaults()
    preset.update_encoder(bank=bank, position=position, active_color=127)

    after = preset.to_dict()
    changed = [
        index
        for index, (old, new) in enumerate(
            zip(before["encoders"], after["encoders"], strict=True)
        )
        if old != new
    ]
    assert changed == [bank * 16 + position]


def test_invalid_named_update_is_rejected_without_partial_mutation() -> None:
    helper = load_helper()
    preset = helper.Preset.defaults()
    before = preset.to_dict()

    with pytest.raises(helper.PresetError, match="unknown encoder field"):
        preset.update_encoder(
            bank=0,
            position=0,
            movement=helper.EncMoveType.RESPONSIVE,
            typo_field=1,
        )
    with pytest.raises(helper.PresetError, match="active_color.*0..127"):
        preset.update_encoder(
            bank=0,
            position=0,
            movement=helper.EncMoveType.RESPONSIVE,
            active_color=128,
        )

    assert preset.to_dict() == before


def test_strict_validation_rejects_boolean_bytes() -> None:
    helper = load_helper()
    data = helper.Preset.defaults().to_dict()
    data["encoders"][0][0] = True

    with pytest.raises(helper.PresetError, match="must be an integer"):
        helper.validate_preset(data)


def test_generated_file_roundtrips_through_canonical_import_export(
    tmp_path: Path,
) -> None:
    helper = load_helper()
    output = tmp_path / "generated.json"
    roundtrip = tmp_path / "roundtrip.json"
    (
        helper.Preset.defaults()
        .update_global(
            midi_channel=helper.user_channel(16),
            side_func_6=helper.SideSwAction.NOTE_HOLD,
        )
        .update_encoder(
            bank=0,
            position=5,
            movement=helper.EncMoveType.VELOCITY_SENSITIVE,
            switch_action_type=helper.EncSwActionType.CC_TOGGLE,
            encoder_midi_channel=helper.user_channel(3),
            encoder_midi_number=91,
            indicator_display_type=helper.DisplayType.DOT,
        )
        .write(output)
    )

    export_config(import_config(output), roundtrip)

    assert helper.load_json(roundtrip) == helper.load_json(output)


def test_benchmark_change_set_is_generated_from_canonical_defaults() -> None:
    helper = load_helper()
    preset = helper.Preset.defaults().update_global(
        midi_channel=helper.user_channel(5),
        rgb_brightness=96,
    )
    expected = DeviceConfig()
    expected.global_config.midi_channel = 4
    expected.global_config.rgb_brightness = 96

    preset.update_encoders(
        bank=1,
        positions=range(4),
        per_encoder={
            "switch_midi_number": range(60, 64),
            "encoder_midi_number": range(40, 44),
        },
        movement=helper.EncMoveType.RESPONSIVE,
        switch_action_type=helper.EncSwActionType.NOTE_TOGGLE,
        switch_midi_channel=helper.user_channel(2),
        switch_midi_type=helper.MidiType.NOTE,
        encoder_midi_channel=helper.user_channel(10),
        encoder_midi_type=helper.MidiType.REL_ENC,
        active_color=107,
        inactive_color=0,
    )
    for offset in range(4):
        encoder = expected.get_encoder(1, offset)
        encoder.movement = EncMoveType.RESPONSIVE
        encoder.switch_action_type = EncSwActionType.NOTE_TOGGLE
        encoder.switch_midi_channel = 1
        encoder.switch_midi_number = 60 + offset
        encoder.switch_midi_type = MidiType.NOTE
        encoder.encoder_midi_channel = 9
        encoder.encoder_midi_number = 40 + offset
        encoder.encoder_midi_type = MidiType.REL_ENC
        encoder.active_color = 107
        encoder.inactive_color = 0

    assert preset.to_dict() == {
        "format": "mft-editor-v1",
        "global": expected.global_config.to_bytes(),
        "encoders": [encoder.to_bytes() for encoder in expected.encoders],
    }


def test_helper_operates_when_copied_to_an_empty_workspace(
    tmp_path: Path,
) -> None:
    scripts_dir = tmp_path / "skill" / "scripts"
    scripts_dir.mkdir(parents=True)
    copied_script = scripts_dir / SCRIPT_PATH.name
    shutil.copy2(SCRIPT_PATH, copied_script)
    code = """
from mft_preset import DisplayType, MidiType, Preset, user_channel

preset = Preset.defaults()
preset.update_encoders(
    bank=1,
    positions=(11, 12),
    per_encoder={"encoder_midi_number": [74, 75]},
    encoder_midi_channel=user_channel(7),
    encoder_midi_type=MidiType.CC,
    indicator_display_type=DisplayType.BAR,
)
preset.write("mapping.json")
    """
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = str(scripts_dir)
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    validated = subprocess.run(
        [sys.executable, str(copied_script), "validate", "mapping.json"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert validated.returncode == 0, validated.stderr
    assert sorted(path.name for path in tmp_path.iterdir()) == [
        "mapping.json",
        "skill",
    ]
    assert not any(
        path.name == "__pycache__" or path.suffix in {".pyc", ".pyo"}
        for path in tmp_path.rglob("*")
    )
