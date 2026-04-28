"""
Application-wide constants for 2048-Nexus.

All magic numbers, paths, and configuration defaults live here.
"""
from __future__ import annotations

import os

# ---------------------------------------------------------------------------
# Application metadata
# ---------------------------------------------------------------------------
APP_NAME: str = "2048-Nexus"
APP_VERSION: str = "1.0.0"
APP_ID: str = "io.github.ayush.2048Nexus"
APP_ORG: str = "Ayush"

# ---------------------------------------------------------------------------
# Grid constraints
# ---------------------------------------------------------------------------
MIN_GRID_SIZE: int = 3
MAX_GRID_SIZE: int = 8
DEFAULT_GRID_SIZE: int = 4

# ---------------------------------------------------------------------------
# Animation durations (milliseconds)
# ---------------------------------------------------------------------------
ANIM_SLIDE_MS: int = 110
ANIM_MERGE_MS: int = 140
ANIM_OVERLAY_MS: int = 380
ANIM_SPAWN_MS: int = 90

# ---------------------------------------------------------------------------
# Tile spawn probabilities
# ---------------------------------------------------------------------------
SPAWN_PROB_2: float = 0.90   # 90 % chance for a "2" tile
SPAWN_PROB_4: float = 0.10   # 10 % chance for a "4" tile

# ---------------------------------------------------------------------------
# Timed mode defaults
# ---------------------------------------------------------------------------
DEFAULT_TIMED_SECONDS: int = 120

# ---------------------------------------------------------------------------
# Undo/redo
# ---------------------------------------------------------------------------
MAX_UNDO_STEPS: int = 50

# ---------------------------------------------------------------------------
# AI
# ---------------------------------------------------------------------------
AI_DEFAULT_DEPTH: int = 4
AI_MOVE_DELAY_MS: int = 320   # ms between autonomous AI moves

# ---------------------------------------------------------------------------
# Fibonacci sequence (used by FibonacciMerge strategy)
# ---------------------------------------------------------------------------
FIBONACCI_SEQUENCE: list[int] = [
    1, 2, 3, 5, 8, 13, 21, 34, 55, 89,
    144, 233, 377, 610, 987, 1597, 2584, 4181, 6765, 10946,
]

# ---------------------------------------------------------------------------
# Classic mode win goal
# ---------------------------------------------------------------------------
CLASSIC_GOAL: int = 2048
FIBONACCI_GOAL: int = 144

# ---------------------------------------------------------------------------
# Typography
# ---------------------------------------------------------------------------
FONT_PRIMARY: str = "Orbitron"
FONT_SECONDARY: str = "Inter"
FONT_FALLBACK: str = "Arial"

# ---------------------------------------------------------------------------
# File system paths (resolved relative to the project root)
# ---------------------------------------------------------------------------
_THIS_FILE = os.path.abspath(__file__)
BASE_DIR: str = os.path.dirname(os.path.dirname(_THIS_FILE))   # project root

ASSETS_DIR: str = os.path.join(BASE_DIR, "assets")
AUDIO_DIR: str = os.path.join(ASSETS_DIR, "audio")
FONTS_DIR: str = os.path.join(ASSETS_DIR, "fonts")
ICONS_DIR: str = os.path.join(ASSETS_DIR, "icons")

CONFIG_DIR: str = os.path.join(BASE_DIR, "config")
SETTINGS_FILE: str = os.path.join(CONFIG_DIR, "settings.json")
SCORES_FILE: str = os.path.join(CONFIG_DIR, "scores.json")
LAST_GAME_FILE: str = os.path.join(CONFIG_DIR, "last_game.json")

# ---------------------------------------------------------------------------
# Audio file names (relative to AUDIO_DIR)
# ---------------------------------------------------------------------------
AUDIO_MUSIC: str = "music_bg.wav"
AUDIO_MOVE: str = "sfx_move.wav"
AUDIO_MERGE: str = "sfx_merge.wav"
AUDIO_WIN: str = "sfx_win.wav"
AUDIO_LOSE: str = "sfx_lose.wav"
AUDIO_SPAWN: str = "sfx_spawn.wav"

# ---------------------------------------------------------------------------
# Leaderboard
# ---------------------------------------------------------------------------
LEADERBOARD_MAX_ENTRIES: int = 10

# ---------------------------------------------------------------------------
# Modes registry (used for labels/IDs)
# ---------------------------------------------------------------------------
MODE_CLASSIC: str = "classic"
MODE_ENDLESS: str = "endless"
MODE_TIMED: str = "timed"
MODE_FIBONACCI: str = "fibonacci"
MODE_CUSTOM: str = "custom"
MODE_AI: str = "ai"

ALL_MODES: list[str] = [
    MODE_CLASSIC, MODE_ENDLESS, MODE_TIMED,
    MODE_FIBONACCI, MODE_CUSTOM, MODE_AI,
]
