"""
Abstract base class for all 2048-Nexus game modes.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from core.engine import GameEngine, MoveResult, Direction
from core.merge_strategy import MergeStrategy, StandardMerge
from utils.constants import DEFAULT_GRID_SIZE, MAX_UNDO_STEPS


class BaseMode(ABC):
    """
    Abstract base for a game mode.

    Subclasses override ``_create_engine`` to supply the right strategy
    and goal, and may override ``on_move`` / ``on_tick`` for extra logic.
    """

    #: Human-readable name shown in the UI
    display_name: str = "Base Mode"
    #: Mode identifier (matches constants.MODE_*)
    mode_id: str = "base"
    #: Whether this mode uses a countdown timer
    has_timer: bool = False

    def __init__(
        self,
        grid_size: int = DEFAULT_GRID_SIZE,
        **kwargs: Any,
    ) -> None:
        self._grid_size = grid_size
        self._kwargs = kwargs
        self._engine: GameEngine = self._create_engine(grid_size, **kwargs)
        self._active: bool = False

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @abstractmethod
    def _create_engine(self, grid_size: int, **kwargs: Any) -> GameEngine:
        """Construct and return the appropriate GameEngine for this mode."""
        ...

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Initialise a fresh game."""
        self._engine.reset()
        self._active = True

    def stop(self) -> None:
        """Stop the mode (e.g. pause / return to menu)."""
        self._active = False

    # ------------------------------------------------------------------
    # Gameplay hooks
    # ------------------------------------------------------------------

    def move(self, direction: Direction) -> MoveResult:
        """
        Execute a move and call ``on_move`` with the result.

        Returns the MoveResult.
        """
        result = self._engine.move(direction)
        if result.moved:
            self.on_move(result)
        return result

    def on_move(self, result: MoveResult) -> None:
        """
        Called after every successful move.

        Override in subclasses for mode-specific logic (e.g. decrement
        a move counter, update difficulty).
        """

    def on_tick(self, elapsed_ms: int) -> None:
        """
        Called regularly by the UI timer.

        Override in timed modes or any mode needing periodic updates.
        """

    def undo(self) -> bool:
        """Delegate undo to the engine."""
        return self._engine.undo()

    # ------------------------------------------------------------------
    # Properties delegated to the engine
    # ------------------------------------------------------------------

    @property
    def engine(self) -> GameEngine:
        return self._engine

    @property
    def is_over(self) -> bool:
        return self._engine.is_over

    @property
    def is_won(self) -> bool:
        return self._engine.is_won

    @property
    def score(self) -> int:
        return self._engine.score

    @property
    def active(self) -> bool:
        return self._active

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def get_state(self) -> Dict:
        """Return a serialisable dict for save/resume."""
        return {
            "mode_id": self.mode_id,
            "grid_size": self._grid_size,
            "engine": self._engine.get_state(),
        }

    def load_state(self, state: Dict) -> None:
        """Restore from a previously saved dict."""
        self._engine.load_state(state["engine"])
