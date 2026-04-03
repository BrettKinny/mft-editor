"""Visual preview of indicator display types (Dot/Bar/BlendedBar/BlendedDot)."""

from __future__ import annotations

import math

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter, QColor, QPen, QConicalGradient
from PySide6.QtWidgets import QWidget

from ..model.enums import DisplayType
from ..model.color_map import COLOR_MAP


class IndicatorPreview(QWidget):
    """Shows a ring-style indicator matching the MFT's LED ring behavior."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._display_type = DisplayType.BLENDED_BAR
        self._active_color_idx = 25
        self._inactive_color_idx = 113
        self._value = 80  # 0-127 simulated position
        self.setFixedSize(100, 100)

    def set_display_type(self, dt: int):
        self._display_type = dt
        self.update()

    def set_colors(self, active: int, inactive: int):
        self._active_color_idx = active
        self._inactive_color_idx = inactive
        self.update()

    def set_value(self, val: int):
        self._value = val
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx, cy = self.width() / 2, self.height() / 2
        radius = min(cx, cy) - 6
        arc_width = 4.0

        r_a, g_a, b_a = COLOR_MAP[self._active_color_idx & 0x7F]
        r_i, g_i, b_i = COLOR_MAP[self._inactive_color_idx & 0x7F]
        active = QColor(r_a, g_a, b_a)
        inactive = QColor(r_i, g_i, b_i)

        # Background circle
        painter.setPen(QPen(QColor(30, 30, 30), 1))
        painter.setBrush(QColor(25, 25, 25))
        painter.drawEllipse(QRectF(cx - radius, cy - radius, radius * 2, radius * 2))

        # LED ring — 11 segments spread across ~270 degrees
        num_leds = 11
        start_angle = 225  # degrees, bottom-left
        sweep = 270  # total arc
        frac = self._value / 127.0
        active_leds = int(frac * num_leds)

        for i in range(num_leds):
            angle = math.radians(start_angle - (i / (num_leds - 1)) * sweep)
            lx = cx + (radius - 3) * math.cos(angle)
            ly = cy - (radius - 3) * math.sin(angle)

            dt = self._display_type
            if dt == DisplayType.BAR:
                color = active if i <= active_leds else inactive
            elif dt == DisplayType.DOT:
                color = active if i == active_leds else inactive
            elif dt == DisplayType.BLENDED_BAR:
                if i <= active_leds:
                    t = i / max(active_leds, 1)
                    color = _blend(inactive, active, t)
                else:
                    color = inactive
            elif dt == DisplayType.BLENDED_DOT:
                if i == active_leds:
                    color = active
                else:
                    dist = abs(i - active_leds)
                    t = max(0, 1 - dist / 3)
                    color = _blend(inactive, active, t)
            else:
                color = inactive

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            painter.drawEllipse(QRectF(lx - arc_width, ly - arc_width,
                                       arc_width * 2, arc_width * 2))

        painter.end()


def _blend(c1: QColor, c2: QColor, t: float) -> QColor:
    """Linear blend between two colors."""
    return QColor(
        int(c1.red() + (c2.red() - c1.red()) * t),
        int(c1.green() + (c2.green() - c1.green()) * t),
        int(c1.blue() + (c2.blue() - c1.blue()) * t),
    )
