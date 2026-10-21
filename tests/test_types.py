from __future__ import annotations

import datetime as dt
from decimal import Decimal

import pytest

import mm
from mm import types as t


@pytest.mark.parametrize(
    ("cls", "raw", "expected"),
    [
        (t.IntFieldType, "1,234", 1234),
        (t.IntFieldType, 3.0, 3),
        (t.IntFieldType, True, 1),
        (t.FloatFieldType, "$1,250.50", 1250.5),
        (t.FloatFieldType, "7", 7),
        (t.DecimalFieldType, "3.14", Decimal("3.14")),
        (t.BoolFieldType, "yes", True),
        (t.BoolFieldType, "FALSE", False),
        (t.BoolFieldType, 0, False),
        (t.DateFieldType, "2024-01-31", dt.date(2024, 1, 31)),
        (t.DateFieldType, "2024-01-31T10:00:00", dt.datetime(2024, 1, 31, 10)),
        (t.DateTimeFieldType, "2024-01-31T10:00:00Z", dt.datetime(2024, 1, 31, 10)),
        (t.DateTimeFieldType, dt.date(2024, 1, 31), dt.datetime(2024, 1, 31)),
        (t.TimeFieldType, "13:45", dt.time(13, 45)),
        (t.DurationFieldType, "1:30:00", dt.timedelta(hours=1, minutes=30)),
        (t.DurationFieldType, 90, dt.timedelta(seconds=90)),
        (t.PercentFieldType, "12.5%", 0.125),
        (t.StringFieldType, {"a": [1, 2]}, '{"a": [1, 2]}'),
        (t.StringFieldType, b"bytes", "bytes"),
        (t.StringFieldType, 5, "5"),
    ],
)
def test_coerce(cls, raw, expected):
    assert cls.coerce(raw) == expected


@pytest.mark.parametrize(
    ("cls", "raw"),
    [
        (t.IntFieldType, "abc"),
        (t.IntFieldType, 2.5),
        (t.IntFieldType, ""),
        (t.BoolFieldType, "maybe"),
        (t.DateFieldType, "not a date"),
        (t.DateFieldType, 12),
        (t.DecimalFieldType, "x"),
        (t.DurationFieldType, "a:b"),
        (t.FloatFieldType, [1]),
    ],
)
def test_coerce_rejects(cls, raw):
    with pytest.raises((TypeError, ValueError)):
        cls.coerce(raw)


def test_legacy_constructors():
    when = dt.datetime(2024, 1, 1)
    date = mm.Date(when, "%Y-%m-%d")
    assert date.data == when
    assert date.format == "%Y-%m-%d"
    url = mm.URL("https://example.com")
    assert url.displayname == "https://example.com"
    assert mm.URL("https://x.org", "X").displayname == "X"
    image = mm.Image("pic.bmp", 10, 20)
    assert (image.width, image.height) == (10, 20)
    assert mm.Formula("=SUM(A1:A2)").expression == "SUM(A1:A2)"
    assert mm.Formula("SUM(A1:A2)").expression == "SUM(A1:A2)"


def test_display_and_json():
    assert mm.Percent(0.256, decimals=1).display() == "25.6%"
    assert mm.Currency(-1234.5).display() == "-$1,234.50"
    assert mm.Currency(10, symbol="€", decimals=0).display() == "€10"
    assert t.BoolFieldType(True).display() == "TRUE"
    assert t.DurationFieldType(dt.timedelta(hours=26, seconds=5)).display() == "26:00:05"
    assert mm.Date(dt.date(2024, 2, 3), "%d/%m/%Y").display() == "03/02/2024"
    assert mm.URL("https://a.b", "A").to_json() == {"url": "https://a.b", "text": "A"}
    assert mm.URL("https://a.b").to_json() == "https://a.b"
    assert mm.Formula("SUM(A1)").to_json() == {"formula": "SUM(A1)"}
    assert t.DecimalFieldType(Decimal("1.5")).to_json() == 1.5
    assert t.NoneFieldType().display() == ""
    assert mm.Image("x.png", 5).to_json() == {"image": "x.png", "width": 5}


def test_tz_aware_datetime_is_made_naive():
    aware = dt.datetime(2024, 1, 1, 12, tzinfo=dt.timezone.utc)
    assert t.DateTimeFieldType(aware).data.tzinfo is None
    assert t.TimeFieldType(dt.time(1, tzinfo=dt.timezone.utc)).data.tzinfo is None


def test_type_names_and_lookup():
    assert t.field_type_for_name("INT") is t.IntFieldType
    assert t.field_type_for_name("money") is t.CurrencyFieldType
    with pytest.raises(ValueError, match="valid types"):
        t.field_type_for_name("blob")
    assert t.IntFieldType in t.all_field_types()
    assert t.PercentFieldType in t.all_field_types()


def test_equality_and_repr():
    assert t.IntFieldType(1) == t.IntFieldType(1)
    assert t.IntFieldType(1) != t.FloatFieldType(1)
    assert hash(t.IntFieldType(1)) == hash(t.IntFieldType(1))
    assert "style='bold'" in repr(t.StringFieldType("x", style="bold"))


def test_cell_helper():
    cell = mm.Cell(42, style="color: red", format="0.0")
    assert isinstance(cell, t.IntFieldType)
    assert (cell.style, cell.format) == ("color: red", "0.0")
    wrapped = mm.Cell(mm.Date(dt.date(2024, 1, 1)), style="color: blue")
    assert isinstance(wrapped, t.DateFieldType)
    assert wrapped.style == "color: blue"
