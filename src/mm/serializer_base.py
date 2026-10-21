"""Backwards-compatible alias for ``mm.serializer_base`` (Marmir 0.x). Prefer ``mm.grid``."""

from .grid import Serializer

__all__ = ["Serializer"]
