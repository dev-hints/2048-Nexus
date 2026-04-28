# 2048-Nexus

<div align="center">

**A production-grade 2048 game built with Python + PyQt6**

*Cosmic design · 6 game modes · AI solver · Smooth animations*

</div>

---

## Features

| Feature | Details |
|---|---|
| **Game Modes** | Classic, Endless, Timed, Fibonacci, Custom, AI Play |
| **Grid Sizes** | 3×3 to 8×8 (configurable) |
| **Themes** | Neon Cosmic (default), Classic |
| **AI Solver** | Expectimax algorithm with heuristics (monotonicity, smoothness, empty tiles) |
| **Audio** | Background music + SFX (move, merge, win, lose) |
| **Undo/Redo** | Configurable undo depth |
| **Leaderboard** | Per-mode local leaderboard (top 10) |
| **Settings** | Grid size, theme, audio, AI depth, timer duration — all persistent |
| **Controls** | Arrow keys or WASD + Ctrl+Z to undo |

---

## Quick Start (Local)

### Prerequisites

Install the Python and PyQt6 libraries from your system package manager:

```bash
sudo apt update
sudo apt install python3 python3-pyqt6 python3-pyqt6.qtmultimedia
```

On some Debian/Ubuntu-based systems, `python3-pyqt6.sip` may be listed separately:

```bash
sudo apt install python3-pyqt6.sip
```

### Installation

```bash
# Clone the project
cd /path/to/2048-Nexus

# Launch the game
python3 main.py
```

That's it! Audio assets are generated automatically on first launch.

---

## Project Structure

```
2048-Nexus/
├── main.py                    # Entry point
├── core/                      # Game engine (grid, merge, undo)
│   ├── engine.py
│   ├── grid.py
│   ├── history.py
│   └── merge_strategy.py
├── modes/                     # 6 gameplay modes
│   ├── base_mode.py
│   ├── classic.py
│   ├── endless.py
│   ├── timed.py
│   ├── fibonacci.py
│   ├── custom.py
│   └── ai_mode.py
├── ui/                        # PyQt6 UI (windows, views, overlays)
│   ├── app.py
│   ├── main_window.py
│   ├── main_menu.py
│   ├── game_view.py
│   ├── hud.py
│   ├── game_over_overlay.py
│   ├── settings_panel.py
│   ├── leaderboard.py
│   └── themes.py
├── audio/                     # Audio management
│   └── audio_manager.py
├── ai/                        # AI solver
│   └── solver.py
├── utils/                     # Shared utilities
│   ├── constants.py
│   ├── settings_manager.py
│   └── score_manager.py
├── assets/
│   ├── audio/                 # WAV sound files (auto-generated)
│   ├── fonts/                 # Optional custom fonts
│   └── icons/                 # App icon
└── config/                    # Runtime config / scores (auto-created)
```

---

## Game Controls

| Key | Action |
|---|---|
| `↑ / W` | Move Up |
| `↓ / S` | Move Down |
| `← / A` | Move Left |
| `→ / D` | Move Right |
| `Ctrl+Z` | Undo |
| `F5` | Restart |
| `Escape` | Main Menu |

---

## Game Modes

| Mode | Description |
|---|---|
| **Classic** | Standard 4×4, reach the 2048 tile |
| **Endless** | No win condition — push your score as high as possible |
| **Timed** | Race against a configurable countdown clock |
| **Fibonacci** | Consecutive Fibonacci tiles merge (1+2=3, 2+3=5, …) |
| **Custom** | Choose grid size, goal, and merge strategy |
| **AI Play** | Watch the Expectimax AI solve the board automatically |

## Configuration

Settings are stored in `config/settings.json`:

```json
{
  "grid_size": 4,
  "theme": "neon",
  "sound_enabled": true,
  "music_enabled": true,
  "volume": 70,
  "ai_depth": 4,
  "timed_seconds": 120,
  "undo_limit": 50
}
```

High scores are stored in `config/scores.json`.

---

## Architecture Notes

- **Separation of concerns**: Game logic (`core/`, `modes/`) has zero PyQt6 imports
- **Strategy pattern**: Merge rules are swappable via `MergeStrategy` ABC
- **Singleton managers**: `SettingsManager` and `ScoreManager` use module-level singletons
- **AI thread safety**: Expectimax runs in `QThread` worker, never blocking the UI thread
- **Graceful audio degradation**: Audio files are generated programmatically; missing files don't crash the app

---

## License

MIT License — see [LICENSE](LICENSE) for details.
