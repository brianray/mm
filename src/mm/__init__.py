"""Marmir: Python data structures to spreadsheets -- built for humans and GenAI agents.

>>> import mm
>>> doc = mm.Document([{"id": 1, "msg": "hello"}])
>>> doc.write("hello.xlsx")  # doctest: +SKIP

See https://github.com/brianray/mm for documentation.
"""

from __future__ import annotations

import logging
from typing import Any

from .composers import available_formats, register_composer
from .composers.base import ComposerBase
from .config import Config, ConfigBase
from .document import Document, DocumentWriter
from .errors import (
    DataMismatchError,
    EmptyDataError,
    MarmirError,
    MissingDependencyError,
    SpecValidationError,
    UnsupportedFormatError,
)
from .grid import GridBase, Serializer
from .model import DataModel
from .reader import Sheet, read, read_document
from .spec import WORKBOOK_SPEC_SCHEMA, from_spec, validate_spec
from .types import (
    BaseFieldType,
    BoolFieldType,
    CurrencyFieldType,
    DateFieldType,
    DateTimeFieldType,
    DecimalFieldType,
    DurationFieldType,
    FloatFieldType,
    FormulaFieldType,
    ImageFieldType,
    IntFieldType,
    NoneFieldType,
    PercentFieldType,
    StringFieldType,
    TimeFieldType,
    URLFieldType,
)

__version__ = "2.0.0"
__author__ = ["Brian Ray <brianhray@gmail.com>"]

logging.getLogger(__name__).addHandler(logging.NullHandler())

# Friendly field-type names (the legacy API used Date, URL, Image and Formula).
Date = DateFieldType
DateTime = DateTimeFieldType
Time = TimeFieldType
Duration = DurationFieldType
URL = URLFieldType
Image = ImageFieldType
Formula = FormulaFieldType
Number = FloatFieldType
Integer = IntFieldType
Text = StringFieldType
Bool = BoolFieldType
Percent = PercentFieldType
Currency = CurrencyFieldType
Empty = NoneFieldType


def Cell(value: Any, *, style: str | None = None, format: str | None = None) -> BaseFieldType:
    """Wrap any value with a per-cell ``style`` and/or number ``format``.

    >>> mm.Cell(42, style="background-color: yellow", format="#,##0")  # doctest: +SKIP
    """
    from .model import figure_out_type

    if isinstance(value, BaseFieldType):
        if style is not None:
            value.style = style
        if format is not None:
            value.format = format
        return value
    return figure_out_type(value).from_value(value, style=style, format=format)


def write(data: Any, target: Any, format: str | None = None, **kwargs: Any) -> Any:
    """One-liner: ``mm.write(rows, "out.xlsx", autofilter=True)``."""
    return Document(data, **kwargs).write(target, format=format)


__all__ = [
    "URL",
    "WORKBOOK_SPEC_SCHEMA",
    "BaseFieldType",
    "Bool",
    "BoolFieldType",
    "Cell",
    "ComposerBase",
    "Config",
    "ConfigBase",
    "Currency",
    "CurrencyFieldType",
    "DataMismatchError",
    "DataModel",
    "Date",
    "DateFieldType",
    "DateTime",
    "DateTimeFieldType",
    "DecimalFieldType",
    "Document",
    "DocumentWriter",
    "Duration",
    "DurationFieldType",
    "Empty",
    "EmptyDataError",
    "FloatFieldType",
    "Formula",
    "FormulaFieldType",
    "GridBase",
    "Image",
    "ImageFieldType",
    "IntFieldType",
    "Integer",
    "MarmirError",
    "MissingDependencyError",
    "NoneFieldType",
    "Number",
    "Percent",
    "PercentFieldType",
    "Serializer",
    "Sheet",
    "SpecValidationError",
    "StringFieldType",
    "Text",
    "Time",
    "TimeFieldType",
    "URLFieldType",
    "UnsupportedFormatError",
    "__version__",
    "available_formats",
    "from_spec",
    "read",
    "read_document",
    "register_composer",
    "validate_spec",
    "write",
]
