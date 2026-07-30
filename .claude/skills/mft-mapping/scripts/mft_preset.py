#!/usr/bin/env python3
"""Build and validate complete MIDI Fighter Twister JSON presets.

This module is intentionally self-contained so the skill can be copied into an
otherwise empty workspace. It uses only the Python standard library.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from collections.abc import Mapping
from copy import deepcopy
from enum import IntEnum
from pathlib import Path
from typing import Any


FORMAT = "mft-editor-v1"
NUM_BANKS = 4
NUM_ENCODERS = 16
TOTAL_ENCODERS = NUM_BANKS * NUM_ENCODERS

GLOBAL_DEFAULTS = [3, 1, 0, 7, 0, 0, 6, 0, 63, 127, 127, 127]
GLOBAL_FIELDS = (
    ("midi_channel", 0, 15),
    ("side_is_banked", 0, 1),
    ("side_func_1", 0, 12),
    ("side_func_2", 0, 12),
    ("side_func_3", 0, 12),
    ("side_func_4", 0, 12),
    ("side_func_5", 0, 12),
    ("side_func_6", 0, 12),
    ("super_knob_start", 0, 127),
    ("super_knob_end", 0, 127),
    ("rgb_brightness", 0, 127),
    ("ind_brightness", 0, 127),
)
ENCODER_FIELDS = (
    ("has_detent", 0, 1),
    ("movement", 0, 2),
    ("switch_action_type", 0, 7),
    ("switch_midi_channel", 0, 15),
    ("switch_midi_number", 0, 127),
    ("switch_midi_type", 0, 5),
    ("encoder_midi_channel", 0, 15),
    ("encoder_midi_number", 0, 127),
    ("encoder_midi_type", 0, 5),
    ("active_color", 0, 127),
    ("inactive_color", 0, 127),
    ("detent_color", 0, 127),
    ("indicator_display_type", 0, 3),
    ("is_super_knob", 0, 1),
    ("encoder_shift_midi_channel", 0, 15),
)
DEFAULT_COLORS = {
    0: (25, 113, 63),
    1: (81, 63, 63),
    2: (25, 100, 63),
    3: (25, 0, 63),
}
GLOBAL_FIELD_INDEX = {
    name: index for index, (name, _minimum, _maximum) in enumerate(GLOBAL_FIELDS)
}
ENCODER_FIELD_INDEX = {
    name: index for index, (name, _minimum, _maximum) in enumerate(ENCODER_FIELDS)
}


class MidiType(IntEnum):
    NOTE = 0
    CC = 1
    REL_ENC = 2
    SWITCH_VEL_CONTROL = 3
    REL_ENC_MOUSE_DRAG = 4
    REL_ENC_MOUSE_SCROLL = 5


class EncSwActionType(IntEnum):
    CC_HOLD = 0
    CC_TOGGLE = 1
    NOTE_HOLD = 2
    NOTE_TOGGLE = 3
    RESET_VALUE = 4
    FINE_ADJUST = 5
    SHIFT_HOLD = 6
    SHIFT_TOGGLE = 7


class EncMoveType(IntEnum):
    DIRECT = 0
    RESPONSIVE = 1
    VELOCITY_SENSITIVE = 2


class DisplayType(IntEnum):
    DOT = 0
    BAR = 1
    BLENDED_BAR = 2
    BLENDED_DOT = 3


class SideSwAction(IntEnum):
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


class PresetError(ValueError):
    """Raised when a preset violates the mft-editor-v1 contract."""


class _MidiChannel:
    """Opaque marker for a user-facing channel converted to stored form."""

    __slots__ = ("_stored",)

    def __init__(self, stored: int) -> None:
        self._stored = stored


def user_channel(displayed_channel: int) -> _MidiChannel:
    """Mark and convert a user-facing MIDI channel (1..16) to stored form."""
    if type(displayed_channel) is not int or not 1 <= displayed_channel <= 16:
        raise PresetError("displayed MIDI channel must be an integer in 1..16")
    return _MidiChannel(displayed_channel - 1)


def load_json(path: str | Path) -> Any:
    """Load JSON from ``path``."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_file(path: str | Path) -> dict[str, Any]:
    """Load and validate one preset file, returning its parsed object."""
    data = load_json(path)
    validate_preset(data)
    return data


def _validate_byte_list(value: Any, *, length: int, label: str) -> None:
    if not isinstance(value, list) or len(value) != length:
        raise PresetError(f"{label} must contain exactly {length} integers")
    for index, item in enumerate(value):
        if type(item) is not int or not 0 <= item <= 127:
            raise PresetError(
                f"{label}[{index}] must be an integer in the range 0..127"
            )


