"""CSS-like style strings.

Marmir styles are written like inline CSS so humans and LLMs can write them without
learning a spreadsheet API::

    "color: #FFFFFF; background-color: navy; font-weight: bold; text-align: center"

Supported properties: ``color``, ``background-color`` (``background``), ``font-family``,
``font-size`` (``pt`` or ``px``), ``font-weight`` (``bold``/``normal``/100-900),
``font-style`` (``italic``/``bold`` for legacy), ``text-decoration``
(``underline``/``line-through``), ``text-align`` (``left``/``center``/``right``/``justify``),
``vertical-align`` (``top``/``middle``/``bottom``), ``white-space`` (``normal`` wraps,
``nowrap``), ``wrap`` (``true``/``false``), ``border``/``border-style``
(``thin``/``medium``/``thick``/``dashed``/``dotted``/``double``/``none``),
``border-color`` and ``number-format``.
"""

from __future__ import annotations

import contextlib
import logging
from dataclasses import dataclass, fields, replace
from functools import lru_cache

from .colors import parse_color

log = logging.getLogger(__name__)

__all__ = ["Style", "StyleBase", "merge_styles", "parse_style"]

_BORDER_STYLES = {"thin", "medium", "thick", "dashed", "dotted", "double", "hair", "none"}
_ALIGN = {"left", "center", "right", "justify", "general", "fill"}
_VALIGN = {"top": "top", "middle": "center", "center": "center", "bottom": "bottom"}


@dataclass(frozen=True)
class Style:
    """A parsed, immutable cell style. ``None`` means "not set"."""

    color: str | None = None  # RRGGBB
    background_color: str | None = None  # RRGGBB
    font_family: str | None = None
    font_size: float | None = None  # points
    bold: bool | None = None
    italic: bool | None = None
    underline: bool | None = None
    strike: bool | None = None
    text_align: str | None = None
    vertical_align: str | None = None
    wrap: bool | None = None
    border_style: str | None = None
    border_color: str | None = None  # RRGGBB
    number_format: str | None = None

    def merged(self, other: Style | None) -> Style:
        """Return a copy with every property set on ``other`` taking precedence."""
        if other is None:
            return self
        updates = {
            f.name: getattr(other, f.name)
            for f in fields(other)
            if getattr(other, f.name) is not None
        }
        return replace(self, **updates)

    def is_empty(self) -> bool:
        return all(getattr(self, f.name) is None for f in fields(self))

    def to_css(self) -> str:
        """Render back to a CSS string (also used by the HTML composer)."""
        parts: list[str] = []
        if self.color:
            parts.append(f"color: #{self.color}")
        if self.background_color:
            parts.append(f"background-color: #{self.background_color}")
        if self.font_family:
            parts.append(f"font-family: {self.font_family}")
        if self.font_size:
            parts.append(f"font-size: {self.font_size:g}pt")
        if self.bold is not None:
            parts.append(f"font-weight: {'bold' if self.bold else 'normal'}")
        if self.italic is not None:
            parts.append(f"font-style: {'italic' if self.italic else 'normal'}")
        decorations = [
            n for n, on in (("underline", self.underline), ("line-through", self.strike)) if on
        ]
        if decorations:
            parts.append(f"text-decoration: {' '.join(decorations)}")
        if self.text_align:
            parts.append(f"text-align: {self.text_align}")
        if self.vertical_align:
            css_valign = "middle" if self.vertical_align == "center" else self.vertical_align
            parts.append(f"vertical-align: {css_valign}")
        if self.wrap is not None:
            parts.append(f"white-space: {'normal' if self.wrap else 'nowrap'}")
        if self.border_style and self.border_style != "none":
            width = {"thin": "1px", "hair": "1px", "medium": "2px", "thick": "3px"}.get(
                self.border_style, "1px"
            )
            line = (
                self.border_style
                if self.border_style in {"dashed", "dotted", "double"}
                else "solid"
            )
            color = f" #{self.border_color}" if self.border_color else ""
            parts.append(f"border: {width} {line}{color}")
        return "; ".join(parts)


@lru_cache(maxsize=1024)
def parse_style(css: str | None) -> Style:
    """Parse a CSS-like string into a ``Style``. Unknown properties are logged and skipped."""
    if not css:
        return Style()
    values: dict[str, object] = {}
    for declaration in css.split(";"):
        if not declaration.strip():
            continue
        if ":" not in declaration:
            log.warning("ignoring malformed style declaration %r", declaration)
            continue
        key, _, raw = declaration.partition(":")
        key = key.strip().lower().replace("_", "-")
        value = raw.strip()
        lowered = value.lower()
        try:
            _apply(values, key, value, lowered)
        except ValueError as exc:
            log.warning("ignoring style %s: %s (%s)", key, value, exc)
    return Style(**values)  # type: ignore[arg-type]


