# Marmir

**Python data in, polished spreadsheets out -- for people and for AI agents.**

[![CI](https://github.com/brianray/mm/actions/workflows/ci.yml/badge.svg)](https://github.com/brianray/mm/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)

[![QR code to repository](https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=https%3A%2F%2Fgithub.com%2Fbrianray%2FMarMir)](https://github.com/brianray/MarMir) < Scan to this repo

Marmir takes lists of dicts, DataFrames, SQL cursors, Django QuerySets -- or a JSON
"workbook spec" written by a language model -- and produces spreadsheets people actually
want to open: typed cells, real dates, live formulas, hyperlinks, styled headers, banded
rows, frozen panes and auto-sized columns. One document can be written as Excel
(`.xlsx`, legacy `.xls`), CSV/TSV, JSON, Markdown, HTML or a plain-text table, and read
back again.

Version 2 is a ground-up rewrite of the 2013 library for modern Python, with first-class
support for GenAI: tool definitions for OpenAI and Anthropic, an MCP server for Claude
Desktop / Claude Code / ChatGPT / the OpenAI Agents SDK, an HTTP API for custom GPT
Actions, a Claude Skill and plugin, and a validator that tells a model exactly what to fix.

```bash
pip install marmir
```

## Thirty-second tour

```python
import datetime as dt
import mm

rows = [
    {"id": 1, "msg": "My first row", "when": dt.datetime.now()},
    {"id": 2, "msg": "My second row", "when": dt.datetime.now()},
]
mm.Document(rows).write("example.xlsx")
```

That is the whole API for the common case. Types are inferred (a date is a date, an int
is an int), the header is styled and frozen, and columns are sized to fit.

Get fancier when you need to:

```python
sales = [
    {"region": "North", "revenue": mm.Currency(125000), "growth": mm.Percent(0.12),
     "closed": mm.Date(dt.date(2024, 9, 30), "%d %b %Y"),
     "crm": mm.URL("https://crm.example.com/north", "North pipeline")},
    {"region": "South", "revenue": mm.Currency(98000), "growth": mm.Percent(-0.03)},
    {"region": mm.Cell("Total", style="font-weight: bold"),
     "revenue": mm.Formula("SUM(B2:B3)")},
]
doc = mm.Document(sales, name="Sales", autofilter=True, title="Q3 Sales")
doc.add_sheet([{"deal": "Acme", "amount": 52000}], name="Deals")  # more sheets
doc.write("sales.xlsx")                      # or .xls .csv .tsv .json .md .html .txt
print(doc.to_markdown())                     # LLM-friendly view of the same data
```

## Built for GenAI

Language models are good at deciding *what* a spreadsheet should contain and bad at
producing binary Excel files. Marmir splits the job: the model writes a small JSON spec,
Marmir validates it and renders the file.

```json
{
  "title": "Q3 Sales",
  "sheets": [{
    "name": "Sales",
    "columns": [{"name": "Region", "type": "string"}, {"name": "Revenue", "type": "currency"}],
    "rows": [["North", 125000], ["South", 98000],
             [{"value": "Total", "style": "font-weight: bold"}, {"formula": "SUM(B2:B3)"}]]
  }]
}
```

When the spec is wrong, the model gets precise, path-prefixed feedback instead of a stack
trace -- for example `sheets[0].rows[2][1]: 'abc' is not a valid integer` or
`sheets[0].rows[4][3].formula: unbalanced parentheses in 'SUM(B2:B4'` -- and can fix it
on the next turn.

| Where you work | How to plug Marmir in | Guide |
| --- | --- | --- |
| Claude Desktop / Claude Code | MCP server: `claude mcp add marmir -- uvx --from "marmir[mcp]" marmir-mcp`, or install this repo as a plugin | [Anthropic](docs/integrations/anthropic.md) |
| Claude API (Messages) | `SpreadsheetTools().anthropic_tools()` + `handle_anthropic_tool_use()` | [Anthropic](docs/integrations/anthropic.md) |
| Claude Skills | `skills/marmir-spreadsheets/SKILL.md` | [Anthropic](docs/integrations/anthropic.md#agent-skill) |
| OpenAI Responses / Chat Completions | `SpreadsheetTools().openai_tools()` + `handle_openai_tool_call()` | [OpenAI](docs/integrations/openai.md) |
| OpenAI Agents SDK, ChatGPT connectors, remote MCP | `marmir-mcp` (stdio or streamable HTTP) | [MCP](docs/integrations/mcp.md) |
| Custom GPTs (Actions) / any HTTP client | `marmir serve` + OpenAPI | [HTTP API](docs/integrations/http-api.md) |
| Shell, CI, other languages | `marmir convert spec.json out.xlsx` | [CLI](docs/cli.md) |

```python
from mm.ai import SpreadsheetTools

tools = SpreadsheetTools(output_dir="out")       # writes are confined to out/
tools.anthropic_tools()                          # tools=[...] for Claude
tools.openai_tools()                             # tools=[...] for OpenAI
tools.call("create_spreadsheet", spec)           # -> {"ok": True, "path": ..., "preview": ...}
```

Three tools are exposed everywhere: `create_spreadsheet`, `preview_spreadsheet` (validate
and render as Markdown without writing) and `read_spreadsheet` (inspect `.xlsx`, `.xls`,
`.csv`, `.json` files).

## Install options

```bash
pip install marmir                 # core: XLSX, CSV, JSON, Markdown, HTML, text, reading
pip install "marmir[xls]"          # legacy Excel 97-2003 (.xls) read/write
pip install "marmir[images]"       # images in cells (Pillow)
pip install "marmir[pandas]"       # DataFrame input
pip install "marmir[mcp]"          # MCP server (marmir-mcp)
pip install "marmir[server]"       # HTTP API (marmir serve)
pip install "marmir[gsheets]"      # publish to Google Sheets
pip install "marmir[all]"          # everything above
```

Python 3.10 or newer. The only required dependency is `openpyxl`.

## Documentation

- [Getting started](docs/getting-started.md)
- **[Tutorial](docs/tutorial/index.md)**: seven hands-on chapters, from a first spreadsheet to AI agents, GPT Actions and extensions
- [Cookbook](docs/cookbook.md): short recipes for common tasks
- [Concepts: Document, DataModel, Grid, Composer, Config](docs/concepts.md)
- [Data sources: dicts, lists, DataFrames, SQL, Django](docs/data-sources.md)
- [Cell types, formats and styling](docs/styling.md)
- [Output formats and reading files](docs/formats.md)
- [The workbook spec (JSON for LLMs)](docs/workbook-spec.md)
- Integrations: [Anthropic / Claude](docs/integrations/anthropic.md) · [OpenAI](docs/integrations/openai.md) · [MCP](docs/integrations/mcp.md) · [HTTP API & GPT Actions](docs/integrations/http-api.md) · [Google Sheets](docs/integrations/google-sheets.md)
- [Command line](docs/cli.md)
- [FAQ and troubleshooting](docs/faq.md)
- [Security model](docs/security.md)
- [Migrating from Marmir 0.x](docs/migration.md)
- [API reference](docs/api-reference.md)
- [Changelog](CHANGELOG.md) · [Contributing](CONTRIBUTING.md)

## Why "Marmir"?

Brian Ray ([@brianray](https://github.com/brianray)) wrote Marmir in 2011 to stop
fighting sub-par Python libraries for business spreadsheets. The name comes from parts of
the names Maura and Miranda, the author's daughters.

Copyright (c) 2013-2026 Brian Ray.
