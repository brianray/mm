# Changelog

## 2.0.0 -- 2026-10-21

A ground-up rewrite for modern Python and GenAI workflows. See
[docs/migration.md](docs/migration.md) for upgrade notes.

### Added
- Python 3.10-3.13 support, type hints, `py.typed`, `pyproject.toml` packaging.
- XLSX output (default) via openpyxl, plus CSV, TSV, JSON, Markdown, HTML and text
  composers; composer registry with `register_composer()`.
- Reading: `mm.read()`, `mm.read_document()`, `Document.from_file()` for
  XLSX/XLS/CSV/TSV/JSON.
- The JSON workbook spec: `from_spec()`, `validate_spec()` with path-prefixed errors,
  `WORKBOOK_SPEC_SCHEMA`, `Document.to_spec()`/`to_json()` round-trip.
- `mm.ai`: `SpreadsheetTools` with OpenAI (Responses and Chat Completions) and
  Anthropic tool definitions and handlers; `SYSTEM_PROMPT`.
- MCP server `marmir-mcp` (stdio, streamable HTTP, SSE).
- HTTP API (`marmir serve`) with OpenAPI for custom GPT Actions.
- `marmir` CLI: convert, read, validate, schema, tools, mcp, serve, openapi.
- Claude Skill (`skills/marmir-spreadsheets`) and Claude Code plugin/marketplace
  manifests.
- New cell types: `Percent`, `Currency`, `Duration`, `Cell(style=, format=)`;
  per-cell/column styles and number formats; autofilter; document properties.
- Input from pandas DataFrames, DB-API cursors, dataclasses, Pydantic models,
  named tuples and column dicts.
- Google Sheets output via gspread (`write_gsheet`).
- Full pytest suite and CI.
- Documentation: a seven-chapter tutorial, a cookbook and an FAQ; every tutorial and
  cookbook code block is executed by the test suite and its printed output checked.

### Changed
- `writestr()` defaults to XLSX; `write()` picks the format from the extension.
- Type inference scans every row and skips blanks; rows with new keys add columns
  (`strict_columns=True` restores the old error).
- Missing values are blank cells; refreshed default styles.
- XLSX writing reuses openpyxl style arrays per distinct style (about 2.5x faster on
  large sheets).
- Django contrib supports current Django, `order`, `column_types`, foreign keys and
  `verbose_names`.

### Removed / deprecated
- Vendored xlwt 0.7.2 (now the optional `xlwt` dependency for `.xls`).
- `write_gdata()` is deprecated (Google retired ClientLogin) and forwards to
  `write_gsheet()`.
- The pickled font-metrics file (now JSON).

## 0.1.3 -- 2013-04-21
- Child (multi) spreadsheet support; dict-like objects; explicit column types.

## 0.1.1 -- 2013-01-25
- Bug fixes; `order` argument; column width fixes.

## 0.1 -- 2013-01-20
- Initial release.
