"""Spreadsheet tools for LLM agents (OpenAI, Anthropic, MCP, HTTP).

One ``SpreadsheetTools`` object holds the tool definitions and runs the calls, so every
integration behaves the same way::

    from mm.ai import SpreadsheetTools

    tools = SpreadsheetTools(output_dir="out")
    tools.anthropic_tools()            # -> tools=[...] for client.messages.create
    tools.openai_tools()               # -> tools=[...] for client.responses.create
    result = tools.call("create_spreadsheet", {"sheets": [...]})

Tool results are JSON-serialisable dicts. Invalid input never raises: the result is
``{"ok": false, "errors": [...]}`` with path-prefixed messages the model can fix.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import re
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..composers import available_formats, get_composer_class, normalise_format
from ..errors import MarmirError, SpecValidationError
from ..spec import WORKBOOK_SPEC_SCHEMA, from_spec, normalize_spec, validate_spec

log = logging.getLogger(__name__)

__all__ = [
    "CREATE_TOOL",
    "PREVIEW_TOOL",
    "READ_TOOL",
    "SpreadsheetTools",
    "ToolDefinition",
]

CREATE_TOOL = "create_spreadsheet"
PREVIEW_TOOL = "preview_spreadsheet"
READ_TOOL = "read_spreadsheet"

WRITE_FORMATS = ["xlsx", "xls", "csv", "tsv", "json", "markdown", "html", "text"]
READ_FORMATS = (".xlsx", ".xlsm", ".xls", ".csv", ".tsv", ".json")

_SPEC_PROPS = WORKBOOK_SPEC_SCHEMA["properties"]

_CREATE_DESCRIPTION = """\
Create a spreadsheet file (Excel .xlsx by default) from structured data and return its path.

