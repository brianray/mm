# The workbook spec

The workbook spec is a small JSON format for describing spreadsheets. It is what the
`create_spreadsheet` tool takes, what `marmir convert spec.json out.xlsx` reads, and what
`doc.to_json()` writes -- so specs round-trip.

The full JSON Schema: `marmir schema`, `mm.WORKBOOK_SPEC_SCHEMA`, the MCP resource
`marmir://schema/workbook`, or `GET /v1/schema` on the HTTP API.

## Shape

```json
{
  "title": "Q3 Sales",                 // optional document properties
  "author": "Sales Ops",
  "description": "...",
  "options": {"autofilter": true},     // optional, applied to every sheet
  "sheets": [
    {
      "name": "Summary",               // tab name (31 chars max, sanitised)
      "columns": [                     // required for array rows
        {"name": "Region", "type": "string", "width": 16},
        {"name": "Revenue", "type": "currency"},
        {"name": "Attainment", "type": "percent", "format": "0.0%"},
        {"name": "Last deal", "type": "date", "format": "%Y-%m-%d"},
        "Notes"                        // a bare string is a title with no type
      ],
      "rows": [
        ["North", 125000, "=B2/120000", "2024-09-30", null],
        [{"value": "Total", "style": "font-weight: bold"}, {"formula": "SUM(B2:B2)"}, null, null, null]
      ],
      "options": {"freeze_col": 1}     // per-sheet options win over global ones
    },
    {
      "name": "Deals",
      "rows": [{"Deal": "Acme", "Amount": 52000}]     // object rows: columns from keys
    }
  ]
}
```

(Comments are for illustration; JSON has none.)

Shorthands accepted by `mm.from_spec` and the tools: a single sheet at the top level
(`{"columns": ..., "rows": ...}`), or a bare list of row objects.

## Columns

| Key | Meaning |
| --- | --- |
| `name` | header text (required) |
| `type` | `string`, `integer`, `number`, `decimal`, `percent`, `currency`, `boolean`, `date`, `datetime`, `time`, `duration`, `url`, `formula`, `image` |
| `format` | Excel number format, or `strftime` codes for dates |
| `width` | width in characters |
| `style` | CSS-like style for the column's cells |

Typed columns coerce values: `"2024-09-30"` -> date, `"1,250"` -> 1250, `"yes"` -> true,
`"12%"` -> 0.12 for percent.

## Cells

| Cell | Meaning |
| --- | --- |
| `"text"`, `42`, `3.5`, `true`, `null` | plain values |
| `"=SUM(B2:B5)"` | formula (when `infer_formulas` is on, the default) |
| `{"formula": "SUM(B2:B5)"}` | formula, explicit |
| `{"url": "https://...", "text": "label"}` | hyperlink |
| `{"value": ..., "type": "...", "format": "...", "style": "..."}` | typed/styled value |
| `{"value": 0.25, "type": "percent", "decimals": 1}` | percent with decimals |
| `{"value": 9.5, "type": "currency", "symbol": "€", "decimals": 2}` | currency |
| `{"image": "logo.png", "width": 80, "height": 40}` | image (disabled in agent tools by default) |

Formulas use A1 references. Row 1 is the header row; data starts at row 2.

## Options

Any [configuration option](concepts.md#configuration) except the Python-only ones. The
most useful for agents: `autofilter`, `freeze_row`, `freeze_col`, `header_style`,
`row_styles`, `headers`, `infer_formulas`, `date_format`.

## Validation

```python
errors = mm.validate_spec(spec)          # [] when valid
doc = mm.from_spec(spec)                 # raises mm.SpecValidationError(errors)
```

```
$ marmir validate bad.json
sheets[0].rows[1]: has 3 cells but there are 2 columns
sheets[0].rows[2][1]: 'abc' is not a valid integer (invalid literal for int() with base 10: 'abc')
sheets[0].rows[3][0].formula: unbalanced parentheses in 'SUM(B2:B4'
sheets[1].columns[0].type: unknown column type 'money!'; valid types: boolean, currency, ...
```

Checks include: unknown keys (catches typos), row width vs columns, unknown columns in
object rows, duplicate column names, value coercion against column/cell types,
balanced parentheses and quotes in formulas, option types, image policy and a total cell
limit (`max_cells`).

## Python equivalents

```python
doc = mm.from_spec(spec, base_dir="assets")   # base_dir resolves relative image paths
spec = doc.to_spec()                           # dict
text = doc.to_json()                           # JSON string
summary = doc.describe(sample_rows=3)          # compact overview for prompts
```
