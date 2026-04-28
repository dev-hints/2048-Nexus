"""
Main menu screen for 2048-Nexus.

Shows an animated title, six mode selection cards, and quick-access
buttons for Leaderboard and Settings.
"""
from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import (
    QEasingCurve, QPropertyAnimation, QRectF, Qt, pyqtSignal, QTimer,
    pyqtProperty,
)
from PyQt6.QtGui import (
    QColor, QFont, QLinearGradient, QPainter, QPainterPath,
    QRadialGradient,
)
from PyQt6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QVBoxLayout, QWidget,
)

from ui.themes import Theme
from utils.constants import (
    FONT_PRIMARY, FONT_SECONDARY, FONT_FALLBACK,
    MODE_CLASSIC, MODE_ENDLESS, MODE_TIMED,
    MODE_FIBONACCI, MODE_CUSTOM, MODE_AI,
)

_MODE_META = [
    (MODE_CLASSIC,  "Classic",    "★",  "4×4 grid · Reach 2048"),
    (MODE_ENDLESS,  "Endless",    "∞",  "No win limit · Play forever"),
    (MODE_TIMED,    "Timed",      "T", "Race against the clock"),
    (MODE_FIBONACCI,"Fibonacci",  "φ",  "Consecutive Fibonacci merges"),
    (MODE_CUSTOM,   "Custom",     "☰",  "Your rules · Your grid"),
    (MODE_AI,       "AI Play",    "AI", "Watch the AI solve it"),
]


class ModeCard(QFrame):
    """A clickable mode selection card."""

    clicked = pyqtSignal(str)  # emits mode_id

    def __init__(self, mode_id: str, name: str, icon: str, desc: str,
                 theme: Theme, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._mode_id = mode_id
        self._theme = theme
        self._hovered = False

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(200, 130)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(4)

        icon_lbl = QLabel(icon)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setObjectName("cardIcon")

        name_lbl = QLabel(name)
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_lbl.setObjectName("cardName")

        desc_lbl = QLabel(desc)
        desc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_lbl.setObjectName("cardDesc")
        desc_lbl.setWordWrap(True)

        layout.addWidget(icon_lbl)
        layout.addWidget(name_lbl)
        layout.addWidget(desc_lbl)

        self._apply_style(False)

    def _apply_style(self, hovered: bool) -> None:
        t = self._theme
        accent = t.accent_primary.name()
        border_color = t.accent_secondary.name() if hovered else accent
        card_bg = t.bg_window.name() if t.name == "classic" else t.hud_bg.name()
        title_color = t.text_dark.name() if t.name == "classic" else t.text_primary.name()
        desc_color = t.text_dark.name() if t.name == "classic" else t.accent_primary.name()
        icon_color = t.text_dark.name() if t.name == "classic" else t.accent_primary.name()
        self.setStyleSheet(
            f"""
            QFrame {{
                background: {card_bg};
                border: 2px solid {border_color};
                border-radius: 14px;
            }}
            QLabel#cardIcon {{
                color: {icon_color};
                font-family: 'Noto Color Emoji', 'Segoe UI Emoji', 'Apple Color Emoji', 'Segoe UI Symbol', '{FONT_PRIMARY}', {FONT_FALLBACK};
                font-size: 30px;
                background: transparent;
            }}
            QLabel#cardName {{
                color: {title_color};
                font-family: '{FONT_PRIMARY}', {FONT_FALLBACK};
                font-size: 16px;
                font-weight: bold;
                background: transparent;
            }}
            QLabel#cardDesc {{
                color: {desc_color};
                font-family: '{FONT_SECONDARY}', {FONT_FALLBACK};
                font-size: 11px;
                background: transparent;
            }}
            """
        )

    def enterEvent(self, event) -> None:
        self._hovered = True
        self._apply_style(True)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._hovered = False
        self._apply_style(False)
        super().leaveEvent(event)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._mode_id)
        super().mousePressEvent(event)


