"""Endless mode — no tile cap, play until no moves remain."""
from __future__ import annotations

from typing import Any

from core.engine import GameEngine
from core.merge_strategy import StandardMerge
from modes.base_mode import BaseMode
from utils.constants import MODE_ENDLESS


_ENDLESS_GOAL = 2 ** 31  # effectively unreachable


class EndlessMode(BaseMode):
    """
    Standard merge rules but no winning condition — play forever.

    The board shows a ★ badge instead of a win screen when the player
    surpasses 2048.
    """

    display_name = "Endless"
    mode_id = MODE_ENDLESS
    has_timer = False

    def _create_engine(self, grid_size: int, **kwargs: Any) -> GameEngine:
        return GameEngine(
            grid_size=grid_size,
            strategy=StandardMerge(goal=_ENDLESS_GOAL),
            goal=_ENDLESS_GOAL,
        )

    @property
    def is_won(self) -> bool:
        # Never triggers the win overlay in endless mode
        return False
