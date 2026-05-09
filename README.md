# MFT Editor

A Linux-first editor for the [DJ Tech Tools MIDI Fighter Twister](https://store.djtechtools.com/products/midi-fighter-twister) — configure encoders, colours, banks, and side switches without needing Windows or macOS.

![MFT Editor](docs/screenshot.png)

> ## ⚠️ v0.1 — early tester release
>
> This is an **early-tester release**. Expect rough edges, missing polish, and the occasional bug.
>
> - **Tested only on Linux.** Cross-platform support is a goal, not a promise — see the roadmap below.
> - **The web build is experimental.** It runs in Chromium-based browsers (Chrome, Edge, Brave, Arc, Opera) via Web MIDI. Firefox and Safari don't support Web MIDI and won't work.
> - If you try it, please [open an issue](../../issues) for anything weird — that feedback is what gets this to a stable release.
>
> **Hardware safety:** the editor only sends standard config SysEx messages that the official MF Utility also sends. There is no firmware-update or flash-erase code path. The worst-case bad mapping is recoverable via **Tools → Factory Reset**.
>
> **Not affiliated with DJ TechTools.** "MIDI Fighter Twister" and "DJ Tech Tools" are trademarks of DJ TechTools — this is a community project that talks to their hardware over the public MIDI/SysEx interface.

## Why

DJ Tech Tools only ships their official MIDI Fighter Utility for Windows and macOS. This project gives Linux users a native editor, plus a browser-based editor that runs anywhere Web MIDI is supported.

## What's in the box

- **`mft_editor/`** — PySide6 (Qt) desktop editor. Talks to the device over ALSA / `python-rtmidi`. The original Linux editor.
- **`web/packages/app/`** — Svelte + TypeScript web editor sharing a byte-exact configuration protocol with the desktop version. Runs in any Chromium-based browser with Web MIDI.
- **`web/packages/core/`** — Shared protocol layer: encoder / global config types, SysEx encode/decode, colour palette. Used by the web editor and consumable by other tooling.
- **`web/design-mockups/`** — Single-file HTML prototypes exploring the editor's visual direction. The screenshot above is `d-focused.html`.

## Features

- All 16 encoders × 4 banks
- Per-encoder MIDI: separate turn and press, channel, number, and type (Note, CC, Relative Enc, Switch Vel Control, Rel Mouse Drag / Scroll)
- Movement modes (Direct, Responsive, Velocity-Sensitive) and indicator display types (Dot, Bar, Blended Bar, Blended Dot)
- Active / Inactive / Detent colour per encoder from the full 128-colour palette
- Detent flag, super-knob flag, shift-channel routing
- Global settings: MIDI channel, RGB + indicator brightness, side-banked mode, super-knob range
- All 6 side switches with every action the firmware supports (CC/Note Hold & Toggle, Shift Pages, Bank Up/Down/1–4/Cycle)
- Pull current state from the device, push edits back, save/load presets to disk

## Running the desktop editor

Linux only at v0.1. Requires Python 3.10+.

```bash
uv sync
uv run mft-editor
```

Or with plain pip:

```bash
pip install -e .
mft-editor
```

## Running the web editor

Requires Node 18+ and `pnpm`.

```bash
cd web
pnpm install
pnpm dev
```

Open the URL Vite prints and authorise Web MIDI access when prompted. You'll need a Chromium-based browser — Firefox doesn't ship Web MIDI.

## Roadmap toward v1.0

- [ ] Verified macOS + Windows support for the desktop editor
- [ ] Non-blocking device pull (current pull blocks the UI thread for ~10–20 s)
- [ ] Push confirmation prompt + per-encoder progress
- [ ] In-app diagnostics / log file
- [ ] Real-device testing matrix for the web build (Chrome/Edge/Brave verified)

## License

LGPL-3.0-or-later. See [`LICENSE`](LICENSE).
