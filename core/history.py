"""
Undo / redo history for 2048-Nexus.

Uses two bounded deques to hold grid + score snapshots.  Each entry
is a lightweight ``Snapshot`` holding a deep-copied cell list and
the score at that point.
"""
from __future__ import annotations

import copy
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, List, Optional

from utils.constants import MAX_UNDO_STEPS


@dataclass
class Snapshot:
    """Immutable snapshot of grid state and score."""
    cells: List[List[int]]
    score: int

    def __post_init__(self) -> None:
        # Ensure the stored cells are independent of the caller's list
        self.cells = copy.deepcopy(self.cells)


class History:
    """
    Manages undo and redo stacks for a game session.

    Typical usage::

        history.push(grid.cells, score)   # before each move
        snap = history.undo()             # restore previous state
        history.redo(grid.cells, score)   # re-apply undone move
    """

    def __init__(self, max_steps: int = MAX_UNDO_STEPS) -> None:
        self._max = max_steps
        self._undo: Deque[Snapshot] = deque(maxlen=max_steps)
        self._redo: Deque[Snapshot] = deque(maxlen=max_steps)

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def push(self, cells: List[List[int]], score: int) -> None:
        """
        Save the current state onto the undo stack.

        Clears the redo stack (a new move invalidates future history).
        """
        self._undo.append(Snapshot(cells, score))
        self._redo.clear()

    def undo(self) -> Optional[Snapshot]:
        """
        Pop and return the most recent undo snapshot.

        Returns ``None`` if no history is available.
        """
        if not self._undo:
            return None
        return self._undo.pop()

    def push_redo(self, cells: List[List[int]], score: int) -> None:
        """Save a state onto the redo stack (used by the engine)."""
        self._redo.append(Snapshot(cells, score))

    def redo(self) -> Optional[Snapshot]:
        """
        Pop and return the most recent redo snapshot.

        Returns ``None`` if nothing to redo.
        """
        if not self._redo:
            return None
        return self._redo.pop()

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def can_undo(self) -> bool:
        return bool(self._undo)

    def can_redo(self) -> bool:
        return bool(self._redo)

    def clear(self) -> None:
        """Discard all undo and redo history."""
        self._undo.clear()
        self._redo.clear()

    def __len__(self) -> int:
        return len(self._undo)
