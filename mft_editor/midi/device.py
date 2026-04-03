"""Real MIDI device discovery and communication via python-rtmidi."""

from __future__ import annotations

import time
import logging
from typing import Protocol

import rtmidi
import mido

from ..model.config import DeviceConfig, NUM_BANKS, NUM_ENCODERS
from . import sysex

log = logging.getLogger(__name__)

DEVICE_NAME_PATTERN = "Midi Fighter Twister"
SYSEX_START = 0xF0
SYSEX_END = 0xF7


class MidiTransport(Protocol):
    """Protocol for MIDI send/receive (real or mock)."""
    name: str
    firmware_version: str
    connected: bool

    def send(self, data: list[int]) -> None: ...
    def receive(self) -> list[int] | None: ...
    def receive_all(self) -> list[list[int]]: ...


def find_mft_ports() -> list[str]:
    """Return list of MIDI port names that match the MFT."""
    midi_in = rtmidi.MidiIn()
    ports = []
    for i, name in enumerate(midi_in.get_ports()):
        if DEVICE_NAME_PATTERN.lower() in name.lower():
            ports.append(name)
    del midi_in
    return ports


class RealDevice:
    """Communicates with a physical MFT over USB MIDI."""

    def __init__(self, port_name: str):
        self._port_name = port_name
        self._midi_out = mido.open_output(port_name)  # type: ignore[arg-type]
        self._midi_in = mido.open_input(port_name)  # type: ignore[arg-type]
        self.connected = True
        self._firmware_version = "Unknown"
        self._name = port_name

    @property
    def name(self) -> str:
        return self._name

    @property
    def firmware_version(self) -> str:
        return self._firmware_version

    def send(self, data: list[int]):
        """Send a SysEx message. `data` is the payload (no F0/F7)."""
        msg = mido.Message("sysex", data=data)
        self._midi_out.send(msg)

    def receive(self, timeout: float = 0.5) -> list[int] | None:
        """Receive a single SysEx message, or None on timeout."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            msg = self._midi_in.poll()
            if msg is not None and msg.type == "sysex":
                return list(msg.data)
            time.sleep(0.005)
        return None

    def receive_all(self, timeout: float = 0.5) -> list[list[int]]:
        """Receive all available SysEx messages within timeout."""
        messages = []
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            msg = self._midi_in.poll()
            if msg is not None and msg.type == "sysex":
                messages.append(list(msg.data))
                deadline = time.monotonic() + 0.1  # extend slightly
            else:
                time.sleep(0.005)
        return messages

    def close(self):
        self.connected = False
        self._midi_out.close()
        self._midi_in.close()


def pull_device_config(device: MidiTransport) -> DeviceConfig:
    """Pull the complete configuration from the device."""
    config = DeviceConfig()

    # Pull global config
    device.send(sysex.build_pull_global())
    time.sleep(0.05)
    resp = device.receive()
    if resp:
        result = sysex.identify_message(resp)
        if result and result[0] == sysex.CMD_PUSH_CONF:
            config.global_config = sysex.parse_push_global(result[1])

    # Pull all 64 encoder configs
    for bank in range(NUM_BANKS):
        for enc in range(NUM_ENCODERS):
            device.send(sysex.build_bulk_pull_encoder(bank, enc))
            time.sleep(0.02)
            responses = device.receive_all(timeout=0.3)
            # Accumulate multi-part payload
            payload: list[int] = []
            for resp in responses:
                result = sysex.identify_message(resp)
                if result and result[0] == sysex.CMD_BULK_XFER:
                    bulk_data = result[1]
                    if len(bulk_data) >= 5 and bulk_data[0] == sysex.BULK_PUSH:
                        size = bulk_data[4]
                        payload.extend(bulk_data[5 : 5 + size])
            if payload:
                enc_cfg = sysex.parse_encoder_payload(payload)
                config.set_encoder(bank, enc, enc_cfg)

    return config


def push_device_config(device: MidiTransport, config: DeviceConfig):
    """Push the complete configuration to the device."""
    # Push global config
    device.send(sysex.build_push_global(config.global_config))
    time.sleep(0.05)

    # Push all 64 encoder configs
    for bank in range(NUM_BANKS):
        for enc in range(NUM_ENCODERS):
            cfg = config.get_encoder(bank, enc)
            messages = sysex.build_bulk_push_encoder(bank, enc, cfg)
            for msg in messages:
                device.send(msg)
                time.sleep(0.02)
