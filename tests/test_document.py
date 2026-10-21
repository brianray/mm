from __future__ import annotations

import datetime as dt
import io

import pytest

import mm
from mm import types as t
from mm.errors import DataMismatchError, UnsupportedFormatError

from .helpers import sheet_values


def test_minimal_dicts(records, now):
    doc = mm.Document(records)
    data = doc.writestr()
    assert isinstance(data, bytes) and data[:2] == b"PK"
    assert sheet_values(data) == [
        ["msg", "id", "when"],
        ["My first Cell", 1, now],
        ["My second Cell", 2, now],
    ]


def test_minimal_lists(now):
    doc = mm.Document(
        ((1, "my first row", now), (2, "my second row", now)), order=("id", "msg", "when")
    )
    assert sheet_values(doc.writestr())[0] == ["id", "msg", "when"]
    assert doc.rows == [[1, "my first row", now], [2, "my second row", now]]
    assert doc.to_records()[1] == {"id": 2, "msg": "my second row", "when": now}


def test_order_on_dicts(records):
    doc = mm.Document(records, order=["when", "id"])
    assert doc.data_model.field_titles == ["when", "id"]
    assert sheet_values(doc.writestr())[1][1] == 1


def test_options_kwargs_and_config_dict(records):
    doc = mm.Document(records, config_dict={"headers": False}, autofilter=True, name="Data")
    assert doc.config.headers is False and doc.config.autofilter is True
    assert sheet_values(doc.writestr())[0][0] == "My first Cell"
    assert "Data" in repr(doc)


def test_missing_values_are_blank(now):
    doc = mm.Document([{"msg": "a", "id": 1, "when": now}, {"msg": "b", "id": 2}])
    assert isinstance(doc.grid.grid_data[1][2], t.NoneFieldType)
    assert sheet_values(doc.writestr())[2] == ["b", 2, None]


def test_missing_values_strict(now):
    with pytest.raises(DataMismatchError):
        mm.Document([{"a": 1, "b": 2}, {"a": 1}], ignore_data_mismatch=False)
    with pytest.raises(DataMismatchError):
        mm.Document([{"a": 1}, {"a": 2, "b": 3}], strict_columns=True)


def test_extra_keys_add_columns():
    doc = mm.Document([{"a": 1}, {"a": 2, "b": 3}])
    assert doc.data_model.field_titles == ["a", "b"]


def test_column_types_coerce(caplog):
    doc = mm.Document(
        [{"date": "2003-01-01", "n": "12"}, {"date": "bad", "n": "x"}],
        column_types={"date": mm.Date, "n": "integer"},
    )
    first = doc.grid.grid_data[0]
    assert first[0] == t.DateFieldType(dt.date(2003, 1, 1))
    assert first[1] == t.IntFieldType(12)
    assert isinstance(doc.grid.grid_data[1][0], t.StringFieldType)
    with pytest.raises(DataMismatchError, match="not a valid date"):
        mm.Document([{"date": "bad"}], column_types={"date": mm.Date}, ignore_data_mismatch=False)


def test_unconvertible_values_become_strings():
    class Weird:
        def __str__(self):
            return "weird"

    doc = mm.Document([{"w": Weird()}])
    assert doc.rows == [["weird"]]


def test_write_by_extension(tmp_path, records):
    doc = mm.Document(records)
    for name, check in [
        ("a.xlsx", lambda b: b[:2] == b"PK"),
        ("a.csv", lambda b: b.startswith(b"msg,id,when")),
        ("a.md", lambda b: b.startswith(b"| msg")),
        ("a.html", lambda b: b.startswith(b"<!DOCTYPE html>")),
        ("a.json", lambda b: b.lstrip().startswith(b"{")),
        ("a.txt", lambda b: b.startswith(b"+")),
        ("a.unknown", lambda b: b[:2] == b"PK"),
    ]:
        path = tmp_path / name
        assert doc.write(path) == path
        assert check(path.read_bytes()), name


