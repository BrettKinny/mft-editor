"""Global settings panel — MIDI channel, side buttons, brightness, etc."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget, QFormLayout, QCheckBox, QComboBox, QSpinBox, QGroupBox,
    QVBoxLayout, QSlider, QLabel,
)
from PySide6.QtCore import Qt

from ..model.config import GlobalConfig
from ..model.enums import SideSwAction

_SIDE_SW_LABELS = [
    "CC Hold", "CC Toggle", "Note Hold", "Note Toggle",
    "Shift Page 1", "Shift Page 2",
    "Bank Up", "Bank Down",
    "Bank 1", "Bank 2", "Bank 3", "Bank 4",
    "Cycle Bank",
]


class GlobalSettingsPanel(QWidget):
    """Form for editing global device settings."""

    config_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._updating = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        title = QLabel("Global Settings")
        title.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(title)

        # MIDI
        midi_group = QGroupBox("MIDI")
        midi_form = QFormLayout(midi_group)
        self._midi_channel = QSpinBox()
        self._midi_channel.setRange(1, 16)
        midi_form.addRow("MIDI Channel:", self._midi_channel)
        layout.addWidget(midi_group)

        # Side buttons
        side_group = QGroupBox("Side Buttons")
        side_form = QFormLayout(side_group)

        self._side_banked = QCheckBox("Bank Side Buttons")
        side_form.addRow(self._side_banked)

        self._side_funcs: list[QComboBox] = []
        for i in range(6):
            combo = QComboBox()
            combo.addItems(_SIDE_SW_LABELS)
            side_form.addRow(f"Button {i + 1}:", combo)
            self._side_funcs.append(combo)

        layout.addWidget(side_group)

        # Super Knob
        super_group = QGroupBox("Super Knob")
        super_form = QFormLayout(super_group)
        self._super_start = QSpinBox()
        self._super_start.setRange(0, 127)
        super_form.addRow("Start Value:", self._super_start)
        self._super_end = QSpinBox()
        self._super_end.setRange(0, 127)
        super_form.addRow("End Value:", self._super_end)
        layout.addWidget(super_group)

        # Brightness
        bright_group = QGroupBox("Brightness")
        bright_form = QFormLayout(bright_group)

        self._rgb_brightness = QSlider(Qt.Orientation.Horizontal)
        self._rgb_brightness.setRange(0, 127)
        bright_form.addRow("RGB Brightness:", self._rgb_brightness)

        self._ind_brightness = QSlider(Qt.Orientation.Horizontal)
        self._ind_brightness.setRange(0, 127)
        bright_form.addRow("Indicator Brightness:", self._ind_brightness)

        layout.addWidget(bright_group)
        layout.addStretch()

        # Connect signals
        self._midi_channel.valueChanged.connect(self._on_changed)
        self._side_banked.toggled.connect(self._on_changed)
        for combo in self._side_funcs:
            combo.currentIndexChanged.connect(self._on_changed)
        self._super_start.valueChanged.connect(self._on_changed)
        self._super_end.valueChanged.connect(self._on_changed)
        self._rgb_brightness.valueChanged.connect(self._on_changed)
        self._ind_brightness.valueChanged.connect(self._on_changed)

    def _on_changed(self):
        if not self._updating:
            self.config_changed.emit()

    def load_config(self, cfg: GlobalConfig):
        self._updating = True
        self._midi_channel.setValue(cfg.midi_channel + 1)
        self._side_banked.setChecked(bool(cfg.side_is_banked))
        funcs = [cfg.side_func_1, cfg.side_func_2, cfg.side_func_3,
                 cfg.side_func_4, cfg.side_func_5, cfg.side_func_6]
        for combo, val in zip(self._side_funcs, funcs):
            combo.setCurrentIndex(val)
        self._super_start.setValue(cfg.super_knob_start)
        self._super_end.setValue(cfg.super_knob_end)
        self._rgb_brightness.setValue(cfg.rgb_brightness)
        self._ind_brightness.setValue(cfg.ind_brightness)
        self._updating = False

    def save_config(self) -> GlobalConfig:
        return GlobalConfig(
            midi_channel=self._midi_channel.value() - 1,
            side_is_banked=int(self._side_banked.isChecked()),
            side_func_1=self._side_funcs[0].currentIndex(),
            side_func_2=self._side_funcs[1].currentIndex(),
            side_func_3=self._side_funcs[2].currentIndex(),
            side_func_4=self._side_funcs[3].currentIndex(),
            side_func_5=self._side_funcs[4].currentIndex(),
            side_func_6=self._side_funcs[5].currentIndex(),
            super_knob_start=self._super_start.value(),
            super_knob_end=self._super_end.value(),
            rgb_brightness=self._rgb_brightness.value(),
            ind_brightness=self._ind_brightness.value(),
        )
