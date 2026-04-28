"""
Expectimax AI solver for 2048-Nexus.

Uses a heuristic evaluation function combining:
- Monotonicity  (tiles decrease from corner to centre)
- Smoothness    (adjacent tiles close in value)
- Empty tiles   (more space → more flexibility)
- Max tile in corner bonus

The search runs to ``depth`` plies (default 4).  Chance nodes sample
the two possible spawn values weighted by their probabilities.
"""
from __future__ import annotations

import copy
import math
from typing import List, Optional, Tuple

from core.engine import GameEngine, Direction, DIRECTIONS
from core.grid import Grid
from core.merge_strategy import MergeStrategy
from utils.constants import AI_DEFAULT_DEPTH


# ---------------------------------------------------------------------------
# Heuristic weights  (tuned empirically)
# ---------------------------------------------------------------------------
W_MONOTONICITY = 1.0
W_SMOOTHNESS = 0.1
W_EMPTY = 2.7
W_MAX_CORNER = 1.0


class AIPlayer:
    """
    Expectimax-based 2048 solver.

    Usage::

        player = AIPlayer(depth=4)
        best = player.best_move(engine)   # returns Direction or None
    """

    def __init__(self, depth: int = AI_DEFAULT_DEPTH) -> None:
        self._depth = depth

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def best_move(self, engine: GameEngine) -> Optional[Direction]:
        """Return the best Direction for the current engine state."""
        best_score = -math.inf
        best_dir: Optional[Direction] = None

        for direction in DIRECTIONS:
            clone = self._clone_engine(engine)
            result = clone.move(direction)
            if not result.moved:
                continue
            score = self._expectimax(clone, self._depth - 1, is_max=False)
            if score > best_score:
                best_score = score
                best_dir = direction

        return best_dir

    # ------------------------------------------------------------------
    # Expectimax
    # ------------------------------------------------------------------

    def _expectimax(self, engine: GameEngine, depth: int, is_max: bool) -> float:
        if depth == 0 or engine.is_over:
            return self._evaluate(engine.grid)

        if is_max:
            return self._max_node(engine, depth)
        else:
            return self._chance_node(engine, depth)

    def _max_node(self, engine: GameEngine, depth: int) -> float:
        best = -math.inf
        for direction in DIRECTIONS:
            clone = self._clone_engine(engine)
            result = clone.move(direction)
            if not result.moved:
                continue
            val = self._expectimax(clone, depth - 1, is_max=False)
            if val > best:
                best = val
        return best if best != -math.inf else self._evaluate(engine.grid)

    def _chance_node(self, engine: GameEngine, depth: int) -> float:
        empty = engine.grid.empty_cells()
        if not empty:
            return self._evaluate(engine.grid)

        spawn_values = engine.strategy.get_spawn_values()
        total = 0.0
        n = len(empty)

        for row, col in empty:
            for value, prob in spawn_values:
                clone = self._clone_engine(engine)
                clone.grid.set(row, col, value)
                total += prob * self._expectimax(clone, depth - 1, is_max=True) / n

        return total

    # ------------------------------------------------------------------
    # Heuristic evaluation
    # ------------------------------------------------------------------

    def _evaluate(self, grid: Grid) -> float:
        size = grid.size
        cells = grid.cells

        # 1. Empty tile count
        empty = sum(1 for r in range(size) for c in range(size) if cells[r][c] == 0)

        # 2. Monotonicity (prefer values decreasing from top-left corner)
        mono = self._monotonicity(cells, size)

        # 3. Smoothness (penalise large differences between neighbours)
        smooth = self._smoothness(cells, size)

        # 4. Max tile in corner bonus
        max_val = max(cells[r][c] for r in range(size) for c in range(size))
        corner_bonus = math.log2(max_val + 1) if cells[0][0] == max_val else 0.0

        return (
            W_EMPTY * math.log2(empty + 1)
            + W_MONOTONICITY * mono
            + W_SMOOTHNESS * smooth
            + W_MAX_CORNER * corner_bonus
        )

    @staticmethod
    def _monotonicity(cells: List[List[int]], size: int) -> float:
        score = 0.0
        # Horizontal monotonicity
        for r in range(size):
            inc = dec = 0.0
            for c in range(size - 1):
                a, b = cells[r][c], cells[r][c + 1]
                la = math.log2(a) if a > 0 else 0
                lb = math.log2(b) if b > 0 else 0
                if la > lb:
                    dec += la - lb
                else:
                    inc += lb - la
            score += max(inc, dec)

        # Vertical monotonicity
        for c in range(size):
            inc = dec = 0.0
            for r in range(size - 1):
                a, b = cells[r][c], cells[r + 1][c]
                la = math.log2(a) if a > 0 else 0
                lb = math.log2(b) if b > 0 else 0
                if la > lb:
                    dec += la - lb
                else:
                    inc += lb - la
            score += max(inc, dec)

        return score

    @staticmethod
    def _smoothness(cells: List[List[int]], size: int) -> float:
        penalty = 0.0
        for r in range(size):
            for c in range(size):
                if cells[r][c] == 0:
                    continue
                lv = math.log2(cells[r][c])
                for dr, dc in ((0, 1), (1, 0)):
                    nr, nc = r + dr, c + dc
                    while nr < size and nc < size:
                        if cells[nr][nc] != 0:
                            ln = math.log2(cells[nr][nc])
                            penalty -= abs(lv - ln)
                            break
                        nr += dr
                        nc += dc
        return penalty

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _clone_engine(engine: GameEngine) -> GameEngine:
        """Return a lightweight copy of the engine for tree exploration."""
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
