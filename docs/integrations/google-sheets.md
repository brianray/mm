# Google Sheets

`pip install "marmir[gsheets]"` (uses [gspread](https://docs.gspread.org)).

```python
doc = mm.Document(rows, name="Sales")
doc.add_sheet(detail, name="Detail")
sheet = doc.write_gsheet(
    "Q3 Sales",
    credentials_file="service-account.json",   # or client=gspread_client
    share_with="you@example.com",
    folder_id=None,
)
print(sheet.url)
```

Each sheet becomes a worksheet. Values are sent with `USER_ENTERED`, so formulas stay
live and links become `HYPERLINK()` formulas; text that starts with `=`, `+`, `-` or `@`
is escaped. Frozen header rows/columns carry over; cell styling does not.

The 0.x `write_gdata()` relied on Google's retired ClientLogin API. It now emits a
`DeprecationWarning` and forwards to `write_gsheet()`.
