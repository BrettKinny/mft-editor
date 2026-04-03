"""Color palette widget — 126-color HSL ring matching firmware color map."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QRectF
from PySide6.QtGui import QPainter, QColor, QBrush, QPen
from PySide6.QtWidgets import (
    QWidget, QGridLayout, QLabel, QSizePolicy, QVBoxLayout, QHBoxLayout,
    QGroupBox,
)

from ..model.color_map import COLOR_MAP


class ColorSwatch(QWidget):
    """Single clickable color swatch."""

    clicked = Signal(int)

    def __init__(self, index: int, parent=None):
        super().__init__(parent)
        self.index = index
        r, g, b = COLOR_MAP[index]
        self._color = QColor(r, g, b)
        self._selected = False
        self.setFixedSize(18, 18)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(f"Color {index}")

    def set_selected(self, selected: bool):
        self._selected = selected
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(1, 1, self.width() - 2, self.height() - 2)
        painter.setBrush(QBrush(self._color))
        if self._selected:
            painter.setPen(QPen(QColor(255, 255, 255), 2))
        else:
            painter.setPen(QPen(QColor(60, 60, 60), 1))
        painter.drawRect(rect)
        painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.index)


class ColorPalette(QWidget):
    """Grid of 126 color swatches (indices 1-126), plus off (0) and white (127)."""

    color_selected = Signal(int)  # emits color index

    def __init__(self, parent=None):
        super().__init__(parent)
        self._swatches: dict[int, ColorSwatch] = {}
        self._current = 0

        layout = QGridLayout(self)
        layout.setSpacing(2)
        layout.setContentsMargins(4, 4, 4, 4)

        # Off swatch (index 0)
        sw = ColorSwatch(0)
        sw.clicked.connect(self._on_clicked)
        layout.addWidget(sw, 0, 0)
        self._swatches[0] = sw

        # Color swatches 1-126 in a grid (9 columns)
        cols = 9
        for i in range(1, 127):
            row = (i - 1) // cols + 1
            col = (i - 1) % cols
            sw = ColorSwatch(i)
            sw.clicked.connect(self._on_clicked)
            layout.addWidget(sw, row, col)
            self._swatches[i] = sw

        # White swatch (index 127)
        sw = ColorSwatch(127)
        sw.clicked.connect(self._on_clicked)
        last_row = (126 - 1) // cols + 2
        layout.addWidget(sw, last_row, 0)
        self._swatches[127] = sw

    def _on_clicked(self, index: int):
        if self._current in self._swatches:
            self._swatches[self._current].set_selected(False)
        self._current = index
        self._swatches[index].set_selected(True)
        self.color_selected.emit(index)

    def set_color(self, index: int):
        """Set current selection without emitting signal."""
        if self._current in self._swatches:
            self._swatches[self._current].set_selected(False)
        self._current = index
        if index in self._swatches:
            self._swatches[index].set_selected(True)


class ColorPickerPanel(QWidget):
    """Color picker with Active/Inactive/Detent selector tabs."""

    color_changed = Signal(str, int)  # ("active"|"inactive"|"detent", color_index)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._mode = "active"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Mode selector buttons
        btn_layout = QHBoxLayout()
        self._btn_active = _make_mode_btn("Active Color")
        self._btn_inactive = _make_mode_btn("Inactive Color")
        self._btn_detent = _make_mode_btn("Detent Color")
        self._btn_active.setChecked(True)

        self._btn_active.clicked.connect(lambda: self._set_mode("active"))
        self._btn_inactive.clicked.connect(lambda: self._set_mode("inactive"))
        self._btn_detent.clicked.connect(lambda: self._set_mode("detent"))

        btn_layout.addWidget(self._btn_active)
        btn_layout.addWidget(self._btn_inactive)
        btn_layout.addWidget(self._btn_detent)
        layout.addLayout(btn_layout)

        # Color palette
        self._palette = ColorPalette()
        self._palette.color_selected.connect(self._on_color_selected)
        layout.addWidget(self._palette)

    def _set_mode(self, mode: str):
        self._mode = mode
        self._btn_active.setChecked(mode == "active")
        self._btn_inactive.setChecked(mode == "inactive")
        self._btn_detent.setChecked(mode == "detent")

    def _on_color_selected(self, index: int):
        self.color_changed.emit(self._mode, index)

    def set_colors(self, active: int, inactive: int, detent: int):
        """Update the palette selection to match current encoder."""
        if self._mode == "active":
            self._palette.set_color(active)
        elif self._mode == "inactive":
            self._palette.set_color(inactive)
        else:
            self._palette.set_color(detent)
        # Store all for mode switching
        self._active = active
        self._inactive = inactive
        self._detent = detent

    def set_mode_and_update(self, mode: str):
        self._set_mode(mode)
        colors = {"active": self._active, "inactive": self._inactive, "detent": self._detent}
        self._palette.set_color(colors.get(mode, 0))


def _make_mode_btn(text: str):
    from PySide6.QtWidgets import QPushButton
    btn = QPushButton(text)
    btn.setCheckable(True)
    btn.setFixedHeight(28)
    return btn
