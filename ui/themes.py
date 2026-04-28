"""
Theme definitions for 2048-Nexus.

Each theme provides:
- Background / surface colors
- Per-tile colors (value → QColor)
- Typography sizes
- Accent colors
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Tuple

from PyQt6.QtGui import QColor


# ---------------------------------------------------------------------------
# Color type alias
# ---------------------------------------------------------------------------
RGB = Tuple[int, int, int]


# ---------------------------------------------------------------------------
# Theme dataclass
# ---------------------------------------------------------------------------

@dataclass
class Theme:
    name: str
    # Window / surface
    bg_window: QColor
    bg_board: QColor
    bg_cell: QColor
    # Text
    text_light: QColor
    text_dark: QColor
    text_primary: QColor
    # Accents
    accent_primary: QColor
    accent_secondary: QColor
    # HUD
    hud_bg: QColor
    hud_text: QColor
    # Tile palette: tile value → (background, text) colors
    tile_palette: Dict[int, Tuple[QColor, QColor]] = field(default_factory=dict)

    def tile_bg(self, value: int) -> QColor:
        """Return background color for a tile value."""
        if value in self.tile_palette:
            return self.tile_palette[value][0]
        # Fallback for very large tiles
        return self.tile_palette.get(2048, (QColor("#6a1ea0"), QColor("#ffffff")))[0]

    def tile_fg(self, value: int) -> QColor:
        """Return text color for a tile value."""
        if value in self.tile_palette:
            return self.tile_palette[value][1]
        return QColor("#ffffff")


# ---------------------------------------------------------------------------
# Neon Cosmic theme (default)
# ---------------------------------------------------------------------------

def _neon_palette() -> Dict[int, Tuple[QColor, QColor]]:
    W = QColor("#ffffff")
    D = QColor("#1a0033")

    return {
        0:    (QColor("#1e1e3a"), QColor("#3a3a5a")),  # empty cell ghost
        1:    (QColor("#2d2b55"), W),
        2:    (QColor("#3d2b6e"), W),
        3:    (QColor("#4e2b80"), W),
        4:    (QColor("#5e2b91"), W),
        5:    (QColor("#6f2ba3"), W),
        8:    (QColor("#7f1fa8"), W),
        13:   (QColor("#9a1aa0"), W),
        16:   (QColor("#a81a88"), W),
        21:   (QColor("#c01870"), W),
        32:   (QColor("#d81550"), W),
        34:   (QColor("#e81840"), W),
        55:   (QColor("#f02030"), W),
        64:   (QColor("#f03010"), W),
        89:   (QColor("#f04800"), W),
        128:  (QColor("#f06000"), W),
        144:  (QColor("#f07800"), W),
        233:  (QColor("#f09000"), D),
        256:  (QColor("#f0a800"), D),
        377:  (QColor("#f0c000"), D),
        512:  (QColor("#f0d800"), D),
        610:  (QColor("#f0e800"), D),
        987:  (QColor("#e8f000"), D),
        1024: (QColor("#c8f000"), D),
        1597: (QColor("#a0f000"), D),
        2048: (QColor("#00f5ff"), D),
        4096: (QColor("#00d4ff"), D),
        8192: (QColor("#00aaff"), D),
    }


NEON_THEME = Theme(
    name="neon",
    bg_window=QColor("#0a0a1a"),
    bg_board=QColor("#12122a"),
    bg_cell=QColor("#1e1e3a"),
    text_light=QColor("#ffffff"),
    text_dark=QColor("#1a0033"),
    text_primary=QColor("#ffffff"),
    accent_primary=QColor("#00f5ff"),
    accent_secondary=QColor("#ff00e4"),
    hud_bg=QColor("#16162e"),
    hud_text=QColor("#e0e0ff"),
    tile_palette=_neon_palette(),
)


# ---------------------------------------------------------------------------
# Classic theme
# ---------------------------------------------------------------------------

def _classic_palette() -> Dict[int, Tuple[QColor, QColor]]:
    W = QColor("#f9f6f2")
    D = QColor("#776e65")

    return {
        0:    (QColor("#cdc1b4"), D),
        2:    (QColor("#eee4da"), D),
        4:    (QColor("#ede0c8"), D),
        8:    (QColor("#f2b179"), W),
        16:   (QColor("#f59563"), W),
        32:   (QColor("#f67c5f"), W),
        64:   (QColor("#f65e3b"), W),
        128:  (QColor("#edcf72"), W),
        256:  (QColor("#edcc61"), W),
        512:  (QColor("#edc850"), W),
        1024: (QColor("#edc53f"), W),
        2048: (QColor("#edc22e"), W),
        4096: (QColor("#ff6464"), W),
        8192: (QColor("#ff4040"), W),
    }


CLASSIC_THEME = Theme(
    name="classic",
    bg_window=QColor("#faf8ef"),
    bg_board=QColor("#bbada0"),
    bg_cell=QColor("#cdc1b4"),
    text_light=QColor("#f9f6f2"),
    text_dark=QColor("#776e65"),
    text_primary=QColor("#776e65"),
    accent_primary=QColor("#f67c5f"),
    accent_secondary=QColor("#edc22e"),
    hud_bg=QColor("#bbada0"),
    hud_text=QColor("#f9f6f2"),
    tile_palette=_classic_palette(),
)


# ---------------------------------------------------------------------------
# Minimal theme
# ---------------------------------------------------------------------------

def _minimal_palette() -> Dict[int, Tuple[QColor, QColor]]:
    W = QColor("#ffffff")
    D = QColor("#111111")

    def grey(r: int) -> QColor:
        v = int(240 - r * 8)
        return QColor(v, v, v)

    levels = [0, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192]
    palette = {}
    for i, lvl in enumerate(levels):
        bg = grey(i)
        fg = W if i > 7 else D
        palette[lvl] = (bg, fg)
    return palette


MINIMAL_THEME = Theme(
    name="minimal",
    bg_window=QColor("#e0e0e0"),
    bg_board=QColor("#c0c0c0"),
    bg_cell=QColor("#d0d0d0"),
    text_light=QColor("#ffffff"),
    text_dark=QColor("#111111"),
    text_primary=QColor("#111111"),
    accent_primary=QColor("#333333"),
    accent_secondary=QColor("#666666"),
    hud_bg=QColor("#c0c0c0"),
    hud_text=QColor("#111111"),
    tile_palette=_minimal_palette(),
)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

THEMES: Dict[str, Theme] = {
    "neon": NEON_THEME,
    "classic": CLASSIC_THEME,
}


def get_theme(name: str) -> Theme:
    """Return a theme by name, defaulting to neon."""
    return THEMES.get(name, NEON_THEME)
