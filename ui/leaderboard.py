"""
Local leaderboard screen for 2048-Nexus.

Displays per-mode top scores in a styled table.
"""
from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox, QHBoxLayout, QHeaderView, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)

from ui.themes import Theme
from utils.score_manager import ScoreManager
from utils.constants import ALL_MODES, FONT_PRIMARY, FONT_SECONDARY


class LeaderboardView(QWidget):
    """
    Leaderboard screen.

    Shows the top-10 scores for each mode, selectable via dropdown.
    Emits ``back_requested`` when the user clicks Back.
    """

    back_requested = pyqtSignal()

    def __init__(self, theme: Theme, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._theme = theme
        self._sm = ScoreManager()
        self._build_ui()
        self._apply_style()
        self._load_data(ALL_MODES[0])

    def set_theme(self, theme: Theme) -> None:
        self._theme = theme
        self._apply_style()

    def refresh(self) -> None:
        self._load_data(self._mode_combo.currentText())

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 24, 30, 24)
        layout.setSpacing(16)

        # Header row
        header = QHBoxLayout()
        title = QLabel("🏆  Leaderboard")
        title.setObjectName("lbTitle")
        header.addWidget(title)
        header.addStretch()

        self._mode_combo = QComboBox()
        self._mode_combo.addItems(ALL_MODES)
        self._mode_combo.currentTextChanged.connect(self._load_data)
        header.addWidget(QLabel("Mode:"))
        header.addWidget(self._mode_combo)
        layout.addLayout(header)

        # Table
        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(["Rank", "Score", "Grid", "Date"])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.verticalHeader().setVisible(False)
        layout.addWidget(self._table)

        # Back button
        back_btn = QPushButton("← Back to Menu")
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self.back_requested)
        back_btn.setObjectName("backBtn")
        layout.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignLeft)

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def _load_data(self, mode: str) -> None:
        entries = self._sm.get_leaderboard(mode)
        self._table.setRowCount(len(entries))
        for row, entry in enumerate(entries):
            rank_item = QTableWidgetItem(f"#{row + 1}")
            rank_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            score_item = QTableWidgetItem(f"{entry['score']:,}")
            score_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            grid_item = QTableWidgetItem(f"{entry.get('grid', 4)}×{entry.get('grid', 4)}")
            grid_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            date_item = QTableWidgetItem(entry.get("date", ""))
            date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            if row == 0:
                for item in (rank_item, score_item, grid_item, date_item):
                    item.setForeground(self._theme.accent_primary)

            self._table.setItem(row, 0, rank_item)
            self._table.setItem(row, 1, score_item)
            self._table.setItem(row, 2, grid_item)
            self._table.setItem(row, 3, date_item)

    # ------------------------------------------------------------------
    # Styling
    # ------------------------------------------------------------------

    def _apply_style(self) -> None:
        t = self._theme
        accent = t.accent_primary.name()
        bg = t.bg_window.name()
        hud = t.hud_bg.name()
        text = t.text_primary.name()
        board = t.bg_board.name()

        self.setStyleSheet(
            f"""
            QWidget {{ background: {bg}; color: {text}; }}
            QLabel#lbTitle {{
                color: {accent};
                font-family: '{FONT_PRIMARY}', Arial;
                font-size: 26px;
                font-weight: bold;
                background: transparent;
            }}
            QLabel {{ color: {text}; font-family: '{FONT_SECONDARY}', Arial; background: transparent; }}
            QComboBox {{
                background: {hud};
                color: {text};
                border: 1px solid {accent};
                border-radius: 6px;
                padding: 4px 8px;
                font-family: '{FONT_SECONDARY}', Arial;
            }}
            QTableWidget {{
                background: {board};
                color: {text};
                border: 1px solid {accent};
                border-radius: 8px;
                gridline-color: {hud};
                font-family: '{FONT_SECONDARY}', Arial;
                font-size: 13px;
            }}
            QHeaderView::section {{
                background: {hud};
                color: {accent};
                font-family: '{FONT_PRIMARY}', Arial;
                font-weight: bold;
                padding: 6px;
                border: none;
            }}
            QTableWidget::item:selected {{ background: {accent}; color: #000000; }}
            QPushButton#backBtn {{
                background: transparent;
                border: 2px solid {accent};
                border-radius: 8px;
                color: {accent};
                font-family: '{FONT_PRIMARY}', Arial;
                font-weight: bold;
                padding: 8px 20px;
            }}
            QPushButton#backBtn:hover {{ background: {accent}; color: #000000; }}
            """
        )
