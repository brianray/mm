# 3. Multi-sheet reports from real data

<!-- requires: pandas -->

**Goal:** build Acme's quarterly workbook -- a summary by customer, a monthly trend and
the order detail -- straight from a database and pandas, then publish it in several
formats. Needs `pip install "marmir[pandas]"`.

## The database

Acme's orders live in SQL. Any DB-API database works (PostgreSQL, MySQL, SQL Server,
...); we use SQLite so the tutorial runs anywhere:

```python
import sqlite3

import pandas as pd

import mm

conn = sqlite3.connect(":memory:")
conn.executescript("""
create table orders (order_id integer, customer text, placed date, bags integer, price real);
insert into orders values
  (1001, 'Blue Door Cafe', '2024-07-02', 40, 14.50),
  (1002, 'Harbor Bakery',  '2024-07-09', 12, 15.00),
  (1003, 'Union Diner',    '2024-08-01', 75, 13.75),
  (1004, 'Blue Door Cafe', '2024-09-18', 40, 14.50),
  (1005, 'Harbor Bakery',  '2024-09-20', 18, 15.00),
  (1006, 'Union Diner',    '2024-09-27', 60, 13.75);
""")
```

## Sheet 1: order detail from a SQL cursor

Pass the cursor itself. Column names come from the query, and `column_types` turns
SQLite's date strings into real dates:

```python
cursor = conn.execute("select order_id, customer, placed, bags, price from orders order by placed")
detail = mm.Document(cursor, name="Orders", column_types={"placed": "date", "price": "currency"})
print([c["type"] for c in detail.columns])
```

Output:

```text
['integer', 'string', 'date', 'integer', 'currency']
```

## Sheet 2: summary by customer from pandas

Analysis is pandas' job; presentation is Marmir's. A DataFrame goes straight in:

```python
df = pd.read_sql_query("select * from orders", conn, parse_dates=["placed"])
df["revenue"] = df["bags"] * df["price"]

by_customer = (
    df.groupby("customer", as_index=False)
    .agg(orders=("order_id", "count"), bags=("bags", "sum"), revenue=("revenue", "sum"))
    .sort_values("revenue", ascending=False)
)
by_customer["share"] = by_customer["revenue"] / by_customer["revenue"].sum()

summary = mm.Document(
    by_customer,
    name="By customer",
    column_types={"revenue": "currency", "share": "percent"},
)
print(summary.to_markdown())
```

Output:

```text
## By customer

| customer | orders | bags | revenue | share |
| --- | ---: | ---: | ---: | ---: |
| Union Diner | 2 | 135 | $1,856.25 | 54% |
| Blue Door Cafe | 2 | 80 | $1,160.00 | 33% |
| Harbor Bakery | 2 | 30 | $450.00 | 13% |
```

pandas details are handled for you: `NaN`/`NaT` become blank cells, numpy numbers become
Python numbers and Timestamps become dates.

## Sheet 3: monthly trend

```python
monthly = (
    df.groupby(df["placed"].dt.to_period("M").dt.start_time)["revenue"]
    .sum()
    .reset_index()
    .rename(columns={"placed": "month"})
)
monthly["month"] = monthly["month"].dt.date
trend = mm.Document(
    monthly,
    name="Monthly",
    column_types={"revenue": "currency"},
    number_formats={"month": "mmm yyyy"},
)
print(trend.to_text())
```

Output:

```text
Monthly
+------------+-----------+
|   month    |  revenue  |
+------------+-----------+
| 2024-07-01 |   $760.00 |
| 2024-08-01 | $1,031.25 |
| 2024-09-01 | $1,675.00 |
+------------+-----------+
```

`number_formats` only affects spreadsheet output: Excel shows `Jul 2024`, while the text
preview shows the underlying date.

## One workbook, three sheets

The first document is the workbook; `add_child` appends sheets in order. (Use
`add_sheet(data, name=...)` to create a child that inherits the parent's options.)

```python
workbook = mm.Document(
    by_customer,
    name="By customer",
    title="Acme Coffee - Q3 2024",
    author="Finance",
    column_types={"revenue": "currency", "share": "percent"},
)
workbook.add_child(trend)
workbook.add_child(detail)
workbook.write("acme_q3.xlsx")

print([sheet.name for sheet in workbook.sheets])
```

Output:

```text
['By customer', 'Monthly', 'Orders']
```

## Publish everywhere

The same document renders to every format; the file extension chooses:

```python
for name in ["acme_q3.xlsx", "acme_q3.html", "acme_q3.md", "acme_q3.json", "acme_q3.csv"]:
    workbook.write(name)
```

- `.html` -- a styled page with one table per sheet, ready for email or an intranet.
- `.md` -- Markdown tables for a wiki, a pull request or an LLM prompt.
- `.json` -- a [workbook spec](../workbook-spec.md) that rebuilds the exact workbook.
- `.csv` -- CSV holds a single sheet, so only the first sheet is written.
- `.xls` -- also available for old systems (`pip install "marmir[xls]"`).

## Read it back, convert it

```python
for sheet in mm.read("acme_q3.xlsx"):
    print(f"{sheet.name}: {len(sheet.rows)} rows, columns {sheet.columns}")
```

Output:

```text
By customer: 3 rows, columns ['customer', 'orders', 'bags', 'revenue', 'share']
Monthly: 3 rows, columns ['month', 'revenue']
Orders: 6 rows, columns ['order_id', 'customer', 'placed', 'bags', 'price']
```

`mm.read_document` loads a file as a `Document`, so converting is one line:

```python
mm.read_document("acme_q3.xlsx").write("acme_q3_copy.html")
```

The same from the shell:

```bash
marmir read acme_q3.xlsx --sheet Monthly
marmir convert acme_q3.xlsx acme_q3.md
marmir convert acme_q3.json acme_q3_rebuilt.xlsx
```

## Recap

- DB-API cursors, DataFrames, dicts and lists all work as input.
- Build sheets separately, then combine them with `add_child` / `add_sheet`.
- One document writes to XLSX, XLS, HTML, Markdown, JSON, CSV/TSV and text.
- `mm.read` / `mm.read_document` and `marmir convert` handle the reverse direction.

Next: [4. The workbook spec](04-workbook-spec.md).
