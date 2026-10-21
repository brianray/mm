from __future__ import annotations

import base64
import json
from types import SimpleNamespace

import pytest

from mm import ai
from mm.ai.tools import SpreadsheetTools

SPEC = {
    "title": "Budget",
    "sheets": [
        {
            "name": "Budget",
            "columns": [{"name": "Item", "type": "string"}, {"name": "Cost", "type": "currency"}],
            "rows": [
                ["Laptops", 4200],
                ["Software", 1300],
                [{"value": "Total", "style": "font-weight: bold"}, {"formula": "SUM(B2:B3)"}],
            ],
        }
    ],
}


@pytest.fixture
def tools(tmp_path):
    return SpreadsheetTools(output_dir=tmp_path / "out", read_dirs=[tmp_path])


def test_definitions_for_each_provider(tools):
    names = ["create_spreadsheet", "preview_spreadsheet", "read_spreadsheet"]
    anthropic = tools.anthropic_tools()
    assert [t["name"] for t in anthropic] == names
    assert anthropic[0]["input_schema"]["required"] == ["sheets"]
    responses = tools.openai_tools()
    assert responses[0]["type"] == "function" and responses[0]["parameters"]["type"] == "object"
    assert responses[0]["strict"] is False
    chat = tools.openai_tools("chat")
    assert chat[2]["function"]["name"] == "read_spreadsheet"
    with pytest.raises(ValueError):
        tools.openai_tools("other")
    assert "filename" not in tools.anthropic_tools()[1]["input_schema"]["properties"]
    json.dumps([anthropic, responses, chat])
    assert [t["name"] for t in SpreadsheetTools(enable_read=False).anthropic_tools()] == names[:2]


def test_create_xlsx(tools):
    result = tools.call("create_spreadsheet", SPEC)
    assert result["ok"], result
    assert result["filename"].startswith("Budget-") and result["filename"].endswith(".xlsx")
    assert result["sheets"] == [{"name": "Budget", "rows": 3, "columns": ["Item", "Cost"]}]
    assert "| Laptops | $4,200.00 |" in result["preview"]
    assert (tools.output_dir / result["filename"]).read_bytes()[:2] == b"PK"


def test_create_other_formats_and_filename_sanitising(tools):
    result = tools.call(
        "create_spreadsheet", {**SPEC, "format": "csv", "filename": "../../etc/evil name.txt"}
    )
    assert result["ok"]
    assert result["filename"] == "evil name.csv"
    assert result["path"].startswith(str(tools.output_dir.resolve()))
    md = tools.call("create_spreadsheet", json.dumps({**SPEC, "format": "md", "filename": "r"}))
    assert md["filename"] == "r.md" and md["media_type"].startswith("text/markdown")
    assert tools.call("create_spreadsheet", {**SPEC, "format": "pdf"})["ok"] is False


def test_create_base64(tmp_path):
    result = SpreadsheetTools(output_dir=tmp_path, include_base64=True).call(
        "create_spreadsheet", SPEC
    )
    assert base64.b64decode(result["content_base64"])[:2] == b"PK"


def test_errors_are_returned_not_raised(tools):
    bad = {"sheets": [{"columns": ["a"], "rows": [[1, 2]]}], "bogus": 1}
    result = tools.call("create_spreadsheet", bad)
    assert result["ok"] is False
    assert "$.bogus: unknown argument" in result["errors"]
    assert any("has 2 cells" in e for e in result["errors"])
    assert tools.call("create_spreadsheet", "{not json")["ok"] is False
    assert tools.call("create_spreadsheet", "[1]")["ok"] is False
    assert tools.call("nope", {})["errors"][0].startswith("unknown tool")
    assert tools.call("read_spreadsheet", {})["ok"] is False  # missing path
    image = {"sheets": [{"columns": ["p"], "rows": [[{"image": "/etc/hosts"}]]}]}
    assert "images are not allowed" in tools.call("create_spreadsheet", image)["errors"][0]
    huge = {"sheets": [{"columns": ["a"], "rows": [[1]] * 11}]}
    assert SpreadsheetTools(max_cells=10).call("preview_spreadsheet", huge)["ok"] is False