def _apply(values: dict[str, object], key: str, value: str, lowered: str) -> None:
    if key == "color":
        values["color"] = parse_color(value)
    elif key in ("background-color", "background"):
        values["background_color"] = parse_color(value)
    elif key == "font-family":
        values["font_family"] = value.split(",")[0].strip().strip("'\"").replace("-", " ")
    elif key == "font-size":
        values["font_size"] = _font_size(lowered)
    elif key == "font-weight":
        values["bold"] = lowered == "bold" or (lowered.isdigit() and int(lowered) >= 600)
    elif key == "font-style":
        # legacy marmir used "font-style: bold"
        if lowered == "bold":
            values["bold"] = True
        else:
            values["italic"] = lowered in ("italic", "oblique")
    elif key == "text-decoration":
        values["underline"] = "underline" in lowered
        values["strike"] = "line-through" in lowered
    elif key == "text-align":
        if lowered not in _ALIGN:
            raise ValueError(f"expected one of {sorted(_ALIGN)}")
        values["text_align"] = lowered
    elif key == "vertical-align":
        if lowered not in _VALIGN:
            raise ValueError(f"expected one of {sorted(_VALIGN)}")
        values["vertical_align"] = _VALIGN[lowered]
    elif key == "white-space":
        values["wrap"] = lowered in ("normal", "pre-wrap", "wrap")
    elif key == "wrap":
        values["wrap"] = lowered in ("true", "yes", "1", "wrap")
    elif key in ("border", "border-style"):
        _border(values, lowered)
    elif key == "border-color":
        values["border_color"] = parse_color(value)
    elif key == "number-format":
        values["number_format"] = value.strip("'\"")
    else:
        raise ValueError("unknown style property")


def _font_size(lowered: str) -> float:
    if lowered.endswith("pt"):
        return float(lowered[:-2])
    if lowered.endswith("px"):
        return round(float(lowered[:-2]) * 0.75, 1)  # 96 dpi
    return float(lowered)


def _border(values: dict[str, object], lowered: str) -> None:
    # accepts "thin", "1px solid #ccc", "none"
    tokens = lowered.split()
    style = None
    for token in tokens:
        if token in _BORDER_STYLES:
            style = token
        elif token == "solid":
            style = style or "thin"
        elif token.endswith("px"):
            width = float(token[:-2])
            style = "thin" if width <= 1 else "medium" if width <= 2 else "thick"
        else:
            with contextlib.suppress(ValueError):
                values["border_color"] = parse_color(token)
    values["border_style"] = style or "thin"


def merge_styles(*styles: str | Style | None) -> Style:
    """Merge styles left to right; later values win."""
    result = Style()
    for item in styles:
        if item is None:
            continue
        result = result.merged(parse_style(item) if isinstance(item, str) else item)
    return result


class StyleBase:
    """Legacy mutable style object (``mm.style_base.StyleBase``).

    Kept for backwards compatibility; new code should use ``parse_style``.
    """

    color: str | None = None
    font_family: str | None = None
    background_color: str | None = None
    border_color: str | None = None
    font_style: str | None = None
    text_align: str | None = None
    _font_size_points: float | None = None

    @property
    def font_size(self) -> float | None:
        return self._font_size_points

    @font_size.setter
    def font_size(self, value: str) -> None:
        try:
            self._font_size_points = _font_size(str(value).lower())
        except ValueError:
            self._font_size_points = None

    def style_from_string(self, in_str: str) -> None:
        for attr in in_str.split(";"):
            if not attr.strip() or ":" not in attr:
                continue
            k, _, v = attr.partition(":")
            key = k.strip().replace("-", "_")
            if not hasattr(self, key):
                log.warning("Unknown style attribute %s: %s", key, v.strip())
                continue
            setattr(self, key, v.strip())

    def to_style(self) -> Style:
        css = "; ".join(
            f"{name.replace('_', '-')}: {getattr(self, name)}"
            for name in (
                "color",
                "font_family",
                "background_color",
                "border_color",
                "font_style",
                "text_align",
            )
            if getattr(self, name)
        )
        style = parse_style(css)
        if self.font_size:
            style = replace(style, font_size=self.font_size)
        return style
