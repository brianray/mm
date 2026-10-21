"""HTTP API (FastAPI) for ChatGPT custom GPT Actions, OpenAI/Anthropic agents and any client.

Run::

    pip install 'marmir[server]'
    MARMIR_API_KEY=secret marmir serve --port 8080

Endpoints (OpenAPI document at ``/openapi.json``; set ``MARMIR_PUBLIC_URL`` so links and
the OpenAPI ``servers`` entry use your public address):

* ``POST /v1/spreadsheets`` -- create a file from a workbook spec; returns a download URL
* ``GET  /v1/spreadsheets/{file_id}`` -- download a created file
* ``POST /v1/spreadsheets/preview`` -- validate a spec and return a Markdown preview
* ``POST /v1/spreadsheets/render`` -- create a file and return its bytes directly
* ``POST /v1/spreadsheets/read`` -- upload a file, get Markdown/JSON back
* ``GET  /v1/schema`` -- the workbook spec JSON Schema
"""

from __future__ import annotations

import os
import re
import secrets
import tempfile
from pathlib import Path
from typing import Any

from .errors import MissingDependencyError

try:
    from fastapi import Body, Depends, FastAPI, File, HTTPException, Query, Request, UploadFile
    from fastapi.responses import FileResponse, JSONResponse, Response
    from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
except ImportError as exc:  # pragma: no cover
    raise MissingDependencyError("fastapi", "server", "The HTTP server") from exc

from . import __version__
from .ai.tools import WRITE_FORMATS, SpreadsheetTools
from .composers import format_for_path, get_composer_class
from .spec import WORKBOOK_SPEC_SCHEMA

__all__ = ["create_app"]

_FILE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._ -]{0,120}$")
_MAX_UPLOAD = 20 * 1024 * 1024

_SPEC_EXAMPLE = {
    "title": "Team budget",
    "format": "xlsx",
    "sheets": [
        {
            "name": "Budget",
            "columns": [
                {"name": "Item", "type": "string"},
                {"name": "Cost", "type": "currency"},
            ],
            "rows": [
                ["Laptops", 4200],
                ["Software", 1300],
                [{"value": "Total", "style": "font-weight: bold"}, {"formula": "SUM(B2:B3)"}],
            ],
        }
    ],
}


