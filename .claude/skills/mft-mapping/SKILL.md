---
name: mft-mapping
description: >
  Generate MFT Editor JSON mapping files for the MIDI Fighter Twister.
  Use when the user describes a MIDI mapping they want — encoder assignments,
  colors, button behaviors, global settings — and you produce a valid
  mft-editor-v1 JSON preset file they can import into the editor.
  Triggers: MIDI mapping, MFT preset, encoder mapping, twister mapping,
  create mapping, generate mapping, mapping file.
---

# MFT Mapping Generator

Generate valid `mft-editor-v1` JSON preset files for the MIDI Fighter Twister
based on the user's description of their desired mapping.

## How to use this skill

1. Read the user's description of the mapping they want.
2. Ask clarifying questions ONLY if critical information is ambiguous (e.g., which bank an encoder is in). For anything not specified, use sensible defaults.
3. Generate the preset with the adjacent `scripts/mft_preset.py` helper. Never hand-write or directly edit the 64 raw encoder arrays.
4. Run the helper's strict validator on the finished file.
5. Briefly summarize what was generated (banks used, notable settings).

## JSON Format

```json
{
  "format": "mft-editor-v1",
  "global": [12 integers],
  "encoders": [
    [15 integers],  // encoder 0 (bank 0, position 0)
    [15 integers],  // encoder 1 (bank 0, position 1)
    ...             // 64 total (16 per bank x 4 banks)
  ]
}
```

**Constraints:**
- `global`: exactly 12 integers, all 0-127
- `encoders`: exactly 64 arrays of exactly 15 integers each, all 0-127
- Encoder ordering: bank 0 encoders 0-15, then bank 1 encoders 0-15, etc.

## Physical Layout

The MFT has a 4x4 grid of encoders (16 total visible at once), with 4 banks switchable via side buttons. Encoders are numbered left-to-right, top-to-bottom:

```
 [0]  [1]  [2]  [3]       Row 1
 [4]  [5]  [6]  [7]       Row 2
 [8]  [9]  [10] [11]      Row 3
 [12] [13] [14] [15]      Row 4
```

Each encoder has a push-button switch and an RGB LED ring indicator.

## Global Config Fields (12 fields, by index)

| Idx | Field              | Range | Default | Notes |
|-----|--------------------|-------|---------|-------|
| 0   | midi_channel       | 0-15  | 3       | Stored byte; named updates require `user_channel(1..16)` |
| 1   | side_is_banked     | 0-1   | 1       | Side buttons affected by banking |
| 2   | side_func_1        | 0-12  | 0       | Left top side button |
| 3   | side_func_2        | 0-12  | 7       | Left middle side button |
| 4   | side_func_3        | 0-12  | 0       | Left bottom side button |
| 5   | side_func_4        | 0-12  | 0       | Right top side button |
| 6   | side_func_5        | 0-12  | 6       | Right middle side button |
| 7   | side_func_6        | 0-12  | 0       | Right bottom side button |
| 8   | super_knob_start   | 0-127 | 63      | Super knob range start |
| 9   | super_knob_end     | 0-127 | 127     | Super knob range end |
| 10  | rgb_brightness     | 0-127 | 127     | RGB LED brightness |
| 11  | ind_brightness     | 0-127 | 127     | Indicator ring brightness |

### Side Button Actions (SideSwAction)

| Value | Action       |
|-------|--------------|
| 0     | CC Hold      |
| 1     | CC Toggle    |
| 2     | Note Hold    |
| 3     | Note Toggle  |
| 4     | Shift Page 1 |
| 5     | Shift Page 2 |
| 6     | Bank Up      |
| 7     | Bank Down    |
| 8     | Bank 1       |
| 9     | Bank 2       |
| 10    | Bank 3       |
| 11    | Bank 4       |
| 12    | Cycle Bank   |

## Encoder Config Fields (15 fields per encoder, by index)

