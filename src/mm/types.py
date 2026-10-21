"""Cell field types.

Every cell in a Marmir grid is an instance of a ``BaseFieldType`` subclass. Most of the
time Marmir infers the type from the Python value; wrap a value yourself (``mm.Date``,
``mm.URL``, ``mm.Formula``, ...) or pass ``column_types`` to be explicit.

Each type has a stable ``type_name`` (``"integer"``, ``"date"``, ...) that is used by the
JSON workbook spec, so GenAI tools can name types without knowing Python classes.
"""

from __future__ import annotations

import datetime as dt
import json
import re
from decimal import Decimal, InvalidOperation
from typing import Any, ClassVar

__all__ = [
    "TYPE_ALIASES",
    "BaseFieldType",
    "BoolFieldType",
    "CurrencyFieldType",
    "DateFieldType",
    "DateTimeFieldType",
    "DecimalFieldType",
    "DurationFieldType",
    "FloatFieldType",
    "FormulaFieldType",
    "HeaderFieldType",
    "ImageFieldType",
    "IntFieldType",
    "NoneFieldType",
    "PercentFieldType",
    "StringFieldType",
    "TimeFieldType",
    "URLFieldType",
    "all_field_types",
    "field_type_for_name",
    "is_custom_mm_type",
]


class BaseFieldType:
    """A typed cell value.

    Args:
        data: the raw Python value.
        style: optional CSS-like style string applied to just this cell, e.g.
            ``"background-color: yellow; font-weight: bold"``.
        format: optional number format. Excel format codes (``"0.00%"``) work everywhere;
            date types also accept C ``strftime`` codes (``"%Y-%m-%d"``).
    """

    type_name: ClassVar[str] = "base"
    #: Number format used when neither the cell, its style nor its column sets one.
    default_format: str | None = None

    def __init__(self, data: Any, *, style: str | None = None, format: str | None = None):
        self.data = data
        self.style = style
        self.format = format

    @classmethod
    def coerce(cls, value: Any) -> Any:
        """Convert ``value`` into the Python type this field holds.

        Raises ``ValueError``/``TypeError`` when the value cannot be converted.
        """
        return value

    @classmethod
    def from_value(cls, value: Any, **kwargs: Any) -> BaseFieldType:
        """Build an instance, coercing ``value`` first."""
        return cls(cls.coerce(value), **kwargs)

    def to_json(self) -> Any:
        """A JSON-safe representation of the value (used by JSON/Markdown output)."""
        return _json_safe(self.data)

    def display(self) -> str:
        """Plain-text rendering used by the text, Markdown, CSV and HTML composers."""
        if self.data is None:
            return ""
        return str(self.data)

    def __eq__(self, other: object) -> bool:
        if type(other) is not type(self):
            return NotImplemented
        return bool(self.__dict__ == other.__dict__)

    def __hash__(self) -> int:
        return hash((type(self), repr(self.data)))

    def __repr__(self) -> str:
        extras = "".join(
            f", {k}={v!r}"
            for k, v in self.__dict__.items()
            if k not in ("data", "default_format") and v is not None
        )
        return f"{type(self).__name__}({self.data!r}{extras})"


class HeaderFieldType(BaseFieldType):
    """A header (column title) cell."""

    type_name = "header"


class NoneFieldType(BaseFieldType):
    """An empty cell."""

    type_name = "empty"

    def __init__(self, data: Any = None, **kwargs: Any):
        super().__init__(data, **kwargs)

    @classmethod
    def coerce(cls, value: Any) -> Any:
        return None

    def to_json(self) -> Any:
        return None

    def display(self) -> str:
        return ""