def test_preview(tools):
    result = tools.call("preview_spreadsheet", {"sheets": SPEC["sheets"]})
    assert result["ok"] and "=SUM(B2:B3)" in result["preview"]
    assert not any(tools.output_dir.glob("*")) if tools.output_dir.exists() else True


def test_read_tool_and_sandbox(tools, tmp_path):
    created = tools.call("create_spreadsheet", {**SPEC, "filename": "b.xlsx"})
    read = tools.call("read_spreadsheet", {"path": "b.xlsx"})
    assert read["ok"], read
    assert "| Laptops | 4200 |" in read["content"]
    assert "=SUM(B2:B3)" in read["content"]
    as_json = tools.call(
        "read_spreadsheet", {"path": created["path"], "output": "json", "max_rows": 1}
    )
    assert as_json["data"][0]["rows"] == [["Laptops", 4200]]
    outside = tools.call("read_spreadsheet", {"path": "/etc/hosts"})
    assert "not allowed" in outside["errors"][0]
    (tmp_path / "x.exe").write_text("x")
    assert (
        "unsupported file type"
        in tools.call("read_spreadsheet", {"path": str(tmp_path / "x.exe")})["errors"][0]
    )
    assert (
        "no such file"
        in tools.call("read_spreadsheet", {"path": str(tmp_path / "none.csv")})["errors"][0]
    )
    (tmp_path / "empty.csv").write_text("")
    assert (
        "empty sheet"
        in tools.call("read_spreadsheet", {"path": str(tmp_path / "empty.csv")})["content"]
    )


def test_provider_glue(tools):
    block = SimpleNamespace(
        type="tool_use", id="toolu_1", name="preview_spreadsheet", input={"sheets": SPEC["sheets"]}
    )
    result = tools.handle_anthropic_tool_use(block)
    assert result["type"] == "tool_result" and result["tool_use_id"] == "toolu_1"
    assert result["is_error"] is False
    bad = tools.handle_anthropic_tool_use({"id": "t2", "name": "preview_spreadsheet", "input": {}})
    assert bad["is_error"] is True

    responses_call = SimpleNamespace(
        type="function_call",
        call_id="call_1",
        name="preview_spreadsheet",
        arguments=json.dumps({"sheets": SPEC["sheets"]}),
    )
    out = tools.handle_openai_tool_call(responses_call)
    assert out["type"] == "function_call_output" and out["call_id"] == "call_1"
    assert json.loads(out["output"])["ok"] is True

    chat_call = {
        "id": "c1",
        "type": "function",
        "function": {"name": "preview_spreadsheet", "arguments": json.dumps(SPEC)},
    }
    msg = tools.handle_openai_tool_call(chat_call)
    assert msg["role"] == "tool" and msg["tool_call_id"] == "c1"


def test_module_level_helpers(chdir_tmp):
    assert ai.anthropic_tools()[0]["name"] == "create_spreadsheet"
    assert ai.openai_tools("chat")[0]["function"]["name"] == "create_spreadsheet"
    result = ai.handle_tool_call("create_spreadsheet", SPEC)
    assert result["ok"] and (chdir_tmp / "marmir_output").is_dir()
    assert "create_spreadsheet" in ai.SYSTEM_PROMPT


def test_env_configuration(tmp_path, monkeypatch):
    monkeypatch.setenv("MARMIR_OUTPUT_DIR", str(tmp_path / "env-out"))
    monkeypatch.setenv("MARMIR_READ_DIRS", str(tmp_path))
    tools = SpreadsheetTools()
    assert tools.output_dir == tmp_path / "env-out"
    assert tools.read_dirs == [tmp_path.resolve()]
