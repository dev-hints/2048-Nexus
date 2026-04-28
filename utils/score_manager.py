"""
Score and leaderboard persistence for 2048-Nexus.

Stores per-mode high scores and a global leaderboard (top-N entries)
in a JSON file. All I/O uses atomic writes.
"""
from __future__ import annotations

import json
import os
import shutil
import tempfile
from datetime import datetime
from typing import Any

from utils.constants import (
    SCORES_FILE, CONFIG_DIR, LEADERBOARD_MAX_ENTRIES, ALL_MODES,
)


class ScoreManager:
    """
    Manages high scores and leaderboard entries.

    Data format (JSON)::

        {
          "best": {"classic": 12345, "endless": 0, ...},
          "leaderboard": {
            "classic": [
              {"score": 12345, "date": "2026-04-27", "grid": 4}, ...
            ],
            ...
          }
        }
    """

    _instance: "ScoreManager | None" = None

    def __new__(cls) -> "ScoreManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._data: dict[str, Any] = {}
            cls._instance._loaded = False
        return cls._instance

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def load(self) -> None:
        """Load scores from disk."""
        self._data = self._empty_data()
        if os.path.exists(SCORES_FILE):
            try:
                with open(SCORES_FILE, "r", encoding="utf-8") as fh:
                    on_disk: dict[str, Any] = json.load(fh)
                # Merge carefully
                for mode in ALL_MODES:
                    best = on_disk.get("best", {}).get(mode)
                    if isinstance(best, int):
                        self._data["best"][mode] = best
                    lb = on_disk.get("leaderboard", {}).get(mode)
                    if isinstance(lb, list):
                        self._data["leaderboard"][mode] = lb
            except (json.JSONDecodeError, OSError):
                pass
        self._loaded = True

    def save(self) -> None:
        """Atomically write scores to disk."""
        os.makedirs(CONFIG_DIR, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=CONFIG_DIR, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(self._data, fh, indent=2)
            shutil.move(tmp, SCORES_FILE)
        except OSError:
            if os.path.exists(tmp):
                os.unlink(tmp)

    # ------------------------------------------------------------------
    # High scores
    # ------------------------------------------------------------------

    def get_best(self, mode: str) -> int:
        """Return the all-time best score for *mode*."""
        self._ensure_loaded()
        return self._data["best"].get(mode, 0)

    def submit_score(self, mode: str, score: int, grid_size: int = 4) -> bool:
        """
        Submit a score for *mode*. Returns True if it is a new best.

        The entry is also added to the leaderboard.
        """
        self._ensure_loaded()
        is_best = score > self._data["best"].get(mode, 0)
        if is_best:
            self._data["best"][mode] = score

        entry: dict[str, Any] = {
            "score": score,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "grid": grid_size,
        }
        lb: list[dict[str, Any]] = self._data["leaderboard"].setdefault(mode, [])
        lb.append(entry)
        lb.sort(key=lambda e: e["score"], reverse=True)
        # Keep only top-N
        self._data["leaderboard"][mode] = lb[:LEADERBOARD_MAX_ENTRIES]
        self.save()
        return is_best

    def get_leaderboard(self, mode: str) -> list[dict[str, Any]]:
        """Return the leaderboard entries for *mode* (highest first)."""
        self._ensure_loaded()
        return list(self._data["leaderboard"].get(mode, []))

    def get_all_bests(self) -> dict[str, int]:
        """Return a dict mapping each mode to its best score."""
        self._ensure_loaded()
        return {m: self._data["best"].get(m, 0) for m in ALL_MODES}

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _ensure_loaded(self) -> None:
        if not self._loaded:
            self.load()

    @staticmethod
    def _empty_data() -> dict[str, Any]:
        return {
            "best": {m: 0 for m in ALL_MODES},
            "leaderboard": {m: [] for m in ALL_MODES},
        }
