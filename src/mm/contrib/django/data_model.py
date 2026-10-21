"""``DjangoDataModel``: column definitions from a Django model's fields."""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import Any

from django.db import models

from mm import types as t
from mm.errors import EmptyDataError

log = logging.getLogger(__name__)

__all__ = ["DjangoDataModel"]


def _fields(*names: str) -> tuple[type, ...]:
    # some field classes were removed in newer Django versions
    return tuple(getattr(models, n) for n in names if hasattr(models, n))


# Order matters: more specific classes first (DateTimeField subclasses DateField, and
# BigAutoField/PositiveIntegerField subclass IntegerField).
TYPE_MAPPING: tuple[tuple[tuple[type, ...], type[t.BaseFieldType]], ...] = (
    (_fields("DateTimeField"), t.DateTimeFieldType),
    (_fields("DateField"), t.DateFieldType),
    (_fields("TimeField"), t.TimeFieldType),
    (_fields("DurationField"), t.DurationFieldType),
    (_fields("URLField"), t.URLFieldType),
    (_fields("BooleanField", "NullBooleanField"), t.BoolFieldType),
    (
        _fields(
            "AutoField",
            "BigAutoField",
            "SmallAutoField",
            "IntegerField",
            "BigIntegerField",
            "SmallIntegerField",
            "PositiveIntegerField",
            "PositiveSmallIntegerField",
            "PositiveBigIntegerField",
        ),
        t.IntFieldType,
    ),
    (_fields("DecimalField"), t.DecimalFieldType),
    (_fields("FloatField"), t.FloatFieldType),
    (_fields("FileField", "ImageField", "BinaryField"), t.NoneFieldType),
    (
        _fields(
            "CharField",
            "TextField",
            "EmailField",
            "SlugField",
            "FilePathField",
            "GenericIPAddressField",
            "IPAddressField",
            "CommaSeparatedIntegerField",
            "UUIDField",
            "JSONField",
        ),
        t.StringFieldType,
    ),
)


class DjangoDataModel:
    """Builds ``field_titles``/``field_headers`` from the model's concrete fields.

    Args:
        data: a QuerySet (or list of model instances).
        order: optional field names to include, in order.
        column_types: optional ``{"field": mm.Date}`` overrides.
        verbose_names: use ``verbose_name`` as the header text (default False).
    """

    def __init__(
        self,
        data: Any,
        order: Sequence[str] | None = None,
        column_types: Mapping[str, Any] | None = None,
        verbose_names: bool = False,
        **_: Any,
    ):
        model = getattr(data, "model", None)
        if model is None:
            items = list(data)
            if not items:
                raise EmptyDataError("Can not make spreadsheets with an empty set")
            model = type(items[0])
        fields = {f.name: f for f in model._meta.concrete_fields}
        names = list(order) if order else list(fields)
        unknown = [n for n in names if n not in fields]
        if unknown:
            raise ValueError(f"unknown field(s) {unknown} on {model.__name__}")
        self.field_names = names
        self.field_titles = [str(fields[n].verbose_name) if verbose_names else n for n in names]
        self.field_headers = []
        for name in names:
            override = (column_types or {}).get(name)
            if isinstance(override, str):
                override = t.field_type_for_name(override)
            self.field_headers.append(override or self.figure_out_type(fields[name]))
            log.debug("created field type %s for %s", self.field_headers[-1].__name__, name)

    @staticmethod
    def figure_out_type(field: Any) -> type[t.BaseFieldType]:
        if field.is_relation:
            return t.StringFieldType
        for classes, field_type in TYPE_MAPPING:
            if classes and isinstance(field, classes):
                return field_type
        log.warning("Returning string type for field type %s", type(field).__name__)
        return t.StringFieldType
