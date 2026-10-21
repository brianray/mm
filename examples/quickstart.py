"""Marmir quickstart: Python data in, formatted spreadsheets out.

Run: python examples/quickstart.py
"""

import datetime as dt
from pathlib import Path

import mm

out = Path("marmir_output")
out.mkdir(exist_ok=True)
now = dt.datetime.now().replace(microsecond=0)

# 1. The classic: a list of dicts. Types, widths and styles are automatic.
rows = [
    {"id": 1, "msg": "My first row", "when": now},
    {"id": 2, "msg": "My second row", "when": now},
]
mm.Document(rows).write(out / "example.xlsx")

# 2. Lists plus an explicit column order.
mm.Document([(1, "first", now), (2, "second", now)], order=("id", "msg", "when")).write(
    out / "lists.xlsx"
)

# 3. Rich cells: links, formulas, percents, currency, custom date formats and styles.
sales = [
    {"region": "North", "revenue": mm.Currency(125000), "growth": mm.Percent(0.12),
     "closed": mm.Date(dt.date(2024, 9, 30), "%d %b %Y"),
     "crm": mm.URL("https://crm.example.com/north", "North pipeline")},
    {"region": "South", "revenue": mm.Currency(98000), "growth": mm.Percent(-0.03),
     "closed": mm.Date(dt.date(2024, 9, 28), "%d %b %Y"), "crm": None},
    {"region": mm.Cell("Total", style="font-weight: bold"), "revenue": mm.Formula("SUM(B2:B3)"),
     "growth": None, "closed": None, "crm": None},
]
doc = mm.Document(sales, name="Sales", autofilter=True, title="Q3 Sales")

# 4. More sheets in the same workbook.
doc.add_sheet([{"note": "Numbers are unaudited"}], name="Notes")
doc.write(out / "sales.xlsx")

# 5. Same document, other formats.
doc.write(out / "sales.csv")
doc.write(out / "sales.html")
print(doc.to_markdown())

# 6. Read it back.
for sheet in mm.read(out / "sales.xlsx"):
    print(sheet.name, sheet.columns, sheet.rows[:2])
