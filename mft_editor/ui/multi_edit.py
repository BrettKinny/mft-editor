"""Multi-encoder edit mode — select and edit multiple encoders at once."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, QAbstractItemView,
    QPushButton, QHBoxLayout,
)

from ..model.config import DeviceConfig, EncoderConfig, NUM_ENCODERS


class MultiEditPanel(QWidget):
    """Allows selecting multiple encoders in the same bank for batch editing."""

    selection_changed = Signal(list)  # list of encoder indices

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        label = QLabel("Multi-Encoder Select")
        label.setStyleSheet("font-weight: bold;")
        layout.addWidget(label)

        self._list = QListWidget()
        self._list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        for i in range(NUM_ENCODERS):
            self._list.addItem(f"Encoder {i + 1}")
        self._list.itemSelectionChanged.connect(self._on_selection)
        layout.addWidget(self._list)

        btn_layout = QHBoxLayout()
        select_all = QPushButton("Select All")
        select_all.clicked.connect(self._list.selectAll)
        btn_layout.addWidget(select_all)

        clear = QPushButton("Clear")
        clear.clicked.connect(self._list.clearSelection)
        btn_layout.addWidget(clear)
        layout.addLayout(btn_layout)

    def _on_selection(self):
        indices = [idx.row() for idx in self._list.selectedIndexes()]
        self.selection_changed.emit(sorted(indices))

    def selected_indices(self) -> list[int]:
        return sorted(idx.row() for idx in self._list.selectedIndexes())


def apply_to_multiple(config: DeviceConfig, bank: int, indices: list[int],
                      changes: EncoderConfig, fields: list[str]):
    """Apply specific field changes to multiple encoders in the same bank."""
    for idx in indices:
        enc = config.get_encoder(bank, idx)
        for field in fields:
            if hasattr(changes, field) and hasattr(enc, field):
                setattr(enc, field, getattr(changes, field))
