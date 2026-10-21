"""Color parsing and the legacy Excel 97 (XLS) palette."""

from __future__ import annotations

import re
from functools import lru_cache

__all__ = ["EXCEL_PALETTE", "get_closest_rgb_match", "parse_color", "rgb", "to_hex"]

NAMED_COLORS: dict[str, str] = {
    "black": "000000",
    "white": "FFFFFF",
    "red": "FF0000",
    "green": "008000",
    "lime": "00FF00",
    "blue": "0000FF",
    "yellow": "FFFF00",
    "cyan": "00FFFF",
    "aqua": "00FFFF",
    "magenta": "FF00FF",
    "fuchsia": "FF00FF",
    "maroon": "800000",
    "navy": "000080",
    "olive": "808000",
    "purple": "800080",
    "teal": "008080",
    "silver": "C0C0C0",
    "gray": "808080",
    "grey": "808080",
    "lightgray": "D3D3D3",
    "lightgrey": "D3D3D3",
    "darkgray": "A9A9A9",
    "darkgrey": "A9A9A9",
    "orange": "FFA500",
    "pink": "FFC0CB",
    "brown": "A52A2A",
    "gold": "FFD700",
    "lightblue": "ADD8E6",
    "lightgreen": "90EE90",
    "lightyellow": "FFFFE0",
    "darkblue": "00008B",
    "darkgreen": "006400",
    "darkred": "8B0000",
}

#: Excel 97 palette: "r, g, b" -> palette index (used by the XLS composer).
EXCEL_PALETTE: dict[tuple[int, int, int], int] = {
    (0, 0, 0): 0x08,
    (255, 255, 255): 0x09,
    (255, 0, 0): 0x0A,
    (0, 255, 0): 0x0B,
    (0, 0, 255): 0x0C,
    (255, 255, 0): 0x0D,
    (255, 0, 255): 0x0E,
    (0, 255, 255): 0x0F,
    (128, 0, 0): 0x10,
    (0, 128, 0): 0x11,
    (0, 0, 128): 0x12,
    (128, 128, 0): 0x13,
    (128, 0, 128): 0x14,
    (0, 128, 128): 0x15,
    (192, 192, 192): 0x16,
    (128, 128, 128): 0x17,
    (153, 153, 255): 0x18,
    (153, 51, 102): 0x1A,
    (255, 255, 204): 0x1C,
    (204, 255, 255): 0x1D,
    (102, 0, 102): 0x1E,
    (255, 128, 128): 0x1F,
    (0, 102, 204): 0x28,
    (204, 204, 255): 0x29,
    (0, 204, 255): 0x2A,
    (204, 255, 204): 0x2B,
    (255, 255, 153): 0x2C,
    (153, 204, 255): 0x2D,
    (255, 153, 204): 0x2E,
    (204, 153, 255): 0x2F,
    (255, 204, 153): 0x30,
    (51, 102, 255): 0x31,
    (51, 204, 204): 0x32,
    (153, 204, 0): 0x33,
    (255, 204, 0): 0x34,
    (255, 153, 0): 0x35,
    (255, 102, 0): 0x36,
    (102, 102, 153): 0x37,
    (150, 150, 150): 0x38,
    (0, 51, 102): 0x39,
    (51, 153, 102): 0x3A,
    (0, 51, 0): 0x3B,
    (51, 51, 0): 0x3C,
    (153, 51, 0): 0x3D,
    (51, 51, 153): 0x3E,
    (51, 51, 51): 0x3F,
}

_RGB_FUNC = re.compile(r"^rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*[\d.]+\s*)?\)$")


@lru_cache(maxsize=512)
def parse_color(value: str) -> str:
    """Normalise ``#RGB``, ``#RRGGBB``, ``rgb(r, g, b)`` or a CSS name to ``RRGGBB``.

    Raises ``ValueError`` for anything else.
    """
    text = value.strip().lower()
    if text in NAMED_COLORS:
        return NAMED_COLORS[text]
    match = _RGB_FUNC.match(text)
    if match:
        parts = [max(0, min(255, int(p))) for p in match.groups()]
        return "".join(f"{p:02X}" for p in parts)
    text = text.lstrip("#")
    if re.fullmatch(r"[0-9a-f]{3}", text):
        text = "".join(c * 2 for c in text)
    if re.fullmatch(r"[0-9a-f]{6}", text):
        return text.upper()
    if re.fullmatch(r"[0-9a-f]{8}", text):  # ARGB
        return text[2:].upper()
    raise ValueError(f"unrecognised color {value!r}")


def rgb(value: str) -> tuple[int, int, int]:
    """``"FF8000"`` (or any ``parse_color`` input) -> ``(255, 128, 0)``."""
    hexval = parse_color(value)
    return int(hexval[0:2], 16), int(hexval[2:4], 16), int(hexval[4:6], 16)


def to_hex(value: str) -> str:
    """``"red"`` -> ``"#FF0000"``."""
    return "#" + parse_color(value)


@lru_cache(maxsize=512)
def get_closest_rgb_match(value: str) -> int:
    """Return the Excel 97 palette index closest to ``value`` (legacy XLS output)."""
    r, g, b = rgb(value)
    best = min(
        EXCEL_PALETTE.items(),
        key=lambda item: (r - item[0][0]) ** 2 + (g - item[0][1]) ** 2 + (b - item[0][2]) ** 2,
    )
    return best[1]
