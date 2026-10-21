from __future__ import annotations

import datetime as dt
from decimal import Decimal

import pytest

import mm
from mm.contrib.gsheets import sheet_values, write_gsheet


class FakeWorksheet:
    def __init__(self, title="Sheet1"):
        self.title = title
        self.calls = []

    def update_title(self, title):
        self.title = title

    def resize(self, rows, cols):
        self.calls.append(("resize", rows, cols))

    def update(self, values, start, value_input_option):
        self.calls.append(("update", values, start, value_input_option))

    def freeze(self, rows=None, cols=None):
        self.calls.append(("freeze", rows, cols))


class FakeSpreadsheet:
    def __init__(self):
        self.sheet1 = FakeWorksheet()
        self.added = []
        self.shared = []

    def add_worksheet(self, title, rows, cols):
        ws = FakeWorksheet(title)
        self.added.append(ws)
        return ws

    def share(self, email, perm_type, role):
        self.shared.append((email, perm_type, role))


class FakeClient:
    def __init__(self):
        self.created = []

    def create(self, title, folder_id=None):
        self.created.append((title, folder_id))
        self.spreadsheet = FakeSpreadsheet()
        return self.spreadsheet


def test_sheet_values():
    doc = mm.Document(
        [
            {
                "s": "-x",
                "d": dt.date(2024, 1, 2),
                "dt": dt.datetime(2024, 1, 2, 3, 4),
                "n": Decimal("1.5"),
                "f": mm.Formula("SUM(A1)"),
                "u": mm.URL("https://a.b", 'Q"'),
                "dur": dt.timedelta(minutes=90),
                "none": None,
                "b": True,
            }
        ],
        column_types={"s": "string"},
    )
    header, row = sheet_values(doc)
    assert header[0] == "s"
    assert row == [
        "'-x",
        "2024-01-02",
        "2024-01-02 03:04:00",
        1.5,
        "=SUM(A1)",
        '=HYPERLINK("https://a.b", "Q""")',
        "1:30:00",
        "",
        True,
    ]


def test_write_gsheet_with_client(records):
    doc = mm.Document(records, name="Main", freeze_col=1)
    doc.add_sheet([{"x": 1}], name="Other", headers=False)
    client = FakeClient()
    result = write_gsheet(doc, "Title", client=client, share_with="a@b.c", folder_id="F")
    assert client.created == [("Title", "F")]
    assert result.sheet1.title == "Main"
    assert ("freeze", 1, 1) in result.sheet1.calls
    assert result.added[0].title == "Other"
    assert result.added[0].calls[0][1] == [[1]]
    assert result.shared == [("a@b.c", "user", "writer")]


def test_document_write_gsheet_and_deprecated_gdata(records):
    client = FakeClient()
    doc = mm.Document(records)
    assert doc.write_gsheet("T", client=client) is client.spreadsheet
    with pytest.warns(DeprecationWarning):
        doc.write_gdata("T2", "user", "pass", client=client)
    assert client.created[-1] == ("T2", None)


def test_prettytable_composer(records, now):
    pytest.importorskip("prettytable")
    from mm.contrib.prettytable.composers import ComposerPrettyTable

    doc = mm.Document(records)
    doc.set_composer_class(ComposerPrettyTable)
    text = str(doc.writestr())
    assert f"| My first Cell  | 1  | {now} |" in text
    doc.add_sheet([{"a": 1}])
    tables = doc.writestr()
    assert len(tables) == 2
    no_header = mm.Document(records, headers=False)
    no_header.set_composer_class(ComposerPrettyTable)
    assert "msg" not in str(no_header.writestr())
