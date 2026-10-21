# Cookbook

Short, self-contained recipes. Every Python block here is executed by the test suite.

```python
import datetime as dt
import io

import mm

orders = [
    {"region": "North", "customer": "Blue Door Cafe", "bags": 40, "revenue": 580.0},
    {"region": "North", "customer": "Union Diner", "bags": 75, "revenue": 1031.25},
    {"region": "South", "customer": "Harbor Bakery", "bags": 12, "revenue": 180.0},
]
```

## Excel file in memory (HTTP responses, e-mail, S3)

```python
data = mm.Document(orders).to_bytes()            # xlsx bytes
csv_bytes = mm.Document(orders).to_bytes("csv")  # any format
buffer = io.BytesIO()
mm.Document(orders).write(buffer)                # or any binary file object
print(data[:2], buffer.getvalue()[:2])
```

Output:

```text
b'PK' b'PK'
```

Serve it from a web framework:

<!-- skip -->
```python
# FastAPI
from fastapi import Response

@app.get("/report.xlsx")
def report():
    return Response(
        mm.Document(load_orders()).to_bytes(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="report.xlsx"'},
    )
```

## A totals row

```python
def with_totals(rows, sum_columns, label_column):
    """Append a bold row of SUM formulas under the data."""
    titles = list(rows[0])
    last = len(rows) + 1
    total = {label_column: mm.Cell("Total", style="font-weight: bold")}
    for name in sum_columns:
        letter = chr(ord("A") + titles.index(name))
        total[name] = mm.Formula(f"SUM({letter}2:{letter}{last})", style="font-weight: bold")
    return [*rows, total]


doc = mm.Document(with_totals(orders, ["bags", "revenue"], "region"))
print(doc.rows[-1])
```

Output:

```text
['Total', None, '=SUM(C2:C4)', '=SUM(D2:D4)']
```

## Highlight cells by a rule

```python
rows = [
    {**o, "revenue": mm.Cell(o["revenue"], style="background-color: #FFC7CE") if o["revenue"] < 500 else o["revenue"]}
    for o in orders
]
doc = mm.Document(rows)
print([row[3].style for row in doc.grid.grid_data])
```

Output:

```text
[None, None, 'background-color: #FFC7CE']
```

For rules on every cell, a custom grid is tidier -- see
[tutorial chapter 7](tutorial/07-extending.md#custom-cell-behaviour-a-grid).

## One sheet per group

```python
from itertools import groupby

regions = {key: list(group) for key, group in groupby(orders, key=lambda o: o["region"])}
names = list(regions)
book = mm.Document(regions[names[0]], name=names[0], order=["customer", "bags", "revenue"])
for name in names[1:]:
    book.add_sheet(regions[name], name=name, order=["customer", "bags", "revenue"])
print([sheet.name for sheet in book.sheets])
```

Output:

```text
['North', 'South']
```

With pandas: `for name, group in df.groupby("region"): book.add_sheet(group, name=name)`.

## Long text that wraps

```python
notes = [{"customer": "Union Diner", "note": "Prefers delivery before 7am. Ask for Sam at the back door; front entrance is locked until opening."}]
doc = mm.Document(notes, column_widths={"note": 40}, column_styles={"note": "white-space: normal; vertical-align: top"})
doc.write("notes.xlsx")
```

## Dates the way your readers write them

```python
from openpyxl import load_workbook

when = dt.date(2024, 9, 30)
uk = mm.Document([{"due": when}], date_format="dd/mm/yyyy")              # every date column
us = mm.Document([{"due": mm.Date(when, "%B %d, %Y")}])                  # one cell, strftime codes
print(load_workbook(io.BytesIO(uk.to_bytes())).active["A2"].number_format)
print(us.to_markdown().splitlines()[2])
```

Output:

```text
dd/mm/yyyy
| September 30, 2024 |
```

Excel applies the number format (`30/09/2024`); text formats follow strftime patterns
and otherwise show ISO dates.

## Untrusted data: never turn text into formulas

When rows come from users, uploads or the web, switch formula inference off so a value
like `=HYPERLINK(...)` stays text. CSV output also escapes such text by default.

```python
untrusted = [{"comment": "=HYPERLINK(\"http://evil.example\",\"click\")"}]
safe = mm.Document(untrusted, infer_formulas=False)
print(type(safe.grid.grid_data[0][0]).__name__)
print(safe.to_csv().splitlines()[1])
```

Output:

```text
StringFieldType
"'=HYPERLINK(""http://evil.example"",""click"")"
```

## A spreadsheet into an LLM prompt

```python
sheet_text = mm.read_document("notes.xlsx").to_markdown(max_rows=50)
prompt = f"Here is the customer notes sheet:\n\n{sheet_text}\n\nWho prefers early deliveries?"
print(sheet_text.splitlines()[2])
```

Output:

```text
| customer | note |
```

`max_rows` keeps big sheets inside the context window; `doc.describe()` gives an even
shorter summary (columns, types and a few sample rows).

## Combine a folder of CSV files into one workbook

```python
from pathlib import Path

Path("exports").mkdir(exist_ok=True)
Path("exports/north.csv").write_text("customer,bags\nBlue Door Cafe,40\nUnion Diner,75\n")
Path("exports/south.csv").write_text("customer,bags\nHarbor Bakery,12\n")

sheets = [
    mm.Document(sheet.rows, order=sheet.columns, name=path.stem.title())
    for path in sorted(Path("exports").glob("*.csv"))
    for sheet in mm.read(path)
]
book = sheets[0]
for extra in sheets[1:]:
    book.add_child(extra)
book.write("combined.xlsx")
print([s.name for s in mm.read("combined.xlsx")])
```

Output:

```text
['North', 'South']
```

## No header, no styling (raw data dump)

```python
raw = mm.Document(orders, headers=False, header_style="", row_styles=(), adjust_all_col_width=False)
print(raw.to_csv().splitlines()[0])
```

Output:

```text
North,Blue Door Cafe,40,580.0
```

## Legacy `.xls` for old systems

```bash
pip install "marmir[xls]"
```

<!-- skip -->
```python
mm.Document(orders).write("for_the_mainframe.xls")
```

XLS is limited to 65,536 rows, 256 columns and the 56-colour Excel 97 palette (Marmir
picks the nearest colour).
