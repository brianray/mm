"""Number-format helpers: C ``strftime`` codes -> Excel number formats."""

from __future__ import annotations

import re
from typing import Any

from .errors import UnsupportedFormatCodeException

__all__ = ["excel_date_format", "to_excel_from_C_codes"]

# (C code, Excel code or None when unsupported, reason)
_PAIRS: tuple[tuple[str, str | None, str], ...] = (
    ("%a", "ddd", ""),
    ("%A", "dddd", ""),
    ("%b", "mmm", ""),
    ("%B", "mmmm", ""),
    ("%c", "{datetime_format}", ""),
    ("%d", "dd", ""),
    ("%-d", "d", ""),
    ("%e", "d", ""),
    ("%f", "000", ""),  # use as "%S.%f" -> ss.000
    ("%H", "hh", ""),
    ("%-H", "h", ""),
    ("%I", "hh", ""),
    ("%-I", "h", ""),
    ("%j", None, "day of year is not supported in Excel number formats"),
    ("%m", "mm", ""),
    ("%-m", "m", ""),
    ("%M", "mm", ""),
    ("%p", "AM/PM", ""),
    ("%S", "ss", ""),
    ("%U", None, "Excel number formats have no week number"),
    ("%w", None, "Excel number formats have no numeric weekday"),
    ("%W", None, "Excel number formats have no week number"),
    ("%x", "{date_format}", ""),
    ("%X", "{time_format}", ""),
    ("%y", "yy", ""),
    ("%Y", "yyyy", ""),
    ("%z", None, "Excel has no time zone support"),
    ("%Z", None, "Excel has no time zone support"),
    ("%%", "%", ""),
)
_LOOKUP = {code: (excel, reason) for code, excel, reason in _PAIRS}
_TOKEN = re.compile(r"%-?[a-zA-Z%]")


def to_excel_from_C_codes(cdate_str: str, config: Any = None) -> str:
    """Translate a ``strftime`` pattern such as ``"%Y-%m-%dT%H:%M:%S"`` to Excel's syntax.

    Literal text other than common separators is quoted so Excel never mistakes it for a
    format code. Raises ``UnsupportedFormatCodeException`` for codes Excel cannot express.

    >>> to_excel_from_C_codes("%Y-%m-%dT%H:%M")
    'yyyy-mm-dd"T"hh:mm'
    """
    defaults = {
        "datetime_format": _cfg(config, "datetime_format", "M/D/YY h:mm:ss"),
        "date_format": _cfg(config, "date_format", "M/D/YY"),
        "time_format": _cfg(config, "time_format", "h:mm:ss"),
    }
    out: list[str] = []
    pos = 0
    for match in _TOKEN.finditer(cdate_str):
        if match.start() > pos:
            out.append(_literal(cdate_str[pos : match.start()]))
        code = match.group()
        if code not in _LOOKUP:
            raise UnsupportedFormatCodeException(f"Unknown format code {code} in {cdate_str!r}")
        if code in ("%I", "%-I") and "%p" not in _TOKEN.findall(cdate_str):
            raise UnsupportedFormatCodeException(
                f"{code} requires %p for a 12-hour Excel clock in {cdate_str!r}"
            )
        excel, reason = _LOOKUP[code]
        if excel is None:
            raise UnsupportedFormatCodeException(
                f"Could not replace {code} ({reason}) found in {cdate_str!r}"
            )
        if code == "%%":
            out.append(_literal("%"))
        else:
            out.append(excel.format(**defaults))
        pos = match.end()
    if pos < len(cdate_str):
        out.append(_literal(cdate_str[pos:]))
    return "".join(out)


def excel_date_format(fmt: str | None, default: str, config: Any = None) -> str:
    """Return an Excel format: C codes are translated, Excel codes pass through."""
    if not fmt:
        return default
    if "%" in fmt:
        return to_excel_from_C_codes(fmt, config)
    return fmt


_SAFE = set(" -/:.,()$+")


def _literal(text: str) -> str:
    # separators Excel understands stay bare (keeps "ss.000" fractional seconds working);
    # anything else is quoted so letters such as the "T" in ISO timestamps stay literal
    if set(text) <= _SAFE:
        return text
    return '"' + text.replace('"', "") + '"'


def _cfg(config: Any, key: str, default: str) -> str:
    if config is None:
        return default
    if hasattr(config, "get"):
        return str(config.get(key, default))
    return str(getattr(config, key, default))
