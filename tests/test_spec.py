from __future__ import annotations

import datetime as dt
import json
from decimal import Decimal

import pytest

import mm
from mm import types as t
from mm.errors import SpecValidationError
from mm.spec import WORKBOOK_SPEC_SCHEMA, normalize_spec, validate_spec

from .helpers import load_xlsx

SPEC = {
    "title": "Q3 Sales",
    "author": "Agent",
    "options": {"autofilter": True},
    "sheets": [
        {
            "name": "Sales",
            "columns": [
                {"name": "Region", "type": "string", "width": 18, "style": "font-weight: bold"},
                {"name": "Revenue", "type": "currency"},
                {"name": "Growth", "type": "percent", "format": "0.0%"},
                {"name": "Closed", "type": "date", "format": "%Y-%m-%d"},
                "Notes",
            ],
            "rows": [
                [
                    "North",
                    125000,
                    0.12,
                    "2024-09-30",
                    {"url": "https://example.com", "text": "deal"},
                ],
                ["South", "98,000", -0.03, "2024-09-28", None],
                [
                    {"value": "Total", "style": "font-weight: bold"},
                    {"formula": "SUM(B2:B3)"},
                    None,
                    None,
                    {"value": 0.5, "type": "percent", "decimals": 1},
                ],
            ],
            "options": {"freeze_col": 1},
        },
        {"name": "Raw", "rows": [{"k": "a", "v": 1}, {"k": "b", "v": "=B2*2", "extra": True}]},
    ],
}


def test_schema_is_json_serialisable():
    assert json.loads(json.dumps(WORKBOOK_SPEC_SCHEMA))["required"] == ["sheets"]


def test_valid_spec_builds_document():
    assert validate_spec(SPEC) == []
    doc = mm.from_spec(SPEC)
    assert [d.name for d in doc.sheets] == ["Sales", "Raw"]
    assert doc.config.title == "Q3 Sales"
    assert doc.config.autofilter is True and doc.config.freeze_col == 1
    assert doc.children[0].config.title is None
    assert doc.data_model.field_headers[:4] == [
        t.StringFieldType,
        t.CurrencyFieldType,
        t.PercentFieldType,
        t.DateFieldType,
    ]
    first = doc.grid.grid_data[0]
    assert first[1] == t.CurrencyFieldType(125000)
    assert first[3].data == dt.date(2024, 9, 30)
    assert doc.grid.grid_data[1][1].data == 98000
    total = doc.grid.grid_data[2]
    assert isinstance(total[1], t.FormulaFieldType)
    assert total[0].style == "font-weight: bold"
    assert total[4].display() == "50.0%"
    raw = doc.children[0]
    assert raw.data_model.field_titles == ["k", "v", "extra"]
    assert isinstance(raw.grid.grid_data[1][1], t.FormulaFieldType)


def test_spec_xlsx_output():
    wb = load_xlsx(mm.from_spec(SPEC).to_bytes())
    ws = wb["Sales"]
    assert ws["B4"].value == "=SUM(B2:B3)"
    assert ws["C2"].number_format == "0.0%"
    assert ws["D2"].number_format == "yyyy-mm-dd"
    assert ws["E2"].hyperlink.target == "https://example.com"
    assert ws.column_dimensions["A"].width == 18
    assert ws["A2"].font.bold is True
    assert ws.auto_filter.ref == "A1:E4"
    assert wb.properties.creator == "Agent"


def test_round_trip_through_json():
    doc = mm.from_spec(SPEC)
    again = mm.from_spec(doc.to_json())
    assert again.rows == doc.rows
    assert [d.name for d in again.sheets] == ["Sales", "Raw"]
    assert again.data_model.field_headers == doc.data_model.field_headers


def test_document_round_trip_types():
    now = dt.datetime(2024, 1, 2, 3, 4, 5)
    doc = mm.Document(
        [
            {
                "a": Decimal("1.5"),
                "b": dt.time(1, 2),
                "c": dt.timedelta(minutes=3),
                "d": now,
                "e": True,
                "f": mm.URL("https://x", "x"),
            }
        ]
    )
    again = mm.from_spec(doc.to_spec())
    assert again.rows == [
        [Decimal("1.5"), dt.time(1, 2), dt.timedelta(minutes=3), now, True, "https://x"]
    ]


