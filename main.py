"""
2048-Nexus — Entry Point
========================

Launch with:
    python3 main.py
"""
from __future__ import annotations

import sys
import os

# Ensure the project root is on sys.path so all package imports work
_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from ui.app import create_app
from ui.main_window import MainWindow
from audio.audio_manager import AudioManager, generate_audio_assets
from utils.settings_manager import SettingsManager
from utils.score_manager import ScoreManager


def main() -> int:
    # --- Bootstrap application ---
    app = create_app(sys.argv)

    # --- Pre-load singletons ---
    sm = SettingsManager()
    sm.load()

    score_mgr = ScoreManager()
    score_mgr.load()

    # --- Generate audio assets if absent ---
    generate_audio_assets()

    # --- Build and show main window ---
    window = MainWindow()
    window.show()

    # --- Start background music ---
    try:
        audio = AudioManager.instance()
        audio.set_sound_enabled(sm.get("sound_enabled", True))
        audio.set_music_enabled(sm.get("music_enabled", True))
        audio.set_volume(sm.get("volume", 70))
        if sm.get("music_enabled", True):
            audio.play_music()
    except Exception:
        pass  # Audio is non-critical

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
