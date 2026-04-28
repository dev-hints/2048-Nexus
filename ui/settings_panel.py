"""
Settings panel dialog for 2048-Nexus.

Allows the user to configure: grid size, theme, sound, music, volume,
AI depth, timed-mode duration, and animation speed.
Settings are saved via SettingsManager on Accept.
"""
from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox,
    QFormLayout, QGroupBox, QLabel, QSlider,
    QSpinBox, QTabWidget, QVBoxLayout, QWidget,
)

from ui.themes import Theme
from utils.settings_manager import SettingsManager
from utils.constants import (
    MIN_GRID_SIZE, MAX_GRID_SIZE, DEFAULT_GRID_SIZE,
    FONT_PRIMARY, FONT_SECONDARY,
)


class SettingsPanel(QDialog):
    """
    Modal settings dialog.

    Emits ``settings_changed`` when the user accepts so the main
    window can reload theme / audio / etc.
    """

    settings_changed = pyqtSignal()

    def __init__(self, theme: Theme, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._theme = theme
        self._sm = SettingsManager()
        self._sm.load()

        self.setWindowTitle("Settings — 2048-Nexus")
        self.setMinimumWidth(420)
        self.setModal(True)

        self._build_ui()
        self._load_values()
        self._apply_style()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        tabs = QTabWidget()
        tabs.addTab(self._build_game_tab(), "Game")
        tabs.addTab(self._build_audio_tab(), "Audio")
        tabs.addTab(self._build_display_tab(), "Display")
        layout.addWidget(tabs)

        bbox = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        bbox.accepted.connect(self._on_accept)
        bbox.rejected.connect(self.reject)
        layout.addWidget(bbox)

    def _build_game_tab(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        form.setSpacing(12)

        # Grid size
        self._grid_spin = QSpinBox()
        self._grid_spin.setRange(MIN_GRID_SIZE, MAX_GRID_SIZE)
        form.addRow("Grid Size:", self._grid_spin)

        # AI depth
        self._ai_depth_spin = QSpinBox()
        self._ai_depth_spin.setRange(1, 6)
        self._ai_depth_spin.setToolTip("Higher = stronger AI but slower")
        form.addRow("AI Search Depth:", self._ai_depth_spin)

        # Timed seconds
        self._timed_spin = QSpinBox()
        self._timed_spin.setRange(30, 600)
        self._timed_spin.setSuffix(" s")
        form.addRow("Timed Mode Duration:", self._timed_spin)

        # Undo limit
        self._undo_spin = QSpinBox()
        self._undo_spin.setRange(0, 200)
        form.addRow("Undo Steps Limit:", self._undo_spin)

        return w

    def _build_audio_tab(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        form.setSpacing(12)

        self._sound_chk = QCheckBox("Enable Sound Effects")
        self._music_chk = QCheckBox("Enable Background Music")
        form.addRow(self._sound_chk)
        form.addRow(self._music_chk)

        self._vol_slider = QSlider(Qt.Orientation.Horizontal)
        self._vol_slider.setRange(0, 100)
        self._vol_label = QLabel("70%")
        self._vol_slider.valueChanged.connect(
            lambda v: self._vol_label.setText(f"{v}%")
        )
        form.addRow("Volume:", self._vol_slider)
        form.addRow("", self._vol_label)

        return w

    def _build_display_tab(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        form.setSpacing(12)

        # Theme
        self._theme_combo = QComboBox()
        self._theme_combo.addItems(["neon", "classic"])
        form.addRow("Theme:", self._theme_combo)

        # Animations
        self._anim_chk = QCheckBox("Show Animations")
        form.addRow(self._anim_chk)

        # Animation speed
        self._speed_combo = QComboBox()
        self._speed_combo.addItems(["slow", "normal", "fast"])
        form.addRow("Animation Speed:", self._speed_combo)

        return w

    # ------------------------------------------------------------------
    # Load / save
    # ------------------------------------------------------------------

    def _load_values(self) -> None:
        sm = self._sm
        self._grid_spin.setValue(sm.get("grid_size", DEFAULT_GRID_SIZE))
        self._ai_depth_spin.setValue(sm.get("ai_depth", 4))
        self._timed_spin.setValue(sm.get("timed_seconds", 120))
        self._undo_spin.setValue(sm.get("undo_limit", 50))
        self._sound_chk.setChecked(sm.get("sound_enabled", True))
        self._music_chk.setChecked(sm.get("music_enabled", True))
        self._vol_slider.setValue(sm.get("volume", 70))
        theme_idx = {"neon": 0, "classic": 1}.get(sm.get("theme", "neon"), 0)
        self._theme_combo.setCurrentIndex(theme_idx)
        self._anim_chk.setChecked(sm.get("show_animations", True))
        speed_idx = {"slow": 0, "normal": 1, "fast": 2}.get(sm.get("animation_speed", "normal"), 1)
        self._speed_combo.setCurrentIndex(speed_idx)

    def _on_accept(self) -> None:
        sm = self._sm
        sm.set("grid_size", self._grid_spin.value())
        sm.set("ai_depth", self._ai_depth_spin.value())
        sm.set("timed_seconds", self._timed_spin.value())
        sm.set("undo_limit", self._undo_spin.value())
        sm.set("sound_enabled", self._sound_chk.isChecked())
        sm.set("music_enabled", self._music_chk.isChecked())
        sm.set("volume", self._vol_slider.value())
        sm.set("theme", self._theme_combo.currentText())
        sm.set("show_animations", self._anim_chk.isChecked())
        sm.set("animation_speed", self._speed_combo.currentText())
        self.settings_changed.emit()
        self.accept()

    # ------------------------------------------------------------------
    # Styling
    # ------------------------------------------------------------------

    def _apply_style(self) -> None:
        t = self._theme
        accent = t.accent_primary.name()
        bg = t.bg_window.name()
        hud = t.hud_bg.name()
        text = t.text_primary.name()

        self.setStyleSheet(
            f"""
            QDialog, QWidget {{ background: {bg}; color: {text}; }}
            QTabWidget::pane {{ border: 1px solid {accent}; border-radius: 8px; }}
            QTabBar::tab {{
                background: {hud};
                color: {text};
                border-radius: 6px;
                padding: 6px 16px;
                margin: 2px;
                font-family: '{FONT_PRIMARY}', Arial;
            }}
            QTabBar::tab:selected {{ background: {accent}; color: #000000; }}
            QLabel {{ color: {text}; font-family: '{FONT_SECONDARY}', Arial; }}
            QCheckBox {{ color: {text}; font-family: '{FONT_SECONDARY}', Arial; }}
            QSpinBox, QComboBox, QSlider {{
                background: {hud};
                color: {text};
                border: 1px solid {accent};
                border-radius: 6px;
                padding: 4px;
            }}
            QDialogButtonBox QPushButton {{
                background: transparent;
                border: 2px solid {accent};
                border-radius: 8px;
                color: {accent};
                font-family: '{FONT_PRIMARY}', Arial;
                font-weight: bold;
                padding: 6px 20px;
            }}
            QDialogButtonBox QPushButton:hover {{
                background: {accent};
                color: #000000;
            }}
            """
        )