class StringFieldType(BaseFieldType):
    type_name = "string"

    @classmethod
    def coerce(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value
        if isinstance(value, (dict, list, tuple)):
            return json.dumps(_json_safe(value), ensure_ascii=False)
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")
        return str(value)


class IntFieldType(BaseFieldType):
    type_name = "integer"

    @classmethod
    def coerce(cls, value: Any) -> Any:
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            if not value.is_integer():
                raise ValueError(f"{value!r} is not a whole number")
            return int(value)
        if isinstance(value, Decimal):
            return int(value)
        if isinstance(value, str):
            return int(_clean_number(value))
        raise TypeError(f"cannot convert {type(value).__name__} to integer")


class FloatFieldType(BaseFieldType):
    """A number. ``mm.Number(value, format="#,##0.00")`` is an alias."""

    type_name = "number"

    @classmethod
    def coerce(cls, value: Any) -> Any:
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, (int, float, Decimal)):
            return value
        if isinstance(value, str):
            text = _clean_number(value)
            try:
                return int(text)
            except ValueError:
                return float(text)
        raise TypeError(f"cannot convert {type(value).__name__} to number")


class DecimalFieldType(BaseFieldType):
    type_name = "decimal"

    @classmethod
    def coerce(cls, value: Any) -> Any:
        if isinstance(value, Decimal):
            return value
        if isinstance(value, bool):
            return Decimal(int(value))
        try:
            text = _clean_number(value) if isinstance(value, str) else str(value)
            return Decimal(text)
        except InvalidOperation as exc:
            raise ValueError(f"{value!r} is not a decimal") from exc

    def to_json(self) -> Any:
        return float(self.data) if self.data is not None else None


class PercentFieldType(FloatFieldType):
    """A fraction shown as a percent: ``mm.Percent(0.256, decimals=1)`` shows ``25.6%``."""

    type_name = "percent"

    def __init__(self, data: Any, decimals: int = 0, **kwargs: Any):
        self.decimals = decimals
        self.default_format = "0" + ("." + "0" * decimals if decimals else "") + "%"
        super().__init__(data, **kwargs)

    @classmethod
    def coerce(cls, value: Any) -> Any:
        if isinstance(value, str) and value.strip().endswith("%"):
            return float(_clean_number(value.strip()[:-1])) / 100
        return super().coerce(value)

    def display(self) -> str:
        if self.data is None:
            return ""
        return f"{float(self.data) * 100:.{self.decimals}f}%"


class CurrencyFieldType(FloatFieldType):
    """Money: ``mm.Currency(1234.5)`` shows ``$1,234.50``."""

    type_name = "currency"

    def __init__(self, data: Any, symbol: str = "$", decimals: int = 2, **kwargs: Any):
        self.symbol = symbol
        self.decimals = decimals
        places = "." + "0" * decimals if decimals else ""
        self.default_format = f'"{symbol}"#,##0{places};-"{symbol}"#,##0{places}'
        super().__init__(data, **kwargs)

    def display(self) -> str:
        if self.data is None:
            return ""
        value = float(self.data)
        sign = "-" if value < 0 else ""
        return f"{sign}{self.symbol}{abs(value):,.{self.decimals}f}"


class BoolFieldType(BaseFieldType):
    type_name = "boolean"

    _TRUE: ClassVar[set[str]] = {"true", "t", "yes", "y", "1", "on"}
    _FALSE: ClassVar[set[str]] = {"false", "f", "no", "n", "0", "off", ""}

    @classmethod
    def coerce(cls, value: Any) -> Any:
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            text = value.strip().lower()
            if text in cls._TRUE:
                return True
            if text in cls._FALSE:
                return False
        raise ValueError(f"{value!r} is not a boolean")

    def display(self) -> str:
        if self.data is None:
            return ""
        return "TRUE" if self.data else "FALSE"


class DateFieldType(BaseFieldType):
    """A date. ``format`` may be C ``strftime`` codes (legacy) or an Excel format."""

    type_name = "date"

    def __init__(self, data: Any, format: str | None = None, **kwargs: Any):
        super().__init__(data, format=format, **kwargs)

    @classmethod
    def coerce(cls, value: Any) -> Any:
        if isinstance(value, (dt.date, dt.datetime)):
            return _naive(value)
        if isinstance(value, str):
            text = value.strip()
            try:
                return dt.date.fromisoformat(text)
            except ValueError:
                return _parse_datetime(text)
        raise TypeError(f"cannot convert {type(value).__name__} to date")

    def to_json(self) -> Any:
        return self.data.isoformat() if self.data is not None else None

    def display(self) -> str:
        if self.data is None:
            return ""
        if self.format and "%" in self.format:
            return str(self.data.strftime(self.format))
        return str(
            self.data.isoformat(sep=" ") if isinstance(self.data, dt.datetime) else self.data
        )


