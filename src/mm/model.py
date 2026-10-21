"""Data models: turn arbitrary Python data into rows plus typed column definitions.

``normalize_data`` accepts the shapes people (and LLMs) actually have:

* a list/tuple/generator of dicts, ``Mapping`` objects or dict-like rows
  (``psycopg2`` ``DictRow``/``RealDictRow``, ``sqlite3.Row``)
* a list of lists/tuples (pass ``order`` for the headers)
* dataclasses, ``NamedTuple``\\s, ``attrs``-style objects and Pydantic models
* a column-oriented dict: ``{"name": ["a", "b"], "qty": [1, 2]}``
* a pandas ``DataFrame``
* a DB-API cursor after ``execute()`` (column names come from ``cursor.description``)

``DataModel`` then decides one field type per column (``field_headers``) next to the
column titles (``field_titles``), exactly like the legacy API.
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import logging
import math
from collections.abc import Iterable, Mapping, Sequence
from decimal import Decimal
from typing import Any

from .errors import DataMismatchError, EmptyDataError
from .types import (
    BaseFieldType,
    BoolFieldType,
    DateFieldType,
    DateTimeFieldType,
    DecimalFieldType,
    DurationFieldType,
    FloatFieldType,
    FormulaFieldType,
    IntFieldType,
    NoneFieldType,
    StringFieldType,
    TimeFieldType,
    field_type_for_name,
)

log = logging.getLogger(__name__)

__all__ = ["DataModel", "Table", "figure_out_type", "normalize_data"]


@dataclasses.dataclass
class Table:
    """Normalised input: ``rows`` are dicts (``by_key=True``) or sequences."""

    rows: list[Any]
    columns: list[Any]
    by_key: bool


def normalize_data(data: Any, order: Sequence[Any] | None = None, strict: bool = False) -> Table:
    """Normalise ``data`` into a ``Table``. See the module docstring for accepted shapes."""
    order_list = list(order) if order is not None else None

    if _is_dataframe(data):
        return _from_dataframe(data, order_list)
    if _is_cursor(data):
        columns = [d[0] for d in data.description]
        rows = [list(r) for r in data.fetchall()]
        return Table(rows=rows, columns=order_list or columns, by_key=False)
    if isinstance(data, Mapping):
        return _from_columns(data, order_list)
    if isinstance(data, (str, bytes)) or not isinstance(data, Iterable):
        raise TypeError(
            f"cannot build a spreadsheet from {type(data).__name__}; "
            "pass a list of dicts, a list of lists with order=..., or a DataFrame"
        )

    rows = [_row_to_python(r) for r in data]
    if not rows:
        if order_list:
            return Table(rows=[], columns=order_list, by_key=True)
        raise EmptyDataError(
            "Can not make spreadsheets with an empty set (pass order= for headers)"
        )

    first = rows[0]
    if isinstance(first, Mapping):
        if order_list is not None:
            columns = order_list
        else:
            columns = list(first.keys())
            seen = set(columns)
            for index, row in enumerate(rows[1:], start=2):
                if not isinstance(row, Mapping):
                    raise DataMismatchError(f"Row {index} is not a mapping like row 1")
                extra = [k for k in row if k not in seen]
                if extra and strict:
                    raise DataMismatchError(
                        f"Data mismatch: Row {index} has {len(extra)} more columns than row 1: "
                        f"{extra}"
                    )
                for key in extra:
                    seen.add(key)
                    columns.append(key)
        return Table(rows=rows, columns=columns, by_key=True)

    if order_list is None:
        width = max(len(r) for r in rows)
        order_list = [f"Column {i + 1}" for i in range(width)]
        log.info("no order given for list rows; using generic headers")
    return Table(rows=[list(r) for r in rows], columns=order_list, by_key=False)


def _row_to_python(row: Any) -> Any:
    if isinstance(row, Mapping):
        return row
    if dataclasses.is_dataclass(row) and not isinstance(row, type):
        return {f.name: getattr(row, f.name) for f in dataclasses.fields(row)}
    if hasattr(row, "model_dump"):  # pydantic v2
        return row.model_dump()
    if hasattr(row, "_asdict"):  # namedtuple
        return row._asdict()
    if hasattr(row, "keys") and hasattr(row, "__getitem__"):  # sqlite3.Row, psycopg DictRow
        return {k: row[k] for k in row.keys()}  # noqa: SIM118 -- sqlite3.Row has no __iter__ over keys
    if hasattr(row, "iteritems"):  # legacy dict-like objects
        return dict(row.iteritems())
    if isinstance(row, (list, tuple)):
        return row
    if isinstance(row, (str, bytes)):
        return [row]
    if isinstance(row, Iterable):
        return list(row)
    if hasattr(row, "__dict__"):
        return {k: v for k, v in vars(row).items() if not k.startswith("_")}
    return [row]


def _from_columns(data: Mapping[Any, Any], order: list[Any] | None) -> Table:
    columns = order or list(data.keys())
    lengths = {len(list(v)) if not isinstance(v, (str, bytes)) else -1 for v in data.values()}
    if -1 in lengths or not data:
        raise TypeError("a dict must map column names to lists of values (column-oriented data)")
    if len(lengths) > 1:
        raise DataMismatchError(f"column lists have different lengths: {sorted(lengths)}")
    height = lengths.pop()
    lists = {k: list(v) for k, v in data.items()}
    rows = [{k: lists[k][i] for k in lists} for i in range(height)]
    if not rows and not columns:
        raise EmptyDataError("Can not make spreadsheets with an empty set")
    return Table(rows=rows, columns=columns, by_key=True)


def _is_dataframe(data: Any) -> bool:
    return (
        type(data).__name__ == "DataFrame" and hasattr(data, "to_dict") and hasattr(data, "columns")
    )


def _is_cursor(data: Any) -> bool:
    return (
        hasattr(data, "description")
        and hasattr(data, "fetchall")
        and getattr(data, "description", None) is not None
    )


def _from_dataframe(df: Any, order: list[Any] | None) -> Table:
    columns = order or [str(c) for c in df.columns]
    rename = {c: str(c) for c in df.columns}
    records = df.rename(columns=rename).to_dict(orient="records")
    rows = [{k: _from_numpy(v) for k, v in r.items()} for r in records]
    return Table(rows=rows, columns=columns, by_key=True)


def _from_numpy(value: Any) -> Any:
    if value is None:
        return None
    if type(value).__name__ in ("NaTType", "NAType"):
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if hasattr(value, "to_pydatetime"):
        return value.to_pydatetime()
    if hasattr(value, "to_pytimedelta"):
        return value.to_pytimedelta()
    if type(value).__module__ == "numpy" and hasattr(value, "item"):
        item = value.item()
        if isinstance(item, float) and math.isnan(item):
            return None
        return item
    return value


def figure_out_type(item: Any, infer_formulas: bool = True) -> type[BaseFieldType]:
    """Pick the field type for a single Python value."""
    if isinstance(item, BaseFieldType):
        return type(item)
    if item is None:
        return NoneFieldType
    if isinstance(item, bool):
        return BoolFieldType
    if isinstance(item, int):
        return IntFieldType
    if isinstance(item, float):
        return NoneFieldType if math.isnan(item) else FloatFieldType
    if isinstance(item, Decimal):
        return DecimalFieldType
    if isinstance(item, dt.datetime):
        return DateTimeFieldType
    if isinstance(item, dt.date):
        return DateFieldType
    if isinstance(item, dt.time):
        return TimeFieldType
    if isinstance(item, dt.timedelta):
        return DurationFieldType
    if isinstance(item, str):
        if infer_formulas and item.startswith("=") and len(item) > 1:
            return FormulaFieldType
        return StringFieldType
    return StringFieldType


_NUMERIC_RANK = {IntFieldType: 0, FloatFieldType: 1, DecimalFieldType: 2}


def _merge_column_types(types: list[type[BaseFieldType]]) -> type[BaseFieldType]:
    concrete = [t for t in types if t is not NoneFieldType]
    if not concrete:
        return NoneFieldType
    unique = list(dict.fromkeys(concrete))
    if len(unique) == 1:
        return unique[0]
    # formulas mixed with values: the column's type is the value type
    values = [t for t in unique if t is not FormulaFieldType]
    if len(values) == 1:
        return values[0]
    if all(t in _NUMERIC_RANK for t in values):
        return max(values, key=lambda t: _NUMERIC_RANK[t])
    if set(values) <= {DateFieldType, DateTimeFieldType}:
        return DateTimeFieldType
    return StringFieldType


class DataModel:
    """Creates the column definitions for a sheet.

    Attributes:
        field_titles: column titles in display order.
        field_headers: one field type class per column.
        table: the normalised input rows (used by ``GridBase``).
    """

    def __init__(
        self,
        data: Any,
        order: Sequence[Any] | None = None,
        column_types: Mapping[Any, Any] | None = None,
        config: Any = None,
    ):
        strict = bool(getattr(config, "strict_columns", False))
        self.infer_formulas = bool(getattr(config, "infer_formulas", True))
        infer_rows = getattr(config, "infer_rows", None)

        self.table = normalize_data(data, order=order, strict=strict)
        self.field_titles: list[Any] = list(self.table.columns)
        self.column_types: dict[Any, type[BaseFieldType]] = {}
        for key, value in (column_types or {}).items():
            self.column_types[key] = field_type_for_name(value) if isinstance(value, str) else value

        sample = self.table.rows if infer_rows is None else self.table.rows[:infer_rows]
        self.field_headers: list[type[BaseFieldType]] = []
        for index, title in enumerate(self.field_titles):
            explicit = self.column_types.get(title, self.column_types.get(index))
            if explicit is not None:
                field_type = explicit
            else:
                seen = [self.figure_out_type(self.value_at(row, index)) for row in sample]
                field_type = _merge_column_types(seen)
            self.field_headers.append(field_type)
            log.debug("column %r -> %s", title, field_type.__name__)

    def value_at(self, row: Any, index: int) -> Any:
        """Return the raw value for column ``index`` of ``row`` (``MISSING`` if absent)."""
        if self.table.by_key:
            return (
                row.get(self.field_titles[index], MISSING) if isinstance(row, Mapping) else MISSING
            )
        return row[index] if index < len(row) else MISSING

    def figure_out_type(self, item: Any) -> type[BaseFieldType]:
        if item is MISSING:
            return NoneFieldType
        return figure_out_type(item, self.infer_formulas)

    def columns(self) -> list[dict[str, Any]]:
        """Column descriptions: ``[{"name": ..., "type": "integer"}, ...]``."""
        return [
            {"name": title, "type": header.type_name}
            for title, header in zip(self.field_titles, self.field_headers)
        ]


class _Missing:
    def __repr__(self) -> str:
        return "MISSING"

    def __bool__(self) -> bool:
        return False


#: Sentinel for a key or index that is not present in a row.
MISSING: Any = _Missing()
