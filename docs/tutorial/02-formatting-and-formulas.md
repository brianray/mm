# 2. Formatting, formulas and styles

**Goal:** turn chapter 1's raw order list into a report a finance team would sign off:
money shown as money, dates shown the way people read them, live totals, and a few
visual cues.

We start from the same `orders` list:

```python
import datetime as dt

import mm

orders = [
    {"order_id": 1001, "customer": "Blue Door Cafe", "placed": dt.date(2024, 7, 2), "bags": 40, "price": 14.5, "paid": True},
    {"order_id": 1002, "customer": "Harbor Bakery", "placed": dt.date(2024, 7, 9), "bags": 12, "price": 15.0, "paid": False},
    {"order_id": 1003, "customer": "Union Diner", "placed": dt.date(2024, 8, 1), "bags": 75, "price": 13.75, "paid": True},
    {"order_id": 1004, "customer": "Blue Door Cafe", "placed": dt.date(2024, 9, 18), "bags": 40, "price": 14.5, "paid": True},
]
```

## Values keep their meaning; formats change their look

The most important habit: **store raw values and let the format do the presentation.**
`14.5` stays a number Excel can add up; `mm.Currency` only changes how it is shown.

| You write | The cell holds | Shown as |
| --- | --- | --- |
| `mm.Currency(14.5)` | `14.5` | `$14.50` |
| `mm.Currency(14.5, symbol="€", decimals=0)` | `14.5` | `€15` |
| `mm.Percent(0.125, decimals=1)` | `0.125` | `12.5%` |
| `mm.Date(d, "%d %b %Y")` | the date | `02 Jul 2024` |
| `mm.Cell(1234.5, format="#,##0.0")` | `1234.5` | `1,234.5` |

Date formats accept the `strftime` codes you already know; Marmir translates them to
Excel's syntax. Other formats use Excel codes (`"#,##0.00"`, `"0.0%"`).

## Live formulas

Spreadsheets are valuable because they recalculate. Marmir writes real formulas with
`mm.Formula("...")` (or any string starting with `=`). References use A1 notation, and
**row 1 is the header**, so the first data row is row 2.

Let's build the report rows. Each line gets a `Total` formula (`bags x price`), and a
final row sums everything:

```python
rows = []
for excel_row, order in enumerate(orders, start=2):
    rows.append({
        "Order": order["order_id"],
        "Customer": order["customer"],
        "Placed": mm.Date(order["placed"], "%d %b %Y"),
        "Bags": order["bags"],
        "Price": mm.Currency(order["price"]),
        "Total": mm.Formula(f"D{excel_row}*E{excel_row}"),
        "Status": "Paid" if order["paid"] else mm.Cell("Unpaid", style="color: #C00000; font-weight: bold"),
    })

last = len(rows) + 1          # the last data row in Excel terms
rows.append({
    "Order": mm.Cell("Total", style="font-weight: bold"),
    "Bags": mm.Formula(f"SUM(D2:D{last})"),
    "Total": mm.Formula(f"SUM(F2:F{last})", style="font-weight: bold; border: thin"),
})
```

The total row only fills three columns; the others are left blank automatically.

> **Tip:** compute references from data (`last = len(rows) + 1`) instead of
> hard-coding `D5`. The report keeps working when next quarter has 400 orders.

## Styles are CSS

Styling uses CSS-like strings, so you rarely need to look anything up:

```python
coffee_brown = "#6F4E37"
report = mm.Document(
    rows,
    name="Q3 Orders",
    title="Acme Coffee - Q3 orders",
    header_style=f"color: white; background-color: {coffee_brown}; font-weight: bold; text-align: center",
    row_styles=("background-color: #FFFFFF", "background-color: #F5EFE6"),
    column_styles={"Customer": "font-weight: bold"},
    number_formats={"Total": '"$"#,##0.00'},
    column_widths={"Customer": 22},
    autofilter=True,
    freeze_col=2,
)
report.write("q3_orders.xlsx")
```

What each option does:

- `header_style` styles the header row; `row_styles` alternates down the rows
  (banding). Pass `row_styles=()` for none.
- `column_styles` styles every cell in a column; a cell's own `style` wins over it.
- `number_formats` sets a column's number format -- here the formula column `Total`,
  which has no type of its own.
- `column_widths` fixes a width in characters; other columns are auto-sized.

Supported properties include `color`, `background-color`, `font-family`, `font-size`,
`font-weight`, `font-style`, `text-decoration`, `text-align`, `vertical-align`,
`white-space`, `border` and `border-color`. See [styling](../styling.md).

## Check your work without opening Excel

```python
print(report.to_markdown())
```

Output:

```text
## Q3 Orders

| Order | Customer | Placed | Bags | Price | Total | Status |
| --- | --- | --- | ---: | ---: | --- | --- |
| 1001 | Blue Door Cafe | 02 Jul 2024 | 40 | $14.50 | =D2*E2 | Paid |
| 1002 | Harbor Bakery | 09 Jul 2024 | 12 | $15.00 | =D3*E3 | Unpaid |
| 1003 | Union Diner | 01 Aug 2024 | 75 | $13.75 | =D4*E4 | Paid |
| 1004 | Blue Door Cafe | 18 Sep 2024 | 40 | $14.50 | =D5*E5 | Paid |
| Total |  |  | =SUM(D2:D5) |  | =SUM(F2:F5) |  |
```

Formulas appear as text in Markdown (nothing calculates them there); Excel, LibreOffice
and Google Sheets calculate them when the file is opened.

Notice the `Order` column holds numbers *and* the word "Total". Marmir records the
column as `string`, but each cell keeps its own type, so 1001 is still written as a
number:

```python
from openpyxl import load_workbook

sheet = load_workbook("q3_orders.xlsx").active
print(repr(sheet["A2"].value), repr(sheet["A6"].value))
print(sheet["E2"].number_format, "|", sheet["F2"].number_format, "|", sheet["C2"].number_format)
print(sheet.freeze_panes, sheet.auto_filter.ref)
```

Output:

```text
1001 'Total'
"$"#,##0.00;-"$"#,##0.00 | "$"#,##0.00 | dd mmm yyyy
C2 A1:G6
```

## Text that starts with "="

Strings beginning with `=` are treated as formulas -- convenient, but not what you want
for, say, a product note like `"=== fragile ==="`. Either type the column as string or
switch inference off:

```python
notes = mm.Document([{"note": "=== fragile ==="}], column_types={"note": "string"})
print(type(notes.grid.grid_data[0][0]).__name__)
```

Output:

```text
StringFieldType
```

(`mm.Document(rows, infer_formulas=False)` does the same for every column.)

## Recap

- Keep values raw; use `mm.Currency`, `mm.Percent`, `mm.Date(value, "%d %b %Y")`,
  `format=` and `number_formats` for presentation.
- `mm.Formula` writes live formulas; data starts at row 2.
- `header_style`, `row_styles`, `column_styles` and per-cell `style` take CSS.

Next: [3. Multi-sheet reports from real data](03-multi-sheet-reports.md).
