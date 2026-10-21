from __future__ import annotations

import dataclasses
import datetime as dt
import sqlite3
from collections import namedtuple
from decimal import Decimal

import pytest

from mm import types as t
from mm.config import Config
from mm.errors import DataMismatchError, EmptyDataError
from mm.model import DataModel, figure_out_type, normalize_data


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, t.NoneFieldType),
        (True, t.BoolFieldType),
        (3, t.IntFieldType),
        (3.5, t.FloatFieldType),
        (float("nan"), t.NoneFieldType),
        (Decimal("1"), t.DecimalFieldType),
        (dt.datetime(2024, 1, 1), t.DateTimeFieldType),
        (dt.date(2024, 1, 1), t.DateFieldType),
        (dt.time(1, 2), t.TimeFieldType),
        (dt.timedelta(1), t.DurationFieldType),
        ("text", t.StringFieldType),
        ("=SUM(A1:A2)", t.FormulaFieldType),
        ("=", t.StringFieldType),
        ({"a": 1}, t.StringFieldType),
        (t.URLFieldType("x"), t.URLFieldType),
    ],
)
def test_figure_out_type(value, expected):
    assert figure_out_type(value) is expected


def test_formula_inference_can_be_disabled():
    assert figure_out_type("=1+1", infer_formulas=False) is t.StringFieldType


def test_column_types_scan_past_none():
    model = DataModel([{"a": None, "b": 1}, {"a": 5, "b": 2.5}, {"a": 6, "b": Decimal("1")}])
    assert model.field_headers == [t.IntFieldType, t.DecimalFieldType]


def test_mixed_column_types():
    model = DataModel(
        [
            {"d": dt.date(2024, 1, 1), "s": "x", "f": 1},
            {"d": dt.datetime(2024, 1, 1), "s": 2, "f": "=SUM(A1)"},
        ]
    )
    assert model.field_headers == [t.DateTimeFieldType, t.StringFieldType, t.IntFieldType]


def test_infer_rows_limits_sampling():
    model = DataModel([{"a": None}, {"a": 1}], config=Config(infer_rows=1))
    assert model.field_headers == [t.NoneFieldType]


def test_explicit_column_types_by_name_index_and_string():
    model = DataModel(
        [[1, "2024-01-01"]], order=["n", "d"], column_types={0: "number", "d": t.DateFieldType}
    )
    assert model.field_headers == [t.FloatFieldType, t.DateFieldType]
    assert model.columns() == [{"name": "n", "type": "number"}, {"name": "d", "type": "date"}]


def test_union_of_keys_and_strict_mode():
    rows = [{"a": 1}, {"a": 2, "b": 3}]
    assert normalize_data(rows).columns == ["a", "b"]
    with pytest.raises(DataMismatchError, match="Row 2"):
        normalize_data(rows, strict=True)
    with pytest.raises(DataMismatchError):
        normalize_data([{"a": 1}, [1]])


def test_empty_data():
    with pytest.raises(EmptyDataError):
        normalize_data([])
    table = normalize_data([], order=["a", "b"])
    assert table.columns == ["a", "b"]
    assert table.rows == []


def test_lists_without_order_get_generic_headers():
    table = normalize_data([[1, 2], [3]])
    assert table.columns == ["Column 1", "Column 2"]


def test_rejects_scalars():
    with pytest.raises(TypeError):
        normalize_data("abc")
    with pytest.raises(TypeError):
        normalize_data(42)


def test_column_oriented_dict():
    table = normalize_data({"a": [1, 2], "b": ["x", "y"]})
    assert table.rows == [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}]
    with pytest.raises(DataMismatchError):
        normalize_data({"a": [1], "b": [1, 2]})
    with pytest.raises(TypeError):
        normalize_data({"a": "not a list"})


def test_object_rows():
    @dataclasses.dataclass
    class Point:
        x: int
        y: int

    Pair = namedtuple("Pair", "left right")

    class Plain:
        def __init__(self):
            self.name = "n"
            self._hidden = 1

    class Legacy:
        def iteritems(self):
            return iter([("k", "v")])

    assert normalize_data([Point(1, 2)]).rows == [{"x": 1, "y": 2}]
    assert normalize_data([Pair(1, 2)]).columns == ["left", "right"]
    assert normalize_data([Plain()]).rows == [{"name": "n"}]
    assert normalize_data([Legacy()]).rows == [{"k": "v"}]
    assert normalize_data(iter([(1, 2)]), order=["a", "b"]).rows == [[1, 2]]
    assert normalize_data([range(2)], order=["a", "b"]).rows == [[0, 1]]
    assert normalize_data(["solo"], order=["a"]).rows == [["solo"]]


def test_pydantic_rows():
    pydantic = pytest.importorskip("pydantic")

    class Item(pydantic.BaseModel):
        name: str
        qty: int

    assert normalize_data([Item(name="a", qty=1)]).rows == [{"name": "a", "qty": 1}]


def test_dbapi_cursor_and_rows():
    conn = sqlite3.connect(":memory:")
    conn.execute("create table t (num integer, data text)")
    conn.executemany("insert into t values (?, ?)", [(100, "abc"), (200, "mmmmaaarrrr")])
    table = normalize_data(conn.execute("select * from t"))
    assert table.columns == ["num", "data"]
    assert table.rows == [[100, "abc"], [200, "mmmmaaarrrr"]]
    conn.row_factory = sqlite3.Row
    table = normalize_data(conn.execute("select * from t").fetchall())
    assert table.rows[1] == {"num": 200, "data": "mmmmaaarrrr"}


def test_pandas_dataframe():
    pd = pytest.importorskip("pandas")
    df = pd.DataFrame(
        {
            "when": pd.to_datetime(["2024-01-01", None]),
            "n": [1, 2],
            "f": [1.5, float("nan")],
            "s": ["a", None],
        }
    )
    model = DataModel(df)
    assert model.field_titles == ["when", "n", "f", "s"]
    assert model.field_headers == [
        t.DateTimeFieldType,
        t.IntFieldType,
        t.FloatFieldType,
        t.StringFieldType,
    ]
    rows = model.table.rows
    assert rows[0]["when"] == dt.datetime(2024, 1, 1)
    assert rows[1]["when"] is None
    assert rows[1]["f"] is None
    assert type(rows[0]["n"]) is int
