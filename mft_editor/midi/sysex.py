"""SysEx protocol: build and parse all MFT command types.

Protocol summary:
  Header: F0 00 01 79 [CMD] ... F7
  Commands: 0x01=PUSH_CONF, 0x02=PULL_CONF, 0x03=SYSTEM, 0x04=BULK_XFER
"""

from __future__ import annotations

from ..model.config import EncoderConfig, GlobalConfig, NUM_ENCODERS

# SysEx manufacturer ID bytes (DJ Tech Tools)
MFR_ID = (0x00, 0x01, 0x79)

# Command IDs
CMD_PUSH_CONF = 0x01
CMD_PULL_CONF = 0x02
CMD_SYSTEM = 0x03
CMD_BULK_XFER = 0x04

# System sub-commands
SYS_FACTORY_RESET = 0x02

# Bulk transfer sub-commands
BULK_PUSH = 0x00
BULK_PULL = 0x01

# Encoder config SysEx tag offset (firmware subtracts 10 from tags)
ENC_TAG_OFFSET = 10
ENC_CFG_SIZE = 15
MAX_BULK_PAYLOAD = 30


def _header(cmd: int) -> list[int]:
    """Build SysEx header (without F0/F7 framing — mido adds those)."""
    return [*MFR_ID, cmd]


# ---------------------------------------------------------------------------
# Global config (PUSH_CONF / PULL_CONF)
# ---------------------------------------------------------------------------

# Mapping from GlobalConfig field index to SysEx tag.
# Tags 0-9 are straightforward; tags 10-11 are sent as 31-32 to avoid
# collision with the encoder tag range (10-29).
_GLOBAL_TAG_MAP = {
    0: 0,    # midi_channel
    1: 1,    # side_is_banked
    2: 2,    # side_func_1
    3: 3,    # side_func_2
    4: 4,    # side_func_3
    5: 5,    # side_func_4
    6: 6,    # side_func_5
    7: 7,    # side_func_6
    8: 8,    # super_knob_start
    9: 9,    # super_knob_end
    10: 31,  # rgb_brightness
    11: 32,  # ind_brightness
}

# Reverse map for parsing
_GLOBAL_TAG_REVERSE: dict[int, int] = {v: k for k, v in _GLOBAL_TAG_MAP.items()}


def build_push_global(cfg: GlobalConfig) -> list[int]:
    """Build PUSH_CONF SysEx data for global settings.

    MIDI channels are transmitted as value+1 (1-16).
    """
    data = _header(CMD_PUSH_CONF)
    values = cfg.to_bytes()
    for field_idx, tag in _GLOBAL_TAG_MAP.items():
        val = values[field_idx]
        if field_idx == 0:  # midi_channel: stored 0-15, sent 1-16
            val = val + 1
        data.extend([tag, val & 0x7F])
    return data


def build_pull_global() -> list[int]:
    """Build PULL_CONF request (ask device to send global config)."""
    return _header(CMD_PULL_CONF) + [0x00]


def parse_push_global(data: list[int]) -> GlobalConfig:
    """Parse a PUSH_CONF response into GlobalConfig.

    `data` should be the SysEx payload after the header (after CMD byte).
    """
    values = [0] * 12
    i = 0
    while i + 1 < len(data):
        tag = data[i]
        val = data[i + 1]
        if tag in _GLOBAL_TAG_REVERSE:
            field_idx = _GLOBAL_TAG_REVERSE[tag]
            if field_idx == 0:  # midi_channel: received 1-16, store 0-15
                val = val - 1
            values[field_idx] = val
        i += 2
    return GlobalConfig.from_bytes(values)


# ---------------------------------------------------------------------------
# Encoder config (BULK_XFER)
# ---------------------------------------------------------------------------

def _encoder_tag(bank: int, encoder: int) -> int:
    """Compute the SysEx tag for an encoder: (bank*16) + encoder + 1."""
    return bank * NUM_ENCODERS + encoder + 1


