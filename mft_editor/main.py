"""Entry point for the MFT Editor application."""

import sys
import logging

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt

from .ui.main_window import MainWindow


def _apply_dark_theme(app: QApplication):
    """Apply a dark color palette matching DJTT aesthetic."""
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(35, 35, 35))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(208, 208, 208))
    palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(45, 45, 45))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(50, 50, 50))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(208, 208, 208))
    palette.setColor(QPalette.ColorRole.Text, QColor(208, 208, 208))
    palette.setColor(QPalette.ColorRole.Button, QColor(45, 45, 45))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(208, 208, 208))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.Link, QColor(100, 149, 237))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(70, 130, 180))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(100, 100, 100))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(100, 100, 100))
    app.setPalette(palette)
    app.setStyleSheet(
        "QToolTip { color: #d0d0d0; background-color: #323232; border: 1px solid #555; }"
        "QGroupBox { border: 1px solid #555; margin-top: 8px; padding-top: 8px; }"
        "QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }"
    )


def main():
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(name)s %(levelname)s %(message)s")

    app = QApplication(sys.argv)
    app.setApplicationName("MFT Editor")
    app.setOrganizationName("DJTT-Community")

    _apply_dark_theme(app)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
