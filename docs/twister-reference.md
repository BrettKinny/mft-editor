# Midi Fighter Twister — Protocol & Hardware Reference

Distilled from the official DJ TechTools *Midi Fighter Twister User Guide v1.01* and the
DJ TechTools Zendesk help articles. This is the reference for building/validating mappings
in this repo — channel and CC numbers here are the *defaults from firmware*, and the
hardware's color/animation inputs described below are hard-wired to channels 1 and 2 and
**cannot be remapped**.

Sources:
- [User Guide v1.01 (PDF)](https://r2.gear4music.com/media/19/196749/download_196749.pdf)
- [Zendesk section index](https://techtools.zendesk.com/hc/en-us/sections/200468434-Midi-Fighter-Twister)
- [Channel settings article](https://techtools.zendesk.com/hc/en-us/articles/16809770523917-Midi-Fighter-Twister-channel-settings)
- [Super Knob article](https://techtools.zendesk.com/hc/en-us/articles/115000366966-How-do-I-map-the-Super-Knobs-for-my-Twister)
- [App Guide](https://techtools.zendesk.com/hc/en-us/articles/7002462346893-Midi-Fighter-Twister-App-Guide)

Channels throughout are 0-indexed (0–15), matching the guide and the MF Utility.

## Hardware overview

- 16 endless rotary encoders, each with an integrated push switch.
- Each encoder has:
  - 11 white LEDs around the ring (current value / position).
  - A large RGB segment at the 6 o'clock position (switch state / color).
  - A red/blue LED indicating detent state.
- 6 side buttons (3 left, 3 right).
- 4 virtual banks → up to 64 unique encoder+switch controls.
- USB bus-powered, class-compliant MIDI.

## MIDI channel map (firmware defaults)

| Purpose                                | Channel |
|----------------------------------------|---------|
| Encoder rotation (value out)           | 0       |
| Encoder switch (press)                 | 1       |
| RGB segment color override (MIDI in)   | 1       |
| RGB segment animation override (in)    | 2       |
| Side buttons & bank change notes       | 3       |

Encoder rotation, switch, color-in and animation-in all share the **same CC/note number**
per encoder — e.g. encoder 1 bank 1 is CC 0 on ch 0 (rotation), CC 0 on ch 1 (switch and
color-in), CC 0 on ch 2 (animation-in).

**Important:** if you remap an encoder or encoder-switch's MIDI channel/number away from
default, the color and animation inputs do **not** follow. They stay on the original
ch1/ch2 + original CC number. Keep this in mind when editing mappings — custom remaps
can break per-encoder LED feedback.

Also: MIDI OUT (display sync) cannot be remapped. To sync an encoder's LED display to a
DAW parameter, send the parameter's MIDI out to the same CC on channel 0.

## Encoder default MIDI (all 4 banks)

Encoder rotation: channel 0. Encoder switch: channel 1. Switch default type: CC
(can be changed to Note; Note column shown for reference).

### Bank 1
| Encoder | Enc CC | Switch CC | Switch Note |
|---------|--------|-----------|-------------|
| 1       | 0      | 0         | C-1         |
| 2       | 1      | 1         | C#-1        |
| 3       | 2      | 2         | D-1         |
| 4       | 3      | 3         | D#-1        |
| 5       | 4      | 4         | E-1         |
| 6       | 5      | 5         | F-1         |
| 7       | 6      | 6         | F#-1        |
| 8       | 7      | 7         | G-1         |
| 9       | 8      | 8         | G#-1        |
| 10      | 9      | 9         | A-1         |
| 11      | 10     | 10        | A#-1        |
| 12      | 11     | 11        | B-1         |
| 13      | 12     | 12        | C0          |
| 14      | 13     | 13        | C#0         |
| 15      | 14     | 14        | D0          |
| 16      | 15     | 15        | D#0         |

### Bank 2
Encoders use CC 16–31 (and switch CC 16–31, notes E0–G1).

### Bank 3
Encoders use CC 32–47 (and switch CC 32–47, notes G#1–B2).
Note: the guide's table has a one-off oddity — encoders 6–16 in bank 3 show
switch CCs 38–47 (skipping 37) while the encoder-rotation CCs run 37–47 normally.
Treat the user guide PDF as authoritative if this matters; the utility's factory
reset is the ground truth.

### Bank 4
Encoders use CC 48–63 (and switch CC 48–63, notes C3–D#4).

## Side buttons (channel 3)

| Button           | Bank 1 CC / Note | Bank 2 CC / Note | Bank 3 CC / Note | Bank 4 CC / Note |
|------------------|------------------|------------------|------------------|------------------|
| Left Side 1      | 8 / G#-1         | 14 / D0          | 20 / G#0         | 26 / D1          |
| Left Side 2      | 9 / A-1          | 15 / D#0         | 21 / A0          | 27 / D#1         |
| Left Side 3      | 10 / A#-1        | 16 / E0          | 22 / A#0         | 28 / E1          |
| Right Side 1     | 11 / B-1         | 17 / F0          | 23 / B0          | 29 / F1          |
| Right Side 2     | 12 / C0          | 18 / F#0         | 24 / C1          | 30 / F#1         |
| Right Side 3     | 13 / C#0         | 19 / G0          | 25 / C#1         | 31 / G1          |

Side buttons only change per-bank when the **Bank Side Buttons** global option is
enabled. If disabled, they send the same MIDI regardless of bank.

## Bank change notifications (channel 3)

The Twister announces bank changes by sending a Note Off for the previous bank and a
Note On for the new bank on channel 3. You can also *force* a bank by sending a Note On.

| Bank | Note   |
|------|--------|
| 1    | C-1    |
| 2    | C#-1   |
| 3    | D-1    |
| 4    | D#-1   |

Example: changing from bank 1 → bank 2, the Twister sends `Ch3 NoteOff C-1`
then `Ch3 NoteOn C#-1`.

## Encoder switch action types

- **CC Hold** — CC 127 on press, CC 0 on release.
- **CC Toggle** — alternates CC 127 / CC 0 on each press.
- **Note Hold** — NoteOn vel 127 on press, NoteOff vel 0 on release.
- **Note Toggle** — alternates NoteOn / NoteOff.
- **Reset Encoder Value** — resets encoder to 0 (or 64 if detent is on). Also sends CC
  hold messages while pressed.
- **Encoder Fine Adjust** — while pressed, sensitivity drops for fine control.
- **Shift Encoder Hold** — while pressed, encoder sends a secondary value; lets one
  encoder control two parameters.
- **Shift Encoder Toggle** — press toggles between primary and secondary (shift)
  encoder values.

## Encoder MIDI types

- **Note** — NoteOn where velocity = encoder value.
- **CC** — absolute CC.
- **Enc 3FH/41H** — relative CC: value 65 per clockwise step, value 63 per
  anti-clockwise step.

## Per-encoder settings

- **Enable Detent** — behaves like a pot with center detent. LED starts from the middle.
  At 50% (MIDI 64) the indicator LED changes color.
- **Detent Color** — controls the red↔blue LED. 0 = red, 127 = blue, interpolated in
  between.
- **Sensitivity** — *Responsive* (270° sweep = full 0–127) or *High Resolution*.
- **Indicator Type** — Dot, Bar, or Blended Bar (leading LED fades for smooth feedback).
- **Enable Super Knob** — see below.
- **Encoder Switch Action Type** — see list above.
- **Encoder & Switch MIDI Number / Channel** — overrides per bank. Warning: remapping
  breaks hardware LED feedback routing (see channel map note).

## Super Knob

Per-encoder flag. When enabled, the encoder sends a *secondary* CC over a range
bounded by the **Super Knob Start Point** and **End Point** — both **global** settings
that apply to *every* Super Knob-enabled encoder.

Below the start point, only the primary CC is sent. Between start and end, the encoder
sends the secondary CC. This lets a single knob e.g. drive dry/wet for the first half
of its travel and feedback for the second half.

When MIDI-learning the secondary mapping in your DAW, rotate only within the upper
range (past the start point) so only the secondary CC is seen.

## RGB segment color override (MIDI in, channel 1)

Send a Note or CC on **channel 1** with the same number as the encoder's switch to
override the encoder's RGB segment color:

- Value **0** → force inactive color (configured off-color).
- Value **127** → force active color (configured on-color).
- Values **1–126** → select a color along the full 128-step spectrum.

## Animation override (MIDI in, channel 2)

Send a Note or CC on **channel 2** with the same number as the encoder to set an
animation. Animations *modify* the current color; color and animation can be set
independently.

| Value | Animation    | Rate                                 |
|-------|--------------|--------------------------------------|
| 0     | None         | —                                    |
| 1     | Gate (strobe)| every 4 beats                        |
| 2     | Gate         | every 2 beats                        |
| 3     | Gate         | every beat                           |
| 4     | Gate         | every 1/2 beat                       |
| 5     | Gate         | every 1/4 beat                       |
| 6     | Gate         | every 1/8 beat                       |
| 7     | Gate         | every 1/16 beat                      |
| 8     | Gate         | every 1/32 beat                      |
| 9     | Pulse        | brightness cycles over 16 beats      |
| 10    | Pulse        | brightness cycles over 8 beats       |
| 11    | Pulse        | brightness cycles over 4 beats       |
| 12    | Pulse        | brightness cycles over 2 beats       |
| 13    | Pulse        | brightness cycles every beat         |
| 14    | Pulse        | brightness cycles every 1/2 beat     |
| 15    | Pulse        | brightness cycles every 1/4 beat     |
| 16    | Pulse        | brightness cycles every 1/8 beat     |
| 127   | Rainbow Cycle| fixed 4-beat cycle                   |

Gate/Pulse rates follow incoming MIDI clock if present; otherwise they fall back to a
120 BPM (1/2 second beat) reference.

Example: yellow flashing at 1/2 beat on encoder 1 → first send `Ch1 CC0 val 64` (color),
then `Ch2 CC0 val 4` (animation).

## Side button action types (global settings)

Same four base modes as encoder switches (CC Hold, CC Toggle, Note Hold, Note Toggle),
plus bank / shift actions:

- **Shift Page A / Shift Page B** — while held, encoder switches send a modified set of
  MIDI (effectively giving two extra banks of buttons). In shift state, encoder ring
  LEDs reflect the shifted switch state — map MIDI output to the same note/channel the
  switch sends to drive those LEDs.
- **Next Bank** — bank += 1 (no wrap).
- **Previous Bank** — bank −= 1 (no wrap).
- **Cycle Bank** — bank += 1, wraps 4 → 1.
- **Bank 1 / 2 / 3 / 4** — jump to a specific bank.

Defaults: middle-left side button = previous bank, middle-right = next bank.

## Global settings summary

- **Super Knob Start Point / End Point** — the value thresholds shared by all Super
  Knob-enabled encoders.
- **Bank Side Buttons** — when on, side buttons have per-bank MIDI; when off, they send
  the same MIDI in every bank.
- **Side Button Functions** — one of the actions listed above, per button.

## Utility workflow notes

- The MF Utility is the official PC/Mac configuration app. Changes only take effect
  after clicking **Send to Midi Fighter**.
- **Import / Export Settings** writes/reads a settings file, but you still have to
  press *Send to Midi Fighter* after importing.
- **Factory reset**: `Tools → Midi Fighter → Factory Reset`.
- **Firmware updates** must be done with the device plugged directly into a USB port,
  not a hub — updating over a hub risks bricking.

## Appendix: relevance to this repo

For the editor in this repo, the load-bearing invariants are:
1. Encoder rotation is always ch 0; switch, color-in, and animation-in are always
   ch 1 / ch 1 / ch 2 respectively at the hardware level — editing "switch channel"
   in a mapping only affects *outgoing* switch MIDI, not the incoming LED controls.
2. Default CC layout is contiguous: bank *n* encoder *i* → CC `(n-1)*16 + (i-1)` on
   ch 0. The switch shares the same number on ch 1.
3. Animations 1–8 (gate) and 9–16 (pulse) map to musical divisions; value 127 is
   rainbow; every other value between 17 and 126 is undefined.
4. Super Knob thresholds are **global**, not per-encoder — a UI that exposes them
   per-encoder would be misleading.
