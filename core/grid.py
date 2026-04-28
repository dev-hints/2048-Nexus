"""
Grid data structure for 2048-Nexus.

Provides a 2D grid of integers (0 = empty) with random tile spawning,
deep-copy support, and utility queries.
"""
from __future__ import annotations

import copy
import random
from typing import List, Optional, Tuple


class Grid:
    """
    A square 2D grid of integers.

    Tile value 0 represents an empty cell.  Supports any size from
    3 × 3 to 8 × 8.
    """

    def __init__(self, size: int = 4) -> None:
        if not (2 <= size <= 10):
            raise ValueError(f"Grid size must be between 2 and 10, got {size}")
        self._size: int = size
        self._cells: List[List[int]] = [[0] * size for _ in range(size)]

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def size(self) -> int:
        """Side length of the grid."""
        return self._size

    @property
    def cells(self) -> List[List[int]]:
        """Direct reference to the 2-D cells list (row-major)."""
        return self._cells

    # ------------------------------------------------------------------
    # Cell access
    # ------------------------------------------------------------------

    def get(self, row: int, col: int) -> int:
        return self._cells[row][col]

    def set(self, row: int, col: int, value: int) -> None:
        self._cells[row][col] = value

    def __getitem__(self, pos: Tuple[int, int]) -> int:
        r, c = pos
        return self._cells[r][c]

    def __setitem__(self, pos: Tuple[int, int], value: int) -> None:
        r, c = pos
        self._cells[r][c] = value

    # ------------------------------------------------------------------
    # Utility queries
    # ------------------------------------------------------------------

    def empty_cells(self) -> List[Tuple[int, int]]:
        """Return a list of (row, col) for every empty (0-valued) cell."""
        return [
            (r, c)
            for r in range(self._size)
            for c in range(self._size)
            if self._cells[r][c] == 0
        ]

    def is_full(self) -> bool:
        """Return True when no empty cells remain."""
        return not self.empty_cells()

    def max_tile(self) -> int:
        """Return the highest tile value currently on the board."""
        return max(
            self._cells[r][c]
            for r in range(self._size)
            for c in range(self._size)
        )

    def tile_count(self) -> int:
        """Return the number of non-empty tiles."""
        return sum(
            1
            for r in range(self._size)
            for c in range(self._size)
            if self._cells[r][c] != 0
        )

    # ------------------------------------------------------------------
    # Tile spawning
    # ------------------------------------------------------------------

    def spawn_tile(
        self,
        spawn_values: List[Tuple[int, float]],
    ) -> Optional[Tuple[int, int, int]]:
        """
        Place a tile at a random empty cell.

        *spawn_values* is a list of ``(value, probability)`` pairs.

        Returns ``(row, col, value)`` on success, or ``None`` if the
        grid is full.
        """
        empty = self.empty_cells()
        if not empty:
            return None
        row, col = random.choice(empty)
        values, weights = zip(*spawn_values)
        value = random.choices(values, weights=weights, k=1)[0]
        self._cells[row][col] = value
        return row, col, value

    # ------------------------------------------------------------------
    # Copy / serialisation
    # ------------------------------------------------------------------

    def clone(self) -> "Grid":
        """Return a deep copy of this grid."""
        new = Grid(self._size)
        new._cells = copy.deepcopy(self._cells)
        return new

    def to_list(self) -> List[List[int]]:
        """Serialise to a plain 2-D list of ints."""
        return copy.deepcopy(self._cells)

    def from_list(self, data: List[List[int]]) -> None:
        """Restore cells from a plain 2-D list."""
        self._cells = copy.deepcopy(data)

    # ------------------------------------------------------------------
    # Debug
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        rows = [
            " ".join(f"{self._cells[r][c]:6}" for c in range(self._size))
            for r in range(self._size)
        ]
        return "\n".join(rows)