class DateTimeFieldType(DateFieldType):
    """A date and time. Time zones are dropped (spreadsheets have none)."""

    type_name = "datetime"

    def __init__(self, data: Any, format: str | None = None, **kwargs: Any):
        if isinstance(data, dt.datetime) and data.tzinfo is not None:
            data = data.replace(tzinfo=None)
        super().__init__(data, format=format, **kwargs)

    @classmethod
    def coerce(cls, value: Any) -> Any:
        if isinstance(value, dt.datetime):
            return _naive(value)
        if isinstance(value, dt.date):
            return dt.datetime(value.year, value.month, value.day)
        if isinstance(value, str):
            return _parse_datetime(value.strip())
        raise TypeError(f"cannot convert {type(value).__name__} to datetime")


class TimeFieldType(BaseFieldType):
    type_name = "time"

    def __init__(self, data: Any, format: str | None = None, **kwargs: Any):
        if isinstance(data, dt.time) and data.tzinfo is not None:
            data = data.replace(tzinfo=None)
        super().__init__(data, format=format, **kwargs)

    @classmethod
    def coerce(cls, value: Any) -> Any:
        if isinstance(value, dt.datetime):
            return value.time()
        if isinstance(value, dt.time):
            return value.replace(tzinfo=None)
        if isinstance(value, str):
            return dt.time.fromisoformat(value.strip())
        raise TypeError(f"cannot convert {type(value).__name__} to time")

    def to_json(self) -> Any:
        return self.data.isoformat() if self.data is not None else None

    def display(self) -> str:
        if self.data is None:
            return ""
        if self.format and "%" in self.format:
            return str(self.data.strftime(self.format))
        return str(self.data.isoformat())


class DurationFieldType(BaseFieldType):
    """A ``timedelta``; shown as ``[h]:mm:ss``. Strings like ``"1:30:00"`` or seconds work."""

    type_name = "duration"

    @classmethod
    def coerce(cls, value: Any) -> Any:
        if isinstance(value, dt.timedelta):
            return value
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return dt.timedelta(seconds=value)
        if isinstance(value, str):
            parts = value.strip().split(":")
            if 1 <= len(parts) <= 3:
                nums = [float(p) for p in parts]
                while len(nums) < 3:
                    nums.insert(0, 0.0)
                return dt.timedelta(hours=nums[0], minutes=nums[1], seconds=nums[2])
        raise ValueError(f"{value!r} is not a duration")

    def to_json(self) -> Any:
        return self.data.total_seconds() if self.data is not None else None

    def display(self) -> str:
        if self.data is None:
            return ""
        total = int(self.data.total_seconds())
        sign = "-" if total < 0 else ""
        total = abs(total)
        return f"{sign}{total // 3600}:{total % 3600 // 60:02d}:{total % 60:02d}"


class URLFieldType(BaseFieldType):
    """A hyperlink. ``mm.URL("https://example.com", "Example")``."""

    type_name = "url"

    def __init__(self, path: Any, displayname: str | None = None, **kwargs: Any):
        self.displayname = displayname or path
        super().__init__(path, **kwargs)

    @classmethod
    def coerce(cls, value: Any) -> Any:
        return str(value)

    def to_json(self) -> Any:
        if self.displayname and self.displayname != self.data:
            return {"url": self.data, "text": self.displayname}
        return self.data

    def display(self) -> str:
        return "" if self.displayname is None else str(self.displayname)