Describe the workbook as sheets of columns and rows. Prefer array rows in column order.
- Column types: string, integer, number, decimal, percent (0.25 shows 25%), currency, \
boolean, date/datetime/time (ISO 8601 strings like "2024-09-30"), duration, url, formula.
- Formulas: {"formula": "SUM(B2:B10)"} or a string starting with "=". Use A1 references; \
row 1 is the header row, so the first data row is row 2 and column A is the first column.
- Links: {"url": "https://...", "text": "label"}. Styling: {"value": ..., "style": \
"font-weight: bold; background-color: #FFF2CC"}.
- Options per sheet: autofilter, freeze_row, freeze_col, header_style, row_styles.
If the input is invalid, the result lists every problem with its location; fix them and \
call again. The result includes a Markdown preview of the first rows."""

_PREVIEW_DESCRIPTION = """\
Validate a workbook spec and render it as Markdown without writing a file. Takes the same \
input as create_spreadsheet. Use it to check formulas, types and layout before creating \
the file."""

_READ_DESCRIPTION = """\
Read a spreadsheet file (.xlsx, .xls, .csv, .tsv or .json) and return its contents as \
Markdown tables (or JSON). Formulas are returned as text such as "=SUM(B2:B5)". Use \
max_rows to limit output for large files."""


@dataclass(frozen=True)
class ToolDefinition:
    """Provider-neutral tool definition."""

    name: str
    description: str
    input_schema: dict[str, Any]

    def anthropic(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }

    def openai_responses(self) -> dict[str, Any]:
        return {
            "type": "function",
            "name": self.name,
            "description": self.description,
            "parameters": self.input_schema,
            "strict": False,
        }

    def openai_chat(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.input_schema,
            },
        }


def _create_schema(include_filename: bool = True) -> dict[str, Any]:
    properties: dict[str, Any] = {
        "title": _SPEC_PROPS["title"],
        "sheets": _SPEC_PROPS["sheets"],
        "options": _SPEC_PROPS["options"],
        "format": {
            "type": "string",
            "enum": WRITE_FORMATS,
            "description": "Output format (default xlsx).",
        },
    }
    if include_filename:
        properties["filename"] = {
            "type": "string",
            "description": (
                "File name such as 'q3-sales.xlsx'. Generated from the title if omitted."
            ),
        }
    return {"type": "object", "properties": properties, "required": ["sheets"]}


_READ_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "path": {"type": "string", "description": "Path of the file to read."},
        "sheet": {"type": "string", "description": "Only read this sheet (name)."},
        "max_rows": {
            "type": "integer",
            "description": "Maximum data rows per sheet (default 50).",
            "minimum": 1,
        },
        "output": {
            "type": "string",
            "enum": ["markdown", "json"],
            "description": "markdown (default) or json.",
        },
    },
    "required": ["path"],
}


class SpreadsheetTools:
    """Tool definitions plus a safe executor.

    Args:
        output_dir: where created files go (created on demand). Tool callers can only
            choose a file *name*, never a directory.
        read_dirs: directories ``read_spreadsheet`` may read from. Defaults to
            ``output_dir`` and the current working directory. Pass ``[]`` to allow only
            ``output_dir``.
        allow_images: allow ``{"image": path}`` cells (off by default: a path from a model
            could point anywhere on disk).
        max_cells: reject specs larger than this.
        include_base64: add the file content as base64 to ``create_spreadsheet`` results
            (for hosted agents that cannot reach the local disk).
        enable_read: expose ``read_spreadsheet``.
    """

    def __init__(
        self,
        output_dir: str | os.PathLike[str] | None = None,
        read_dirs: list[str | os.PathLike[str]] | None = None,
        allow_images: bool = False,
        max_cells: int = 250_000,
        include_base64: bool = False,
        enable_read: bool = True,
        preview_rows: int = 5,
    ):
        self.output_dir = Path(output_dir or os.environ.get("MARMIR_OUTPUT_DIR", "marmir_output"))
        if read_dirs is None:
            env = os.environ.get("MARMIR_READ_DIRS")
            dirs: list[str | os.PathLike[str]] = [Path.cwd()]
            if env:
                dirs = list(env.split(os.pathsep))
        else:
            dirs = list(read_dirs)
        self.read_dirs = [Path(d).resolve() for d in dirs]
        self.allow_images = allow_images
        self.max_cells = max_cells
        self.include_base64 = include_base64
        self.enable_read = enable_read
        self.preview_rows = preview_rows

    # -- definitions -----------------------------------------------------------------
    def definitions(self) -> list[ToolDefinition]:
        tools = [
            ToolDefinition(CREATE_TOOL, _CREATE_DESCRIPTION, _create_schema()),
            ToolDefinition(
                PREVIEW_TOOL, _PREVIEW_DESCRIPTION, _create_schema(include_filename=False)
            ),
        ]
        if self.enable_read:
            tools.append(ToolDefinition(READ_TOOL, _READ_DESCRIPTION, _READ_SCHEMA))
        return tools

    def anthropic_tools(self) -> list[dict[str, Any]]:
        """Tool definitions for the Anthropic Messages API (``tools=[...]``)."""
        return [t.anthropic() for t in self.definitions()]

    def openai_tools(self, api: str = "responses") -> list[dict[str, Any]]:
        """Tool definitions for OpenAI: ``api="responses"`` (default) or ``"chat"``."""
        if api == "chat":
            return [t.openai_chat() for t in self.definitions()]
        if api == "responses":
            return [t.openai_responses() for t in self.definitions()]
        raise ValueError("api must be 'responses' or 'chat'")

    # -- dispatch ----------------------------------------------------------------------
    def call(self, name: str, arguments: Mapping[str, Any] | str | None) -> dict[str, Any]:
        """Run a tool by name. ``arguments`` may be a dict or a JSON string."""
        try:
            args = _parse_args(arguments)
        except ValueError as exc:
            return {"ok": False, "errors": [str(exc)]}
        handlers: dict[str, Callable[..., dict[str, Any]]] = {
            CREATE_TOOL: self.create_spreadsheet,
            PREVIEW_TOOL: self.preview_spreadsheet,
        }
        if self.enable_read:
            handlers[READ_TOOL] = self.read_spreadsheet
        handler = handlers.get(name)
        if handler is None:
            return {"ok": False, "errors": [f"unknown tool {name!r}; tools are {sorted(handlers)}"]}
        try:
            return handler(**args)
        except TypeError as exc:
            return {"ok": False, "errors": [f"bad arguments for {name}: {exc}"]}
        except (MarmirError, ValueError, KeyError, OSError) as exc:
            log.info("tool %s failed: %s", name, exc)
            return {"ok": False, "errors": [str(exc)]}

    def call_json(self, name: str, arguments: Mapping[str, Any] | str | None) -> str:
        """Like ``call`` but returns the JSON string to send back to the model."""
        return json.dumps(self.call(name, arguments), ensure_ascii=False, default=str)

    def handle_anthropic_tool_use(self, block: Any) -> dict[str, Any]:
        """Turn a ``tool_use`` content block into a ``tool_result`` block."""
        name, block_id, args = _get(block, "name"), _get(block, "id"), _get(block, "input")
        result = self.call(name, args)
        return {
            "type": "tool_result",
            "tool_use_id": block_id,
            "content": json.dumps(result, ensure_ascii=False, default=str),
            "is_error": not result.get("ok", False),
        }

    def handle_openai_tool_call(self, call: Any) -> dict[str, Any]:
        """Run an OpenAI tool call and return the item/message to append.

        Accepts a Responses API ``function_call`` item (returns a
        ``function_call_output`` item) or a Chat Completions ``tool_call`` (returns a
        ``{"role": "tool", ...}`` message).
        """
        function = _get(call, "function")
        if function is not None:  # chat completions
            output = self.call_json(_get(function, "name"), _get(function, "arguments"))
            return {"role": "tool", "tool_call_id": _get(call, "id"), "content": output}
        output = self.call_json(_get(call, "name"), _get(call, "arguments"))
        return {"type": "function_call_output", "call_id": _get(call, "call_id"), "output": output}

    # -- tools -------------------------------------------------------------------------
    def create_spreadsheet(
        self,
        sheets: Any = None,
        format: str = "xlsx",
        filename: str | None = None,
        title: str | None = None,
        options: Mapping[str, Any] | None = None,
        **extra: Any,
    ) -> dict[str, Any]:
        spec = self._spec(sheets, title, options, extra)
        if isinstance(spec, list):
            return {"ok": False, "errors": spec}
        fmt = normalise_format(format or "xlsx")
        document = from_spec(
            spec, allow_images=self.allow_images, max_cells=self.max_cells, validate=False
        )
        path = self._output_path(filename, title or spec.get("title"), fmt)
        data = document.to_bytes(fmt)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        result: dict[str, Any] = {
            "ok": True,
            "path": str(path),
            "filename": path.name,
            "format": fmt,
            "media_type": get_composer_class(fmt).media_type,
            "size_bytes": len(data),
            "sheets": _summary(document),
            "preview": document.to_markdown(max_rows=self.preview_rows),
        }
        if self.include_base64:
            result["content_base64"] = base64.b64encode(data).decode("ascii")
        return result

    def preview_spreadsheet(
        self,
        sheets: Any = None,
        format: str | None = None,
        title: str | None = None,
        options: Mapping[str, Any] | None = None,
        **extra: Any,
    ) -> dict[str, Any]:
        spec = self._spec(sheets, title, options, extra)
        if isinstance(spec, list):
            return {"ok": False, "errors": spec}
        document = from_spec(
            spec, allow_images=self.allow_images, max_cells=self.max_cells, validate=False
        )
        return {
            "ok": True,
            "sheets": _summary(document),
            "preview": document.to_markdown(max_rows=max(self.preview_rows, 20)),
        }

    def read_spreadsheet(
        self,
        path: str,
        sheet: str | None = None,
        max_rows: int | None = 50,
        output: str = "markdown",
    ) -> dict[str, Any]:
        from ..reader import read

        target = self._readable_path(path)
        sheets = read(target, sheet=sheet, max_rows=max_rows)
        result: dict[str, Any] = {
            "ok": True,
            "path": str(target),
            "sheets": [
                {"name": s.name, "columns": s.columns, "rows_returned": len(s.rows)} for s in sheets
            ],
        }
        if output == "json":
            result["data"] = [
                {
                    "name": s.name,
                    "columns": s.columns,
                    "rows": json.loads(json.dumps(s.rows, default=str)),
                }
                for s in sheets
            ]
        else:
            from ..document import Document

            parts = []
            for s in sheets:
                if not s.columns:
                    parts.append(f"## {s.name}\n\n_(empty sheet)_")
                    continue
                doc = Document(s.rows, order=s.columns, name=s.name, infer_formulas=False)
                parts.append(doc.to_markdown().strip())
            result["content"] = "\n\n".join(parts)
        return result

    # -- helpers -----------------------------------------------------------------------
    def _spec(
        self,
        sheets: Any,
        title: str | None,
        options: Mapping[str, Any] | None,
        extra: Mapping[str, Any],
    ) -> dict[str, Any] | list[str]:
        raw: dict[str, Any] = {
            k: v
            for k, v in extra.items()
            if k in ("author", "description", "rows", "columns", "name")
        }
        unknown = [k for k in extra if k not in raw]
        if sheets is not None:
            raw["sheets"] = sheets
        if title:
            raw["title"] = title
        if options:
            raw["options"] = dict(options)
        try:
            spec = normalize_spec(raw)
        except SpecValidationError as exc:
            return exc.errors
        errors = [f"$.{k}: unknown argument" for k in unknown]
        errors += validate_spec(spec, allow_images=self.allow_images, max_cells=self.max_cells)
        return errors if errors else spec

    def _output_path(self, filename: str | None, title: str | None, fmt: str) -> Path:
        ext = {"markdown": ".md", "text": ".txt"}.get(fmt, "." + fmt)
        if filename:
            stem = Path(Path(filename).name).stem  # never trust directories from a model
        else:
            stem = (title or "spreadsheet") + "-" + uuid.uuid4().hex[:8]
        stem = re.sub(r"[^A-Za-z0-9._ -]+", "", stem).strip(" .") or "spreadsheet"
        return (self.output_dir / (stem[:100] + ext)).resolve()

    def _readable_path(self, path: str) -> Path:
        candidate = Path(path).expanduser()
        if not candidate.is_absolute():
            local = (self.output_dir / candidate).resolve()
            candidate = local if local.exists() else candidate.resolve()
        else:
            candidate = candidate.resolve()
        allowed = [self.output_dir.resolve(), *self.read_dirs]
        if not any(candidate.is_relative_to(root) for root in allowed):
            raise PermissionError_(
                f"reading {path!r} is not allowed (outside the permitted directories)"
            )
        if candidate.suffix.lower() not in READ_FORMATS:
            raise ValueError(
                f"unsupported file type {candidate.suffix!r}; readable: {', '.join(READ_FORMATS)}"
            )
        if not candidate.is_file():
            raise FileNotFoundError(f"no such file: {path}")
        return candidate


class PermissionError_(MarmirError):
    """Raised when a tool tries to read outside the permitted directories."""


def _summary(document: Any) -> list[dict[str, Any]]:
    return [
        {
            "name": d.name,
            "rows": len(d.grid.grid_data),
            "columns": [str(t) for t in d.data_model.field_titles],
        }
        for d in document.sheets
    ]


def _parse_args(arguments: Mapping[str, Any] | str | None) -> dict[str, Any]:
    if arguments is None or arguments == "":
        return {}
    if isinstance(arguments, str):
        try:
            parsed = json.loads(arguments)
        except json.JSONDecodeError as exc:
            raise ValueError(f"arguments are not valid JSON: {exc.msg}") from exc
        arguments = parsed
    if not isinstance(arguments, Mapping):
        raise ValueError("arguments must be a JSON object")
    return dict(arguments)


def _get(obj: Any, key: str) -> Any:
    if isinstance(obj, Mapping):
        return obj.get(key)
    return getattr(obj, key, None)


def supported_formats() -> list[str]:
    return [f for f in available_formats() if f in WRITE_FORMATS]
