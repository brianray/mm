from __future__ import annotations

import datetime as dt
import json

import mm


def test_csv_values_and_escaping(now):
    doc = mm.Document(
        [
            {
                "s": "=cmd|' /C calc'!A0",
                "n": 1.5,
                "d": dt.date(2024, 1, 2),
                "f": mm.Formula("SUM(B2:B2)"),
                "u": mm.URL("https://x.org", "X"),
                "b": True,
                "c": mm.Date(now, "%d/%m/%Y"),
                "e": None,
            },
            {"s": "-5", "n": 2, "d": None, "f": None, "u": None, "b": False, "c": None, "e": None},
        ],
        column_types={"s": "string"},
    )
    lines = doc.to_csv().splitlines()
    assert lines[0] == "s,n,d,f,u,b,c,e"
    assert (
        lines[1] == "'=cmd|' /C calc'!A0,1.5,2024-01-02,=SUM(B2:B2),https://x.org,TRUE,14/03/2024,"
    )
    assert lines[2].startswith("'-5,2,")
    raw = mm.Document([{"s": "=x"}], escape_formula_strings=False, infer_formulas=False).to_csv()
    assert raw.splitlines()[1] == "=x"


def test_csv_only_first_sheet(caplog, records):
    doc = mm.Document(records)
    doc.add_sheet([{"other": 1}])
    out = doc.to_csv()
    assert "other" not in out
    assert "child sheet" in caplog.text


def test_tsv_and_delimiter(records):
    doc = mm.Document(records)
    assert doc.writestr("tsv").splitlines()[0] == "msg\tid\twhen"
    assert mm.Document(records, csv_delimiter=";").to_csv().splitlines()[0] == "msg;id;when"
    assert mm.Document(records, headers=False).to_csv().startswith("My first Cell")


def test_markdown(records):
    doc = mm.Document(
        [
            {
                "a": "pipe | here\nnewline",
                "n": 1,
                "u": mm.URL("https://x.org", "X"),
                "i": mm.Image("p.png"),
            }
        ]
    )
    md = doc.to_markdown()
    assert "| a | n | u | i |" in md
    assert "| --- | ---: | --- | --- |" in md
    assert "pipe \\| here<br>newline" in md
    assert "[X](https://x.org)" in md
    assert "![image](p.png)" in md
    multi = mm.Document(records, name="One")
    multi.add_sheet(records, name="Two")
    assert "## One" in multi.to_markdown() and "## Two" in multi.to_markdown()


def test_markdown_empty_sheet():
    doc = mm.Document([], order=["a"])
    assert doc.to_markdown().startswith("| a |")


def test_html_escaping_and_links():
    doc = mm.Document(
        [
            {"t": "<script>alert(1)</script>", "u": mm.URL("javascript:alert(1)", "bad"), "n": 5},
            {"t": "ok", "u": mm.URL("https://good.example/?a=1&b=2", "good"), "n": 6},
        ],
        title="<Title>",
    )
    html = doc.to_html()
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert 'href="javascript' not in html
    assert '<a href="https://good.example/?a=1&amp;b=2">good</a>' in html
    assert "<title>&lt;Title&gt;</title>" in html
    assert "text-align: right" in html
    fragment = mm.Document([{"a": 1}], html_fragment=True, headers=False).to_html()
    assert fragment.startswith("<table") and "<thead>" not in fragment
    assert "more row" in mm.Document([{"a": 1}, {"a": 2}]).to_html(max_rows=1)


def test_text_table(records, now):
    out = mm.Document(records).to_text()
    assert out.splitlines()[1] == "|      msg       | id |        when         |"
    assert f"| My first Cell  |  1 | {now} |" in out
    wide = mm.Document([{"k": "日本"}]).to_text()
    assert "| 日本 |" in wide
    assert "more row" in mm.Document(records).to_text(max_rows=1)
    no_header = mm.Document(records, headers=False).to_text()
    assert "msg" not in no_header


def test_json_spec_shape(now):
    doc = mm.Document(
        [
            {
                "n": 1,
                "when": now,
                "p": mm.Percent(0.5, decimals=1),
                "c": mm.Currency(3, symbol="€", decimals=0),
                "s": mm.Cell("x", style="color: red"),
                "f": "=SUM(A2:A2)",
                "d": mm.Date(now, "%Y"),
            },
        ],
        name="S",
        autofilter=True,
        title="Doc",
    )
    spec = json.loads(doc.to_json())
    assert spec["title"] == "Doc"
    sheet = spec["sheets"][0]
    assert sheet["name"] == "S"
    assert sheet["options"] == {"autofilter": True}
    assert sheet["columns"][0] == {"name": "n", "type": "integer"}
    row = sheet["rows"][0]
    assert row[0] == 1
    assert row[1] == now.isoformat()
    assert row[2] == {"value": 0.5, "type": "percent", "decimals": 1}
    assert row[3] == {"value": 3, "type": "currency", "symbol": "€", "decimals": 0}
    assert row[4] == {"value": "x", "style": "color: red"}
    assert row[5] == {"formula": "SUM(A2:A2)"}
    assert sheet["columns"][6] == {"name": "d", "type": "date"}
    assert row[6] == {"value": now.isoformat(), "format": "%Y"}