class ImageFieldType(BaseFieldType):
    """An image file placed in the cell (XLSX/XLS). ``width``/``height`` are pixels."""

    type_name = "image"

    def __init__(
        self, path: Any, width: int | None = None, height: int | None = None, **kwargs: Any
    ):
        self.width = width
        self.height = height
        super().__init__(path, **kwargs)

    @classmethod
    def coerce(cls, value: Any) -> Any:
        return str(value)

    def to_json(self) -> Any:
        out: dict[str, Any] = {"image": str(self.data)}
        if self.width:
            out["width"] = self.width
        if self.height:
            out["height"] = self.height
        return out

    def display(self) -> str:
        return f"[image: {self.data}]"


class FormulaFieldType(BaseFieldType):
    """A spreadsheet formula. The leading ``=`` is optional: ``mm.Formula("SUM(B2:B5)")``."""

    type_name = "formula"

    @classmethod
    def coerce(cls, value: Any) -> Any:
        return str(value)

    @property
    def expression(self) -> str:
        """The formula without its leading ``=``."""
        return re.sub(r"^\s*=", "", str(self.data))

    def to_json(self) -> Any:
        return {"formula": self.expression}

    def display(self) -> str:
        return "=" + self.expression


TYPE_ALIASES: dict[str, type[BaseFieldType]] = {
    "string": StringFieldType,
    "str": StringFieldType,
    "text": StringFieldType,
    "integer": IntFieldType,
    "int": IntFieldType,
    "number": FloatFieldType,
    "float": FloatFieldType,
    "decimal": DecimalFieldType,
    "percent": PercentFieldType,
    "percentage": PercentFieldType,
    "currency": CurrencyFieldType,
    "money": CurrencyFieldType,
    "boolean": BoolFieldType,
    "bool": BoolFieldType,
    "date": DateFieldType,
    "datetime": DateTimeFieldType,
    "timestamp": DateTimeFieldType,
    "time": TimeFieldType,
    "duration": DurationFieldType,
    "url": URLFieldType,
    "link": URLFieldType,
    "hyperlink": URLFieldType,
    "image": ImageFieldType,
    "formula": FormulaFieldType,
    "empty": NoneFieldType,
    "none": NoneFieldType,
}


def field_type_for_name(name: str) -> type[BaseFieldType]:
    """Return the field type class for a spec type name such as ``"integer"``."""
    try:
        return TYPE_ALIASES[name.strip().lower()]
    except KeyError:
        valid = ", ".join(sorted({c.type_name for c in TYPE_ALIASES.values()}))
        raise ValueError(f"unknown column type {name!r}; valid types: {valid}") from None


def all_field_types() -> list[type[BaseFieldType]]:
    """Every concrete field type, including subclasses registered by users."""
    seen: list[type[BaseFieldType]] = []
    stack = [BaseFieldType]
    while stack:
        cls = stack.pop()
        for sub in cls.__subclasses__():
            if sub not in seen:
                seen.append(sub)
                stack.append(sub)
    return seen


def is_custom_mm_type(inst: Any) -> bool:
    """True when ``inst`` is already a Marmir field type instance."""
    return isinstance(inst, BaseFieldType)


def _naive(value: dt.date) -> dt.date:
    if isinstance(value, dt.datetime) and value.tzinfo is not None:
        return value.replace(tzinfo=None)
    return value


def _parse_datetime(text: str) -> dt.datetime:
    if text.endswith(("Z", "z")):
        text = text[:-1] + "+00:00"
    return _naive(dt.datetime.fromisoformat(text))  # type: ignore[return-value]


def _clean_number(text: str) -> str:
    cleaned = text.strip().replace(",", "").replace("_", "")
    cleaned = re.sub(r"^[$€£¥]", "", cleaned)
    if not cleaned:
        raise ValueError(f"{text!r} is not a number")
    return cleaned


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (dt.date, dt.time)):
        return value.isoformat()
    if isinstance(value, dt.timedelta):
        return value.total_seconds()
    if isinstance(value, BaseFieldType):
        return value.to_json()
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(v) for v in value]
    return str(value)