class MainMenu(QWidget):
    """
    Main menu screen.

    Signals:
    - ``mode_selected(mode_id)`` — user chose a mode
    - ``leaderboard_requested``
    - ``settings_requested``
    """

    mode_selected = pyqtSignal(str)
    leaderboard_requested = pyqtSignal()
    settings_requested = pyqtSignal()

    def __init__(self, theme: Theme, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._theme = theme
        self._title_alpha: float = 0.0
        self._cards: list[ModeCard] = []
        self._build_ui()
        self._fade_in_title()

    def set_theme(self, theme: Theme) -> None:
        self._theme = theme
        self._restyle()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 30, 40, 30)
        root.setSpacing(20)

        # Title
        self._title = QLabel("2048 NEXUS")
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title.setObjectName("mainTitle")

        self._subtitle = QLabel("Choose your mode")
        self._subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._subtitle.setObjectName("mainSubtitle")

        root.addWidget(self._title)
        root.addWidget(self._subtitle)
        root.addSpacing(10)

        # Mode cards grid (2 × 3)
        grid_widget = QWidget()
        grid = QGridLayout(grid_widget)
        grid.setSpacing(16)
        grid.setContentsMargins(0, 0, 0, 0)

        for i, (mid, name, icon, desc) in enumerate(_MODE_META):
            card = ModeCard(mid, name, icon, desc, self._theme)
            card.clicked.connect(self.mode_selected)
            grid.addWidget(card, i // 3, i % 3)
            self._cards.append(card)

        root.addWidget(grid_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        root.addSpacing(10)

        # Action buttons row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(14)

        self._lb_btn = self._make_action_btn("🏆  Leaderboard")
        self._st_btn = self._make_action_btn("⚙  Settings")
        self._lb_btn.clicked.connect(self.leaderboard_requested)
        self._st_btn.clicked.connect(self.settings_requested)

        btn_row.addStretch()
        btn_row.addWidget(self._lb_btn)
        btn_row.addWidget(self._st_btn)
        btn_row.addStretch()
        root.addLayout(btn_row)

        root.addStretch()
        self._restyle()

    def _make_action_btn(self, text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        return btn

    # ------------------------------------------------------------------
    # Styling
    # ------------------------------------------------------------------

    def _restyle(self) -> None:
        t = self._theme
        accent = t.accent_primary.name()
        accent2 = t.accent_secondary.name()
        bg = t.bg_window.name()
        hud = t.hud_bg.name()

        self.setStyleSheet(
            f"""
            QWidget {{ background: {bg}; }}
            QLabel#mainTitle {{
                color: {accent};
                font-family: '{FONT_PRIMARY}', {FONT_FALLBACK};
                font-size: 48px;
                font-weight: bold;
                letter-spacing: 6px;
                background: transparent;
            }}
            QLabel#mainSubtitle {{
                color: {accent2};
                font-family: '{FONT_SECONDARY}', {FONT_FALLBACK};
                font-size: 16px;
                letter-spacing: 3px;
                background: transparent;
            }}
            QPushButton {{
                background: transparent;
                border: 2px solid {accent};
                border-radius: 10px;
                color: {accent};
                font-family: '{FONT_PRIMARY}', {FONT_FALLBACK};
                font-size: 13px;
                font-weight: bold;
                padding: 10px 24px;
            }}
            QPushButton:hover {{
                background: {accent};
                color: #000000;
            }}
            """
        )
        # Update existing cards
        for card in self._cards:
            card._theme = t
            card._apply_style(False)

    # ------------------------------------------------------------------
    # Title fade-in animation
    # ------------------------------------------------------------------

    def _fade_in_title(self) -> None:
        # Stagger card entry using QTimer
        for i, card in enumerate(self._cards):
            card.setVisible(False)
            QTimer.singleShot(200 + i * 80, lambda c=card: c.setVisible(True))
