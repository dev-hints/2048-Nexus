"""
Game-over / win overlay for 2048-Nexus.

A full-screen semi-transparent overlay that fades in and displays
either "You Win!" or "Game Over" with the final score and action buttons.
"""
from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import (
    QEasingCurve, QPropertyAnimation, QRectF, Qt, pyqtSignal,
    pyqtProperty,
)
from PyQt6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QPushButton, QVBoxLayout, QWidget, QLabel, QHBoxLayout

from ui.themes import Theme
from utils.constants import ANIM_OVERLAY_MS, FONT_PRIMARY, FONT_SECONDARY


class GameOverOverlay(QWidget):
    """
    Animated overlay displayed on win or loss.

    Emits:
    - ``restart_requested`` — user clicked Restart
    - ``menu_requested``    — user clicked Main Menu
    """

    restart_requested = pyqtSignal()
    menu_requested = pyqtSignal()

    def __init__(self, theme: Theme, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._theme = theme
        self._alpha: float = 0.0
        self._is_win = False
        self._score = 0

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAutoFillBackground(False)
        self.hide()

        # Build central panel
        self._panel = QWidget(self)
        self._panel.setObjectName("overlayPanel")

        inner = QVBoxLayout(self._panel)
        inner.setSpacing(18)
        inner.setContentsMargins(40, 40, 40, 40)

        self._title_label = QLabel("", self._panel)
        self._title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._score_label = QLabel("", self._panel)
        self._score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn_row = QHBoxLayout()
        self._restart_btn = QPushButton("↺  Restart")
        self._menu_btn = QPushButton("⌂  Main Menu")
        btn_row.addWidget(self._restart_btn)
        btn_row.addWidget(self._menu_btn)

        self._restart_btn.clicked.connect(self.restart_requested)
        self._menu_btn.clicked.connect(self.menu_requested)

        inner.addWidget(self._title_label)
        inner.addWidget(self._score_label)
        inner.addLayout(btn_row)

        self._apply_styles()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_theme(self, theme: Theme) -> None:
        self._theme = theme
        self._apply_styles()

    def show_win(self, score: int) -> None:
        self._is_win = True
        self._score = score
        self._title_label.setText("🏆  You Win!")
        self._score_label.setText(f"Score: {score:,}")
        self._fade_in()

    def show_lose(self, score: int) -> None:
        self._is_win = False
        self._score = score
        self._title_label.setText("💀  Game Over")
        self._score_label.setText(f"Score: {score:,}")
        self._fade_in()

    def hide_overlay(self) -> None:
        self.hide()
        self._alpha = 0.0

    # ------------------------------------------------------------------
    # Animation
    # ------------------------------------------------------------------

    def _get_alpha(self) -> float:
        return self._alpha

    def _set_alpha(self, val: float) -> None:
        self._alpha = val
        self.update()

    alpha_value = pyqtProperty(float, _get_alpha, _set_alpha)

    def _fade_in(self) -> None:
        self.show()
        self.raise_()
        self._resize_panel()
        anim = QPropertyAnimation(self, b"alpha_value", self)
        anim.setDuration(ANIM_OVERLAY_MS)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start()
        self._anim = anim  # keep reference

    # ------------------------------------------------------------------
    # Painting
    # ------------------------------------------------------------------

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Dark semi-transparent background
        bg = QColor(0, 0, 0, int(180 * self._alpha))
        p.fillRect(self.rect(), bg)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._resize_panel()

    def _resize_panel(self) -> None:
        pw, ph = 380, 280
        x = (self.width() - pw) // 2
        y = (self.height() - ph) // 2
        self._panel.setGeometry(x, y, pw, ph)

    # ------------------------------------------------------------------
    # Styling
    # ------------------------------------------------------------------

    def _apply_styles(self) -> None:
        t = self._theme
        accent = t.accent_primary.name()
        bg_str = t.bg_board.name()
        btn_style = f"""
            QPushButton {{
                background: transparent;
                border: 2px solid {accent};
                border-radius: 8px;
                color: {accent};
                font-family: '{FONT_PRIMARY}', '{FONT_SECONDARY}', Arial;
                font-size: 13px;
                font-weight: bold;
                padding: 10px 20px;
            }}
            QPushButton:hover {{
                background: {accent};
                color: #000000;
            }}
        """
        self._restart_btn.setStyleSheet(btn_style)
        self._menu_btn.setStyleSheet(btn_style)

        title_color = "#ffd700" if self._is_win else "#ff4444"
        self._title_label.setStyleSheet(
            f"color: {title_color}; font-family: '{FONT_PRIMARY}', Arial; "
            f"font-size: 32px; font-weight: bold;"
        )
        self._score_label.setStyleSheet(
            f"color: {t.hud_text.name()}; font-family: '{FONT_SECONDARY}', Arial; font-size: 18px;"
        )
        self._panel.setStyleSheet(
            f"#overlayPanel {{ background: {bg_str}; border-radius: 20px; "
            f"border: 2px solid {accent}; }}"
        )
