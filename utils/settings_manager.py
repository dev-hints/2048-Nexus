"""
Settings manager for 2048-Nexus.

Handles persistent user preferences via a JSON file backed by
an in-memory dict. Uses atomic writes to avoid data corruption.
"""
from __future__ import annotations

import json
import os
import shutil
import tempfile
from typing import Any

from utils.constants import SETTINGS_FILE, CONFIG_DIR

# ---------------------------------------------------------------------------
# Default settings (used when no config file exists)
# ---------------------------------------------------------------------------
_DEFAULTS: dict[str, Any] = {
    "grid_size": 4,
    "theme": "neon",
    "sound_enabled": True,
    "music_enabled": False,
    "volume": 70,
    "difficulty": "normal",
    "ai_depth": 4,
    "timed_seconds": 120,
    "undo_limit": 50,
    "show_animations": True,
    "animation_speed": "normal",
}


class SettingsManager:
    """
    Singleton-style settings manager.

    Usage::

        sm = SettingsManager()
        sm.get("theme")          # "neon"
        sm.set("theme", "classic")
        sm.save()
    """

    _instance: "SettingsManager | None" = None

    def __new__(cls) -> "SettingsManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._data: dict[str, Any] = {}
            cls._instance._loaded = False
        return cls._instance

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def load(self) -> None:
        """Load settings from disk, falling back to defaults."""
        self._data = dict(_DEFAULTS)
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as fh:
                    on_disk = json.load(fh)
                # Only accept known keys to avoid cruft
                for key in _DEFAULTS:
                    if key in on_disk:
                        self._data[key] = on_disk[key]
            except (json.JSONDecodeError, OSError):
                pass  # corrupt file → use defaults
        self._loaded = True

    def save(self) -> None:
        """Atomically write current settings to disk."""
        os.makedirs(CONFIG_DIR, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(dir=CONFIG_DIR, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(self._data, fh, indent=2)
            shutil.move(tmp_path, SETTINGS_FILE)
        except OSError:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def reset(self) -> None:
        """Reset all settings to factory defaults."""
        self._data = dict(_DEFAULTS)

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    def get(self, key: str, default: Any = None) -> Any:
        """Return the value for *key*, or *default* if missing."""
        if not self._loaded:
            self.load()
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set *key* to *value* and persist immediately."""
        if not self._loaded:
            self.load()
        self._data[key] = value
        self.save()

    def get_all(self) -> dict[str, Any]:
        """Return a shallow copy of all settings."""
        if not self._loaded:
            self.load()
        return dict(self._data)
