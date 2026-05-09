# Example presets

Sample `mft-editor-v1` JSON presets you can import via **File → Import Settings…** in the desktop editor or the **Load…** button in the web editor.

| File | Description |
|------|-------------|
| `dj-mapping.json` | A four-bank DJ mapping (Bank 1: 16 CCs ch 1, Banks 2–4: per-channel EFX bus layout). |

## Format

```jsonc
{
  "format": "mft-editor-v1",
  "global":   [12 ints],          // see GlobalConfig.to_bytes()
  "encoders": [[15 ints] x 64]    // see EncoderConfig.to_bytes(), bank-major order
}
```

Field order matches the firmware structs — see `mft_editor/model/config.py` and `web/packages/core/src/model.ts` for the canonical layout.