| Idx | Field                      | Range | Default       | Notes |
|-----|----------------------------|-------|---------------|-------|
| 0   | has_detent                 | 0-1   | 0             | Detent (center click) enabled |
| 1   | movement                   | 0-2   | 0             | Encoder sensitivity mode |
| 2   | switch_action_type         | 0-7   | 0             | Push button behavior |
| 3   | switch_midi_channel        | 0-15  | 1             | Stored byte; named updates require `user_channel(1..16)` |
| 4   | switch_midi_number         | 0-127 | flat_index    | Push button CC/Note number |
| 5   | switch_midi_type           | 0-5   | 1 (CC)        | Push button MIDI message type |
| 6   | encoder_midi_channel       | 0-15  | 0             | Stored byte; named updates require `user_channel(1..16)` |
| 7   | encoder_midi_number        | 0-127 | flat_index    | Encoder rotation CC/Note number |
| 8   | encoder_midi_type          | 0-5   | 1 (CC)        | Encoder rotation MIDI message type |
| 9   | active_color               | 0-127 | bank-dependent | LED color when active |
| 10  | inactive_color             | 0-127 | bank-dependent | LED color when inactive |
| 11  | detent_color               | 0-127 | 63            | LED color at detent |
| 12  | indicator_display_type     | 0-3   | 2             | Ring display mode |
| 13  | is_super_knob              | 0-1   | 0             | Part of super knob group |
| 14  | encoder_shift_midi_channel | 0-15  | 4             | Stored byte; named updates require `user_channel(1..16)` |

**flat_index** = bank * 16 + encoder_position (0-63)

### Movement Types (EncMoveType)

| Value | Type               | Description |
|-------|--------------------|-------------|
| 0     | Direct             | Immediate response |
| 1     | Responsive         | Acceleration/emulation |
| 2     | Velocity Sensitive | Speed-dependent |

### Switch Action Types (EncSwActionType)

| Value | Action       | Description |
|-------|--------------|-------------|
| 0     | CC Hold      | CC on while held |
| 1     | CC Toggle    | CC toggles on/off |
| 2     | Note Hold    | Note on while held |
| 3     | Note Toggle  | Note toggles on/off |
| 4     | Reset Value  | Reset encoder to default |
| 5     | Fine Adjust  | Fine-grained control while held |
| 6     | Shift Hold   | Shift modifier while held |
| 7     | Shift Toggle | Shift modifier toggles |

### MIDI Message Types (MidiType)

| Value | Type                | Description |
|-------|---------------------|-------------|
| 0     | Note                | Note on/off messages |
| 1     | CC                  | Control Change (most common) |
| 2     | Rel Enc             | Relative encoder (3Fh/41h) |
| 3     | Velocity Control    | CC with velocity |
| 4     | Mouse Drag          | Relative encoder as mouse drag |
| 5     | Mouse Scroll        | Relative encoder as mouse scroll |

### Indicator Display Types (DisplayType)

| Value | Type         | Description |
|-------|--------------|-------------|
| 0     | Dot          | Single position dot |
| 1     | Bar          | Filled bar from bottom |
| 2     | Blended Bar  | Anti-aliased filled bar (default) |
| 3     | Blended Dot  | Anti-aliased dot |

## Color Palette Reference

Colors are indexed 0-127 into a fixed palette. Approximate color names:

| Index Range | Color        |
|-------------|--------------|
| 0           | Off (black)  |
| 1-10        | Blue         |
| 11-16       | Blue-Cyan    |
| 17-21       | Cyan         |
| 22-25       | Cyan-Teal    |
| 25-32       | Teal-Green   |
| 33-42       | Green (warm) |
| 43-50       | Green (pure) |
| 51-58       | Green-Yellow |
| 59-63       | Yellow-Green |
| 64          | Yellow       |
| 65-68       | Yellow-Orange|
| 69-74       | Orange       |
| 75-83       | Orange-Red   |
| 84-85       | Red (pure)   |
| 86-95       | Red-Pink     |
| 96-100      | Pink-Magenta |
| 101-107     | Magenta      |
| 108-113     | Purple       |
| 114-120     | Purple-Blue  |
| 121-126     | Dark Blue    |
| 127         | White        |

**Common useful colors:**
- Blue: 1, Cyan: 20, Teal: 25, Green: 45, Yellow-Green: 63, Yellow: 64
- Orange: 72, Red: 84, Pink: 96, Magenta: 107, Purple: 113, White: 127, Off: 0

## Default Colors Per Bank

