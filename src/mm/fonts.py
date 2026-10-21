"""Text width measurement for automatic column sizing.

Uses per-character advance widths and kerning pairs for the common Microsoft core fonts
(Arial, Times New Roman, Verdana, Georgia, ...), shipped as ``_data/font_metrics.json.gz``.
Widths are in 1/256ths of the font's em; unknown fonts fall back to Arial.
"""

from __future__ import annotations

import gzip
import json
import unicodedata
from functools import lru_cache
from importlib import resources
from typing import Any

__all__ = ["available_fonts", "get_string_width", "string_width_chars"]

_DEFAULT_FONT = "Arial"


@lru_cache(maxsize=1)
def _font_data() -> dict[str, Any]:
    raw = resources.files("mm").joinpath("_data/font_metrics.json.gz").read_bytes()
    data: dict[str, Any] = json.loads(gzip.decompress(raw))
    return data


def available_fonts() -> list[str]:
    """Font names with metrics, e.g. ``["Arial", "Arial Bold", ...]``."""
    return sorted(name.replace("_", " ") for name in _font_data())


@lru_cache(maxsize=256)
def _resolve_font(font_name: str | None, bold: bool = False, italic: bool = False) -> str:
    data = _font_data()
    base = (font_name or _DEFAULT_FONT).strip().replace("-", "_").replace(" ", "_")
    candidates = []
    suffix = "_".join(s for s, on in (("Bold", bold), ("Italic", italic)) if on)
    for name in (base, base.title(), base.capitalize()):
        if suffix:
            candidates.append(f"{name}_{suffix}")
        candidates.append(name)
    for name in candidates:
        if name in data:
            return name
    lowered = {k.lower(): k for k in data}
    for name in candidates:
        if name.lower() in lowered:
            return lowered[name.lower()]
    return f"{_DEFAULT_FONT}_Bold" if bold else _DEFAULT_FONT


def get_string_width(
    font_name: str | None, point_size: float, text: str, bold: bool = False, italic: bool = False
) -> float:
    """Width of ``text`` in points (1/72 inch) when set in ``font_name`` at ``point_size``."""
    font = _font_data()[_resolve_font(font_name, bold, italic)]
    values = font["values"]
    default = font["default_width"]
    total = 0.0
    for index, char in enumerate(text):
        entry = values.get(char)
        if entry is None:
            wide = unicodedata.east_asian_width(char) in ("W", "F")
            total += default * (2 if wide else 1)
            continue
        width, kerns = entry
        total += width
        if index + 1 < len(text):
            total += kerns.get(text[index + 1], 0)
    return total * point_size / 256.0


def string_width_chars(
    text: str, font_name: str | None = None, point_size: float = 10, bold: bool = False
) -> float:
    """Width of the longest line of ``text`` in Excel "character" units.

    Excel column widths count characters of the default font (Calibri/Arial 10-11pt,
    whose digit is ~5.5pt wide).
    """
    longest = max(
        (get_string_width(font_name, point_size, line, bold) for line in text.splitlines() or [""]),
        default=0.0,
    )
    return longest / 5.5
