"""
Main game view widget for 2048-Nexus.

Renders the game grid using QPainter with smooth tile slide and merge
animations.  Handles keyboard input and delegates game logic to the
active BaseMode.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from PyQt6.QtCore import (
    QEasingCurve, QPointF, QPropertyAnimation, QRectF,
    QSequentialAnimationGroup, Qt, QTimer, pyqtProperty, pyqtSignal,
    QParallelAnimationGroup,
)
from PyQt6.QtGui import (
    QColor, QFont, QFontMetrics, QPainter, QPainterPath,
    QRadialGradient, QLinearGradient, QPen, QKeyEvent,
)
from PyQt6.QtWidgets import QSizePolicy, QWidget

from core.engine import Direction, MoveResult
from modes.base_mode import BaseMode
from ui.themes import Theme, get_theme
from utils.constants import (
    ANIM_SLIDE_MS, ANIM_MERGE_MS, ANIM_SPAWN_MS,
    FONT_PRIMARY, FONT_SECONDARY, FONT_FALLBACK,
)

# ---------------------------------------------------------------------------
# Internal tile representation
# ---------------------------------------------------------------------------

_TILE_ID = 0


def _next_id() -> int:
    global _TILE_ID
    _TILE_ID += 1
    return _TILE_ID


@dataclass
class DisplayTile:
    """Represents a single tile's visual state."""
    tile_id: int
    value: int
    row: int
    col: int
    # Animation targets (fractional row/col)
    anim_row: float = 0.0
    anim_col: float = 0.0
    # Scale for merge pop (1.0 = normal)
    scale: float = 1.0
    # Opacity for spawn fade-in
    opacity: float = 1.0
    merging: bool = False
    spawning: bool = False

    def __post_init__(self) -> None:
        self.anim_row = float(self.row)
        self.anim_col = float(self.col)


# ---------------------------------------------------------------------------
# Game View
# ---------------------------------------------------------------------------

