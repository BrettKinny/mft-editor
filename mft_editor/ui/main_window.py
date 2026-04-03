"""Main window: menu bar, device info, central layout with all panels."""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QTabWidget,
    QPushButton, QStatusBar, QMenuBar, QMessageBox, QFileDialog,
    QLabel, QToolBar, QComboBox, QSplitter,
)

from ..model.config import DeviceConfig, NUM_ENCODERS, NUM_BANKS
from ..midi.mock import MockDevice
from ..midi.device import find_mft_ports, RealDevice, pull_device_config, push_device_config
from ..midi import sysex
from ..io.preset_file import export_config, import_config

from .device_view import DeviceView
from .encoder_settings import EncoderSettingsPanel
from .global_settings import GlobalSettingsPanel
from .color_picker import ColorPickerPanel
from .indicator_preview import IndicatorPreview
from .multi_edit import MultiEditPanel, apply_to_multiple

log = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MIDI Fighter Twister Editor")
        self.setMinimumSize(1000, 700)

        self._config = DeviceConfig()
        self._device = None  # MidiTransport or None
        self._current_bank = 0
        self._current_encoder = 0

        self._build_menu()
        self._build_toolbar()
        self._build_ui()
        self._build_statusbar()

        # Start in mock mode
        self._connect_mock()
        self._refresh_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_menu(self):
        menu = self.menuBar()

        file_menu = menu.addMenu("&File")

        import_act = QAction("&Import Settings...", self)
        import_act.triggered.connect(self._on_import)
        file_menu.addAction(import_act)

        export_act = QAction("&Export Settings...", self)
        export_act.triggered.connect(self._on_export)
        file_menu.addAction(export_act)

        file_menu.addSeparator()
        quit_act = QAction("&Quit", self)
        quit_act.triggered.connect(self.close)
        file_menu.addAction(quit_act)

        tools_menu = menu.addMenu("&Tools")

        factory_act = QAction("Factory &Reset", self)
        factory_act.triggered.connect(self._on_factory_reset)
        tools_menu.addAction(factory_act)

        bootloader_act = QAction("Enter &Bootloader", self)
        bootloader_act.triggered.connect(self._on_bootloader)
        tools_menu.addAction(bootloader_act)

        device_menu = menu.addMenu("&Device")

        connect_act = QAction("&Connect to Device", self)
        connect_act.triggered.connect(self._on_connect)
        device_menu.addAction(connect_act)

        mock_act = QAction("Use &Mock Device", self)
        mock_act.triggered.connect(self._connect_mock)
        device_menu.addAction(mock_act)

        pull_act = QAction("&Pull Config from Device", self)
        pull_act.triggered.connect(self._on_pull)
        device_menu.addAction(pull_act)

    def _build_toolbar(self):
        toolbar = QToolBar("Main")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # Bank selector
        toolbar.addWidget(QLabel(" Bank: "))
        self._bank_combo = QComboBox()
        self._bank_combo.addItems(["Bank 1", "Bank 2", "Bank 3", "Bank 4"])
        self._bank_combo.currentIndexChanged.connect(self._on_bank_changed)
        toolbar.addWidget(self._bank_combo)

        toolbar.addSeparator()

        # Send button
        send_btn = QPushButton("Send to Midi Fighter")
        send_btn.setStyleSheet("QPushButton { background-color: #2a6e2a; color: white; "
                               "padding: 6px 16px; font-weight: bold; }")
        send_btn.clicked.connect(self._on_push)
        toolbar.addWidget(send_btn)

        toolbar.addSeparator()

        # Pull button
        pull_btn = QPushButton("Pull from Device")
        pull_btn.clicked.connect(self._on_pull)
        toolbar.addWidget(pull_btn)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        # Left panel: settings tabs
        left_panel = QTabWidget()
        left_panel.setMinimumWidth(320)
        left_panel.setMaximumWidth(400)

        self._encoder_panel = EncoderSettingsPanel()
        self._encoder_panel.config_changed.connect(self._on_encoder_config_changed)
        left_panel.addTab(self._encoder_panel, "Encoder")

        self._global_panel = GlobalSettingsPanel()
        self._global_panel.config_changed.connect(self._on_global_config_changed)
        left_panel.addTab(self._global_panel, "Global")

        self._multi_panel = MultiEditPanel()
        left_panel.addTab(self._multi_panel, "Multi-Edit")

        main_layout.addWidget(left_panel)

        # Right panel: device view + color picker + preview
        right = QVBoxLayout()

        # Device view (4x4 grid)
        self._device_view = DeviceView()
        self._device_view.encoder_selected.connect(self._on_encoder_selected)
        right.addWidget(self._device_view, stretch=4)

        # Bottom: color picker + indicator preview
        bottom = QHBoxLayout()

        self._color_picker = ColorPickerPanel()
        self._color_picker.color_changed.connect(self._on_color_changed)
        bottom.addWidget(self._color_picker, stretch=1)

        self._indicator_preview = IndicatorPreview()
        bottom.addWidget(self._indicator_preview)

        right.addLayout(bottom, stretch=0)
        main_layout.addLayout(right, stretch=1)

    def _build_statusbar(self):
        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._device_label = QLabel("No device")
        self._status.addPermanentWidget(self._device_label)

    # ------------------------------------------------------------------
    # Device connection
    # ------------------------------------------------------------------

    def _connect_mock(self):
        mock = MockDevice(self._config.copy())
        self._device = mock
        self._device_label.setText(f"Connected: {mock.name}")
        self._status.showMessage("Using mock device (offline mode)", 3000)

    @Slot()
    def _on_connect(self):
        ports = find_mft_ports()
        if not ports:
            QMessageBox.warning(self, "No Device Found",
                                "Could not find a MIDI Fighter Twister.\n"
                                "Make sure it is connected via USB.")
            return
        try:
            dev = RealDevice(ports[0])
            self._device = dev
            self._device_label.setText(f"Connected: {dev.name}")
            self._status.showMessage("Connected to device", 3000)
            self._on_pull()
        except Exception as e:
            QMessageBox.critical(self, "Connection Error", str(e))

    # ------------------------------------------------------------------
    # Pull / Push
    # ------------------------------------------------------------------

    @Slot()
    def _on_pull(self):
        if self._device is None:
            return
        self._status.showMessage("Pulling configuration from device...")
        try:
            self._config = pull_device_config(self._device)
            self._refresh_ui()
            self._status.showMessage("Configuration loaded from device", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Pull Error", str(e))
            self._status.showMessage("Pull failed", 3000)

    @Slot()
    def _on_push(self):
        if self._device is None:
            return
        self._status.showMessage("Sending configuration to device...")
        try:
            push_device_config(self._device, self._config)
            self._status.showMessage("Configuration sent to device", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Push Error", str(e))
            self._status.showMessage("Send failed", 3000)

    # ------------------------------------------------------------------
    # Bank / encoder selection
    # ------------------------------------------------------------------

    @Slot(int)
    def _on_bank_changed(self, bank: int):
        self._current_bank = bank
        self._refresh_ui()

    @Slot(int)
    def _on_encoder_selected(self, index: int):
        self._current_encoder = index
        self._load_encoder_to_ui()

    def _load_encoder_to_ui(self):
        enc = self._config.get_encoder(self._current_bank, self._current_encoder)
        self._encoder_panel.set_title(self._current_encoder, self._current_bank)
        self._encoder_panel.load_config(enc)
        self._color_picker.set_colors(enc.active_color, enc.inactive_color, enc.detent_color)
        self._indicator_preview.set_display_type(enc.indicator_display_type)
        self._indicator_preview.set_colors(enc.active_color, enc.inactive_color)

    # ------------------------------------------------------------------
    # Config change handlers
    # ------------------------------------------------------------------

    @Slot()
    def _on_encoder_config_changed(self):
        new_cfg = self._encoder_panel.save_config()
        old_cfg = self._config.get_encoder(self._current_bank, self._current_encoder)
        # Preserve colors (managed by color picker)
        new_cfg.active_color = old_cfg.active_color
        new_cfg.inactive_color = old_cfg.inactive_color
        new_cfg.detent_color = old_cfg.detent_color
        self._config.set_encoder(self._current_bank, self._current_encoder, new_cfg)
        self._indicator_preview.set_display_type(new_cfg.indicator_display_type)

    @Slot()
    def _on_global_config_changed(self):
        self._config.global_config = self._global_panel.save_config()

    @Slot(str, int)
    def _on_color_changed(self, mode: str, color_index: int):
        enc = self._config.get_encoder(self._current_bank, self._current_encoder)
        if mode == "active":
            enc.active_color = color_index
        elif mode == "inactive":
            enc.inactive_color = color_index
        elif mode == "detent":
            enc.detent_color = color_index
        self._device_view.update_colors(self._config, self._current_bank)
        self._indicator_preview.set_colors(enc.active_color, enc.inactive_color)

    # ------------------------------------------------------------------
    # Import / Export
    # ------------------------------------------------------------------

    @Slot()
    def _on_import(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Settings", "",
            "MFT Settings (*.json *.mfs);;All Files (*)")
        if path:
            try:
                self._config = import_config(path)
                self._refresh_ui()
                self._status.showMessage(f"Imported settings from {path}", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Import Error", str(e))

    @Slot()
    def _on_export(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Settings", "mft_config.json",
            "JSON Files (*.json);;All Files (*)")
        if path:
            try:
                export_config(self._config, path)
                self._status.showMessage(f"Exported settings to {path}", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Export Error", str(e))

    # ------------------------------------------------------------------
    # System commands
    # ------------------------------------------------------------------

    @Slot()
    def _on_factory_reset(self):
        reply = QMessageBox.question(
            self, "Factory Reset",
            "This will reset ALL settings on the device to factory defaults.\n\nContinue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes and self._device:
            self._device.send(sysex.build_system_factory_reset())
            self._status.showMessage("Factory reset sent", 3000)

    @Slot()
    def _on_bootloader(self):
        reply = QMessageBox.question(
            self, "Enter Bootloader",
            "This will put the device into bootloader mode for firmware updates.\n\nContinue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes and self._device:
            self._device.send(sysex.build_system_bootloader())
            self._status.showMessage("Bootloader mode activated", 3000)

    # ------------------------------------------------------------------
    # Refresh
    # ------------------------------------------------------------------

    def _refresh_ui(self):
        """Reload all UI from current config state."""
        self._device_view.update_colors(self._config, self._current_bank)
        self._load_encoder_to_ui()
        self._global_panel.load_config(self._config.global_config)
