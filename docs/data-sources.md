# Data sources

`mm.Document(data)` accepts the shapes data usually arrives in. All of them end up as
rows plus column titles.

| Input | Column titles come from | Notes |
| --- | --- | --- |
| list/tuple/generator of dicts or `Mapping`s | keys (first-seen order) or `order=` | later rows may add keys |
| list of lists/tuples | `order=` | without `order`: `Column 1`, `Column 2`, ... |
| dataclasses, `NamedTuple`s, Pydantic models, plain objects | field names | |
| column dict `{"a": [1, 2], "b": [3, 4]}` | keys | lists must be the same length |
| pandas `DataFrame` | `df.columns` | NaN/NaT become blanks; numpy scalars and Timestamps become Python values |
| DB-API cursor after `execute()` | `cursor.description` | sqlite3, psycopg, mysqlclient, ... |
| `sqlite3.Row`, psycopg `DictRow`/`RealDictRow` | keys | |
| Django QuerySet | model fields | see below |

## pandas

```python
import pandas as pd
import mm

df = pd.read_csv("visits.csv", parse_dates=["date"])
mm.Document(df, name="Visits", number_formats={"visits": "#,##0"}).write("visits.xlsx")
```

## SQL

```python
cursor = conn.execute("select id, customer, total from orders")
doc = mm.Document.from_cursor(cursor, column_types={"total": "currency"})
```

With psycopg's dict cursors (the legacy `psycopg2.extras.DictCursor` example still
works), pass `cursor.fetchall()`.

## Django

`QuerySet.values(...)` works with the default model. To use the model's field
definitions (types come from the field classes, not the values), use the contrib model
and grid:

```python
from mm.contrib.django import DjangoDataModel, DjangoGrid

doc = mm.Document(
    Book.objects.select_related("author"),
    data_model_class=DjangoDataModel,
    grid_class=DjangoGrid,
    order=["title", "author", "published", "price"],   # optional
)
```

Foreign keys are written with `str(related_object)`. `DjangoDataModel(...,
verbose_names=True)` uses each field's `verbose_name` as the header.

## Files

```python
doc = mm.Document.from_file("input.csv")      # .xlsx .xls .csv .tsv .json
```

## Type control

```python
mm.Document(rows, column_types={"joined": "date", "salary": mm.Currency})
```

Explicit types coerce strings (`"2024-01-31"`, `"1,250.50"`, `"yes"`, `"12.5%"`), which
is handy for CSV input and LLM-generated data.
