---
name: marmir-spreadsheets
description: Create, convert and read spreadsheets (Excel .xlsx/.xls, CSV, Markdown, HTML) with the Marmir Python library. Use when the user asks for a spreadsheet, Excel file, workbook, tracker, budget, financial model, data export or table file, or wants to read/summarise an existing .xlsx/.xls/.csv file.
---

# Marmir spreadsheets

Marmir turns Python data or a JSON *workbook spec* into well-formatted spreadsheets:
typed cells, number/date formats, live formulas, hyperlinks, styled headers, banded
rows, frozen panes, auto-sized columns and multiple sheets.

## Setup

```bash
pip install marmir            # add 'marmir[xls]' for legacy .xls, 'marmir[images]' for images
```

If the `create_spreadsheet` / `read_spreadsheet` MCP tools are available, prefer them;
they take the same workbook spec described below.

## Create a spreadsheet from a workbook spec (preferred)

1. Write the spec as JSON (one object per sheet; array rows in column order).
2. Validate, then build:

```bash
marmir validate spec.json          # prints every problem with its JSON path
marmir convert spec.json report.xlsx
marmir read report.xlsx            # check the result as Markdown
```

Spec shape:

```json
{
  "title": "Q3 Sales",
  "sheets": [{
    "name": "Sales",
    "columns": [
      {"name": "Region", "type": "string"},
      {"name": "Revenue", "type": "currency"},
      {"name": "Growth", "type": "percent"},
      {"name": "Closed", "type": "date", "format": "%Y-%m-%d"}
    ],
    "rows": [
      ["North", 125000, 0.12, "2024-09-30"],
      ["South", 98000, -0.03, "2024-09-28"],
      [{"value": "Total", "style": "font-weight: bold"}, {"formula": "SUM(B2:B3)"}, null, null]
    ],
    "options": {"autofilter": true, "freeze_row": 1}
  }]
}
```

Rules that keep spreadsheets correct:

- **Types**: string, integer, number, decimal, percent, currency, boolean, date,
  datetime, time, duration, url, formula. Keep values raw: `0.12` for 12%,
  `125000` not `"$125,000"`. Dates are ISO strings.
- **Formulas**: `{"formula": "SUM(B2:B10)"}` or a string starting with `=`. Row 1 is
  the header row, so data starts at row 2; column A is the first column. Prefer
  formulas for totals and derived columns so the sheet stays live.
- **Links**: `{"url": "https://...", "text": "label"}`.
- **Styling**: CSS-like strings on cells (`{"value": ..., "style": "..."}`), columns
  (`"style"`) or `options.header_style` / `options.row_styles`. Properties: color,
  background-color, font-family, font-size, font-weight, font-style, text-decoration,
  text-align, vertical-align, white-space, border, border-color, number-format.
- **Formats**: Excel codes (`"#,##0.00"`, `"0.0%"`) or strftime codes for dates.
- Several sheets: add more objects to `sheets`.

## Create from Python data

```python
import mm

rows = [{"region": "North", "revenue": 125000, "growth": mm.Percent(0.12)}]
doc = mm.Document(rows, name="Sales", autofilter=True)
doc.add_sheet(other_rows, name="Detail")
doc.write("sales.xlsx")         # format from extension: .xlsx .xls .csv .tsv .json .md .html .txt
print(doc.to_markdown())        # check what you built
```

Accepted data: list of dicts, list of lists (`order=[...]` gives headers), dataclasses,
pydantic models, a column dict, a pandas DataFrame, or a DB-API cursor.

## Read a spreadsheet

```bash
marmir read file.xlsx --max-rows 50            # Markdown, formulas shown as =...
marmir read file.xlsx --output json
```

```python
for sheet in mm.read("file.xlsx", max_rows=100):
    print(sheet.name, sheet.columns, sheet.rows[:3])
```

## After creating a file

Tell the user the file name and summarise the sheets, columns and any formulas.
Run `marmir read <file>` to double-check the output before reporting success.
