"""
AI auto-play mode.

Wraps ClassicMode and drives it with the Expectimax AI solver
running in a QThread worker.  Emits ``move_ready`` signal with
the best direction, which the GameView applies.
"""
from __future__ import annotations

import copy
from typing import Any, Optional

from PyQt6.QtCore import QObject, QMetaObject, Qt, QThread, pyqtSignal, pyqtSlot, QTimer

from core.engine import GameEngine, Direction
from core.merge_strategy import StandardMerge
from modes.base_mode import BaseMode
from utils.constants import (
    CLASSIC_GOAL, MODE_AI, AI_DEFAULT_DEPTH, AI_MOVE_DELAY_MS,
    DEFAULT_GRID_SIZE,
)


class _AIWorker(QObject):
    """Runs the solver in a background thread."""

    move_ready = pyqtSignal(str)   # emits Direction

    def __init__(self, depth: int) -> None:
        super().__init__()
        self._depth = depth
        self._engine: Optional[GameEngine] = None

    def set_engine(self, engine: GameEngine) -> None:
        self._engine = engine

    @pyqtSlot()
    def compute(self) -> None:
        if self._engine is None:
            return
        try:
            from ai.solver import AIPlayer
            player = AIPlayer(depth=self._depth)
            best = player.best_move(self._engine)
            if best:
                self.move_ready.emit(best)
        except Exception:
            # Protect the UI thread from solver failures during AI play.
            import traceback
            traceback.print_exc()


class AIModeController(QObject):
    """
    Manages the AI thread lifecycle and schedules moves.

    Connect ``move_ready`` to the game view's move handler.
    """

    move_ready = pyqtSignal(str)

    def __init__(
        self,
        engine: GameEngine,
        depth: int = AI_DEFAULT_DEPTH,
        delay_ms: int = AI_MOVE_DELAY_MS,
    ) -> None:
        super().__init__()
        self._engine = engine
        self._delay_ms = delay_ms
        self._running = False

        self._thread = QThread()
        self._worker = _AIWorker(depth)
        self._worker.moveToThread(self._thread)
        self._worker.move_ready.connect(self._on_move_ready)
        self._thread.start()

        self._timer = QTimer()
        self._timer.setInterval(delay_ms)
        self._timer.timeout.connect(self._schedule_move)

    # ------------------------------------------------------------------
    # Control
    # ------------------------------------------------------------------

    def start(self) -> None:
        self._running = True
        self._timer.start()

    def stop(self) -> None:
        self._running = False
        self._timer.stop()

    def cleanup(self) -> None:
        self.stop()
        self._thread.quit()
        self._thread.wait(2000)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _clone_engine_snapshot(self, engine: GameEngine) -> GameEngine:
        clone = GameEngine(
            grid_size=engine.grid.size,
            strategy=engine.strategy,
            goal=engine.goal,
            max_undo=0,
        )
        clone._grid._cells = copy.deepcopy(engine.grid.cells)
        clone._score = engine.score
        clone._won = engine.is_won
        clone._over = engine.is_over
        return clone

    def _schedule_move(self) -> None:
        if not self._running or self._engine.is_over:
            self._timer.stop()
            return
        self._worker.set_engine(self._clone_engine_snapshot(self._engine))
        # Invoke compute in worker thread
        QMetaObject.invokeMethod(self._worker, "compute", Qt.ConnectionType.QueuedConnection)

    def _on_move_ready(self, direction: str) -> None:
        self.move_ready.emit(direction)


class AIMode(BaseMode):
    """AI auto-play mode using the Expectimax heuristic solver."""

    display_name = "AI Play"
    mode_id = MODE_AI
    has_timer = False

    def __init__(
        self,
        grid_size: int = DEFAULT_GRID_SIZE,
        ai_depth: int = AI_DEFAULT_DEPTH,
        **kwargs: Any,
    ) -> None:
        self._ai_depth = ai_depth
        self._controller: Optional[AIModeController] = None
        super().__init__(grid_size, **kwargs)

    def _create_engine(self, grid_size: int, **kwargs: Any) -> GameEngine:
        return GameEngine(
            grid_size=grid_size,
            strategy=StandardMerge(goal=CLASSIC_GOAL),
            goal=CLASSIC_GOAL,
        )

    def start(self) -> None:
        super().start()
        self._controller = AIModeController(self._engine, depth=self._ai_depth)

    def get_controller(self) -> Optional[AIModeController]:
        return self._controller

    def stop(self) -> None:
        if self._controller:
            self._controller.cleanup()
            self._controller = None
        super().stop()
