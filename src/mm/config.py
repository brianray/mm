"""Document configuration.

``Config`` keeps the legacy ``ConfigBase`` behaviour (class-level defaults that can be
overridden per instance with ``config_dict``) while adding new options. Unknown keys are
kept, so custom composers can read their own settings with ``config.get("my_key")``.
"""

from __future__ import annotations

import copy
import logging
from typing import Any

log = logging.getLogger(__name__)

__all__ = ["DEFAULTS", "Config", "ConfigBase"]

#: Every documented option and its default value.
DEFAULTS: dict[str, Any] = {
    # -- layout ---------------------------------------------------------------------
    "headers": True,
    "freeze_row": 1,
    "freeze_col": 0,
    "autofilter": False,
    "adjust_all_col_width": True,
    "min_col_width": 6,
    "max_col_width": 60,
    "column_widths": {},
    # -- styling (CSS-like strings, see mm.style) ------------------------------------
    "header_style": (
        "color: #FFFFFF; font-family: Arial; font-weight: bold; "
        "background-color: #1F4E79; font-size: 11pt; text-align: center"
    ),
    "row_styles": (
        "color: #000000; font-family: Arial; font-size: 10pt; background-color: #FFFFFF",
        "color: #000000; font-family: Arial; font-size: 10pt; background-color: #F2F2F2",
    ),
    "column_styles": {},
    # -- formats ----------------------------------------------------------------------
    "datetime_format": "M/D/YY h:mm:ss",
    "date_format": "M/D/YY",
    "time_format": "h:mm:ss",
    "duration_format": "[h]:mm:ss",
    "number_formats": {},
    # -- data handling ----------------------------------------------------------------
    "ignore_data_mismatch": True,
    "strict_columns": False,
    "infer_formulas": True,
    "infer_rows": None,
    "escape_formula_strings": True,
    # -- text formats -----------------------------------------------------------------
    "csv_delimiter": ",",
    "max_rows": None,
    # -- document properties ------------------------------------------------------------
    "title": None,
    "author": None,
    "description": None,
}

#: Legacy spellings that map onto current option names.
ALIASES: dict[str, str] = {
    "INGORE_DATA_MISMATCH": "ignore_data_mismatch",
    "IGNORE_DATA_MISMATCH": "ignore_data_mismatch",
}


class Config:
    """Holds the configuration for one ``Document`` (one sheet).

    >>> cfg = Config({"headers": False})
    >>> cfg.headers, cfg.freeze_row
    (False, 1)
    """

    def __init__(self, config_dict: dict[str, Any] | None = None, **options: Any):
        # subclasses may override defaults with class attributes (legacy ConfigBase style)
        for key, value in DEFAULTS.items():
            object.__setattr__(self, key, copy.deepcopy(getattr(type(self), key, value)))
        if config_dict:
            self.set_dict(config_dict)
        if options:
            self.set_dict(options)

    def __setattr__(self, key: str, value: Any) -> None:
        object.__setattr__(self, ALIASES.get(key, key), value)

    def __getattr__(self, key: str) -> Any:
        # only called for missing attributes: resolve legacy aliases
        if key in ALIASES:
            return getattr(self, ALIASES[key])
        raise AttributeError(key)

    def get(self, key: str, default: Any = None) -> Any:
        """Return an option, or ``default`` when it is unset or ``None``."""
        value = getattr(self, ALIASES.get(key, key), None)
        return default if value is None else value

    def set_dict(self, config_dict: dict[str, Any]) -> Config:
        """Update options from a dict; returns ``self`` for chaining."""
        for key, value in config_dict.items():
            name = ALIASES.get(key, key)
            if name not in DEFAULTS:
                log.debug("custom config option %r", name)
            if name == "row_styles" and isinstance(value, str):
                value = (value,)
            setattr(self, name, value)
        return self

    def to_dict(self) -> dict[str, Any]:
        """All options (defaults plus overrides) as a plain dict."""
        return {k: v for k, v in vars(self).items() if not k.startswith("_")}

    def changed(self) -> dict[str, Any]:
        """Only the options that differ from the defaults."""
        return {
            k: v
            for k, v in self.to_dict().items()
            if k not in DEFAULTS or _normalise(DEFAULTS[k]) != _normalise(v)
        }

    def copy(self) -> Config:
        return Config(copy.deepcopy(self.to_dict()))

    def __repr__(self) -> str:
        return f"Config({self.changed()!r})"


def _normalise(value: Any) -> Any:
    return list(value) if isinstance(value, tuple) else value


#: Backwards compatible name (``mm.config_base.ConfigBase``).
ConfigBase = Config
