"""
QApplication setup and font loading for 2048-Nexus.
"""
from __future__ import annotations

import os
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QFontDatabase, QIcon
from PyQt6.QtWidgets import QApplication

from utils.constants import (
    APP_NAME, APP_ORG, FONTS_DIR, ICONS_DIR,
    FONT_PRIMARY, FONT_SECONDARY,
)


def _load_fonts() -> None:
    """Register custom fonts from assets/fonts/."""
    if not os.path.isdir(FONTS_DIR):
        return
    for fname in os.listdir(FONTS_DIR):
        if fname.lower().endswith((".ttf", ".otf")):
            QFontDatabase.addApplicationFont(os.path.join(FONTS_DIR, fname))


def _set_app_icon(app: QApplication) -> None:
    icon_path = os.path.join(ICONS_DIR, "icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))


def create_app(argv: list[str] | None = None) -> QApplication:
    """
    Create and configure the QApplication.

    Call this exactly once at program startup before creating any widgets.
    """
    if argv is None:
        argv = sys.argv

    # High-DPI support
    app = QApplication(argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(APP_ORG)
    app.setApplicationVersion("1.0.0")

    # Load custom fonts
    _load_fonts()

    # Set default application font
    font = QFont(FONT_SECONDARY, 10)
    app.setFont(font)

    # Set app icon
    _set_app_icon(app)

    return app
