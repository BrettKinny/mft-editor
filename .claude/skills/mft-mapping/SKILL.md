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
3. Generate a valid JSON file and write it to the path the user specifies, or default to `./mapping.json` in the current working directory.
4. Briefly summarize what was generated (banks used, notable settings).

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
| 0   | midi_channel       | 0-15  | 3       | Base MIDI channel (0-indexed; displayed as ch 1-16 in most DAWs) |
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
| 3   | switch_midi_channel        | 0-15  | 1             | Push button MIDI channel |
| 4   | switch_midi_number         | 0-127 | flat_index    | Push button CC/Note number |
| 5   | switch_midi_type           | 0-5   | 1 (CC)        | Push button MIDI message type |
| 6   | encoder_midi_channel       | 0-15  | 0             | Encoder rotation MIDI channel |
| 7   | encoder_midi_number        | 0-127 | flat_index    | Encoder rotation CC/Note number |
| 8   | encoder_midi_type          | 0-5   | 1 (CC)        | Encoder rotation MIDI message type |
| 9   | active_color               | 0-127 | bank-dependent | LED color when active |
| 10  | inactive_color             | 0-127 | bank-dependent | LED color when inactive |
| 11  | detent_color               | 0-127 | 63            | LED color at detent |
| 12  | indicator_display_type     | 0-3   | 2             | Ring display mode |
| 13  | is_super_knob              | 0-1   | 0             | Part of super knob group |
| 14  | encoder_shift_midi_channel | 0-15  | 4             | Shift modifier MIDI channel |

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

When the user describes their mapping, follow this approach:

1. **Start from defaults.** For any encoder the user doesn't mention, use the default config for that bank:
   ```
   [0, 0, 0, 1, FLAT_INDEX, 1, 0, FLAT_INDEX, 1, ACTIVE, INACTIVE, 63, 2, 0, 4]
   ```
   where FLAT_INDEX = bank*16 + position, and ACTIVE/INACTIVE come from the bank defaults above.

2. **Map user descriptions to field values.** Common patterns:
   - "CC 20 on channel 1" -> encoder_midi_number=20, encoder_midi_channel=0 (0-indexed!)
   - "Note 60" -> encoder_midi_type=0 (Note), encoder_midi_number=60
   - "Toggle button" -> switch_action_type=1 (CC Toggle)
   - "Red color" -> active_color=84
   - "Relative encoder" -> encoder_midi_type=2

3. **MIDI channels are 0-indexed internally.** When the user says "channel 1", use value 0. "Channel 10" = value 9.

4. **Always output all 64 encoders.** Even if only bank 0 is configured, fill banks 1-3 with defaults.

5. **Write valid JSON** with `"format": "mft-editor-v1"` and proper structure.

## Example: Simple DJ Mapping (Bank 0 Only)

User says: "4 volume faders on top row (CC 7-10 ch1), 4 EQ knobs on row 2 (CC 20-23 ch1), 4 effect sends on row 3 (CC 24-27 ch1), 4 filter knobs on bottom row (CC 28-31 ch1). All blue active, dark inactive."

This translates to:
- Encoders 0-3: CC 7-10, channel 0, active_color=1 (blue), inactive_color=0 (off)
- Encoders 4-7: CC 20-23, same colors
- Encoders 8-11: CC 24-27, same colors
- Encoders 12-15: CC 28-31, same colors
- Banks 1-3: defaults
