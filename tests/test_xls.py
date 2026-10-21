from __future__ import annotations

import datetime as dt
from decimal import Decimal

import pytest

import mm

xlrd = pytest.importorskip("xlrd")
pytest.importorskip("xlwt")


def _book(doc):
    return xlrd.open_workbook(file_contents=doc.writestr("xls"), formatting_info=True)


def test_values_types_and_sheets(records, now):
    doc = mm.Document(records, name="My Sheet 1")
    doc.add_child(mm.Document(records, name="My Sheet 2"))
    book = _book(doc)
    assert book.sheet_names() == ["My Sheet 1", "My Sheet 2"]
    for sheet in book.sheets():
        assert sheet.row_values(0) == ["msg", "id", "when"]
        assert sheet.cell_value(1, 0) == "My first Cell"
        assert sheet.cell_value(2, 1) == 2
        assert sheet.cell(1, 2).ctype == xlrd.XL_CELL_DATE
        assert xlrd.xldate.xldate_as_datetime(sheet.cell_value(1, 2), book.datemode) == now


def test_more_types(image_path):
    doc = mm.Document(
        [
            {
                "none": None,
                "t": True,
                "f": False,
                "dec": Decimal("3.14"),
                "dur": dt.timedelta(hours=12),
                "url": mm.URL("https://example.com", 'Say "hi"'),
                "formula": mm.Formula("1+1"),
                "styled": mm.Cell(
                    "x",
                    style="color: red; background-color: #00FF00; border: thick; "
                    "text-decoration: underline; white-space: normal; vertical-align: top",
                ),
            }
        ]
    )
    sheet = _book(doc).sheet_by_index(0)
    assert sheet.cell(1, 0).ctype in (xlrd.XL_CELL_EMPTY, xlrd.XL_CELL_BLANK)
    assert sheet.cell_value(1, 1) == 1 and sheet.cell(1, 1).ctype == xlrd.XL_CELL_BOOLEAN
    assert sheet.cell_value(1, 3) == pytest.approx(3.14)
    assert sheet.cell_value(1, 4) == pytest.approx(0.5)


def test_freeze_and_no_headers(records):
    sheet = _book(mm.Document(records, freeze_col=1)).sheet_by_index(0)
    assert sheet.horz_split_pos == 1 and sheet.vert_split_pos == 1
    sheet = _book(mm.Document(records, headers=False, column_widths={"msg": 40})).sheet_by_index(0)
    assert sheet.cell_value(0, 0) == "My first Cell"
    assert sheet.colinfo_map[0].width == 40 * 256


def test_image_bmp(image_path):
    assert _book(mm.Document([{"p": mm.Image(str(image_path))}])).nsheets == 1


def test_image_resized_via_pillow(image_path):
    pytest.importorskip("PIL")
    assert _book(mm.Document([{"p": mm.Image(str(image_path), 50, 60)}])).nsheets == 1


def test_too_many_rows():
    from mm.errors import MarmirError

    doc = mm.Document([[i] for i in range(65536)], order=["n"])
    with pytest.raises(MarmirError, match="xlsx"):
        doc.writestr("xls")


def test_legacy_composer_import():
    from mm.composer_xls import ComposerXLS

    assert ComposerXLS.format_name == "xls"
