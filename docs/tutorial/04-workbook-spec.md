# 4. The workbook spec

**Goal:** describe a workbook as plain JSON, validate it, and render it. This is the
format AI models write in [chapter 5](05-ai-agents.md), and it is just as handy for
config-driven reports, other programming languages and the command line.

## Why a spec?

Python objects are great inside one program. A JSON description works *between*
programs: a front end, a job queue, a different language -- or a language model, which
is good at deciding what a sheet should contain and bad at emitting binary `.xlsx`
files. Marmir validates the JSON, explains every problem, and renders the file.

## A first spec

Here is Acme's Q3 summary as a spec:

```python
import json

import mm

spec = {
    "title": "Acme Coffee - Q3 summary",
    "sheets": [
        {
            "name": "Summary",
            "columns": [
                {"name": "Customer", "type": "string", "width": 20},
                {"name": "Bags", "type": "integer"},
                {"name": "Revenue", "type": "currency"},
                {"name": "Share", "type": "percent", "format": "0.0%"},
                {"name": "Last order", "type": "date", "format": "%d %b %Y"},
            ],
            "rows": [
                ["Union Diner", 135, 1856.25, "=C2/C5", "2024-09-27"],
                ["Blue Door Cafe", 80, 1160, "=C3/C5", "2024-09-18"],
                ["Harbor Bakery", 30, 450, "=C4/C5", "2024-09-20"],
                [
                    {"value": "Total", "style": "font-weight: bold"},
                    {"formula": "SUM(B2:B4)"},
                    {"formula": "SUM(C2:C4)", "style": "font-weight: bold"},
                    None,
                    None,
                ],
            ],
            "options": {"autofilter": True},
        }
    ],
}
```

The pieces:

- **columns** -- a name and optionally a `type`, `format`, `width` and `style`. Types:
  `string`, `integer`, `number`, `decimal`, `percent`, `currency`, `boolean`, `date`,
  `datetime`, `time`, `duration`, `url`, `formula`.
- **rows** -- arrays in column order (or objects keyed by column name). Dates are ISO
  strings; typed columns convert them.
- **cells** -- plain values, formulas (`"=C2/C5"` or `{"formula": "..."}`), links
  (`{"url": ..., "text": ...}`) or styled/typed values (`{"value": ..., "style": ...}`).
- **options** -- any sheet option (`autofilter`, `freeze_row`, `header_style`, ...).

## Validate, then render

```python
print(mm.validate_spec(spec))

doc = mm.from_spec(spec)
doc.write("summary.xlsx")
print(doc.to_markdown())
```

Output:

```text
[]
## Summary

| Customer | Bags | Revenue | Share | Last order |
| --- | ---: | ---: | ---: | --- |
| Union Diner | 135 | $1,856.25 | =C2/C5 | 27 Sep 2024 |
| Blue Door Cafe | 80 | $1,160.00 | =C3/C5 | 18 Sep 2024 |
| Harbor Bakery | 30 | $450.00 | =C4/C5 | 20 Sep 2024 |
| Total | =SUM(B2:B4) | =SUM(C2:C4) |  |  |
```

An empty list from `validate_spec` means valid.

## When the spec is wrong

Validation reports *every* problem, each with a JSON path. Let's break a copy on
purpose:

```python
import copy

broken = copy.deepcopy(spec)
sheet = broken["sheets"][0]
sheet["rows"][0][1] = "lots"                        # not an integer
sheet["rows"][1].append("extra")                    # one cell too many
sheet["rows"][3][2] = {"formula": "SUM(C2:C4"}      # missing parenthesis
sheet["columns"][4]["type"] = "day"                 # no such type
sheet["optons"] = {}                                # typo

for error in mm.validate_spec(broken):
    print(error)
```

Output:

```text
sheets[0].optons: unknown property (allowed: name, columns, rows, options)
sheets[0].columns[4].type: unknown column type 'day'; valid types: boolean, currency, date, datetime, decimal, duration, empty, formula, image, integer, number, percent, string, time, url
sheets[0].rows[0][1]: 'lots' is not a valid integer (invalid literal for int() with base 10: 'lots')
sheets[0].rows[1]: has 6 cells but there are 5 columns
sheets[0].rows[3][2].formula: unbalanced parentheses in 'SUM(C2:C4'
```

These messages are written to be read by people *and* by models: in chapter 5 they go
straight back to the AI, which fixes the spec and tries again. `mm.from_spec` raises
`mm.SpecValidationError` with the same list in `.errors`:

```python
try:
    mm.from_spec(broken)
except mm.SpecValidationError as exc:
    print(len(exc.errors), "problems")
```

Output:

```text
5 problems
```

## Round trips

Any document can be turned back into a spec -- including the ones you built from Python
in chapters 1-3 -- and specs rebuild identical workbooks:

```python
again = mm.from_spec(doc.to_spec())
print(again.rows == doc.rows)
print(json.dumps(doc.to_spec()["sheets"][0]["rows"][3]))
```

Output:

```text
True
[{"value": "Total", "style": "font-weight: bold"}, {"formula": "SUM(B2:B4)"}, {"formula": "SUM(C2:C4)", "style": "font-weight: bold"}, null, null]
```

`doc.to_json()` (or `doc.write("file.json")`) produces the same thing as text.

## A compact description for prompts

`describe()` summarises any document -- columns, types, row counts and a few sample
rows -- small enough to paste into a prompt so a model understands an existing
spreadsheet:

```python
info = doc.describe(sample_rows=1)
print(json.dumps(info["sheets"][0]["columns"][:2]))
print(info["sheets"][0]["row_count"], json.dumps(info["sheets"][0]["sample_rows"]))
```

Output:

```text
[{"name": "Customer", "type": "string"}, {"name": "Bags", "type": "integer"}]
4 [["Union Diner", 135, 1856.25, {"formula": "C2/C5"}, "2024-09-27"]]
```

## From the command line

Specs are files, so the CLI handles them too:

```bash
marmir validate summary.json     # one error per line, exit code 1 when invalid
marmir convert summary.json summary.xlsx
marmir schema > workbook.schema.json   # the JSON Schema, e.g. for editor autocompletion
```

## Recap

- A spec is JSON: `sheets` -> `columns` + `rows` (+ `options`).
- `mm.validate_spec` lists every problem with its path; `mm.from_spec` builds the
  document.
- `doc.to_spec()` / `doc.to_json()` go the other way; `doc.describe()` summarises.

Full reference: [the workbook spec](../workbook-spec.md).

Next: [5. Let an AI agent build spreadsheets](05-ai-agents.md).
