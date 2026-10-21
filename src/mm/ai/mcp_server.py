"""Model Context Protocol server exposing Marmir's spreadsheet tools.

Works with Claude Desktop, Claude Code, the OpenAI Agents SDK, the OpenAI Responses API
(remote MCP over streamable HTTP) and any other MCP client.

Run it::

    marmir-mcp                                   # stdio (Claude Desktop / Claude Code)
    marmir-mcp --transport streamable-http --port 8000   # http://127.0.0.1:8000/mcp

Environment variables: ``MARMIR_OUTPUT_DIR`` (where files are written) and
``MARMIR_READ_DIRS`` (``os.pathsep``-separated directories the read tool may open).
"""

from __future__ import annotations

import argparse
import json
from typing import Annotated, Any

from ..errors import MissingDependencyError

try:
    from pydantic import Field  # installed with the mcp extra
except ImportError as _exc:  # pragma: no cover
    raise MissingDependencyError("mcp", "mcp", "The MCP server") from _exc

from ..spec import WORKBOOK_SPEC_SCHEMA
from .tools import (
    _CREATE_DESCRIPTION,
    _PREVIEW_DESCRIPTION,
    _READ_DESCRIPTION,
    WRITE_FORMATS,
    SpreadsheetTools,
)

__all__ = ["build_server", "main"]

INSTRUCTIONS = (
    "Marmir creates and reads spreadsheets. To build a spreadsheet, call create_spreadsheet "
    "with sheets of columns and rows (see the resource marmir://schema/workbook for the full "
    "JSON schema). Use preview_spreadsheet to check a layout without writing a file, and "
    "read_spreadsheet to inspect existing .xlsx/.xls/.csv files."
)

_SHEETS_DESC = (
    'Sheets to create. Each sheet: {"name": str, "columns": [{"name": str, "type": '
    'str, "format"?: str}], "rows": [[cell, ...], ...], "options"?: {...}}. A cell is a '
    'string, number, boolean, null, {"formula": "SUM(B2:B5)"}, {"url": ..., "text": ...} '
    'or {"value": ..., "type"?: ..., "format"?: ..., "style"?: ...}.'
)

Sheets = Annotated[list[dict[str, Any]], Field(description=_SHEETS_DESC)]
Format = Annotated[str, Field(description=f"Output format: {', '.join(WRITE_FORMATS)}.")]


def _server_class() -> Any:
    try:
        from mcp.server.mcpserver import MCPServer

        return MCPServer
    except ImportError:
        pass
    try:
        from mcp.server.fastmcp import FastMCP  # type: ignore[attr-defined, unused-ignore]  # mcp 1.x

        return FastMCP
    except ImportError as exc:
        raise MissingDependencyError("mcp", "mcp", "The MCP server") from exc


def build_server(tools: SpreadsheetTools | None = None, name: str = "marmir") -> Any:
    """Create the MCP server object (``MCPServer``/``FastMCP``) with the tools registered."""
    toolkit = tools or SpreadsheetTools()
    server = _server_class()(name, instructions=INSTRUCTIONS)

    @server.tool(name="create_spreadsheet", description=_CREATE_DESCRIPTION)
    def create_spreadsheet(
        sheets: Sheets,
        format: Format = "xlsx",
        filename: Annotated[str | None, Field(description="File name, e.g. 'report.xlsx'.")] = None,
        title: Annotated[str | None, Field(description="Document title.")] = None,
        options: Annotated[
            dict[str, Any] | None, Field(description="Options for every sheet.")
        ] = None,
    ) -> dict[str, Any]:
        return toolkit.call(
            "create_spreadsheet",
            {
                "sheets": sheets,
                "format": format,
                "filename": filename,
                "title": title,
                "options": options,
            },
        )

    @server.tool(name="preview_spreadsheet", description=_PREVIEW_DESCRIPTION)
    def preview_spreadsheet(
        sheets: Sheets,
        title: Annotated[str | None, Field(description="Document title.")] = None,
        options: Annotated[
            dict[str, Any] | None, Field(description="Options for every sheet.")
        ] = None,
    ) -> dict[str, Any]:
        return toolkit.call(
            "preview_spreadsheet", {"sheets": sheets, "title": title, "options": options}
        )

    if toolkit.enable_read:

        @server.tool(name="read_spreadsheet", description=_READ_DESCRIPTION)
        def read_spreadsheet(
            path: Annotated[str, Field(description="Path of the file to read.")],
            sheet: Annotated[str | None, Field(description="Only this sheet (name).")] = None,
            max_rows: Annotated[int, Field(description="Max data rows per sheet.", ge=1)] = 50,
            output: Annotated[str, Field(description="'markdown' or 'json'.")] = "markdown",
        ) -> dict[str, Any]:
            return toolkit.call(
                "read_spreadsheet",
                {"path": path, "sheet": sheet, "max_rows": max_rows, "output": output},
            )

    @server.resource(
        "marmir://schema/workbook",
        name="workbook-spec-schema",
        description="JSON Schema for Marmir workbook specs (the create_spreadsheet input).",
        mime_type="application/json",
    )
    def workbook_schema() -> str:
        return json.dumps(WORKBOOK_SPEC_SCHEMA, indent=2)

    server.marmir_tools = toolkit
    return server


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="marmir-mcp", description="Marmir MCP server")
    parser.add_argument("--transport", choices=["stdio", "streamable-http", "sse"], default="stdio")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--output-dir", default=None, help="where created files are written")
    parser.add_argument(
        "--read-dir",
        action="append",
        default=None,
        help="directory the read tool may open (repeatable)",
    )
    parser.add_argument(
        "--allow-images", action="store_true", help="allow image cells (local file paths)"
    )
    parser.add_argument("--no-read", action="store_true", help="disable the read_spreadsheet tool")
    args = parser.parse_args(argv)

    toolkit = SpreadsheetTools(
        output_dir=args.output_dir,
        read_dirs=args.read_dir,
        allow_images=args.allow_images,
        enable_read=not args.no_read,
    )
    server = build_server(toolkit)
    if args.transport == "stdio":
        server.run("stdio")
        return
    try:
        server.run(args.transport, host=args.host, port=args.port)
    except TypeError:  # mcp 1.x takes host/port from settings
        server.settings.host = args.host
        server.settings.port = args.port
        server.run(args.transport)


if __name__ == "__main__":  # pragma: no cover
    main()
