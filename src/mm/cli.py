"""``marmir`` command-line interface.

Examples::

    marmir convert data.json report.xlsx          # records, a workbook spec, CSV, XLSX ...
    marmir convert sales.csv sales.md
    cat spec.json | marmir convert - out.xlsx
    marmir read report.xlsx --max-rows 20
    marmir validate spec.json
    marmir schema > workbook.schema.json
    marmir tools --provider anthropic
    marmir mcp                                    # MCP server on stdio
    marmir serve --port 8080                      # HTTP API (OpenAPI at /openapi.json)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from . import __version__
from .composers import format_for_path
from .errors import MarmirError, SpecValidationError

__all__ = ["main"]


def _load_input(source: str, fmt: str | None) -> Any:
    from .document import Document
    from .reader import read_document
    from .spec import from_spec

    if source == "-":
        data = sys.stdin.buffer.read()
        if fmt in (None, "json") and data.lstrip()[:1] in (b"{", b"["):
            return from_spec(json.loads(data))
        return read_document(data, format=fmt)
    path = Path(source)
    if (fmt or format_for_path(path)) == "json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict) and ("sheets" in payload or "rows" in payload):
            return from_spec(payload, base_dir=path.parent)
        return Document(payload)
    return read_document(path, format=fmt)


def cmd_convert(args: argparse.Namespace) -> int:
    doc = _load_input(args.input, args.input_format)
    for option in args.option or []:
        key, _, value = option.partition("=")
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            parsed = value
        for sheet in doc.sheets:
            sheet.config.set_dict({key: parsed})
    if args.output == "-":
        out = doc.writestr(args.format or "markdown")
        if isinstance(out, bytes):
            sys.stdout.buffer.write(out)
        else:
            sys.stdout.write(out)
        return 0
    doc.write(args.output, format=args.format)
    print(f"wrote {args.output}", file=sys.stderr)
    return 0


def cmd_read(args: argparse.Namespace) -> int:
    from .document import Document
    from .reader import read

    sheets = read(args.path, format=args.format, sheet=args.sheet, max_rows=args.max_rows)
    if args.output == "json":
        payload = [{"name": s.name, "columns": s.columns, "rows": s.rows} for s in sheets]
        print(json.dumps(payload, indent=2, default=str))
        return 0
    parts = []
    for s in sheets:
        doc = Document(s.rows, order=s.columns, name=s.name, infer_formulas=False)
        parts.append(doc.writestr(args.output).strip())
    print("\n\n".join(parts))
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    from .spec import validate_spec

    raw = sys.stdin.read() if args.spec == "-" else Path(args.spec).read_text(encoding="utf-8")
    errors = validate_spec(raw)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("ok")
    return 0


def cmd_schema(args: argparse.Namespace) -> int:
    from .spec import WORKBOOK_SPEC_SCHEMA

    print(json.dumps(WORKBOOK_SPEC_SCHEMA, indent=2))
    return 0


def cmd_tools(args: argparse.Namespace) -> int:
    from .ai.tools import SpreadsheetTools

    tools = SpreadsheetTools(enable_read=not args.no_read)
    if args.provider == "anthropic":
        payload = tools.anthropic_tools()
    elif args.provider == "openai-chat":
        payload = tools.openai_tools("chat")
    else:
        payload = tools.openai_tools("responses")
    print(json.dumps(payload, indent=2))
    return 0


def cmd_mcp(argv: list[str]) -> int:
    from .ai.mcp_server import main as mcp_main

    mcp_main(argv)
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    from .server import main as serve_main

    serve_main(host=args.host, port=args.port)
    return 0


def cmd_openapi(args: argparse.Namespace) -> int:
    from .server import create_app

    print(json.dumps(create_app(public_url=args.url).openapi(), indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="marmir", description="Marmir: spreadsheets from data")
    parser.add_argument("--version", action="version", version=f"marmir {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("convert", help="convert data/spec/spreadsheet files between formats")
    p.add_argument(
        "input", help="input file (.json records or spec, .csv, .tsv, .xlsx, .xls) or - for stdin"
    )
    p.add_argument("output", help="output file (format from extension) or - for stdout")
    p.add_argument(
        "-f", "--format", help="output format (xlsx, xls, csv, tsv, json, markdown, html, text)"
    )
    p.add_argument("--input-format", help="input format when it cannot be guessed")
    p.add_argument(
        "-o",
        "--option",
        action="append",
        metavar="KEY=VALUE",
        help="sheet option, e.g. autofilter=true (repeatable)",
    )
    p.set_defaults(func=cmd_convert)

    p = sub.add_parser("read", help="print a spreadsheet as Markdown, text or JSON")
    p.add_argument("path")
    p.add_argument("--format", help="input format when it cannot be guessed")
    p.add_argument("--sheet", help="only this sheet")
    p.add_argument("--max-rows", type=int, default=None)
    p.add_argument("--output", choices=["markdown", "text", "csv", "json"], default="markdown")
    p.set_defaults(func=cmd_read)

    p = sub.add_parser("validate", help="validate a workbook spec (JSON)")
    p.add_argument("spec", help="spec file or - for stdin")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("schema", help="print the workbook spec JSON Schema")
    p.set_defaults(func=cmd_schema)

    p = sub.add_parser("tools", help="print LLM tool definitions")
    p.add_argument("--provider", choices=["openai", "openai-chat", "anthropic"], default="openai")
    p.add_argument("--no-read", action="store_true", help="omit read_spreadsheet")
    p.set_defaults(func=cmd_tools)

    # "marmir mcp ..." is dispatched in main() so every argument reaches marmir-mcp
    sub.add_parser(
        "mcp", help="run the MCP server (arguments are passed to marmir-mcp)", add_help=False
    )

    p = sub.add_parser("serve", help="run the HTTP API")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8080)
    p.set_defaults(func=cmd_serve)

    p = sub.add_parser("openapi", help="print the HTTP API's OpenAPI document")
    p.add_argument("--url", default=None, help="public server URL to put in 'servers'")
    p.set_defaults(func=cmd_openapi)
    return parser


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else list(argv)
    if argv[:1] == ["mcp"]:
        return cmd_mcp(argv[1:])
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args))
    except SpecValidationError as exc:
        for error in exc.errors:
            print(f"error: {error}", file=sys.stderr)
        return 1
    except (MarmirError, OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
