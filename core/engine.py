"""
Game engine for 2048-Nexus.

Encapsulates all movement, merge, spawn, win/lose detection,
scoring, undo/redo, and state serialisation logic.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from core.grid import Grid
from core.history import History
from core.merge_strategy import MergeStrategy, StandardMerge
from utils.constants import MAX_UNDO_STEPS

Direction = str  # "up" | "down" | "left" | "right"
DIRECTIONS = ("up", "down", "left", "right")


# ---------------------------------------------------------------------------
# Result containers
# ---------------------------------------------------------------------------

@dataclass
class MoveResult:
    """Detailed result of a single player move."""
    moved: bool
    score_delta: int
    merged_positions: List[Tuple[int, int]] = field(default_factory=list)
    spawned: Optional[Tuple[int, int, int]] = None   # (row, col, value)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class GameEngine:
    """
    Core 2048 game engine.

    Thread-safe for reading; callers must serialise writes from a single
    thread (the UI thread).
    """

    def __init__(
        self,
        grid_size: int = 4,
        strategy: Optional[MergeStrategy] = None,
        goal: Optional[int] = None,
        max_undo: int = MAX_UNDO_STEPS,
    ) -> None:
        self._strategy: MergeStrategy = strategy or StandardMerge()
        self._size: int = grid_size
        self._grid: Grid = Grid(grid_size)
        self._score: int = 0
        self._history: History = History(max_undo)
        self._goal: int = goal if goal is not None else self._strategy.get_goal()
        self._won: bool = False
        self._over: bool = False

    # ------------------------------------------------------------------
    # Properties (read-only)
    # ------------------------------------------------------------------

    @property
    def grid(self) -> Grid:
        return self._grid

    @property
    def score(self) -> int:
        return self._score

    @property
    def goal(self) -> int:
        return self._goal

    @property
    def is_won(self) -> bool:
        return self._won

    @property
    def is_over(self) -> bool:
        return self._over

    @property
    def can_undo(self) -> bool:
        return self._history.can_undo()

    @property
    def strategy(self) -> MergeStrategy:
        return self._strategy

    # ------------------------------------------------------------------
    # Game lifecycle
    # ------------------------------------------------------------------

    def reset(self) -> None:
        """Reset to a fresh board and spawn two initial tiles."""
        self._grid = Grid(self._size)
        self._score = 0
        self._history.clear()
        self._won = False
        self._over = False
        sv = self._strategy.get_spawn_values()
        self._grid.spawn_tile(sv)
        self._grid.spawn_tile(sv)

    # ------------------------------------------------------------------
    # Movement
    # ------------------------------------------------------------------

    def move(self, direction: Direction) -> MoveResult:
        """
        Execute a directional move.

        If the board changes, a tile is spawned and the new state is
        checked for win/loss.  Returns a :class:`MoveResult` describing
        what happened.
        """
        if self._over:
            return MoveResult(moved=False, score_delta=0)

        # Snapshot for undo *before* the move
        self._history.push(self._grid.cells, self._score)

        size = self._size
        merged_positions: List[Tuple[int, int]] = []
        total_score: int = 0
        moved = False

        # --- inner helper -------------------------------------------
        def _process_line(line: List[int]) -> Tuple[List[int], int, List[int]]:
            """
            Compress and merge a single row/column (left-to-right logic).

            Returns (new_line, score_gained, merge_indices_in_new_line).
            """
            vals = [v for v in line if v != 0]
            result: List[int] = []
            score = 0
            merge_idxs: List[int] = []
            i = 0
            while i < len(vals):
                if (
                    i + 1 < len(vals)
                    and self._strategy.can_merge(vals[i], vals[i + 1])
                ):
                    res = self._strategy.merge(vals[i], vals[i + 1])
                    result.append(res.new_value)
                    score += res.score
                    merge_idxs.append(len(result) - 1)
                    i += 2
                else:
                    result.append(vals[i])
                    i += 1
            # Pad to original length with zeros
            while len(result) < len(line):
                result.append(0)
            return result, score, merge_idxs
        # -------------------------------------------------------------

        if direction in ("left", "right"):
            reverse = direction == "right"
            for r in range(size):
                line = list(self._grid.cells[r])
                if reverse:
                    line = line[::-1]
                new_line, s, mi = _process_line(line)
                if reverse:
                    new_line = new_line[::-1]
                    mi = [size - 1 - m for m in mi]
                total_score += s
                for idx in mi:
                    merged_positions.append((r, idx))
                if new_line != list(self._grid.cells[r]):
                    moved = True
                    for c in range(size):
                        self._grid.set(r, c, new_line[c])
        else:  # up / down
            reverse = direction == "down"
            for c in range(size):
                line = [self._grid.get(r, c) for r in range(size)]
                if reverse:
                    line = line[::-1]
                new_line, s, mi = _process_line(line)
                if reverse:
                    new_line = new_line[::-1]
                    mi = [size - 1 - m for m in mi]
                total_score += s
                for idx in mi:
                    merged_positions.append((idx, c))
                orig = [self._grid.get(r, c) for r in range(size)]
                if new_line != orig:
                    moved = True
                    for r in range(size):
                        self._grid.set(r, c, new_line[r])

        if not moved:
            # Discard the snapshot we pushed (nothing changed)
            self._history.undo()
            return MoveResult(moved=False, score_delta=0)

        self._score += total_score

        # Check win condition
        if not self._won and self._grid.max_tile() >= self._goal:
            self._won = True

        # Spawn a new tile
        sv = self._strategy.get_spawn_values()
        spawned = self._grid.spawn_tile(sv)

        # Check game-over
        if not self._has_moves():
            self._over = True

        return MoveResult(
            moved=True,
            score_delta=total_score,
            merged_positions=merged_positions,
            spawned=spawned,
        )

    # ------------------------------------------------------------------
    # Undo
    # ------------------------------------------------------------------

    def undo(self) -> bool:
        """
        Restore the previous board state.

        Returns True if undo was successful, False if no history.
        """
        snap = self._history.undo()
        if snap is None:
            return False
        self._grid._cells = copy.deepcopy(snap.cells)
        self._score = snap.score
        self._over = False  # undoing re-opens the game
        return True

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _has_moves(self) -> bool:
        """Return True if at least one valid move exists."""
        if self._grid.empty_cells():
            return True
        size = self._size
        for r in range(size):
            for c in range(size):
                val = self._grid.get(r, c)
                if c + 1 < size and self._strategy.can_merge(val, self._grid.get(r, c + 1)):
                    return True
                if r + 1 < size and self._strategy.can_merge(val, self._grid.get(r + 1, c)):
                    return True
        return False

    def get_possible_moves(self) -> List[Direction]:
        """Return all directions that would change the board."""
        possible = []
        for d in DIRECTIONS:
            tmp = GameEngine(self._size, self._strategy, self._goal)
            tmp._grid._cells = copy.deepcopy(self._grid.cells)
            tmp._score = self._score
            result = tmp.move(d)
            if result.moved:
                possible.append(d)
        return possible

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def get_state(self) -> Dict:
        """Return a JSON-serialisable snapshot of the engine state."""
        return {
            "cells": self._grid.to_list(),
            "score": self._score,
            "won": self._won,
            "over": self._over,
            "size": self._size,
            "goal": self._goal,
        }

    def load_state(self, state: Dict) -> None:
        """Restore engine state from a previously serialised dict."""
        size = state.get("size", 4)
        self._size = size
        self._grid = Grid(size)
        self._grid.from_list(state["cells"])
        self._score = state["score"]
        self._won = state["won"]
        self._over = state["over"]
        self._goal = state["goal"]
        self._history.clear()
