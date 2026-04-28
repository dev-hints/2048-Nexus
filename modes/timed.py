"""
Timed mode — reach the highest score before the countdown expires.

The timer is managed here; the UI calls ``on_tick`` every second and
reads ``time_remaining`` to update the HUD.
"""
from __future__ import annotations

from typing import Any

from core.engine import GameEngine, MoveResult
from core.merge_strategy import StandardMerge
from modes.base_mode import BaseMode
from utils.constants import DEFAULT_TIMED_SECONDS, CLASSIC_GOAL, MODE_TIMED


class TimedMode(BaseMode):
    """Classic rules with a countdown timer."""

    display_name = "Timed"
    mode_id = MODE_TIMED
    has_timer = True

    def __init__(
        self,
        grid_size: int = 4,
        timed_seconds: int = DEFAULT_TIMED_SECONDS,
        **kwargs: Any,
    ) -> None:
        self._total_seconds = timed_seconds
        self._remaining: int = timed_seconds
        self._time_expired: bool = False
        super().__init__(grid_size, **kwargs)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def time_remaining(self) -> int:
        """Seconds remaining on the clock."""
        return self._remaining

    @property
    def total_seconds(self) -> int:
        return self._total_seconds

    @property
    def is_over(self) -> bool:
        return self._time_expired or self._engine.is_over

    # ------------------------------------------------------------------
    # Overrides
    # ------------------------------------------------------------------

    def start(self) -> None:
        self._remaining = self._total_seconds
        self._time_expired = False
        super().start()

    def on_tick(self, elapsed_ms: int) -> None:
        """Called every ~1 000 ms by the UI tick timer."""
        if not self._active or self._time_expired:
            return
        self._remaining = max(0, self._remaining - 1)
        if self._remaining == 0:
            self._time_expired = True

    def _create_engine(self, grid_size: int, **kwargs: Any) -> GameEngine:
        return GameEngine(
            grid_size=grid_size,
            strategy=StandardMerge(goal=CLASSIC_GOAL),
            goal=CLASSIC_GOAL,
        )

    def get_state(self) -> dict:
        state = super().get_state()
        state["remaining"] = self._remaining
        state["total_seconds"] = self._total_seconds
        return state

    def load_state(self, state: dict) -> None:
        super().load_state(state)
        self._remaining = state.get("remaining", self._total_seconds)
        self._total_seconds = state.get("total_seconds", DEFAULT_TIMED_SECONDS)
