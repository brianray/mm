from __future__ import annotations

import json

import pytest

from mm.cli import main

SPEC = {
    "sheets": [
        {"name": "S", "columns": ["a", "b"], "rows": [[1, 2], [3, {"formula": "SUM(B2:B2)"}]]}
    ]
}


@pytest.fixture
def spec_file(tmp_path):
    path = tmp_path / "spec.json"
    path.write_text(json.dumps(SPEC))
    return path


def test_convert_and_read(spec_file, tmp_path, capsys):
    out = tmp_path / "o.xlsx"
    assert (
        main(["convert", str(spec_file), str(out), "-o", "autofilter=true", "-o", "title=hello"])
        == 0
    )
    assert out.read_bytes()[:2] == b"PK"
    assert main(["read", str(out)]) == 0
    assert "| 3 | =SUM(B2:B2) |" in capsys.readouterr().out
    assert main(["read", str(out), "--output", "json", "--max-rows", "1"]) == 0
    assert json.loads(capsys.readouterr().out)[0]["rows"] == [[1, 2]]
    assert main(["read", str(out), "--output", "csv"]) == 0
    assert capsys.readouterr().out.startswith("a,b")


def test_convert_records_csv_and_stdout(tmp_path, capsys, monkeypatch):
    records = tmp_path / "r.json"
    records.write_text(json.dumps([{"x": 1}, {"x": 2}]))
    assert main(["convert", str(records), "-", "--format", "csv"]) == 0
    assert capsys.readouterr().out == "x\n1\n2\n"
    csv_path = tmp_path / "in.csv"
    csv_path.write_text("k,v\na,1\n")
    assert main(["convert", str(csv_path), "-"]) == 0
    assert "| k | v |" in capsys.readouterr().out

    class FakeStdin:
        def __init__(self, data):
            self.buffer = __import__("io").BytesIO(data)

        def read(self):
            return self.buffer.getvalue().decode()

    monkeypatch.setattr("sys.stdin", FakeStdin(json.dumps(SPEC).encode()))
    assert main(["convert", "-", "-", "-f", "text"]) == 0
    assert capsys.readouterr().out.startswith("S\n+")
    monkeypatch.setattr("sys.stdin", FakeStdin(b"a,b\n1,2\n"))
    assert main(["convert", "-", "-", "--input-format", "csv", "-f", "json"]) == 0
    assert json.loads(capsys.readouterr().out)["sheets"][0]["rows"] == [[1, 2]]


def test_convert_binary_stdout(spec_file, capsysbinary):
    assert main(["convert", str(spec_file), "-", "-f", "xlsx"]) == 0
    assert capsysbinary.readouterr().out[:2] == b"PK"


def test_validate(spec_file, tmp_path, capsys):
    assert main(["validate", str(spec_file)]) == 0
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"sheets": [{"rows": [[1]]}]}))
    assert main(["validate", str(bad)]) == 1
    assert "need 'columns'" in capsys.readouterr().err
    assert main(["convert", str(bad), str(tmp_path / "x.xlsx")]) == 1
    assert "error:" in capsys.readouterr().err
    assert main(["read", str(tmp_path / "missing.xlsx")]) == 1


def test_schema_tools_openapi(capsys):
    assert main(["schema"]) == 0
    assert json.loads(capsys.readouterr().out)["required"] == ["sheets"]
    assert main(["tools", "--provider", "anthropic"]) == 0
    assert json.loads(capsys.readouterr().out)[0]["input_schema"]
    assert main(["tools", "--provider", "openai-chat", "--no-read"]) == 0
    assert len(json.loads(capsys.readouterr().out)) == 2
    assert main(["tools"]) == 0
    assert json.loads(capsys.readouterr().out)[0]["type"] == "function"
    pytest.importorskip("fastapi")
    assert main(["openapi", "--url", "https://x.example"]) == 0
    assert json.loads(capsys.readouterr().out)["servers"][0]["url"] == "https://x.example"


def test_mcp_and_serve_dispatch(monkeypatch):
    pytest.importorskip("mcp")
    seen = {}
    monkeypatch.setattr("mm.ai.mcp_server.main", lambda argv: seen.setdefault("mcp", argv))
    assert main(["mcp", "--transport", "sse"]) == 0
    assert seen["mcp"] == ["--transport", "sse"]
    pytest.importorskip("fastapi")
    monkeypatch.setattr("mm.server.main", lambda host, port: seen.setdefault("serve", (host, port)))
    assert main(["serve", "--port", "1234"]) == 0
    assert seen["serve"] == ("127.0.0.1", 1234)
