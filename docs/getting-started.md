# Getting started

## Install

```bash
pip install marmir
```

Extras add optional features: `xls`, `images`, `pandas`, `django`, `prettytable`,
`gsheets`, `mcp`, `server`, or `all`. See the [README](../README.md#install-options).

## Your first spreadsheet

```python
import datetime as dt
import mm

rows = [
    {"id": 1, "msg": "My first row", "when": dt.datetime.now()},
    {"id": 2, "msg": "My second row", "when": dt.datetime.now()},
]
doc = mm.Document(rows)
doc.write("example.xlsx")
```

What you get without any configuration:

- A bold, white-on-navy header row that stays frozen while scrolling.
- `id` written as numbers, `msg` as text, `when` as real Excel date-times.
- Alternating row shading.
- Columns sized to their contents using real font metrics.

## Rows as lists

Pass `order` to name the columns:

```python
doc = mm.Document(
    [(1, "My first row", now), (2, "My second row", now)],
    order=("id", "msg", "when"),
)
```

`order` also works with dicts to pick and reorder columns.

## Options

Options can be passed as keyword arguments, as `config_dict`, or as a `mm.Config`:

```python
mm.Document(rows, autofilter=True, freeze_col=1, headers=True)
mm.Document(rows, config_dict={"headers": False, "freeze_row": 0})
mm.Document(rows, config=mm.Config(row_styles=()))
```

The full list is in [concepts](concepts.md#configuration).

## Richer cells

```python
{
    "homepage": mm.URL("https://github.com/brianray", "GitHub"),
    "joined": mm.Date(dt.date(2013, 1, 20), "%d %B %Y"),
    "share": mm.Percent(0.256, decimals=1),
    "salary": mm.Currency(120000),
    "total": mm.Formula("SUM(B2:B10)"),        # or the string "=SUM(B2:B10)"
    "note": mm.Cell("check", style="background-color: yellow"),
    "photo": mm.Image("me.png", width=120, height=120),   # pip install 'marmir[images]'
}
```

See [cell types, formats and styling](styling.md).

## Several sheets

```python
doc = mm.Document(summary_rows, name="Summary")
doc.add_sheet(detail_rows, name="Detail")      # inherits the parent's options
doc.add_child(mm.Document(other_rows, name="Other"))   # independent options
doc.write("report.xlsx")
```

## Other formats

The file extension picks the format, or pass `format=`:

```python
doc.write("report.csv")
doc.write("report.md")
doc.write("report.html")
data = doc.to_bytes("xlsx")          # bytes for HTTP responses or uploads
text = doc.to_markdown(max_rows=20)  # paste into an LLM prompt
```

## Reading spreadsheets

```python
for sheet in mm.read("report.xlsx"):
    print(sheet.name, sheet.columns)
    for record in sheet.records():
        ...

doc = mm.Document.from_file("report.xlsx")   # all sheets, ready to re-write
doc.write("report.md")
```

## Next steps

- Hand the job to an LLM with the [workbook spec](workbook-spec.md) and the
  [Anthropic](integrations/anthropic.md) or [OpenAI](integrations/openai.md) guides.
- Read the [concepts](concepts.md) to customise models, grids and composers.
