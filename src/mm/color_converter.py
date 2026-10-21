"""Backwards-compatible alias for ``mm.color_converter`` (Marmir 0.x). Prefer ``mm.colors``."""

from .colors import EXCEL_PALETTE, get_closest_rgb_match, rgb

__all__ = ["EXCEL_PALETTE", "get_closest_rgb_match", "rgb"]
