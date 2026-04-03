"""Per-encoder settings form — all 15 config fields."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget, QFormLayout, QCheckBox, QComboBox, QSpinBox, QGroupBox,
    QVBoxLayout, QLabel,
)

from ..model.config import EncoderConfig
from ..model.enums import DisplayType, EncMoveType, EncSwActionType, MidiType


class EncoderSettingsPanel(QWidget):
    """Form for editing a single encoder's configuration."""

    config_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._updating = False  # guard against feedback loops

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self._title = QLabel("Encoder 1 — Bank 1")
        self._title.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(self._title)

        # --- Encoder section ---
        enc_group = QGroupBox("Encoder")
        enc_form = QFormLayout(enc_group)

        self._detent = QCheckBox()
        enc_form.addRow("Enable Detent:", self._detent)

        self._movement = QComboBox()
        self._movement.addItems(["Direct", "Responsive", "Velocity Sensitive"])
        enc_form.addRow("Sensitivity:", self._movement)

        self._enc_midi_type = QComboBox()
        self._enc_midi_type.addItems(["Note", "CC", "Rel Enc (3Fh/41h)",
                                       "Velocity Control", "Mouse Drag", "Mouse Scroll"])
        enc_form.addRow("MIDI Type:", self._enc_midi_type)

        self._enc_midi_channel = QSpinBox()
        self._enc_midi_channel.setRange(1, 16)
        enc_form.addRow("MIDI Channel:", self._enc_midi_channel)

        self._enc_midi_number = QSpinBox()
        self._enc_midi_number.setRange(0, 127)
        enc_form.addRow("MIDI Number:", self._enc_midi_number)

        self._indicator_type = QComboBox()
        self._indicator_type.addItems(["Dot", "Bar", "Blended Bar", "Blended Dot"])
        enc_form.addRow("Indicator Type:", self._indicator_type)

        self._super_knob = QCheckBox()
        enc_form.addRow("Super Knob:", self._super_knob)

        self._shift_channel = QSpinBox()
        self._shift_channel.setRange(1, 16)
        enc_form.addRow("Shift MIDI Ch:", self._shift_channel)

        layout.addWidget(enc_group)

        # --- Switch section ---
        sw_group = QGroupBox("Switch (Push)")
        sw_form = QFormLayout(sw_group)

        self._sw_action = QComboBox()
        self._sw_action.addItems([
            "CC Hold", "CC Toggle", "Note Hold", "Note Toggle",
            "Reset Encoder Value", "Fine Adjust", "Shift Hold", "Shift Toggle",
        ])
        sw_form.addRow("Switch Action:", self._sw_action)

        self._sw_midi_type = QComboBox()
        self._sw_midi_type.addItems(["Note", "CC", "Rel Enc (3Fh/41h)",
                                      "Velocity Control", "Mouse Drag", "Mouse Scroll"])
        sw_form.addRow("MIDI Type:", self._sw_midi_type)

        self._sw_midi_channel = QSpinBox()
        self._sw_midi_channel.setRange(1, 16)
        sw_form.addRow("MIDI Channel:", self._sw_midi_channel)

        self._sw_midi_number = QSpinBox()
        self._sw_midi_number.setRange(0, 127)
        sw_form.addRow("MIDI Number:", self._sw_midi_number)

        layout.addWidget(sw_group)
        layout.addStretch()

        # Connect change signals
        for widget in [self._detent, self._super_knob]:
            widget.toggled.connect(self._on_changed)
        for widget in [self._movement, self._enc_midi_type, self._indicator_type,
                       self._sw_action, self._sw_midi_type]:
            widget.currentIndexChanged.connect(self._on_changed)
        for widget in [self._enc_midi_channel, self._enc_midi_number,
                       self._sw_midi_channel, self._sw_midi_number,
                       self._shift_channel]:
            widget.valueChanged.connect(self._on_changed)

    def _on_changed(self):
        if not self._updating:
            self.config_changed.emit()

    def set_title(self, encoder: int, bank: int):
        self._title.setText(f"Encoder {encoder + 1} — Bank {bank + 1}")

    def load_config(self, cfg: EncoderConfig):
        """Populate form from an EncoderConfig."""
        self._updating = True
        self._detent.setChecked(bool(cfg.has_detent))
        self._movement.setCurrentIndex(cfg.movement)
        self._enc_midi_type.setCurrentIndex(cfg.encoder_midi_type)
        self._enc_midi_channel.setValue(cfg.encoder_midi_channel + 1)  # 0-15 -> 1-16
        self._enc_midi_number.setValue(cfg.encoder_midi_number)
        self._indicator_type.setCurrentIndex(cfg.indicator_display_type)
        self._super_knob.setChecked(bool(cfg.is_super_knob))
        self._shift_channel.setValue(cfg.encoder_shift_midi_channel + 1)

        self._sw_action.setCurrentIndex(cfg.switch_action_type)
        self._sw_midi_type.setCurrentIndex(cfg.switch_midi_type)
        self._sw_midi_channel.setValue(cfg.switch_midi_channel + 1)
        self._sw_midi_number.setValue(cfg.switch_midi_number)
        self._updating = False

    def save_config(self) -> EncoderConfig:
        """Read form values into an EncoderConfig."""
        return EncoderConfig(
            has_detent=int(self._detent.isChecked()),
            movement=self._movement.currentIndex(),
            switch_action_type=self._sw_action.currentIndex(),
            switch_midi_channel=self._sw_midi_channel.value() - 1,
            switch_midi_number=self._sw_midi_number.value(),
            switch_midi_type=self._sw_midi_type.currentIndex(),
            encoder_midi_channel=self._enc_midi_channel.value() - 1,
            encoder_midi_number=self._enc_midi_number.value(),
            encoder_midi_type=self._enc_midi_type.currentIndex(),
            active_color=0,    # colors managed separately via color picker
            inactive_color=0,
            detent_color=0,
            indicator_display_type=self._indicator_type.currentIndex(),
            is_super_knob=int(self._super_knob.isChecked()),
            encoder_shift_midi_channel=self._shift_channel.value() - 1,
        )
