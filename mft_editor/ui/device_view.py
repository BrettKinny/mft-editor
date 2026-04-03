"""4x4 encoder grid visualization — clickable to select encoders."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QRectF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush
from PySide6.QtWidgets import QWidget, QGridLayout, QSizePolicy

from ..model.config import DeviceConfig, NUM_ENCODERS
from ..model.color_map import COLOR_MAP


class EncoderKnob(QWidget):
    """Single encoder knob widget — circular, shows current color."""

    clicked = Signal(int)  # emits encoder index (0-15)

    def __init__(self, index: int, parent=None):
        super().__init__(parent)
        self.index = index
        self._color = QColor(0, 0, 0)
        self._selected = False
        self.setMinimumSize(50, 50)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_color(self, color_index: int):
        r, g, b = COLOR_MAP[color_index & 0x7F]
        self._color = QColor(r, g, b)
        self.update()

    def set_selected(self, selected: bool):
        self._selected = selected
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        size = min(self.width(), self.height()) - 6
        x = (self.width() - size) / 2
        y = (self.height() - size) / 2
        rect = QRectF(x, y, size, size)

        # Draw knob body (dark circle)
        painter.setBrush(QBrush(QColor(40, 40, 40)))
        if self._selected:
            painter.setPen(QPen(QColor(255, 255, 255), 2.5))
        else:
            painter.setPen(QPen(QColor(80, 80, 80), 1))
        painter.drawEllipse(rect)

        # Draw color ring (indicator)
        ring_rect = rect.adjusted(4, 4, -4, -4)
        painter.setPen(QPen(self._color, 3))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(ring_rect)

        # Draw center indicator dot
        center_size = size * 0.2
        center_rect = QRectF(
            self.width() / 2 - center_size / 2,
            self.height() / 2 - center_size / 2,
            center_size, center_size,
        )
        painter.setBrush(QBrush(self._color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(center_rect)

        # Label
        painter.setPen(QColor(180, 180, 180))
        painter.drawText(rect, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
                         str(self.index + 1))

        painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.index)


class DeviceView(QWidget):
    """4x4 grid of encoder knobs with bank tabs."""

    encoder_selected = Signal(int)  # emits encoder index (0-15)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._knobs: list[EncoderKnob] = []
        self._selected_index = 0

        layout = QGridLayout(self)
        layout.setSpacing(8)

        for i in range(NUM_ENCODERS):
            row = i // 4
            col = i % 4
            knob = EncoderKnob(i)
            knob.clicked.connect(self._on_knob_clicked)
            layout.addWidget(knob, row, col)
            self._knobs.append(knob)

        self._knobs[0].set_selected(True)

    def _on_knob_clicked(self, index: int):
        self._knobs[self._selected_index].set_selected(False)
        self._selected_index = index
        self._knobs[index].set_selected(True)
        self.encoder_selected.emit(index)

    def update_colors(self, config: DeviceConfig, bank: int):
        """Refresh all knob colors from config."""
        for i in range(NUM_ENCODERS):
            enc = config.get_encoder(bank, i)
            self._knobs[i].set_color(enc.active_color)

    @property
    def selected_index(self) -> int:
        return self._selected_index

    def set_selected(self, index: int):
        self._on_knob_clicked(index)
