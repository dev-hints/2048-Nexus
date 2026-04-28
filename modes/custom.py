"""
Custom mode — user-defined grid size, goal, and merge strategy.
"""
from __future__ import annotations

from typing import Any, Optional

from core.engine import GameEngine
from core.merge_strategy import MergeStrategy, StandardMerge, FibonacciMerge
from modes.base_mode import BaseMode
from utils.constants import (
    DEFAULT_GRID_SIZE, CLASSIC_GOAL, MODE_CUSTOM,
)


class CustomMode(BaseMode):
    """
    Fully configurable mode.

    Parameters
    ----------
    grid_size : int
        Board side length (3–8).
    goal : int
        Tile value required to win.
    strategy_name : str
        ``"standard"`` or ``"fibonacci"``.
    """

    display_name = "Custom"
    mode_id = MODE_CUSTOM
    has_timer = False

    def __init__(
        self,
        grid_size: int = DEFAULT_GRID_SIZE,
        goal: int = CLASSIC_GOAL,
        strategy_name: str = "standard",
        **kwargs: Any,
    ) -> None:
        self._custom_goal = goal
        self._strategy_name = strategy_name
        super().__init__(grid_size, **kwargs)

    def _build_strategy(self) -> MergeStrategy:
        if self._strategy_name == "fibonacci":
            return FibonacciMerge()
        return StandardMerge(goal=self._custom_goal)

    def _create_engine(self, grid_size: int, **kwargs: Any) -> GameEngine:
        strat = self._build_strategy()
        return GameEngine(
            grid_size=grid_size,
            strategy=strat,
            goal=self._custom_goal,
        )

    def get_state(self) -> dict:
        state = super().get_state()
        state["custom_goal"] = self._custom_goal
        state["strategy_name"] = self._strategy_name
        return state
