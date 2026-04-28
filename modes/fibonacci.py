"""Fibonacci mode — merge consecutive Fibonacci numbers."""
from __future__ import annotations

from typing import Any

from core.engine import GameEngine
from core.merge_strategy import FibonacciMerge
from modes.base_mode import BaseMode
from utils.constants import FIBONACCI_GOAL, MODE_FIBONACCI


class FibonacciMode(BaseMode):
    """
    Uses FibonacciMerge rules.

    Tiles spawn as 1, 2, or 3.  Adjacent Fibonacci tiles merge into the
    next number in the sequence.  Win condition: reach tile 144.
    """

    display_name = "Fibonacci"
    mode_id = MODE_FIBONACCI
    has_timer = False

    def _create_engine(self, grid_size: int, **kwargs: Any) -> GameEngine:
        return GameEngine(
            grid_size=grid_size,
            strategy=FibonacciMerge(),
            goal=FIBONACCI_GOAL,
        )
