"""Backwards-compatible aliases for ``mm.model_base`` (Marmir 0.x). Prefer ``mm.types``."""

from __future__ import annotations

from .model import DataModel
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
    HeaderFieldType,
    ImageFieldType,
    IntFieldType,
    NoneFieldType,
    PercentFieldType,
    StringFieldType,
    TimeFieldType,
    URLFieldType,
    all_field_types,
    is_custom_mm_type,
)


def get_members_list() -> list[type[BaseFieldType]]:
    """Every field type class (legacy helper)."""
    return all_field_types()


__all__ = [
    "BaseFieldType",
    "BoolFieldType",
    "CurrencyFieldType",
    "DataModel",
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
    "get_members_list",
    "is_custom_mm_type",
]
