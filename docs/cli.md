# Command line

`pip install marmir` installs `marmir` (and `marmir-mcp` with the `mcp` extra).

```bash
marmir convert INPUT OUTPUT [-f FORMAT] [--input-format FMT] [-o KEY=VALUE ...]
marmir read PATH [--sheet NAME] [--max-rows N] [--output markdown|text|csv|json]
marmir validate SPEC.json            # exit code 1 and one error per line when invalid
marmir schema                        # workbook spec JSON Schema
marmir tools [--provider openai|openai-chat|anthropic] [--no-read]
marmir mcp [marmir-mcp options]      # MCP server
marmir serve [--host H] [--port P]   # HTTP API
marmir openapi [--url URL]           # OpenAPI document for GPT Actions
```

Examples:

```bash
marmir convert examples/workbook_spec.json sales.xlsx
marmir convert records.json out.xlsx -o autofilter=true -o freeze_col=1
marmir convert orders.csv orders.md
marmir convert legacy.xls modern.xlsx
cat spec.json | marmir convert - - -f html > report.html
marmir read sales.xlsx --sheet Summary --max-rows 20
```

`INPUT` may be a workbook spec, a JSON list of records, CSV/TSV, XLSX or XLS; `-` reads
stdin. `OUTPUT` picks the format from its extension; `-` writes to stdout (Markdown
unless `-f` is given). Option values are parsed as JSON when possible (`true`, `1`,
`["a"]`), otherwise used as strings.
