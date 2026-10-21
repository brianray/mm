from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from mm.ai.tools import SpreadsheetTools
from mm.server import create_app

SPEC = {
    "title": "T",
    "sheets": [{"columns": ["a", "b"], "rows": [[1, 2], [3, {"formula": "SUM(B2:B2)"}]]}],
}
AUTH = {"Authorization": "Bearer secret"}


@pytest.fixture
def client(tmp_path):
    app = create_app(
        SpreadsheetTools(output_dir=tmp_path, read_dirs=[]),
        api_key="secret",
        public_url="https://api.example.com/",
    )
    return TestClient(app)


def test_auth_required(client):
    assert client.post("/v1/spreadsheets", json=SPEC).status_code == 401
    assert (
        client.post(
            "/v1/spreadsheets", json=SPEC, headers={"Authorization": "Bearer wrong"}
        ).status_code
        == 401
    )
    assert client.get("/health").json()["status"] == "ok"


def test_create_and_download(client):
    response = client.post("/v1/spreadsheets", json=SPEC, headers=AUTH)
    assert response.status_code == 200, response.text
    body = response.json()
    assert "path" not in body
    assert body["download_url"] == f"https://api.example.com/v1/spreadsheets/{body['file_id']}"
    download = client.get(f"/v1/spreadsheets/{body['file_id']}", headers=AUTH)
    assert download.status_code == 200 and download.content[:2] == b"PK"
    assert client.get("/v1/spreadsheets/..%2Fsecret", headers=AUTH).status_code == 404
    assert client.get("/v1/spreadsheets/missing.xlsx", headers=AUTH).status_code == 404
    assert client.get("/v1/spreadsheets/.hidden", headers=AUTH).status_code == 404


def test_validation_errors(client):
    response = client.post("/v1/spreadsheets", json={"sheets": [{"rows": [[1]]}]}, headers=AUTH)
    assert response.status_code == 422
    assert "need 'columns'" in response.json()["errors"][0]
    assert (
        client.post("/v1/spreadsheets/render", json={"sheets": []}, headers=AUTH).status_code == 422
    )
    assert (
        client.post("/v1/spreadsheets/preview", json={"sheets": []}, headers=AUTH).status_code
        == 422
    )


def test_preview_render_read(client):
    preview = client.post("/v1/spreadsheets/preview", json=SPEC, headers=AUTH)
    assert "=SUM(B2:B2)" in preview.json()["preview"]
    rendered = client.post("/v1/spreadsheets/render", json={**SPEC, "format": "csv"}, headers=AUTH)
    assert rendered.status_code == 200
    assert rendered.headers["content-type"].startswith("text/csv")
    assert rendered.text.startswith("a,b")
    xlsx = client.post("/v1/spreadsheets/render", json=SPEC, headers=AUTH).content
    read = client.post(
        "/v1/spreadsheets/read?max_rows=1", files={"file": ("x.xlsx", xlsx)}, headers=AUTH
    )
    assert read.status_code == 200, read.text
    assert "| 1 | 2 |" in read.json()["content"]
    as_json = client.post(
        "/v1/spreadsheets/read?output=json", files={"file": ("x.csv", b"a\n1\n")}, headers=AUTH
    )
    assert as_json.json()["data"][0]["rows"] == [[1]]


def test_upload_limit(client, monkeypatch):
    monkeypatch.setattr("mm.server._MAX_UPLOAD", 10)
    response = client.post(
        "/v1/spreadsheets/read", files={"file": ("x.csv", b"a" * 100)}, headers=AUTH
    )
    assert response.status_code == 413


def test_openapi_and_schema(client):
    spec = client.get("/openapi.json").json()
    ops = {op["operationId"] for path in spec["paths"].values() for op in path.values()}
    assert {
        "createSpreadsheet",
        "downloadSpreadsheet",
        "readSpreadsheet",
        "previewSpreadsheet",
        "renderSpreadsheet",
    } <= ops
    assert spec["servers"] == [{"url": "https://api.example.com"}]
    assert client.get("/v1/schema").json()["title"] == "Marmir workbook spec"
    assert "xlsx" in client.get("/v1/formats").json()["formats"]


def test_no_auth_when_key_unset(tmp_path, monkeypatch):
    monkeypatch.delenv("MARMIR_API_KEY", raising=False)
    client = TestClient(create_app(SpreadsheetTools(output_dir=tmp_path)))
    assert client.post("/v1/spreadsheets/preview", json=SPEC).status_code == 200
    assert (
        client.post("/v1/spreadsheets", json=SPEC)
        .json()["download_url"]
        .startswith("http://testserver/")
    )
