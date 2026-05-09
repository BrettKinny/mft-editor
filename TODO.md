# TODO

Working notes for in-flight work. The user-facing roadmap toward v1.0 lives in [`README.md`](README.md#roadmap-toward-v10).

## Desktop (Python)

- [ ] Move `pull_device_config` off the UI thread (currently blocks Qt for ~10–20 s — see `mft_editor/midi/device.py:97`)
- [ ] Wire `logging` calls into `device.py` and `main_window.py` (loggers exist but are never called)
- [ ] Per-encoder progress signal during push, surfaced in the status bar
- [ ] Verify port discovery on JACK / pipewire / macOS / Windows

## Web

- [ ] In-app About / Help link explaining Web MIDI + browser requirements
- [ ] Decide whether the "Use mock" button should ship to production or be `import.meta.env.DEV`-only
- [ ] Real-device verification on Chrome / Edge / Brave / Arc

## Repo

- [ ] Add a screenshot of the web editor to the README
- [ ] `CHANGELOG.md` once there's anything past 0.1.0 to record