class GameView(QWidget):
    """
    The main game canvas.

    Renders a 2048 grid with animated tiles.  Communicates game events
    upward via signals.
    """

    # Signals
    score_changed = pyqtSignal(int, int)   # (current_score, delta)
    game_over = pyqtSignal()
    game_won = pyqtSignal()
    move_made = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._mode: Optional[BaseMode] = None
        self._theme: Theme = get_theme("neon")
        self._tiles: Dict[int, DisplayTile] = {}   # tile_id → DisplayTile
        self._animating: bool = False
        self._anim_group: Optional[QParallelAnimationGroup] = None
        self._font_primary: QFont = self._make_font(FONT_PRIMARY, 24, bold=True)

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(320, 320)

        # Tick timer for timed mode
        self._tick_timer = QTimer(self)
        self._tick_timer.setInterval(1000)
        self._tick_timer.timeout.connect(self._on_tick)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_mode(self, mode: BaseMode) -> None:
        """Attach a game mode and build the initial tile display."""
        self._mode = mode
        self._rebuild_tiles()
        if mode.has_timer:
            self._tick_timer.start()
        else:
            self._tick_timer.stop()
        self.update()

    def set_theme(self, theme: Theme) -> None:
        self._theme = theme
        self.update()

    def trigger_undo(self) -> None:
        if self._mode and not self._animating:
            self._mode.undo()
            self._rebuild_tiles()
            self.update()

    # ------------------------------------------------------------------
    # Geometry helpers
    # ------------------------------------------------------------------

    def _grid_size(self) -> int:
        return self._mode.engine.grid.size if self._mode else 4

    def _cell_size(self) -> float:
        n = self._grid_size()
        gap = self._gap()
        w = self.width() - gap * (n + 1)
        h = self.height() - gap * (n + 1)
        return min(w, h) / n

    def _gap(self) -> float:
        return max(6.0, self.width() * 0.015)

    def _board_rect(self) -> QRectF:
        """Return the QRectF of the board area (centered in widget)."""
        n = self._grid_size()
        cs = self._cell_size()
        gap = self._gap()
        board_w = n * cs + (n + 1) * gap
        board_h = board_w
        x = (self.width() - board_w) / 2
        y = (self.height() - board_h) / 2
        return QRectF(x, y, board_w, board_h)

    def _cell_rect(self, row: float, col: float) -> QRectF:
        br = self._board_rect()
        cs = self._cell_size()
        gap = self._gap()
        x = br.x() + gap + col * (cs + gap)
        y = br.y() + gap + row * (cs + gap)
        return QRectF(x, y, cs, cs)

    # ------------------------------------------------------------------
    # Tile management
    # ------------------------------------------------------------------

    def _rebuild_tiles(self) -> None:
        """Completely rebuild the display tiles from current engine state."""
        if not self._mode:
            return
        self._tiles.clear()
        grid = self._mode.engine.grid
        for r in range(grid.size):
            for c in range(grid.size):
                val = grid.get(r, c)
                if val != 0:
                    tid = _next_id()
                    self._tiles[tid] = DisplayTile(
                        tile_id=tid, value=val, row=r, col=c,
                    )

    # ------------------------------------------------------------------
    # Keyboard input
    # ------------------------------------------------------------------

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if self._animating or not self._mode:
            event.ignore()
            return

        key = event.key()
        direction_map = {
            Qt.Key.Key_Up:    "up",
            Qt.Key.Key_W:     "up",
            Qt.Key.Key_Down:  "down",
            Qt.Key.Key_S:     "down",
            Qt.Key.Key_Left:  "left",
            Qt.Key.Key_A:     "left",
            Qt.Key.Key_Right: "right",
            Qt.Key.Key_D:     "right",
            Qt.Key.Key_Z:     "__undo__",
        }

        if key == Qt.Key.Key_Z and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.trigger_undo()
            return

        direction = direction_map.get(key)
        if direction == "__undo__":
            self.trigger_undo()
            return
        if direction:
            self._execute_move(direction)
        else:
            super().keyPressEvent(event)

    # ------------------------------------------------------------------
    # Move execution & animation
    # ------------------------------------------------------------------

    def _execute_move(self, direction: Direction) -> None:
        """Execute a move via the mode and animate the result."""
        if not self._mode or self._mode.is_over:
            return

        old_cells = [list(row) for row in self._mode.engine.grid.cells]
        result = self._mode.move(direction)

        if not result.moved:
            return

        new_cells = self._mode.engine.grid.cells
        self._animate_move(old_cells, new_cells, result)

        from audio.audio_manager import AudioManager
        audio = AudioManager.instance()
        if result.merged_positions:
            audio.play_merge()
        else:
            audio.play_move()

        self.score_changed.emit(self._mode.score, result.score_delta)
        self.move_made.emit()

    def _animate_move(
        self,
        old_cells: List[List[int]],
        new_cells: List[List[int]],
        result: MoveResult,
    ) -> None:
        """Animate tiles from old positions to new positions."""
        # For simplicity: rebuild tiles with a visual snap + spawn animation
        self._rebuild_tiles()

        # Mark newly spawned tile as spawning
        if result.spawned:
            sr, sc, sv = result.spawned
            for tile in self._tiles.values():
                if tile.row == sr and tile.col == sc and tile.value == sv:
                    tile.spawning = True
                    tile.opacity = 0.0
                    tile.scale = 0.5
                    break

        # Mark merged positions for pop animation
        merged_set = set(result.merged_positions)
        for tile in self._tiles.values():
            if (tile.row, tile.col) in merged_set:
                tile.merging = True
                tile.scale = 0.85

        self._run_spawn_animations()
        self.update()

        # Check end conditions
        QTimer.singleShot(ANIM_SLIDE_MS + ANIM_MERGE_MS + 50, self._check_end_conditions)

    def _run_spawn_animations(self) -> None:
        """Animate spawn and merge pop using QTimer-driven painting."""
        start_time = [0]

        def _tick() -> None:
            t = start_time[0]
            t += 16
            start_time[0] = t
            progress = min(1.0, t / max(1, ANIM_MERGE_MS))
            ease = self._ease_out_back(progress)

            for tile in self._tiles.values():
                if tile.spawning:
                    tile.opacity = min(1.0, progress * 1.5)
                    tile.scale = 0.5 + ease * 0.5
                if tile.merging:
                    if progress < 0.5:
                        tile.scale = 0.85 + progress * 0.6
                    else:
                        tile.scale = 1.0 + (1.0 - progress) * 0.15

            self.update()

            if progress >= 1.0:
                for tile in self._tiles.values():
                    tile.spawning = False
                    tile.merging = False
                    tile.scale = 1.0
                    tile.opacity = 1.0
                _anim_timer.stop()

        _anim_timer = QTimer(self)
        _anim_timer.setInterval(16)
        _anim_timer.timeout.connect(_tick)
        _anim_timer.start()

    @staticmethod
    def _ease_out_back(t: float) -> float:
        c1 = 1.70158
        c3 = c1 + 1
        return 1 + c3 * math.pow(t - 1, 3) + c1 * math.pow(t - 1, 2)

    def _check_end_conditions(self) -> None:
        if not self._mode:
            return
        if self._mode.is_won:
            from audio.audio_manager import AudioManager
            AudioManager.instance().play_win()
            self.game_won.emit()
        elif self._mode.is_over:
            from audio.audio_manager import AudioManager
            AudioManager.instance().play_lose()
            self.game_over.emit()

    def _on_tick(self) -> None:
        if self._mode:
            self._mode.on_tick(1000)
            if self._mode.is_over:
                self._tick_timer.stop()
                self.game_over.emit()

    # ------------------------------------------------------------------
    # Painting
    # ------------------------------------------------------------------

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if not self._mode:
            self._draw_empty_state(painter)
            return

        self._draw_board(painter)
        self._draw_cells(painter)
        self._draw_tiles(painter)

    def _draw_empty_state(self, painter: QPainter) -> None:
        painter.fillRect(self.rect(), self._theme.bg_window)

    def _draw_board(self, painter: QPainter) -> None:
        br = self._board_rect()
        radius = max(8.0, self._gap())
        path = QPainterPath()
        path.addRoundedRect(br, radius, radius)
        painter.fillPath(path, self._theme.bg_board)

    def _draw_cells(self, painter: QPainter) -> None:
        n = self._grid_size()
        radius = max(6.0, self._cell_size() * 0.06)
        for r in range(n):
            for c in range(n):
                rect = self._cell_rect(r, c)
                path = QPainterPath()
                path.addRoundedRect(rect, radius, radius)
                painter.fillPath(path, self._theme.bg_cell)

    def _draw_tiles(self, painter: QPainter) -> None:
        cs = self._cell_size()
        radius = max(6.0, cs * 0.06)

        for tile in self._tiles.values():
            rect = self._cell_rect(tile.anim_row, tile.anim_col)

            painter.save()
            painter.setOpacity(tile.opacity)

            if tile.scale != 1.0:
                cx = rect.center().x()
                cy = rect.center().y()
                painter.translate(cx, cy)
                painter.scale(tile.scale, tile.scale)
                painter.translate(-cx, -cy)

            self._draw_single_tile(painter, rect, tile.value, radius)
            painter.restore()

    def _draw_single_tile(
        self, painter: QPainter, rect: QRectF, value: int, radius: float,
    ) -> None:
        # Background
        bg_color = self._theme.tile_bg(value)
        fg_color = self._theme.tile_fg(value)

        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)

        if self._theme.name == "neon":
            # Gradient fill for neon tiles
            grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
            grad.setColorAt(0, bg_color.lighter(130))
            grad.setColorAt(1, bg_color)
            painter.fillPath(path, grad)

            # Neon glow border
            glow = QPen(bg_color.lighter(200), 1.5)
            painter.setPen(glow)
            painter.drawPath(path)
        else:
            painter.fillPath(path, bg_color)
            painter.setPen(Qt.PenStyle.NoPen)

        # Text
        text = str(value)
        font_size = self._font_size_for(len(text), self._cell_size())
        font = self._make_font(FONT_PRIMARY, font_size, bold=True)
        painter.setFont(font)
        painter.setPen(fg_color)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)

    @staticmethod
    def _font_size_for(num_digits: int, cell_size: float) -> int:
        base = max(10, int(cell_size * 0.38))
        if num_digits <= 2:
            return base
        if num_digits == 3:
            return max(10, int(base * 0.78))
        if num_digits == 4:
            return max(10, int(base * 0.62))
        return max(10, int(base * 0.50))

    @staticmethod
    def _make_font(family: str, size: int, bold: bool = False) -> QFont:
        font = QFont(family)
        if not font.exactMatch():
            font = QFont(FONT_SECONDARY)
            if not font.exactMatch():
                font = QFont(FONT_FALLBACK)
        font.setPointSize(size)
        font.setBold(bold)
        return font

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.update()
