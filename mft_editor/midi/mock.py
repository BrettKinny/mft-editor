"""Mock MIDI device for offline development and testing."""

from __future__ import annotations

from ..model.config import DeviceConfig, EncoderConfig, GlobalConfig, NUM_ENCODERS, NUM_BANKS
from . import sysex


class MockDevice:
    """In-memory MFT that responds to SysEx like real hardware."""

    def __init__(self, config: DeviceConfig | None = None):
        self.config = config or DeviceConfig()
        self.connected = True
        self._response_queue: list[list[int]] = []
        # Accumulate multi-part bulk transfers: {tag: [payload_bytes]}
        self._bulk_accum: dict[int, list[int]] = {}
        self._bulk_parts_seen: dict[int, int] = {}
        self._bulk_parts_total: dict[int, int] = {}

    @property
    def name(self) -> str:
        return "Mock Midi Fighter Twister"

    @property
    def firmware_version(self) -> str:
        return "Mock 2023-12-17"

    def send(self, data: list[int]):
        """Process an outgoing SysEx message and queue any responses."""
        result = sysex.identify_message(data)
        if result is None:
            return
        cmd, payload = result

        if cmd == sysex.CMD_PULL_CONF:
            self._handle_pull_global()
        elif cmd == sysex.CMD_BULK_XFER:
            self._handle_bulk(payload)
        elif cmd == sysex.CMD_PUSH_CONF:
            self._handle_push_global(payload)

    def receive(self, timeout: float = 0) -> list[int] | None:
        """Pop next queued response, or None."""
        if self._response_queue:
            return self._response_queue.pop(0)
        return None

    def receive_all(self, timeout: float = 0) -> list[list[int]]:
        """Pop all queued responses."""
        msgs = self._response_queue[:]
        self._response_queue.clear()
        return msgs

    def _handle_pull_global(self):
        """Respond to PULL_CONF with current global config."""
        self._response_queue.append(
            sysex.build_push_global(self.config.global_config)
        )

    def _handle_push_global(self, payload: list[int]):
        """Apply PUSH_CONF to our config."""
        self.config.global_config = sysex.parse_push_global(payload)

    def _handle_bulk(self, payload: list[int]):
        """Handle BULK_XFER (push or pull)."""
        if len(payload) < 2:
            return
        sub_cmd = payload[0]
        tag = payload[1]

        bank = (tag - 1) // NUM_ENCODERS
        encoder = (tag - 1) % NUM_ENCODERS

        if sub_cmd == sysex.BULK_PULL:
            # Send back encoder config
            cfg = self.config.get_encoder(bank, encoder)
            msgs = sysex.build_bulk_push_encoder(bank, encoder, cfg)
            self._response_queue.extend(msgs)
        elif sub_cmd == sysex.BULK_PUSH:
            # Accumulate multi-part payloads
            if len(payload) < 5:
                return
            part = payload[2]
            total = payload[3]
            size = payload[4]
            chunk = payload[5:5 + size]

            if tag not in self._bulk_accum:
                self._bulk_accum[tag] = []
                self._bulk_parts_seen[tag] = 0
                self._bulk_parts_total[tag] = total

            self._bulk_accum[tag].extend(chunk)
            self._bulk_parts_seen[tag] += 1

            if self._bulk_parts_seen[tag] >= self._bulk_parts_total[tag]:
                cfg = sysex.parse_encoder_payload(self._bulk_accum[tag])
                self.config.set_encoder(bank, encoder, cfg)
                del self._bulk_accum[tag]
                del self._bulk_parts_seen[tag]
                del self._bulk_parts_total[tag]
