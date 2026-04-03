"""Import/export device configuration as JSON or binary .mfs files."""

from __future__ import annotations

import json
from pathlib import Path

from ..model.config import DeviceConfig, EncoderConfig, GlobalConfig, TOTAL_ENCODERS
from ..midi.sysex import ENC_TAG_OFFSET, ENC_CFG_SIZE

# Global config: tag-to-field-index mapping (mirrors sysex._GLOBAL_TAG_REVERSE)
_GLOBAL_TAG_TO_FIELD = {
    0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8, 9: 9,
    31: 10, 32: 11,
}

# Fields that are MIDI channels (transmitted as value+1 in SysEx / .mfs)
_GLOBAL_CHANNEL_FIELDS = {0}
_ENC_CHANNEL_FIELDS = {3, 6, 14}


def export_config(config: DeviceConfig, path: str | Path):
    """Export a DeviceConfig to a JSON file."""
    data = {
        "format": "mft-editor-v1",
        "global": config.global_config.to_bytes(),
        "encoders": [enc.to_bytes() for enc in config.encoders],
    }
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def import_config(path: str | Path) -> DeviceConfig:
    """Import a DeviceConfig from a JSON or binary .mfs file."""
    path = Path(path)
    raw = path.read_bytes()

    # Try JSON first; fall back to binary .mfs
    if _looks_like_json(raw):
        return _import_json(raw)
    return _import_mfs(raw)


def _looks_like_json(data: bytes) -> bool:
    """Check if data starts with a JSON object (skipping whitespace/BOM)."""
    text = data.lstrip(b"\xef\xbb\xbf")  # strip UTF-8 BOM
    for b in text:
        if b in (0x20, 0x09, 0x0A, 0x0D):  # whitespace
            continue
        return b == ord("{")
    return False


def _import_json(raw: bytes) -> DeviceConfig:
    data = json.loads(raw)
    config = DeviceConfig()
    if "global" in data:
        config.global_config = GlobalConfig.from_bytes(data["global"])
    if "encoders" in data:
        for i, enc_data in enumerate(data["encoders"][:TOTAL_ENCODERS]):
            config.encoders[i] = EncoderConfig.from_bytes(enc_data)
    return config


def _import_mfs(raw: bytes) -> DeviceConfig:
    """Parse a binary .mfs file (MF Utility settings dump).

    Format:
      - 2-byte header: [0x00, global_data_size]
      - global_data_size bytes of tag-value pairs (global tags 0-9/31-32,
        plus encoder tags 10-24 which we ignore here)
      - 64 encoder blocks, each:
          [0x00, encoder_tag, 0x01, 0x00, payload_size, ...payload]
        where payload is tag-value pairs (tags 10-24)

    MIDI channel values are stored as value+1 (SysEx convention) and
    converted back to 0-15 during parsing.
    """
    buf = raw
    pos = 0

    if len(buf) < 2:
        raise ValueError("File too short to be a valid .mfs file")

    # -- Global config --
    _marker = buf[pos]; pos += 1
    global_data_size = buf[pos]; pos += 1

    global_values = [0] * 12
    end = pos + global_data_size
    if end > len(buf):
        raise ValueError("Global data extends past end of file")

    while pos + 1 < end:
        tag = buf[pos]; pos += 1
        val = buf[pos]; pos += 1
        if tag in _GLOBAL_TAG_TO_FIELD:
            field_idx = _GLOBAL_TAG_TO_FIELD[tag]
            if field_idx in _GLOBAL_CHANNEL_FIELDS:
                val = max(val - 1, 0)
            global_values[field_idx] = val
        # encoder tags (10-24) in the global section are ignored

    config = DeviceConfig()
    config.global_config = GlobalConfig.from_bytes(global_values)

    # -- Encoder blocks --
    while pos + 5 <= len(buf):
        block_marker = buf[pos]
        if block_marker != 0x00:
            break
        enc_tag = buf[pos + 1]
        # bytes 2-3 are part/total (always 01 00 for single-part)
        payload_size = buf[pos + 4]
        pos += 5

        if pos + payload_size > len(buf):
            break

        # Decode tag-value pairs into encoder field values
        enc_values = [0] * ENC_CFG_SIZE
        p = pos
        p_end = pos + payload_size
        while p + 1 < p_end:
            stag = buf[p]; p += 1
            sval = buf[p]; p += 1
            field_idx = stag - ENC_TAG_OFFSET
            if 0 <= field_idx < ENC_CFG_SIZE:
                if field_idx in _ENC_CHANNEL_FIELDS:
                    sval = max(sval - 1, 0)
                enc_values[field_idx] = sval
        pos = p_end

        # Map encoder tag to flat index: tag = bank*16 + encoder + 1
        flat_idx = enc_tag - 1
        if 0 <= flat_idx < TOTAL_ENCODERS:
            config.encoders[flat_idx] = EncoderConfig.from_bytes(enc_values)

    return config