| Bank | Active | Inactive | Detent |
|------|--------|----------|--------|
| 0    | 25 (teal) | 113 (purple) | 63 (yellow-green) |
| 1    | 81 (orange-red) | 63 (yellow-green) | 63 |
| 2    | 25 (teal) | 100 (pink-magenta) | 63 |
| 3    | 25 (teal) | 0 (off) | 63 |

## Generating a Mapping

Use the bundled helper as an importable module. It is self-contained and uses
only the Python standard library, so it also works when this skill is copied to
an otherwise empty workspace.

1. Resolve `scripts/mft_preset.py` relative to this `SKILL.md`.
2. In inline Python, start with `Preset.defaults()`.
3. Apply globals with `update_global(...)`. Use
   `update_encoder(bank=..., position=..., ...)` only for a truly isolated
   encoder.
4. For every repeated mapping, call `update_encoders(...)` once. Put constant
   fields in shared keyword arguments and each varying field in a
   `per_encoder` list, tuple, or range aligned exactly with `positions`. Never
   loop over `update_encoder` or hand-expand repeated configurations into
   literal per-encoder dictionaries.
5. Pass all four named channel fields (`midi_channel`,
   `switch_midi_channel`, `encoder_midi_channel`, and
   `encoder_shift_midi_channel`) through `user_channel(1..16)`. These setters
   reject raw integers, including stored 0-15 values. The marker is consumed
   by the helper and the JSON still contains plain 0-15 integers. Banks and
   encoder positions passed to the helper are zero-indexed.
6. Use the exported enums (`MidiType`, `EncSwActionType`, `EncMoveType`,
   `DisplayType`, `SideSwAction`) instead of memorized numeric enum values.
7. Call `preset.write(...)`; it strictly validates and atomically writes all 12
   global fields and all 64 encoders.
8. Run `python scripts/mft_preset.py validate <output>` against the same helper
   path. Do not modify the JSON afterward.

Use this executable shell/Python shape, defining the change collections
directly in the inline program instead of creating an intermediate file. Set
`HELPER` to the adjacent script's actual path if the skill is installed
somewhere other than the project-local location shown here.

The documented API is complete for generating mappings. Run it directly; do
not inspect or modify the helper unless this documented invocation itself
errors.

```bash
HELPER=".claude/skills/mft-mapping/scripts/mft_preset.py"
OUTPUT="mapping.json"
test -f "$HELPER"

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$(dirname "$HELPER")" OUTPUT="$OUTPUT" python - <<'PY'
import os

from mft_preset import (
    DisplayType,
    EncMoveType,
    EncSwActionType,
    MidiType,
    Preset,
    SideSwAction,
    user_channel,
)

global_changes = {
    # "midi_channel": user_channel(5),
}

preset = Preset.defaults()
preset.update_global(**global_changes)
# Replace these illustrative values with the requested group.
preset.update_encoders(
    bank=0,
    positions=range(4),
    per_encoder={
        "switch_midi_number": range(20, 24),
        "encoder_midi_number": range(70, 74),
    },
    switch_midi_channel=user_channel(2),
    encoder_midi_channel=user_channel(1),
)
preset.write(os.environ["OUTPUT"])
PY

PYTHONDONTWRITEBYTECODE=1 python "$HELPER" validate "$OUTPUT"
```

The grouped helper rejects empty or duplicate positions, nondeterministic
position containers, invalid or out-of-range indexes, unknown or overlapping
fields, non-sequence or wrong-length `per_encoder` values, and unmarked named
channel values. It validates the entire group before applying any mutation.
Final validation also rejects incomplete or malformed `mft-editor-v1` JSON.

## Example: Simple DJ Mapping (Bank 0 Only)

User says: "4 volume faders on top row (CC 7-10 ch1), 4 EQ knobs on row 2 (CC 20-23 ch1), 4 effect sends on row 3 (CC 24-27 ch1), 4 filter knobs on bottom row (CC 28-31 ch1). All blue active, dark inactive."

Express the repeated configuration as one group:

```python
preset.update_encoders(
    bank=0,
    positions=range(16),
    per_encoder={
        "encoder_midi_number": [
            *range(7, 11),
            *range(20, 32),
        ],
    },
    encoder_midi_channel=user_channel(1),
    encoder_midi_type=MidiType.CC,
    active_color=1,
    inactive_color=0,
)
```

Banks 1-3 remain at their defaults.