def _validate_field_ranges(
    values: list[int],
    fields: tuple[tuple[str, int, int], ...],
    *,
    label: str,
) -> None:
    for value, (name, minimum, maximum) in zip(values, fields, strict=True):
        if not minimum <= value <= maximum:
            raise PresetError(
                f"{label}.{name} must be in the range {minimum}..{maximum}"
            )


def _field_value(
    value: Any,
    field: tuple[str, int, int],
    *,
    label: str,
) -> int:
    name, minimum, maximum = field
    if name == "midi_channel" or name.endswith("_midi_channel"):
        if type(value) is not _MidiChannel:
            raise PresetError(
                f"{label}.{name} must be set with user_channel(1..16)"
            )
        value = value._stored
    elif isinstance(value, IntEnum):
        value = int(value)
    if type(value) is not int or not minimum <= value <= maximum:
        raise PresetError(
            f"{label}.{name} must be an integer in the range "
            f"{minimum}..{maximum}"
        )
    return value


def _index(value: Any, *, label: str, maximum: int) -> int:
    if type(value) is not int or not 0 <= value <= maximum:
        raise PresetError(f"{label} must be an integer in the range 0..{maximum}")
    return value


def validate_preset(data: Any) -> None:
    """Raise ``PresetError`` unless ``data`` is a complete strict preset."""
    if not isinstance(data, dict):
        raise PresetError("preset must be a JSON object")
    expected_keys = {"format", "global", "encoders"}
    if set(data) != expected_keys:
        raise PresetError(
            "preset must contain exactly the keys: format, global, encoders"
        )
    if data["format"] != FORMAT:
        raise PresetError(f"format must be {FORMAT!r}")
    _validate_byte_list(data["global"], length=12, label="global")
    _validate_field_ranges(data["global"], GLOBAL_FIELDS, label="global")
    encoders = data["encoders"]
    if not isinstance(encoders, list) or len(encoders) != TOTAL_ENCODERS:
        raise PresetError(
            f"encoders must contain exactly {TOTAL_ENCODERS} encoder arrays"
        )
    for flat_index, encoder in enumerate(encoders):
        _validate_byte_list(
            encoder,
            length=15,
            label=f"encoders[{flat_index}]",
        )
        _validate_field_ranges(
            encoder,
            ENCODER_FIELDS,
            label=f"encoders[{flat_index}]",
        )


def _default_encoder(bank: int, position: int) -> list[int]:
    flat_index = bank * NUM_ENCODERS + position
    active, inactive, detent = DEFAULT_COLORS[bank]
    return [
        0,
        0,
        0,
        1,
        flat_index,
        1,
        0,
        flat_index,
        1,
        active,
        inactive,
        detent,
        2,
        0,
        4,
    ]