def create_app(
    tools: SpreadsheetTools | None = None,
    api_key: str | None = None,
    public_url: str | None = None,
) -> FastAPI:
    """Build the FastAPI app. ``api_key`` (or ``MARMIR_API_KEY``) enables bearer auth."""
    api_key = api_key if api_key is not None else os.environ.get("MARMIR_API_KEY")
    public_url = (public_url or os.environ.get("MARMIR_PUBLIC_URL") or "").rstrip("/")
    toolkit = tools or SpreadsheetTools(
        output_dir=os.environ.get("MARMIR_OUTPUT_DIR", "marmir_output"),
        read_dirs=[],
        include_base64=False,
    )
    app = FastAPI(
        title="Marmir Spreadsheet API",
        version=__version__,
        description=(
            "Create Excel, CSV, Markdown and HTML spreadsheets from a JSON workbook spec, "
            "and read spreadsheets back as Markdown or JSON."
        ),
        servers=[{"url": public_url}] if public_url else None,
    )
    bearer = HTTPBearer(auto_error=False)

    def check_auth(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> None:
        if not api_key:
            return
        if credentials is None or not secrets.compare_digest(credentials.credentials, api_key):
            raise HTTPException(status_code=401, detail="invalid or missing API key")

    def link(request: Request, file_id: str) -> str:
        base = public_url or str(request.base_url).rstrip("/")
        return f"{base}/v1/spreadsheets/{file_id}"

    @app.get("/health", include_in_schema=False)
    def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    @app.get("/v1/schema", operation_id="getWorkbookSchema", summary="Workbook spec JSON Schema")
    def schema() -> dict[str, Any]:
        return WORKBOOK_SPEC_SCHEMA

    @app.post(
        "/v1/spreadsheets",
        operation_id="createSpreadsheet",
        summary="Create a spreadsheet file from a workbook spec",
        description=(
            "Body: {title?, format?, filename?, sheets: [{name, columns: [{name, type, format?}], "
            "rows: [[cell...]], options?}]}. Cells are scalars or {formula}, {url, text}, "
            "{value, type?, format?, style?}. Returns a download_url. Formulas use A1 "
            "references; row 1 is the header."
        ),
        dependencies=[Depends(check_auth)],
    )
    def create(
        request: Request, spec: dict[str, Any] = Body(..., examples=[_SPEC_EXAMPLE])
    ) -> JSONResponse:
        result = toolkit.call("create_spreadsheet", spec)
        if not result.get("ok"):
            return JSONResponse(result, status_code=422)
        file_id = result.pop("filename")
        result.pop("path", None)
        result["file_id"] = file_id
        result["download_url"] = link(request, file_id)
        return JSONResponse(result)

    @app.post(
        "/v1/spreadsheets/preview",
        operation_id="previewSpreadsheet",
        summary="Validate a workbook spec and preview it as Markdown",
        dependencies=[Depends(check_auth)],
    )
    def preview(spec: dict[str, Any] = Body(..., examples=[_SPEC_EXAMPLE])) -> JSONResponse:
        result = toolkit.call("preview_spreadsheet", spec)
        return JSONResponse(result, status_code=200 if result.get("ok") else 422)

    @app.post(
        "/v1/spreadsheets/render",
        operation_id="renderSpreadsheet",
        summary="Create a spreadsheet and return the file bytes",
        dependencies=[Depends(check_auth)],
        responses={200: {"content": {"application/octet-stream": {}}}},
    )
    def render(spec: dict[str, Any] = Body(..., examples=[_SPEC_EXAMPLE])) -> Response:
        result = toolkit.call("create_spreadsheet", spec)
        if not result.get("ok"):
            return JSONResponse(result, status_code=422)
        path = Path(result["path"])
        data = path.read_bytes()
        path.unlink(missing_ok=True)
        return Response(
            data,
            media_type=result["media_type"],
            headers={"Content-Disposition": f'attachment; filename="{result["filename"]}"'},
        )

    @app.get(
        "/v1/spreadsheets/{file_id}",
        operation_id="downloadSpreadsheet",
        summary="Download a created spreadsheet",
        dependencies=[Depends(check_auth)],
    )
    def download(file_id: str) -> FileResponse:
        if not _FILE_ID.match(file_id):
            raise HTTPException(status_code=404, detail="not found")
        root = toolkit.output_dir.resolve()
        path = (root / file_id).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise HTTPException(status_code=404, detail="not found")
        fmt = format_for_path(path)
        media_type = get_composer_class(fmt).media_type if fmt else None
        return FileResponse(path, filename=path.name, media_type=media_type)

    @app.post(
        "/v1/spreadsheets/read",
        operation_id="readSpreadsheet",
        summary="Upload a spreadsheet and get its contents as Markdown or JSON",
        dependencies=[Depends(check_auth)],
    )
    async def read_upload(
        file: UploadFile = File(...),
        max_rows: int = Query(50, ge=1, le=10_000),
        output: str = Query("markdown", pattern="^(markdown|json)$"),
    ) -> JSONResponse:
        data = await file.read(_MAX_UPLOAD + 1)
        if len(data) > _MAX_UPLOAD:
            raise HTTPException(status_code=413, detail="file too large")
        suffix = Path(file.filename or "upload.xlsx").suffix.lower() or ".xlsx"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / f"upload{suffix}"
            path.write_bytes(data)
            reader = SpreadsheetTools(output_dir=tmp, read_dirs=[tmp])
            result = reader.call(
                "read_spreadsheet", {"path": str(path), "max_rows": max_rows, "output": output}
            )
        result.pop("path", None)
        return JSONResponse(result, status_code=200 if result.get("ok") else 422)

    @app.get("/v1/formats", operation_id="listFormats", summary="Output formats")
    def formats() -> dict[str, list[str]]:
        return {"formats": WRITE_FORMATS}

    return app


def main(host: str = "127.0.0.1", port: int = 8080) -> None:  # pragma: no cover
    try:
        import uvicorn
    except ImportError as exc:
        raise MissingDependencyError("uvicorn", "server", "marmir serve") from exc
    uvicorn.run(create_app(), host=host, port=port)
