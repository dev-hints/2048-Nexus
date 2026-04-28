"""Classic 2048 mode — 4×4 grid, goal tile 2048."""
from __future__ import annotations

from typing import Any

from core.engine import GameEngine
from core.merge_strategy import StandardMerge
from modes.base_mode import BaseMode
from utils.constants import CLASSIC_GOAL, MODE_CLASSIC


class ClassicMode(BaseMode):
    """Standard 2048 on a 4×4 grid with a 2048-tile win condition."""

    display_name = "Classic"
    mode_id = MODE_CLASSIC
    has_timer = False

    def _create_engine(self, grid_size: int, **kwargs: Any) -> GameEngine:
        return GameEngine(
            grid_size=grid_size,
            strategy=StandardMerge(goal=CLASSIC_GOAL),
            goal=CLASSIC_GOAL,
        )
