"""GenAI integrations: tool definitions for OpenAI and Anthropic, an MCP server and helpers.

Quick use with module-level defaults (files go to ``./marmir_output``)::

    from mm import ai

    ai.anthropic_tools()                 # tools=[...] for Anthropic's Messages API
    ai.openai_tools()                    # tools=[...] for OpenAI's Responses API
    ai.handle_tool_call("create_spreadsheet", {"sheets": [...]})

For control over directories and limits, create a ``SpreadsheetTools`` instance.
"""

from __future__ import annotations

from typing import Any

from ..spec import WORKBOOK_SPEC_SCHEMA
from .tools import CREATE_TOOL, PREVIEW_TOOL, READ_TOOL, SpreadsheetTools, ToolDefinition

__all__ = [
    "CREATE_TOOL",
    "PREVIEW_TOOL",
    "READ_TOOL",
    "SYSTEM_PROMPT",
    "WORKBOOK_SPEC_SCHEMA",
    "SpreadsheetTools",
    "ToolDefinition",
    "anthropic_tools",
    "handle_tool_call",
    "openai_tools",
]

#: A short system-prompt snippet that improves spreadsheet quality from any model.
SYSTEM_PROMPT = """\
When the user wants tabular output (a spreadsheet, table, tracker, budget, report or \
export), call create_spreadsheet instead of writing a table in chat.
- Give every column a type; keep numbers as numbers (no "$" or "%" inside values): use \
type "currency" or "percent" (0.15 means 15%).
- Use formulas for totals and derived values ({"formula": "SUM(B2:B9)"}) so the sheet \
stays live. Row 1 is the header, data starts at row 2.
- Dates are ISO strings ("2024-09-30").
- Bold total rows with {"value": "Total", "style": "font-weight: bold"}.
After creating the file, tell the user its name and summarise what is in it."""

_default: SpreadsheetTools | None = None


def _tools() -> SpreadsheetTools:
    global _default
    if _default is None:
        _default = SpreadsheetTools()
    return _default


def anthropic_tools() -> list[dict[str, Any]]:
    """Tool definitions for ``anthropic.Anthropic().messages.create(tools=...)``."""
    return _tools().anthropic_tools()


def openai_tools(api: str = "responses") -> list[dict[str, Any]]:
    """Tool definitions for OpenAI (``api="responses"`` or ``"chat"``)."""
    return _tools().openai_tools(api)


def handle_tool_call(name: str, arguments: Any) -> dict[str, Any]:
    """Run a tool call with the default toolkit; returns a JSON-serialisable dict."""
    return _tools().call(name, arguments)