def test_write_file_objects(records):
    doc = mm.Document(records)
    binary = io.BytesIO()
    doc.write(binary)
    assert binary.getvalue()[:2] == b"PK"
    text = io.StringIO()
    doc.write(text, format="csv")
    assert text.getvalue().startswith("msg,")
    with pytest.raises(TypeError):
        doc.write(io.StringIO(), format="xlsx")


def test_write_and_writestr_match(tmp_path, records):
    doc = mm.Document(records)
    doc.write(tmp_path / "x.xlsx")
    assert sheet_values((tmp_path / "x.xlsx").read_bytes()) == sheet_values(doc.writestr())


def test_set_composer_class(records):
    doc = mm.Document(records)
    doc.set_composer_class("markdown")
    assert doc.writestr().startswith("| msg")
    from mm.composers.text import ComposerCSV

    doc.set_composer_class(ComposerCSV)
    assert doc.writestr().startswith("msg,")
    assert isinstance(doc.composer, ComposerCSV)
    doc.set_composer(None)


def test_unknown_format(records):
    with pytest.raises(UnsupportedFormatError):
        mm.Document(records).writestr("pdf")


def test_children_and_add_sheet(records):
    doc = mm.Document(records, name="One", autofilter=True, title="Workbook")
    child = doc.add_sheet([[1, 2]], name="Two", order=["a", "b"])
    grandchild = child.add_child(mm.Document([{"z": 1}], name="Three"))
    assert child.config.autofilter is True
    assert child.config.title is None
    assert [d.name for d in doc.sheets] == ["One", "Two", "Three"]
    assert grandchild.name == "Three"
    assert len(doc.describe()["sheets"]) == 3


def test_describe_and_spec(records):
    info = mm.Document(records, name="S").describe(sample_rows=1)
    assert info["sheet_count"] == 1
    sheet = info["sheets"][0]
    assert sheet["row_count"] == 2
    assert sheet["columns"][1] == {"name": "id", "type": "integer"}
    assert len(sheet["sample_rows"]) == 1


def test_text_helpers(records):
    doc = mm.Document(records)
    assert "| msg |" in doc.to_markdown()
    assert "more row" in doc.to_markdown(max_rows=1)
    assert doc.config.max_rows is None
    assert "<table" in doc.to_html()
    assert doc.to_csv().startswith("msg,id")
    assert doc.to_text().startswith("+")
    assert '"sheets"' in doc.to_json()
    assert doc.to_spec()["sheets"][0]["rows"][0][0] == "My first Cell"


def test_module_write(tmp_path):
    path = mm.write([{"a": 1}], tmp_path / "x.csv")
    assert path.read_text() == "a\n1\n"


def test_custom_composer_registration(records):
    class Upper(mm.ComposerBase):
        format_name = "upper"

        def run(self, child=None):
            return "\n".join(
                ",".join(c.display().upper() for c in row) for row in self.grid.grid_data
            )

    mm.register_composer("upper", Upper, extensions=("up",))
    assert "upper" in mm.available_formats()
    assert mm.Document(records).writestr("upper").startswith("MY FIRST CELL")
    from mm.composers import format_for_path

    assert format_for_path("x.up") == "upper"


def test_legacy_hooks_iterate_grid(records):
    calls = []

    class Recorder(mm.ComposerBase):
        def start_new_row(self, row_id):
            calls.append(("start", row_id))

        def write_cell(self, row_id, col_id, cell):
            calls.append((row_id, col_id, cell.data))

        def set_option(self, key):
            calls.append(("option", key))

        def run(self, child=None):
            self.write_header()
            self.iterate_grid()
            self.finish()
            return calls

    doc = mm.Document(records)
    doc.set_composer_class(Recorder)
    result = doc.writestr()
    assert (0, 0, "msg") in result
    assert ("start", 1) in result
    assert (2, 1, 2) in result
    assert ("option", "headers") in result


def test_base_composer_run_not_implemented(records):
    doc = mm.Document(records)
    with pytest.raises(NotImplementedError):
        mm.ComposerBase(doc.data_model, doc.grid, doc).run()
    base = mm.ComposerBase(doc.data_model, doc.grid, doc)
    base.write_cell(0, 0, None)
    base.set_option("x")
