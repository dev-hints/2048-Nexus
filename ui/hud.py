"""
In-game HUD (Heads-Up Display) for 2048-Nexus.

Shows: Mode badge · Current score · Best score · Timer (timed mode)
"""
from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QColor, QFont, QPainter, QPainterPath
from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget,
)

from ui.themes import Theme, get_theme
from utils.constants import FONT_PRIMARY, FONT_SECONDARY, FONT_FALLBACK


class _ScoreBox(QWidget):
    """A small labelled score box (label + value)."""

    def __init__(self, label: str, theme: Theme, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._theme = theme
        self._label = label
        self._value = "0"
        self.setMinimumWidth(90)

    def set_value(self, value: str) -> None:
        self._value = value
        self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()

        # Background pill
        path = QPainterPath()
        path.addRoundedRect(0, 0, rect.width(), rect.height(), 10, 10)
        p.fillPath(path, self._theme.hud_bg)

        # Label
        lf = QFont(FONT_SECONDARY)
        lf.setPointSize(8)
        lf.setBold(False)
        p.setFont(lf)
        p.setPen(self._theme.accent_primary)
        p.drawText(rect.adjusted(0, 4, 0, -rect.height() // 2), Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom, self._label)

        # Value
        vf = QFont(FONT_PRIMARY)
        vf.setPointSize(14)
        vf.setBold(True)
        p.setFont(vf)
        p.setPen(self._theme.hud_text)
        p.drawText(rect.adjusted(0, rect.height() // 2, 0, -4), Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, self._value)


class HUD(QWidget):
    """
    Full HUD bar displayed above the game board.

    Layout::

        [Mode Badge]   [SCORE: xxxxxx]  [BEST: xxxxxx]  [TIME: mm:ss]
    """

    def __init__(self, theme: Theme, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._theme = theme
        self._has_timer = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Mode badge
        self._mode_badge = QWidget()
        badge_layout = QHBoxLayout(self._mode_badge)
        badge_layout.setContentsMargins(8, 4, 8, 4)
        badge_layout.setSpacing(4)

        self._mode_icon = QLabel("")
        self._mode_icon.setObjectName("modeIcon")
        self._mode_icon.setVisible(False)

        self._mode_label = QLabel("Classic")
        self._mode_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._mode_label.setObjectName("modeLabel")

        badge_layout.addWidget(self._mode_icon)
        badge_layout.addWidget(self._mode_label)

        self._style_mode_badge()

        # Score boxes
        self._score_box = _ScoreBox("SCORE", theme)
        self._best_box = _ScoreBox("BEST", theme)
        self._timer_box = _ScoreBox("TIME", theme)
        self._timer_box.setVisible(False)

        layout.addWidget(self._mode_badge)
        layout.addStretch()
        layout.addWidget(self._score_box)
        layout.addWidget(self._best_box)
        layout.addWidget(self._timer_box)
        self.setFixedHeight(72)

    # ------------------------------------------------------------------
    # Update methods
    # ------------------------------------------------------------------

    def set_theme(self, theme: Theme) -> None:
        self._theme = theme
        self._score_box._theme = theme
        self._best_box._theme = theme
        self._timer_box._theme = theme
        self._style_mode_badge()
        self.update()

    def set_mode(self, mode_name: str, has_timer: bool) -> None:
        self._mode_label.setText(mode_name.upper())
        self._has_timer = has_timer
        self._timer_box.setVisible(has_timer)
        if has_timer:
            self._mode_icon.setText("T")
            self._mode_icon.setVisible(True)
        else:
            self._mode_icon.setVisible(False)

    def update_score(self, score: int, best: int) -> None:
        self._score_box.set_value(f"{score:,}")
        self._best_box.set_value(f"{best:,}")

    def update_timer(self, seconds: int) -> None:
        m, s = divmod(seconds, 60)
        self._timer_box.set_value(f"{m:02d}:{s:02d}")

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _style_mode_badge(self) -> None:
        accent = self._theme.accent_primary.name()
        text = self._theme.hud_text.name()
        bg = self._theme.hud_bg.name()
        self._mode_badge.setStyleSheet(
            f"""
            QWidget {{
                color: {accent};
                background: {bg};
                border: 2px solid {accent};
                border-radius: 10px;
            }}
            QLabel#modeIcon {{
                color: {accent};
                font-family: 'Noto Color Emoji', 'Segoe UI Emoji', 'Apple Color Emoji', 'Segoe UI Symbol', '{FONT_PRIMARY}', {FONT_FALLBACK};
                font-size: 14px;
                background: transparent;
            }}
            QLabel#modeLabel {{
                color: {accent};
                font-family: '{FONT_PRIMARY}', '{FONT_SECONDARY}', {FONT_FALLBACK};
                font-size: 13px;
                font-weight: bold;
                letter-spacing: 2px;
                background: transparent;
            }}
            """
        )
