"""Backwards-compatible alias for ``mm.config_base`` (Marmir 0.x). Prefer ``mm.config``."""

from .config import Config, ConfigBase

__all__ = ["Config", "ConfigBase"]
