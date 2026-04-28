"""
Main application window for 2048-Nexus.

Houses a QStackedWidget cycling between:
  0 — MainMenu
  1 — Game screen (HUD + GameView + toolbar)
  2 — LeaderboardView

Handles mode launch, settings, AI control, score submission, and
theme propagation.
"""
from __future__ import annotations

import json
import os
from typing import Optional

from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QAction, QIcon, QKeySequence, QPixmap
from PyQt6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QMainWindow, QMenuBar,
    QPushButton, QSizePolicy, QStackedWidget,
    QToolBar, QVBoxLayout, QWidget,
)

from modes.base_mode import BaseMode
from modes.classic import ClassicMode
from modes.endless import EndlessMode
from modes.timed import TimedMode
from modes.fibonacci import FibonacciMode
from modes.custom import CustomMode
from modes.ai_mode import AIMode

from ui.game_view import GameView
from ui.game_over_overlay import GameOverOverlay
from ui.hud import HUD
from ui.leaderboard import LeaderboardView
from ui.main_menu import MainMenu
from ui.settings_panel import SettingsPanel
from ui.themes import Theme, get_theme

from utils.constants import (
    APP_NAME, APP_VERSION, LAST_GAME_FILE, CONFIG_DIR,
    MODE_CLASSIC, MODE_ENDLESS, MODE_TIMED,
    MODE_FIBONACCI, MODE_CUSTOM, MODE_AI,
    FONT_PRIMARY,
)
from utils.score_manager import ScoreManager
from utils.settings_manager import SettingsManager


# Screen indices
_SCREEN_MENU = 0
_SCREEN_GAME = 1
_SCREEN_LEADERBOARD = 2


def _build_mode(mode_id: str, sm: SettingsManager) -> BaseMode:
    """Factory: create the appropriate BaseMode for *mode_id*."""
    grid_size = sm.get("grid_size", 4)
    if mode_id == MODE_CLASSIC:
        return ClassicMode(grid_size=grid_size)
    if mode_id == MODE_ENDLESS:
        return EndlessMode(grid_size=grid_size)
    if mode_id == MODE_TIMED:
        return TimedMode(grid_size=grid_size, timed_seconds=sm.get("timed_seconds", 120))
    if mode_id == MODE_FIBONACCI:
        return FibonacciMode(grid_size=grid_size)
    if mode_id == MODE_CUSTOM:
        return CustomMode(grid_size=grid_size)
    if mode_id == MODE_AI:
        return AIMode(grid_size=grid_size, ai_depth=sm.get("ai_depth", 4))
    return ClassicMode(grid_size=grid_size)


# ---------------------------------------------------------------------------
# About dialog
# ---------------------------------------------------------------------------

