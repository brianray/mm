from __future__ import annotations

import asyncio
import json

import pytest

pytest.importorskip("mcp")

from mm.ai.mcp_server import build_server, main
from mm.ai.tools import SpreadsheetTools


def _run(coro):
    return asyncio.run(coro)


def _payload(result):
    if isinstance(result, tuple):  # mcp 1.x returns (content, structured)
        result = result[0]
    content = getattr(result, "content", result)
    return json.loads(content[0].text)


def test_tools_and_resource(tmp_path):
    server = build_server(SpreadsheetTools(output_dir=tmp_path, read_dirs=[tmp_path]))
    tools = _run(server.list_tools())
    assert [t.name for t in tools] == [
        "create_spreadsheet",
        "preview_spreadsheet",
        "read_spreadsheet",
    ]
    schema = getattr(tools[0], "input_schema", None) or tools[0].inputSchema
    assert "sheets" in schema["properties"]
    resources = _run(server.list_resources())
    assert str(resources[0].uri) == "marmir://schema/workbook"


def test_create_and_read_via_mcp(tmp_path):
    server = build_server(SpreadsheetTools(output_dir=tmp_path, read_dirs=[tmp_path]))
    created = _payload(
        _run(
            server.call_tool(
                "create_spreadsheet",
                {"sheets": [{"columns": ["a"], "rows": [[1], [2]]}], "filename": "m.xlsx"},
            )
        )
    )
    assert created["ok"] and created["filename"] == "m.xlsx"
    read = _payload(_run(server.call_tool("read_spreadsheet", {"path": "m.xlsx"})))
    assert "| 2 |" in read["content"]
    preview = _payload(
        _run(server.call_tool("preview_spreadsheet", {"sheets": [{"rows": [{"x": 1}]}]}))
    )
    assert preview["ok"]


def test_read_tool_can_be_disabled(tmp_path):
    server = build_server(SpreadsheetTools(output_dir=tmp_path, enable_read=False))
    assert [t.name for t in _run(server.list_tools())] == [
        "create_spreadsheet",
        "preview_spreadsheet",
    ]


def test_main_runs_requested_transport(monkeypatch, tmp_path):
    calls = []

    class FakeServer:
        def run(self, transport, **kwargs):
            calls.append((transport, kwargs))

    monkeypatch.setattr("mm.ai.mcp_server.build_server", lambda toolkit: FakeServer())
    main(["--output-dir", str(tmp_path)])
    main(["--transport", "streamable-http", "--port", "9999", "--no-read"])
    assert calls == [("stdio", {}), ("streamable-http", {"host": "127.0.0.1", "port": 9999})]