class Preset:
    """A complete preset with canonical defaults."""

    def __init__(self, global_values: list[int], encoders: list[list[int]]) -> None:
        self._global = deepcopy(global_values)
        self._encoders = deepcopy(encoders)

    @classmethod
    def defaults(cls) -> Preset:
        return cls(
            GLOBAL_DEFAULTS,
            [
                _default_encoder(bank, position)
                for bank in range(NUM_BANKS)
                for position in range(NUM_ENCODERS)
            ],
        )

    def to_dict(self) -> dict[str, Any]:
        """Return an independent JSON-ready copy."""
        return {
            "format": FORMAT,
            "global": deepcopy(self._global),
            "encoders": deepcopy(self._encoders),
        }

    def update_global(self, **fields: int | _MidiChannel) -> Preset:
        """Update globals by name; channel values require ``user_channel``."""
        updates: list[tuple[int, int]] = []
        for name, value in fields.items():
            try:
                field_index = GLOBAL_FIELD_INDEX[name]
            except KeyError as exc:
                raise PresetError(f"unknown global field: {name}") from exc
            updates.append(
                (
                    field_index,
                    _field_value(
                        value,
                        GLOBAL_FIELDS[field_index],
                        label="global",
                    ),
                )
            )
        for field_index, value in updates:
            self._global[field_index] = value
        return self

    def update_encoder(
        self,
        *,
        bank: int,
        position: int,
        **fields: int | _MidiChannel,
    ) -> Preset:
        """Update one encoder; channel values require ``user_channel``."""
        bank = _index(bank, label="bank", maximum=NUM_BANKS - 1)
        position = _index(
            position,
            label="position",
            maximum=NUM_ENCODERS - 1,
        )
        updates: list[tuple[int, int]] = []
        for name, value in fields.items():
            try:
                field_index = ENCODER_FIELD_INDEX[name]
            except KeyError as exc:
                raise PresetError(f"unknown encoder field: {name}") from exc
            updates.append(
                (
                    field_index,
                    _field_value(
                        value,
                        ENCODER_FIELDS[field_index],
                        label="encoder",
                    ),
                )
            )
        encoder = self._encoders[bank * NUM_ENCODERS + position]
        for field_index, value in updates:
            encoder[field_index] = value
        return self

    def update_encoders(
        self,
        *,
        bank: int,
        positions: list[int] | tuple[int, ...] | range,
        per_encoder: (
            Mapping[str, list[Any] | tuple[Any, ...] | range] | None
        ) = None,
        **shared_fields: int | _MidiChannel,
    ) -> Preset:
        """Update a group from shared fields and position-aligned sequences."""
        bank = _index(bank, label="bank", maximum=NUM_BANKS - 1)
        if per_encoder is None:
            per_encoder = {}
        if not isinstance(per_encoder, Mapping):
            raise PresetError("per_encoder must be a mapping")
        if not shared_fields and not per_encoder:
            raise PresetError("provide at least one encoder field")
        overlapping_fields = set(shared_fields).intersection(per_encoder)
        if overlapping_fields:
            name = sorted(overlapping_fields)[0]
            raise PresetError(f"{name} cannot be both shared and per_encoder")
        if not isinstance(positions, (list, tuple, range)):
            raise PresetError("positions must be a list, tuple, or range")
        if not positions:
            raise PresetError("positions must contain at least one position")
        normalized_positions = [
            _index(
                position,
                label=f"positions[{offset}]",
                maximum=NUM_ENCODERS - 1,
            )
            for offset, position in enumerate(positions)
        ]
        if len(set(normalized_positions)) != len(normalized_positions):
            raise PresetError("positions must contain unique indexes")
        shared_updates: list[tuple[int, int]] = []
        for name, value in shared_fields.items():
            try:
                field_index = ENCODER_FIELD_INDEX[name]
            except KeyError as exc:
                raise PresetError(f"unknown encoder field: {name}") from exc
            shared_updates.append(
                (
                    field_index,
                    _field_value(
                        value,
                        ENCODER_FIELDS[field_index],
                        label="encoder",
                    ),
                )
            )
        sequenced_updates: list[tuple[int, list[int]]] = []
        for name, values in per_encoder.items():
            try:
                field_index = ENCODER_FIELD_INDEX[name]
            except KeyError as exc:
                raise PresetError(f"unknown encoder field: {name}") from exc
            if not isinstance(values, (list, tuple, range)):
                raise PresetError(
                    f"per_encoder.{name} must be a list, tuple, or range"
                )
            values = list(values)
            if len(values) != len(normalized_positions):
                raise PresetError(
                    f"per_encoder.{name} must contain exactly "
                    f"{len(normalized_positions)} values"
                )
            sequenced_updates.append(
                (
                    field_index,
                    [
                        _field_value(
                            value,
                            ENCODER_FIELDS[field_index],
                            label="encoder",
                        )
                        for value in values
                    ],
                )
            )
        planned_updates = [
            (
                position,
                [
                    *shared_updates,
                    *[
                        (field_index, values[offset])
                        for field_index, values in sequenced_updates
                    ],
                ],
            )
            for offset, position in enumerate(normalized_positions)
        ]
        for position, updates in planned_updates:
            encoder = self._encoders[bank * NUM_ENCODERS + position]
            for field_index, value in updates:
                encoder[field_index] = value
        return self

    def write(self, path: str | Path) -> Path:
        """Validate and atomically write this complete preset."""
        destination = Path(path)
        data = self.to_dict()
        validate_preset(data)
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                "w",
                encoding="utf-8",
                dir=destination.parent,
                prefix=f".{destination.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary:
                temporary_path = Path(temporary.name)
                json.dump(data, temporary, indent=2)
                temporary.write("\n")
                temporary.flush()
                os.fsync(temporary.fileno())
            os.replace(temporary_path, destination)
            temporary_path = None
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
        return destination


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate_parser = subparsers.add_parser(
        "validate",
        help="strictly validate one mft-editor-v1 JSON preset",
    )
    validate_parser.add_argument("path", type=Path)
    args = parser.parse_args(argv)

    if args.command == "validate":
        try:
            validate_file(args.path)
        except (OSError, json.JSONDecodeError, PresetError) as exc:
            print(f"invalid preset: {exc}", file=sys.stderr)
            return 2
        print(f"valid mft-editor-v1 preset: {args.path}")
        return 0
    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