class _AboutDialog(QDialog):
    """
    Styled About dialog showing developer info, app details, and controls.
    Matches the active theme so it feels native to the app.
    """

    def __init__(self, theme: Theme, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._theme = theme
        self.setWindowTitle(f"About {APP_NAME}")
        self.setMinimumWidth(520)
        self.setModal(True)
        self._build_ui()
        self._apply_style()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        # ── Header banner ────────────────────────────────────────────
        header = QWidget()
        header.setObjectName("aboutHeader")
        h_layout = QVBoxLayout(header)
        h_layout.setContentsMargins(32, 28, 32, 24)
        h_layout.setSpacing(6)

        title = QLabel("2048 NEXUS")
        title.setObjectName("aboutTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel(f"Version {APP_VERSION}  ·  Advanced 2048-style puzzle experience")
        subtitle.setObjectName("aboutSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        h_layout.addWidget(title)
        h_layout.addWidget(subtitle)
        root.addWidget(header)

        # ── Body ─────────────────────────────────────────────────────
        body = QWidget()
        body.setObjectName("aboutBody")
        b_layout = QVBoxLayout(body)
        b_layout.setContentsMargins(32, 24, 32, 20)
        b_layout.setSpacing(18)

        # Developer card
        dev_html = (
            "<table width='100%' cellspacing='0' cellpadding='0'>"
            "<tr><td><b>Developer</b></td><td>StrangeInfinity</td></tr>"
            "<tr><td><b>License</b></td><td>MIT License</td></tr>"
            "<tr><td><b>Built With</b></td><td>Python 3 · PyQt6 · Built-in audio support</td></tr>"
            "<tr><td><b>Architecture</b></td><td>Modular core / modes / UI / AI / audio design</td></tr>"
            "</table>"
        )
        dev_label = QLabel(dev_html)
        dev_label.setObjectName("aboutInfo")
        dev_label.setTextFormat(Qt.TextFormat.RichText)
        dev_label.setWordWrap(True)
        b_layout.addWidget(dev_label)

        # Divider
        div = QLabel()
        div.setFixedHeight(1)
        div.setObjectName("aboutDivider")
        b_layout.addWidget(div)

        # Modes row
        modes_html = (
            "<b>Game Modes</b><br>"
            "Classic · Endless · Timed · Fibonacci · Custom · AI Play"
        )
        modes_label = QLabel(modes_html)
        modes_label.setObjectName("aboutInfo")
        modes_label.setTextFormat(Qt.TextFormat.RichText)
        modes_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        b_layout.addWidget(modes_label)

        # Controls
        ctrl_html = (
            "<b>Controls</b>&nbsp; "
            "Arrow keys / WASD to move · Ctrl+Z to undo · F5 to restart · Esc for menu"
        )
        ctrl_label = QLabel(ctrl_html)
        ctrl_label.setObjectName("aboutInfo")
        ctrl_label.setTextFormat(Qt.TextFormat.RichText)
        ctrl_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ctrl_label.setWordWrap(True)
        b_layout.addWidget(ctrl_label)

        # Divider
        div2 = QLabel()
        div2.setFixedHeight(1)
        div2.setObjectName("aboutDivider")
        b_layout.addWidget(div2)

        # Copyright
        copy_label = QLabel(
            "© 2026 StrangeInfinity · Open Source under the MIT License\n"
            "Built with Python and PyQt6"
        )
        copy_label.setObjectName("aboutCopy")
        copy_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        b_layout.addWidget(copy_label)

        root.addWidget(body)

        # ── Close button ─────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(32, 0, 32, 20)
        close_btn = QPushButton("Close")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setObjectName("aboutClose")
        close_btn.clicked.connect(self.accept)
        btn_row.addStretch()
        btn_row.addWidget(close_btn)
        btn_row.addStretch()
        root.addLayout(btn_row)

    def _apply_style(self) -> None:
        t = self._theme
        accent = t.accent_primary.name()
        accent2 = t.accent_secondary.name()
        bg = t.bg_window.name()
        board = t.bg_board.name()
        hud = t.hud_bg.name()
        text = t.text_primary.name()

        self.setStyleSheet(
            f"""
            QDialog {{ background: {bg}; }}
            QWidget#aboutHeader {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 {board}, stop:1 {hud}
                );
                border-bottom: 2px solid {accent};
            }}
            QLabel#aboutTitle {{
                color: {accent};
                font-family: '{FONT_PRIMARY}', Arial;
                font-size: 34px;
                font-weight: bold;
                letter-spacing: 5px;
                background: transparent;
            }}
            QLabel#aboutSubtitle {{
                color: {accent2};
                font-family: 'Inter', Arial;
                font-size: 12px;
                letter-spacing: 1px;
                background: transparent;
            }}
            QWidget#aboutBody {{ background: {bg}; }}
            QLabel#aboutInfo {{
                color: {text};
                font-family: 'Inter', Arial;
                font-size: 13px;
                background: transparent;
                line-height: 1.6;
            }}
            QLabel#aboutInfo b {{
                color: {accent};
            }}
            QLabel#aboutDivider {{
                background: {accent};
                opacity: 0.3;
            }}
            QLabel#aboutCopy {{
                color: {t.accent_secondary.name()};
                font-family: 'Inter', Arial;
                font-size: 11px;
                background: transparent;
            }}
            QPushButton#aboutClose {{
                background: transparent;
                border: 2px solid {accent};
                border-radius: 10px;
                color: {accent};
                font-family: '{FONT_PRIMARY}', Arial;
                font-weight: bold;
                font-size: 13px;
                padding: 8px 40px;
            }}
            QPushButton#aboutClose:hover {{
                background: {accent};
                color: #000000;
            }}
            """
        )


class _GameScreen(QWidget):
    """Container widget for HUD + GameView + in-game toolbar."""

    def __init__(self, theme: Theme, parent: Optional[QWidget] = None) -> None:

        super().__init__(parent)
        self._theme = theme

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        # HUD
        self.hud = HUD(theme)
        layout.addWidget(self.hud)

        # Game view (main canvas)
        self.game_view = GameView()
        self.game_view.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        layout.addWidget(self.game_view)

        # Bottom toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        self.undo_btn = self._make_btn("↩  Undo", "Ctrl+Z")
        self.restart_btn = self._make_btn("↺  Restart", "F5")
        self.menu_btn = self._make_btn("⌂  Menu", "Escape")

        toolbar.addWidget(self.undo_btn)
        toolbar.addStretch()
        toolbar.addWidget(self.restart_btn)
        toolbar.addWidget(self.menu_btn)
        layout.addLayout(toolbar)

        # Overlay (parented to game_view)
        self.overlay = GameOverOverlay(theme, parent=self.game_view)
        self.game_view.resizeEvent = self._propagate_resize(self.game_view.resizeEvent)

        self._apply_style()

    def _propagate_resize(self, original_handler):
        def handler(event):
            original_handler(event)
            self.overlay.resize(self.game_view.size())
        return handler

    def _make_btn(self, text: str, shortcut: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setShortcut(QKeySequence(shortcut))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        return btn

    def set_theme(self, theme: Theme) -> None:
        self._theme = theme
        self.hud.set_theme(theme)
        self.overlay.set_theme(theme)
        self._apply_style()

    def _apply_style(self) -> None:
        t = self._theme
        accent = t.accent_primary.name()
        bg = t.bg_window.name()
        text = t.text_primary.name()
        self.setStyleSheet(
            f"""
            QWidget {{ background: {bg}; }}
            QPushButton {{
                background: transparent;
                border: 2px solid {accent};
                border-radius: 8px;
                color: {accent};
                font-family: '{FONT_PRIMARY}', Arial;
                font-weight: bold;
                padding: 6px 18px;
                font-size: 12px;
            }}
            QPushButton:hover {{ background: {accent}; color: #000000; }}
            """
        )


class MainWindow(QMainWindow):
    """
    Top-level application window.

    Manages screen navigation, mode lifecycle, score submission, and
    AI controller cleanup.
    """

    def __init__(self) -> None:
        super().__init__()
        self._sm = SettingsManager()
        self._sm.load()
        self._score_mgr = ScoreManager()
        self._score_mgr.load()

        self._theme: Theme = get_theme(self._sm.get("theme", "neon"))
        self._current_mode: Optional[BaseMode] = None
        self._hud_timer: Optional[QTimer] = None

        self.setWindowTitle(f"{APP_NAME}")
        self.setMinimumSize(640, 720)
        self.resize(820, 860)

        self._build_ui()
        self._apply_menu_bar()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)

        # Main menu
        self._menu_screen = MainMenu(self._theme)
        self._menu_screen.mode_selected.connect(self._launch_mode)
        self._menu_screen.leaderboard_requested.connect(self._show_leaderboard)
        self._menu_screen.settings_requested.connect(self._show_settings)

        # Game screen
        self._game_screen = _GameScreen(self._theme)
        self._game_screen.game_view.set_theme(self._theme)
        gv = self._game_screen.game_view
        gs = self._game_screen

        gv.score_changed.connect(self._on_score_changed)
        gv.game_over.connect(self._on_game_over)
        gv.game_won.connect(self._on_game_won)

        gs.undo_btn.clicked.connect(gv.trigger_undo)
        gs.restart_btn.clicked.connect(self._restart_game)
        gs.menu_btn.clicked.connect(self._return_to_menu)
        gs.overlay.restart_requested.connect(self._restart_game)
        gs.overlay.menu_requested.connect(self._return_to_menu)

        # Leaderboard
        self._lb_screen = LeaderboardView(self._theme)
        self._lb_screen.back_requested.connect(self._return_to_menu)

        self._stack.addWidget(self._menu_screen)    # 0
        self._stack.addWidget(self._game_screen)    # 1
        self._stack.addWidget(self._lb_screen)      # 2

        self._stack.setCurrentIndex(_SCREEN_MENU)

        # HUD timer (updates timer in timed mode every second)
        self._hud_timer = QTimer(self)
        self._hud_timer.setInterval(1000)
        self._hud_timer.timeout.connect(self._update_hud_timer)

    def _apply_menu_bar(self) -> None:
        mb = self.menuBar()

        # Game menu
        game_menu = mb.addMenu("Game")
        act_new = QAction("New Game", self)
        act_new.setShortcut("Ctrl+N")
        act_new.triggered.connect(self._restart_game)

        act_undo = QAction("Undo", self)
        act_undo.setShortcut("Ctrl+Z")
        act_undo.triggered.connect(self._game_screen.game_view.trigger_undo)

        act_menu = QAction("Main Menu", self)
        act_menu.setShortcut("Escape")
        act_menu.triggered.connect(self._return_to_menu)

        game_menu.addAction(act_new)
        game_menu.addAction(act_undo)
        game_menu.addSeparator()
        game_menu.addAction(act_menu)

        # Settings
        settings_menu = mb.addMenu("Settings")
        act_settings = QAction("Preferences…", self)
        act_settings.triggered.connect(self._show_settings)
        settings_menu.addAction(act_settings)

        # Help
        help_menu = mb.addMenu("Help")
        act_about = QAction("About 2048-Nexus", self)
        act_about.triggered.connect(self._show_about)
        help_menu.addAction(act_about)

        self._style_menu_bar(mb)

    def _style_menu_bar(self, mb: QMenuBar) -> None:
        t = self._theme
        mb.setStyleSheet(
            f"""
            QMenuBar {{
                background: {t.bg_board.name()};
                color: {t.hud_text.name()};
                font-family: '{FONT_PRIMARY}', Arial;
                font-size: 12px;
            }}
            QMenuBar::item:selected {{ background: {t.accent_primary.name()}; color: #000000; }}
            QMenu {{
                background: {t.bg_board.name()};
                color: {t.hud_text.name()};
                border: 1px solid {t.accent_primary.name()};
            }}
            QMenu::item:selected {{ background: {t.accent_primary.name()}; color: #000000; }}
            """
        )

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    @pyqtSlot(str)
    def _launch_mode(self, mode_id: str) -> None:
        """Build and start the selected game mode."""
        self._stop_current_mode()

        mode = _build_mode(mode_id, self._sm)
        mode.start()
        self._current_mode = mode

        gv = self._game_screen.game_view
        gv.set_mode(mode)
        gv.setFocus()

        hud = self._game_screen.hud
        hud.set_mode(mode.display_name, mode.has_timer)
        best = self._score_mgr.get_best(mode_id)
        hud.update_score(0, best)

        if mode.has_timer:
            self._hud_timer.start()
        else:
            self._hud_timer.stop()

        # Hide overlay if visible
        self._game_screen.overlay.hide_overlay()

        # Wire AI controller if applicable
        if isinstance(mode, AIMode):
            ctrl = mode.get_controller()
            if ctrl:
                ctrl.move_ready.connect(self._ai_move)
                ctrl.start()

        self._stack.setCurrentIndex(_SCREEN_GAME)

    def _return_to_menu(self) -> None:
        self._stop_current_mode()
        self._stack.setCurrentIndex(_SCREEN_MENU)

    def _show_leaderboard(self) -> None:
        self._lb_screen.refresh()
        self._stack.setCurrentIndex(_SCREEN_LEADERBOARD)

    def _show_settings(self) -> None:
        dlg = SettingsPanel(self._theme, parent=self)
        dlg.settings_changed.connect(self._on_settings_changed)
        dlg.exec()

    def _show_about(self) -> None:
        dlg = _AboutDialog(self._theme, parent=self)
        dlg.exec()

    # ------------------------------------------------------------------
    # Game events
    # ------------------------------------------------------------------

    @pyqtSlot(int, int)
    def _on_score_changed(self, score: int, delta: int) -> None:
        if not self._current_mode:
            return
        best = self._score_mgr.get_best(self._current_mode.mode_id)
        self._game_screen.hud.update_score(score, best)

    @pyqtSlot()
    def _on_game_over(self) -> None:
        if not self._current_mode:
            return
        score = self._current_mode.score
        self._score_mgr.submit_score(
            self._current_mode.mode_id, score,
            self._current_mode.engine.grid.size,
        )
        self._game_screen.overlay.show_lose(score)

    @pyqtSlot()
    def _on_game_won(self) -> None:
        if not self._current_mode:
            return
        score = self._current_mode.score
        self._score_mgr.submit_score(
            self._current_mode.mode_id, score,
            self._current_mode.engine.grid.size,
        )
        self._game_screen.overlay.show_win(score)

    @pyqtSlot()
    def _restart_game(self) -> None:
        if self._current_mode:
            self._launch_mode(self._current_mode.mode_id)

    @pyqtSlot(str)
    def _ai_move(self, direction: str) -> None:
        gv = self._game_screen.game_view
        gv._execute_move(direction)

    def _update_hud_timer(self) -> None:
        if isinstance(self._current_mode, TimedMode):
            self._game_screen.hud.update_timer(self._current_mode.time_remaining)

    # ------------------------------------------------------------------
    # Settings reload
    # ------------------------------------------------------------------

    @pyqtSlot()
    def _on_settings_changed(self) -> None:
        self._sm.load()
        self._theme = get_theme(self._sm.get("theme", "neon"))

        # Update audio
        from audio.audio_manager import AudioManager
        audio = AudioManager.instance()
        audio.set_sound_enabled(self._sm.get("sound_enabled", True))
        audio.set_music_enabled(self._sm.get("music_enabled", True))
        audio.set_volume(self._sm.get("volume", 70))

        # Propagate theme
        self._menu_screen.set_theme(self._theme)
        self._game_screen.set_theme(self._theme)
        self._game_screen.game_view.set_theme(self._theme)
        self._lb_screen.set_theme(self._theme)
        self._style_menu_bar(self.menuBar())

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def _stop_current_mode(self) -> None:
        self._hud_timer.stop()
        if isinstance(self._current_mode, AIMode):
            self._current_mode.stop()
        elif self._current_mode:
            self._current_mode.stop()
        self._current_mode = None

    def closeEvent(self, event) -> None:
        self._stop_current_mode()
        super().closeEvent(event)
