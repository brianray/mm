# HTTP API and custom GPT Actions

```bash
pip install "marmir[server]"
MARMIR_API_KEY=change-me MARMIR_PUBLIC_URL=https://sheets.example.com marmir serve --host 0.0.0.0 --port 8080
```

| Method & path | operationId | Purpose |
| --- | --- | --- |
| `POST /v1/spreadsheets` | `createSpreadsheet` | Spec in, `{file_id, download_url, preview, ...}` out |
| `GET /v1/spreadsheets/{file_id}` | `downloadSpreadsheet` | Download a created file |
| `POST /v1/spreadsheets/render` | `renderSpreadsheet` | Spec in, file bytes out |
| `POST /v1/spreadsheets/preview` | `previewSpreadsheet` | Validate + Markdown preview |
| `POST /v1/spreadsheets/read` | `readSpreadsheet` | Upload a file (multipart `file`), get Markdown/JSON |
| `GET /v1/schema` | `getWorkbookSchema` | Workbook spec JSON Schema |
| `GET /v1/formats` | `listFormats` | Output formats |
| `GET /openapi.json`, `/docs` | | OpenAPI document and Swagger UI |

Invalid specs return `422` with `{"ok": false, "errors": [...]}`.

Configuration: `MARMIR_API_KEY` enables `Authorization: Bearer <key>` on every `/v1`
endpoint except the schema and formats; `MARMIR_PUBLIC_URL` sets the base of
`download_url` and the OpenAPI `servers` entry; `MARMIR_OUTPUT_DIR` is where files are
kept (clean it up on your own schedule). Uploads are limited to 20 MB.

```bash
curl -s -X POST https://sheets.example.com/v1/spreadsheets \
  -H "Authorization: Bearer change-me" -H "Content-Type: application/json" \
  -d @examples/workbook_spec.json
```

## Custom GPT (ChatGPT Actions)

1. Deploy the server on an HTTPS host.
2. `marmir openapi --url https://sheets.example.com > openapi.json`
   (or open `https://sheets.example.com/openapi.json`).
3. In the GPT editor: *Configure -> Actions -> Create new action*, paste the schema,
   set *Authentication* to *API Key / Bearer* with your `MARMIR_API_KEY`.
4. Add to the GPT's instructions: *"When the user wants a spreadsheet, call
   createSpreadsheet with a workbook spec and give them the download_url."*

`docs/openapi.json` in this repository is a reference copy of the document.

## Embedding

```python
from mm.server import create_app
from mm.ai import SpreadsheetTools

app = create_app(SpreadsheetTools(output_dir="/srv/sheets", read_dirs=[]), api_key="...")
# mount in your FastAPI/Starlette app or run with uvicorn
```
