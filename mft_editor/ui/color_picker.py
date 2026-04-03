"""Color palette widget — 126-color HSL ring matching firmware color map."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QRectF
from PySide6.QtGui import QPainter, QColor, QBrush, QPen
from PySide6.QtWidgets import (
    QWidget, QGridLayout, QSizePolicy, QVBoxLayout, QHBoxLayout,
    QLabel,
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
        self.setFixedSize(16, 16)
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
            painter.setPen(QPen(QColor(50, 50, 50), 1))
        painter.drawRoundedRect(rect, 2, 2)
        painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.index)


class ColorPalette(QWidget):
    """Grid of 128 color swatches arranged in a wide, compact grid."""

    color_selected = Signal(int)  # emits color index

    def __init__(self, parent=None):
        super().__init__(parent)
        self._swatches: dict[int, ColorSwatch] = {}
        self._current = 0

        layout = QGridLayout(self)
        layout.setSpacing(1)
        layout.setContentsMargins(0, 0, 0, 0)

        # Layout all 128 colors in a wide grid (18 columns)
        cols = 18
        # Off swatch (index 0) and white (127) bookend the palette
        for i in range(128):
            row = i // cols
            col = i % cols
            sw = ColorSwatch(i)
            sw.clicked.connect(self._on_clicked)
            layout.addWidget(sw, row, col)
            self._swatches[i] = sw

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


class _ColorModeButton(QWidget):
    """Clickable color mode selector showing label + current color preview."""

    clicked = Signal(str)

    def __init__(self, mode: str, label: str, parent=None):
        super().__init__(parent)
        self._mode = mode
        self._label = label
        self._color = QColor(0, 0, 0)
        self._active = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(32)
        self.setMinimumWidth(80)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_color(self, color_index: int):
        r, g, b = COLOR_MAP[color_index & 0x7F]
        self._color = QColor(r, g, b)
        self.update()

    def set_active(self, active: bool):
        self._active = active
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        rect = QRectF(0.5, 0.5, w - 1, h - 1)

        # Background
        if self._active:
            painter.setBrush(QBrush(QColor(55, 55, 55)))
            painter.setPen(QPen(QColor(180, 180, 180), 1))
        else:
            painter.setBrush(QBrush(QColor(35, 35, 35)))
            painter.setPen(QPen(QColor(60, 60, 60), 1))
        painter.drawRoundedRect(rect, 4, 4)

        # Color preview square
        swatch_size = 16
        swatch_y = (h - swatch_size) / 2
        swatch_x = 8
        swatch_rect = QRectF(swatch_x, swatch_y, swatch_size, swatch_size)
        painter.setBrush(QBrush(self._color))
        painter.setPen(QPen(QColor(80, 80, 80), 1))
        painter.drawRoundedRect(swatch_rect, 2, 2)

        # Label text
        text_color = QColor(220, 220, 220) if self._active else QColor(150, 150, 150)
        painter.setPen(text_color)
        text_rect = QRectF(swatch_x + swatch_size + 6, 0, w - swatch_x - swatch_size - 14, h)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter, self._label)

        painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._mode)


class ColorPickerPanel(QWidget):
    """Color picker with Active/Inactive/Detent mode selectors showing current colors."""

    color_changed = Signal(str, int)  # ("active"|"inactive"|"detent", color_index)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._mode = "active"
        self._active = 0
        self._inactive = 0
        self._detent = 0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        # Mode selector buttons with color previews
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(4)

        self._btn_active = _ColorModeButton("active", "Active")
        self._btn_inactive = _ColorModeButton("inactive", "Inactive")
        self._btn_detent = _ColorModeButton("detent", "Detent")
        self._btn_active.set_active(True)

        for btn in (self._btn_active, self._btn_inactive, self._btn_detent):
            btn.clicked.connect(self._on_mode_clicked)
            btn_layout.addWidget(btn)

        layout.addLayout(btn_layout)

        # Color palette
        self._palette = ColorPalette()
        self._palette.color_selected.connect(self._on_color_selected)
        layout.addWidget(self._palette)

    def _on_mode_clicked(self, mode: str):
        self._mode = mode
        self._btn_active.set_active(mode == "active")
        self._btn_inactive.set_active(mode == "inactive")
        self._btn_detent.set_active(mode == "detent")
        # Update palette selection to show the color for this mode
        colors = {"active": self._active, "inactive": self._inactive, "detent": self._detent}
        self._palette.set_color(colors[mode])

    def _on_color_selected(self, index: int):
        # Update stored color and mode button preview
        if self._mode == "active":
            self._active = index
            self._btn_active.set_color(index)
        elif self._mode == "inactive":
            self._inactive = index
            self._btn_inactive.set_color(index)
        else:
            self._detent = index
            self._btn_detent.set_color(index)
        self.color_changed.emit(self._mode, index)

    def set_colors(self, active: int, inactive: int, detent: int):
        """Update all color previews and palette selection for current mode."""
        self._active = active
        self._inactive = inactive
        self._detent = detent
        self._btn_active.set_color(active)
        self._btn_inactive.set_color(inactive)
        self._btn_detent.set_color(detent)
        # Show the palette selection for current mode
        colors = {"active": active, "inactive": inactive, "detent": detent}
        self._palette.set_color(colors[self._mode])
