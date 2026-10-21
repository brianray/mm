"""Grid and Serializer: pair normalised rows with column types, one typed cell at a time."""

from __future__ import annotations

import logging
from typing import Any

from .errors import DataMismatchError
from .model import MISSING, DataModel
from .types import BaseFieldType, NoneFieldType, StringFieldType

log = logging.getLogger(__name__)

__all__ = ["GridBase", "Serializer"]


class GridBase:
    """A 2-D list of field type instances (``grid_data``), populated row by row.

    The serializer sets ``row_count``, ``col_count``, ``headers`` (field type classes),
    ``titles`` and ``data_model`` before calling ``populate``. Subclass and override
    ``populate`` to read rows from a custom source (see ``mm.contrib.django.grid``).
    """

    row_count: int
    col_count: int
    headers: list[type[BaseFieldType]]
    titles: list[Any]
    data_model: DataModel | None = None

    def __init__(self) -> None:
        self.grid_data: list[list[BaseFieldType]] = []
        self.missing = 0

    def populate(self, indata: Any, config: Any) -> None:
        for required in ("row_count", "col_count", "headers", "titles"):
            if not hasattr(self, required):
                raise AttributeError(f"missing required attribute to Grid: {required}")
        model = self.data_model
        if model is None or not hasattr(model, "table"):
            model = DataModel(indata, order=self.titles, config=config)
        ignore = bool(config.get("ignore_data_mismatch", True)) if config is not None else True

        self.grid_data = []
        for row_id, row in enumerate(model.table.rows[: self.row_count]):
            cells: list[BaseFieldType] = []
            for col_id in range(self.col_count):
                value = model.value_at(row, col_id)
                cells.append(self.make_cell(model, row_id, col_id, value, ignore))
            self.grid_data.append(cells)
        log.debug("populated grid %sx%s", self.row_count, self.col_count)
        if self.missing:
            log.debug("%d missing items", self.missing)

    def make_cell(
        self, model: DataModel, row_id: int, col_id: int, value: Any, ignore: bool
    ) -> BaseFieldType:
        """Wrap one raw value in its field type."""
        if value is MISSING:
            self.missing += 1
            if not ignore:
                raise DataMismatchError(
                    f"No value for column {self.titles[col_id]!r} in row {row_id + 1}"
                )
            return NoneFieldType()
        if isinstance(value, BaseFieldType):
            return value
        if value is None:
            return NoneFieldType()

        title = self.titles[col_id]
        column_types = getattr(model, "column_types", {})
        explicit = column_types.get(title, column_types.get(col_id))
        if explicit is not None:
            try:
                return explicit.from_value(value)
            except (TypeError, ValueError) as exc:
                if not ignore:
                    raise DataMismatchError(
                        f"Row {row_id + 1}, column {title!r}: {value!r} is not a valid "
                        f"{explicit.type_name} ({exc})"
                    ) from exc
                log.warning(
                    "row %d column %r: %r is not a valid %s; writing as inferred type",
                    row_id + 1,
                    title,
                    value,
                    explicit.type_name,
                )
        field_type = model.figure_out_type(value)
        try:
            return field_type.from_value(value)
        except (TypeError, ValueError):
            return StringFieldType.from_value(value)


class Serializer:
    """Pairs data with models and returns a populated grid."""

    def __init__(self, data_model: Any, data: Any, config: Any, grid_class: type = GridBase):
        self.data = data
        self.data_model = data_model
        self.grid_class = grid_class
        self.config = config

    def serialize(self) -> Any:
        """Return the serialised data as a populated grid instance."""
        grid = self.grid_class()
        table = getattr(self.data_model, "table", None)
        grid.row_count = len(table.rows) if table is not None else _count(self.data)
        grid.headers = list(self.data_model.field_headers)
        grid.col_count = len(grid.headers)
        grid.titles = list(self.data_model.field_titles)
        grid.data_model = self.data_model
        grid.populate(self.data, self.config)
        return grid


def _count(data: Any) -> int:
    if hasattr(data, "count") and callable(data.count):
        try:
            return int(data.count())
        except TypeError:
            pass
    return len(data)
