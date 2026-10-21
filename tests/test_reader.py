from __future__ import annotations

import datetime as dt
import io
import json

import pytest

import mm
from mm.errors import UnsupportedFormatError


@pytest.fixture
def workbook_bytes(now):
    doc = mm.Document(
        [
            {"name": "a", "n": 1, "d": dt.date(2024, 1, 2), "when": now},
            {"name": "b", "n": 2, "d": None, "when": now},
        ],
        name="First",
    )
    doc.add_sheet([{"total": "=SUM(1,2)"}], name="Second")
    return doc.writestr()


def test_read_xlsx(workbook_bytes, now):
    sheets = mm.read(workbook_bytes)
    assert [s.name for s in sheets] == ["First", "Second"]
    first = sheets[0]
    assert first.columns == ["name", "n", "d", "when"]
    assert first.rows[0] == ["a", 1, dt.date(2024, 1, 2), now]
    assert first.records()[1]["d"] is None
    assert len(first) == 2
    assert sheets[1].rows == [["=SUM(1,2)"]]


def test_read_options(workbook_bytes, tmp_path):
    assert mm.read(workbook_bytes, sheet="Second")[0].name == "Second"
    assert mm.read(workbook_bytes, sheet=1)[0].name == "Second"
    assert len(mm.read(workbook_bytes, max_rows=1)[0].rows) == 1
    no_header = mm.read(workbook_bytes, header=False)[0]
    assert no_header.columns[0] == "Column 1"
    assert no_header.rows[0][0] == "name"
    cached = mm.read(workbook_bytes, formulas=False)[1]
    assert cached.rows in ([[None]], [])
    path = tmp_path / "w.xlsx"
    path.write_bytes(workbook_bytes)
    assert mm.read(path)[0].name == "First"
    with path.open("rb") as handle:
        assert mm.read(handle)[0].name == "First"
    assert mm.read(io.BytesIO(workbook_bytes))[0].name == "First"


def test_read_csv_and_sniffing(tmp_path):
    path = tmp_path / "d.csv"
    path.write_text("a;b\n1;'=x\n2.5;hello\n;\n", encoding="utf-8")
    sheet = mm.read(path)[0]
    assert sheet.columns == ["a", "b"]
    assert sheet.rows == [[1, "=x"], [2.5, "hello"]]
    tsv = mm.read(b"x\ty\n1\t2\n", format="tsv")[0]
    assert tsv.rows == [[1, 2]]
    assert mm.read(b"plain text\nmore", format=None)[0].columns == ["plain text"]
    with pytest.raises(KeyError):
        mm.read(path, sheet="nope")


def test_read_xls(records):
    pytest.importorskip("xlrd")
    data = mm.Document([*records, {"msg": "x", "id": True, "when": None}], name="Old").writestr(
        "xls"
    )
    sheet = mm.read(data)[0]
    assert sheet.name == "Old"
    assert sheet.rows[0][0] == "My first Cell"
    assert isinstance(sheet.rows[0][2], dt.datetime)
    assert sheet.rows[2][1] is True
    assert mm.read(data, sheet="Old")[0].name == "Old"
    assert mm.read(data, sheet=0)[0].name == "Old"


def test_read_json(records):
    spec = mm.Document(records, name="J").to_json()
    sheet = mm.read(spec.encode(), format="json")[0]
    assert sheet.name == "J"
    assert sheet.columns == ["msg", "id", "when"]
    assert mm.read(json.dumps([{"a": "=SUM(1)"}]).encode())[0].rows == [["=SUM(1)"]]
    assert len(mm.read(spec.encode(), max_rows=1)[0].rows) == 1


def test_read_document_roundtrip(workbook_bytes, tmp_path, records):
    doc = mm.read_document(workbook_bytes)
    assert [d.name for d in doc.sheets] == ["First", "Second"]
    spec_path = tmp_path / "s.json"
    spec_path.write_text(mm.Document(records, name="R").to_json())
    assert mm.Document.from_file(spec_path).name == "R"
    with pytest.raises(UnsupportedFormatError):
        mm.read(b"x", format="pdf")