@pytest.mark.parametrize(
    ("spec", "fragment"),
    [
        ("not json", "not valid JSON"),
        (42, "expected an object"),
        ({"sheets": []}, "non-empty array"),
        ({"sheets": [1]}, "expected an object"),
        ({"sheets": [{"rows": "x"}]}, "must be an array of rows"),
        ({"sheets": [{"rows": [[1]]}]}, "need 'columns'"),
        ({"sheets": [{"columns": ["a"], "rows": [[1, 2]]}]}, "has 2 cells but there are 1 columns"),
        ({"sheets": [{"columns": ["a"], "rows": [{"b": 1}]}]}, "unknown column(s) ['b']"),
        ({"sheets": [{"columns": ["a", "a"], "rows": []}]}, "duplicate column names"),
        (
            {"sheets": [{"columns": [{"name": "a", "type": "blob"}], "rows": []}]},
            "unknown column type",
        ),
        ({"sheets": [{"columns": [{"nam": "a"}], "rows": []}]}, "string 'name'"),
        (
            {"sheets": [{"columns": [{"name": "a", "width": "x", "zz": 1}], "rows": []}]},
            "width: must be a number",
        ),
        (
            {"sheets": [{"columns": [{"name": "a", "type": "integer"}], "rows": [["abc"]]}]},
            "sheets[0].rows[0][0]: 'abc' is not a valid integer",
        ),
        (
            {
                "sheets": [
                    {"columns": [{"name": "d", "type": "date"}], "rows": [{"d": "31/12/2024"}]}
                ]
            },
            "rows[0]['d']",
        ),
        (
            {"sheets": [{"columns": ["a"], "rows": [[{"formula": "SUM(A1"}]]}]},
            "unbalanced parentheses",
        ),
        ({"sheets": [{"columns": ["a"], "rows": [['=CONCAT("a)']]}]}, "unbalanced double quotes"),
        ({"sheets": [{"columns": ["a"], "rows": [[{"formula": ""}]]}]}, "non-empty string"),
        (
            {"sheets": [{"columns": ["a"], "rows": [[{"value": 1, "formula": "A1"}]]}]},
            "exactly one of",
        ),
        (
            {"sheets": [{"columns": ["a"], "rows": [[{"value": 1, "colour": "red"}]]}]},
            "unknown cell properties",
        ),
        (
            {"sheets": [{"columns": ["a"], "rows": [[{"value": "x", "type": "nope"}]]}]},
            "unknown column type",
        ),
        (
            {"sheets": [{"columns": ["a"], "rows": [[{"url": ""}]]}]},
            "url: must be a non-empty string",
        ),
        ({"sheets": [{"columns": ["a"], "rows": [[[1, 2]]]}]}, "unsupported cell value"),
        ({"sheets": [{"columns": ["a"], "rows": [5]}]}, "array or an object"),
        ({"sheets": [{"rows": [], "name": 3, "zzz": 1}]}, "unknown property"),
        ({"sheets": [{"rows": [], "options": {"nope": 1}}]}, "unknown option"),
        ({"sheets": [{"rows": [], "options": {"headers": "yes"}}]}, "true or false"),
        ({"sheets": [{"rows": [], "options": {"freeze_row": -1}}]}, "non-negative integer"),
        ({"sheets": [{"rows": [], "options": {"row_styles": [1]}}]}, "array of style strings"),
        ({"sheets": [{"rows": [], "options": "x"}]}, "must be an object"),
        ({"sheets": [{"rows": [], "columns": "x"}]}, "must be an array"),
        ({"sheets": [], "extra": 1}, "unknown property"),
    ],
)
def test_validation_messages(spec, fragment):
    errors = validate_spec(spec)
    assert any(fragment in e for e in errors), errors