def build_bulk_push_encoder(bank: int, encoder: int, cfg: EncoderConfig) -> list[list[int]]:
    """Build one or more BULK_XFER PUSH messages for an encoder config.

    Returns a list of SysEx data payloads (one per part).
    MIDI channels are transmitted as value+1.
    """
    tag = _encoder_tag(bank, encoder)
    raw = cfg.to_bytes()

    # Build tag-value pairs for the payload
    # Field indices that are MIDI channels: 3 (switch_midi_channel),
    # 6 (encoder_midi_channel), 14 (encoder_shift_midi_channel)
    channel_fields = {3, 6, 14}
    pairs: list[int] = []
    for i in range(ENC_CFG_SIZE):
        sysex_tag = i + ENC_TAG_OFFSET
        val = raw[i]
        if i in channel_fields:
            val = val + 1  # 0-15 -> 1-16 for transmission
        pairs.extend([sysex_tag, val & 0x7F])

    # Split into parts of MAX_BULK_PAYLOAD bytes each
    messages = []
    total_parts = (len(pairs) + MAX_BULK_PAYLOAD - 1) // MAX_BULK_PAYLOAD
    for part_num in range(total_parts):
        start = part_num * MAX_BULK_PAYLOAD
        chunk = pairs[start : start + MAX_BULK_PAYLOAD]
        msg = _header(CMD_BULK_XFER)
        msg.extend([
            BULK_PUSH,
            tag,
            part_num + 1,    # 1-based part number
            total_parts,
            len(chunk),
        ])
        msg.extend(chunk)
        messages.append(msg)
    return messages


def build_bulk_pull_encoder(bank: int, encoder: int) -> list[int]:
    """Build a BULK_XFER PULL request for one encoder."""
    tag = _encoder_tag(bank, encoder)
    return _header(CMD_BULK_XFER) + [BULK_PULL, tag]


def parse_bulk_push_encoder(data: list[int]) -> tuple[int, int, EncoderConfig | None]:
    """Parse a BULK_XFER PUSH message payload.

    `data` = payload after CMD byte: [sub_cmd, tag, part, total, size, ...payload]
    Returns (bank, encoder_index, EncoderConfig or None if incomplete).

    NOTE: This handles single-part messages. For multi-part, the caller should
    accumulate payloads and call parse_encoder_payload() when complete.
    """
    if len(data) < 5:
        return (0, 0, None)

    sub_cmd = data[0]
    tag = data[1]
    part = data[2]
    total = data[3]
    size = data[4]
    payload = data[5 : 5 + size]

    bank = (tag - 1) // NUM_ENCODERS
    encoder = (tag - 1) % NUM_ENCODERS

    if part == total:  # Single or final part
        cfg = parse_encoder_payload(payload)
        return (bank, encoder, cfg)
    return (bank, encoder, None)


def parse_encoder_payload(payload: list[int]) -> EncoderConfig:
    """Parse accumulated tag-value pairs into an EncoderConfig.

    MIDI channels are received as 1-16, stored as 0-15.
    """
    values = [0] * ENC_CFG_SIZE
    channel_fields = {3, 6, 14}
    i = 0
    while i + 1 < len(payload):
        sysex_tag = payload[i]
        val = payload[i + 1]
        field_idx = sysex_tag - ENC_TAG_OFFSET
        if 0 <= field_idx < ENC_CFG_SIZE:
            if field_idx in channel_fields:
                val = val - 1  # 1-16 -> 0-15
            values[field_idx] = val
        i += 2
    return EncoderConfig.from_bytes(values)


# ---------------------------------------------------------------------------
# System commands
# ---------------------------------------------------------------------------

def build_system_factory_reset() -> list[int]:
    """Build SYSTEM command to factory reset."""
    return _header(CMD_SYSTEM) + [SYS_FACTORY_RESET]


# ---------------------------------------------------------------------------
# Message parsing (dispatch)
# ---------------------------------------------------------------------------

def identify_message(data: list[int]) -> tuple[int, list[int]] | None:
    """Check if `data` is a valid DJTT SysEx message.

    `data` = the SysEx payload (F0 and F7 already stripped by mido).
    Returns (command_id, remaining_data) or None if not a DJTT message.
    """
    if len(data) < 4:
        return None
    if tuple(data[:3]) != MFR_ID:
        return None
    cmd = data[3]
    return (cmd, data[4:])
