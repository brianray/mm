# FAQ and troubleshooting

## Formulas

**My formulas show no values when I read the file back.** Marmir writes formulas;
spreadsheet applications calculate them. Files created by Marmir (or any library) have
no cached results until Excel, LibreOffice or Google Sheets opens and saves them, so
`mm.read(path, formulas=False)` returns `None` for those cells. `mm.read(path)` (the
default) returns the formula text, e.g. `"=SUM(B2:B5)"`.

**My total is off by one row.** Row 1 is the header, so data row *n* (counting from 1)
is Excel row *n + 1*. With `headers=False`, data starts at row 1.

**Text that starts with `=` became a formula.** Strings beginning with `=` are formulas
by default. Use `column_types={"col": "string"}`, `infer_formulas=False`, or (in a spec)
`"options": {"infer_formulas": false}`.

**Can Marmir evaluate formulas?** No. It writes them for the spreadsheet application. If
you need computed values in Python, compute them in Python and write the numbers (or
both: the value in one column, the formula in another).

## Types and formats

**A column came out as `string` although it has numbers.** A column mixing types
(numbers and a "Total" label, say) is summarised as `string`, but every cell keeps its
own type, so numbers are still written as numbers. Check with `doc.grid.grid_data`.

**Dates appear as numbers in Excel.** That happens when a date is written without a date
format. Marmir always sets one; if you set `number_formats` for a date column, make sure
it is a date format (`"yyyy-mm-dd"`), not a number format.

**My date format shows in Excel but not in the Markdown preview.** Excel-style formats
(`"mmm yyyy"`) only affect spreadsheet output. strftime patterns (`"%b %Y"`) apply to
both. See [styling](styling.md#number-formats).

**Time zones disappeared.** Excel has no time zones. Aware datetimes are written as
their wall-clock time (tzinfo dropped). Convert to the zone you want first:
`ts.astimezone(ZoneInfo("Europe/London"))`.

**"... is not a valid integer" warnings.** A value could not be converted to the type
you gave in `column_types`. Marmir writes it as its inferred type and logs a warning;
pass `ignore_data_mismatch=False` to raise `DataMismatchError` instead.

**`UnsupportedFormatCodeException`.** The strftime code has no Excel equivalent
(`%j` day of year, `%U`/`%W` week numbers, `%z`/`%Z` time zones), or a 12-hour `%I`
is used without `%p` (Excel only shows 12-hour times with AM/PM). Format the value as
text yourself or use an Excel format string.

## Installation

**`MissingDependencyError: ... requires the 'xlwt' package`.** Optional features live in
extras: `pip install "marmir[xls]"` (legacy .xls), `[images]` (Pillow), `[pandas]`,
`[django]`, `[gsheets]`, `[mcp]`, `[server]`, or `[all]`.

**Is the import name `marmir` or `mm`?** Install `marmir`, import `mm`.

## Size and speed

Rough numbers on a laptop: building a 100,000-row x 5-column document takes about 1.5 s;
writing it as XLSX takes about 15 s (openpyxl serialisation dominates); CSV takes under
a second. For multi-million-row exports prefer CSV, or split data across sheets. XLSX
holds at most 1,048,576 rows per sheet; legacy XLS holds 65,536.

`adjust_all_col_width=False` and `row_styles=()` make XLSX writing a little faster.

## AI integrations

**The model keeps sending invalid specs.** Return the tool result to the model
unchanged -- the `errors` list tells it what to fix -- and include `mm.ai.SYSTEM_PROMPT`
in your instructions. Strong models usually fix everything on the next call.

**Where did the file go?** `SpreadsheetTools(output_dir=...)`, `--output-dir` or
`MARMIR_OUTPUT_DIR` (default `./marmir_output`, relative to the process's working
directory). The tool result includes the absolute `path`.

**`read_spreadsheet` says "not allowed".** Reading is limited to the output directory
and `read_dirs` / `--read-dir` / `MARMIR_READ_DIRS` (default: the working directory).
Add the folder you want the model to read.

**The MCP server does not show up in Claude Desktop.** Check that `uvx` (or
`marmir-mcp`) is on the PATH Claude Desktop sees -- use an absolute path in `command` if
in doubt -- then fully restart the app and check its MCP logs. Run
`uvx --from "marmir[mcp]" marmir-mcp` in a terminal: it should start and wait silently
for input.

**Can a model embed images?** Image cells reference local files, so they are disabled in
the tool layer by default. Enable with `allow_images=True` / `--allow-images` when you
trust the caller.

## Migrating

**My 0.x code produces `.xlsx` now.** `writestr()` defaults to XLSX in 2.0. Use
`writestr("xls")` or `write("file.xls")`. All changes are listed in the
[migration guide](migration.md).