def test_images_policy(image_path):
    spec = {"sheets": [{"columns": ["p"], "rows": [[{"image": "author.bmp"}]]}]}
    assert "images are not allowed" in validate_spec(spec, allow_images=False)[0]
    typed = {"sheets": [{"columns": [{"name": "p", "type": "image"}], "rows": [["x.png"]]}]}
    assert validate_spec(typed, allow_images=False)
    doc = mm.from_spec(spec, base_dir=image_path.parent)
    assert doc.grid.grid_data[0][0].data == str(image_path)
    assert validate_spec({"sheets": [{"columns": ["p"], "rows": [[{"image": 5}]]}]})


def test_max_cells_and_errors():
    spec = {"sheets": [{"columns": ["a"], "rows": [[1]] * 11}]}
    assert "exceeds the limit" in validate_spec(spec, max_cells=10)[-1]
    with pytest.raises(SpecValidationError) as info:
        mm.from_spec({"sheets": [{"columns": ["a"], "rows": [[1, 2]] * 12}]})
    assert len(info.value.errors) == 12
    assert "more" in str(info.value)


def test_shorthands_and_formula_inference_switch():
    assert normalize_spec([{"a": 1}]) == {"sheets": [{"rows": [{"a": 1}]}]}
    single = normalize_spec(
        {"name": "S", "columns": ["a"], "rows": [[1]], "options": {"headers": False}}
    )
    assert single["sheets"][0]["options"] == {"headers": False}
    doc = mm.from_spec({"rows": [["=1+"]], "columns": ["a"], "options": {"infer_formulas": False}})
    assert isinstance(doc.grid.grid_data[0][0], t.StringFieldType)
    assert (
        validate_spec({"rows": [["=SUM("]], "columns": ["a"], "options": {"infer_formulas": False}})
        == []
    )


def test_value_objects_without_type():
    doc = mm.from_spec(
        {
            "sheets": [
                {"columns": ["a", "b"], "rows": [[{"value": 3, "format": "0.0"}, {"value": None}]]}
            ]
        }
    )
    cell = doc.grid.grid_data[0][0]
    assert isinstance(cell, t.IntFieldType) and cell.format == "0.0"
    assert isinstance(doc.grid.grid_data[0][1], t.NoneFieldType)
    currency = mm.from_spec(
        {
            "rows": [[{"value": 5, "type": "currency", "symbol": "£", "decimals": 0}]],
            "columns": ["c"],
        }
    )
    assert currency.grid.grid_data[0][0].display() == "£5"


def test_document_from_spec_alias():
    assert mm.Document.from_spec({"rows": [{"a": 1}]}).rows == [[1]]


def test_invalid_column_type_reported_once():
    spec = {"sheets": [{"columns": [{"name": "d", "type": "day"}], "rows": [["x"], ["y"]]}]}
    errors = validate_spec(spec)
    assert len(errors) == 1
    assert errors[0].startswith("sheets[0].columns[0].type")


def test_formula_equality_ignores_leading_equals():
    assert t.FormulaFieldType("=SUM(A1)") == t.FormulaFieldType("SUM(A1)")
    assert hash(t.FormulaFieldType("=SUM(A1)")) == hash(t.FormulaFieldType("SUM(A1)"))
    assert mm.Document([{"a": "=SUM(1)"}]).rows == [["=SUM(1)"]]


def test_column_strftime_format_in_text_outputs():
    spec = {
        "sheets": [
            {
                "columns": [{"name": "d", "type": "date", "format": "%d %b %Y"}],
                "rows": [["2024-09-27"]],
            }
        ]
    }
    doc = mm.from_spec(spec)
    assert "27 Sep 2024" in doc.to_markdown()
    assert "27 Sep 2024" in doc.to_text()
    assert "27 Sep 2024" in doc.to_html()
    assert "27 Sep 2024" in doc.to_csv()
    assert load_xlsx(doc.to_bytes())["Sheet 1"]["A2"].number_format == "dd mmm yyyy"
