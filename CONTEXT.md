# MFT Editor

A Linux-first community editor for the DJ TechTools MIDI Fighter Twister, shipped as a
PySide6 desktop app and a Svelte web app sharing one byte-exact protocol layer.

## Language

**Upstream**:
DJ TechTools' official releases for the Twister — the firmware and the Midi Fighter Utility (MFU). Not the open-source firmware repo specifically, which can lag shipping firmware.
_Avoid_: vendor, official editor (ambiguous with MFU)

**Legacy firmware**:
Any Twister firmware up to and including the 2024-era builds whose source is published in `DJ-TechTools/Midi_Fighter_Twister_Open_Source`. The firmware mft-editor's protocol layer is currently built against.

**2026 firmware**:
The closed-source `20260601` firmware released 2026-06-01 alongside MFU 2.91. Adds config fields and enum values whose SysEx encoding is not yet publicly documented.

**Firmware date**:
The Twister's version identifier — a year/month/day triple reported in the standard MIDI Device Identity Response. The discriminator MFU 2.91 uses to gate features per device.
_Avoid_: firmware version number (there is no semver; the date is the version)

**Sparse push**:
The Twister config-push semantics: a push updates only the tags included in the message; omitted tags keep their stored (EEPROM) values. Verified in legacy firmware source; assumed-not-guaranteed on 2026 firmware.
