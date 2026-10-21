# 1. Your first spreadsheet

**Goal:** turn a list of orders into a clean Excel file, understand what Marmir decided
for you, and read the file back.

## The data

Acme keeps its orders as a list of dictionaries -- the shape you get from most APIs,
ORMs and JSON files:

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

## One line to Excel

```python
doc = mm.Document(orders, name="Orders")
doc.write("orders.xlsx")
```

Open `orders.xlsx`. Without any configuration you get:

- a styled header row that stays frozen while you scroll,
- `placed` as real Excel dates (sortable, filterable), `bags` and `price` as numbers,
  `paid` as TRUE/FALSE booleans,
- alternating row shading,
- columns sized to fit, using real font measurements.

## What Marmir decided

Marmir inspects every value in every column to choose a type. `doc.columns` shows the
result:

```python
for column in doc.columns:
    print(column)
```

Output:

```text
{'name': 'order_id', 'type': 'integer'}
{'name': 'customer', 'type': 'string'}
{'name': 'placed', 'type': 'date'}
{'name': 'bags', 'type': 'integer'}
{'name': 'price', 'type': 'number'}
{'name': 'paid', 'type': 'boolean'}
```

`doc.to_text()` is a quick way to eyeball a document without opening Excel:

```python
print(doc.to_text())
```

Output:

```text
Orders
+----------+----------------+------------+------+-------+-------+
| order_id |    customer    |   placed   | bags | price | paid  |
+----------+----------------+------------+------+-------+-------+
|     1001 | Blue Door Cafe | 2024-07-02 |   40 |  14.5 | TRUE  |
|     1002 | Harbor Bakery  | 2024-07-09 |   12 |  15.0 | FALSE |
|     1003 | Union Diner    | 2024-08-01 |   75 | 13.75 | TRUE  |
|     1004 | Blue Door Cafe | 2024-09-18 |   40 |  14.5 | TRUE  |
+----------+----------------+------------+------+-------+-------+
```

## Choosing and ordering columns

`order` picks the columns and their order:

```python
summary = mm.Document(orders, order=["customer", "bags", "paid"], name="Summary")
print(summary.to_markdown())
```

Output:

```text
## Summary

| customer | bags | paid |
| --- | ---: | --- |
| Blue Door Cafe | 40 | TRUE |
| Harbor Bakery | 12 | FALSE |
| Union Diner | 75 | TRUE |
| Blue Door Cafe | 40 | TRUE |
```

## Rows as lists, and data that arrives as text

Data from CSV exports and many APIs comes as lists of strings. Give the column names
with `order` and the types with `column_types`, and Marmir converts the values:

```python
raw = [
    ("1005", "Harbor Bakery", "2024-09-20", "18", "15.00", "no"),
    ("1006", "Union Diner", "2024-09-27", "60", "13.75", "yes"),
]
imported = mm.Document(
    raw,
    order=["order_id", "customer", "placed", "bags", "price", "paid"],
    column_types={"order_id": "integer", "placed": "date", "bags": "integer", "price": "number", "paid": "boolean"},
)
print(imported.rows[0])
```

Output:

```text
[1005, 'Harbor Bakery', datetime.date(2024, 9, 20), 18, 15.0, False]
```

`column_types` accepts type names (`"date"`, `"currency"`, ...) or field classes
(`mm.Date`, `mm.Currency`, ...).

## Options

Options are keyword arguments. A few useful ones:

```python
doc = mm.Document(
    orders,
    name="Orders",
    autofilter=True,      # filter dropdowns on the header row
    freeze_col=2,         # keep order_id and customer visible when scrolling right
    date_format="yyyy-mm-dd",
)
doc.write("orders.xlsx")
```

The full list is in [Concepts -> Configuration](../concepts.md#configuration).

## Reading it back

`mm.read` returns one `Sheet` per worksheet:

```python
sheet = mm.read("orders.xlsx")[0]
print(sheet.name, sheet.columns)
print(sheet.records()[0])
```

Output:

```text
Orders ['order_id', 'customer', 'placed', 'bags', 'price', 'paid']
{'order_id': 1001, 'customer': 'Blue Door Cafe', 'placed': datetime.date(2024, 7, 2), 'bags': 40, 'price': 14.5, 'paid': True}
```

Types survive the round trip: dates come back as dates, booleans as booleans.

## Recap

- `mm.Document(rows).write("file.xlsx")` covers most needs.
- `doc.columns` shows the inferred types; `column_types` overrides them and converts text.
- `order` selects and orders columns.
- `mm.read` reads files back.

Next: [2. Formatting, formulas and styles](02-formatting-and-formulas.md).
