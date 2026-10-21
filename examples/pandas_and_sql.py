"""DataFrames and SQL cursors straight to Excel.

    pip install 'marmir[pandas]'
"""

import sqlite3
from pathlib import Path

import pandas as pd

import mm

df = pd.DataFrame(
    {"date": pd.date_range("2024-01-01", periods=5), "visits": [120, 98, 143, 87, 160]}
)
doc = mm.Document(df, name="Visits", number_formats={"visits": "#,##0"})

conn = sqlite3.connect(":memory:")
conn.execute("create table orders (id integer, customer text, total real)")
conn.executemany("insert into orders values (?, ?, ?)", [(1, "Acme", 99.5), (2, "Globex", 250.0)])
doc.add_sheet(conn.execute("select * from orders"), name="Orders", column_types={"total": "currency"})

Path("marmir_output").mkdir(exist_ok=True)
doc.write("marmir_output/report.xlsx")
print(doc.to_markdown())
