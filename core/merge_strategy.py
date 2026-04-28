"""
Merge strategy abstraction for 2048-Nexus.

Defines the MergeStrategy ABC and two concrete implementations:
- StandardMerge: classic 2048 rules (equal tiles merge)
- FibonacciMerge: consecutive Fibonacci numbers merge into the next
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Tuple

from utils.constants import FIBONACCI_SEQUENCE, CLASSIC_GOAL, FIBONACCI_GOAL


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class MergeResult:
    """Result returned by a successful merge operation."""
    new_value: int
    score: int


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------

class MergeStrategy(ABC):
    """Abstract merge rule set used by the game engine."""

    @abstractmethod
    def can_merge(self, a: int, b: int) -> bool:
        """Return True if tile values *a* and *b* can merge."""
        ...

    @abstractmethod
    def merge(self, a: int, b: int) -> MergeResult:
        """Return the MergeResult for combining *a* and *b*."""
        ...

    @abstractmethod
    def get_goal(self) -> int:
        """Return the tile value that constitutes a win."""
        ...

    @abstractmethod
    def get_spawn_values(self) -> List[Tuple[int, float]]:
        """Return [(value, probability), ...] for tile spawning."""
        ...

    @property
    def name(self) -> str:
        return self.__class__.__name__


# ---------------------------------------------------------------------------
# Standard 2048 merge
# ---------------------------------------------------------------------------

class StandardMerge(MergeStrategy):
    """
    Classic 2048 merge rules.

    Two equal tiles merge into their sum. Default goal is 2048.
    """

    def __init__(self, goal: int = CLASSIC_GOAL) -> None:
        self._goal = goal

    def can_merge(self, a: int, b: int) -> bool:
        return a != 0 and a == b

    def merge(self, a: int, b: int) -> MergeResult:
        new_val = a + b
        return MergeResult(new_value=new_val, score=new_val)

    def get_goal(self) -> int:
        return self._goal

    def get_spawn_values(self) -> List[Tuple[int, float]]:
        return [(2, 0.90), (4, 0.10)]


# ---------------------------------------------------------------------------
# Fibonacci merge
# ---------------------------------------------------------------------------

class FibonacciMerge(MergeStrategy):
    """
    Fibonacci merge rules.

    Two tiles whose values are *adjacent* Fibonacci numbers merge into
    the next Fibonacci number in the sequence.

    Example: 3 + 5 = 8,  8 + 13 = 21
    """

    _seq: List[int] = FIBONACCI_SEQUENCE
    _idx: dict[int, int] = {v: i for i, v in enumerate(FIBONACCI_SEQUENCE)}

    def can_merge(self, a: int, b: int) -> bool:
        if a not in self._idx or b not in self._idx:
            return False
        ia, ib = self._idx[a], self._idx[b]
        # Must be adjacent in the sequence and both ≥ index 1
        return abs(ia - ib) == 1 and min(ia, ib) >= 1

    def merge(self, a: int, b: int) -> MergeResult:
        ia, ib = self._idx[a], self._idx[b]
        next_idx = max(ia, ib) + 1
        new_val = self._seq[next_idx] if next_idx < len(self._seq) else self._seq[-1]
        return MergeResult(new_value=new_val, score=new_val)

    def get_goal(self) -> int:
        return FIBONACCI_GOAL

    def get_spawn_values(self) -> List[Tuple[int, float]]:
        # Spawn 1s and 2s since those are the lowest Fibonacci tiles
        return [(1, 0.50), (2, 0.30), (3, 0.20)]
