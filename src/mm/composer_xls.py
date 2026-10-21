"""Backwards-compatible alias for ``mm.composer_xls`` (Marmir 0.x)."""

from .composers.xls import ComposerXLS
from .composers.xlsx import ComposerXLSX

__all__ = ["ComposerXLS", "ComposerXLSX"]
