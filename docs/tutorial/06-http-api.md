# 6. A spreadsheet API for GPTs and apps

<!-- requires: fastapi, httpx -->

**Goal:** run Marmir as a web service so a custom GPT, a no-code tool or an app in any
language can create spreadsheets over HTTP. Needs `pip install "marmir[server]"`.

## Start the server

```bash
export MARMIR_API_KEY="pick-a-long-random-string"
export MARMIR_PUBLIC_URL="https://sheets.acme-coffee.example"    # where clients reach it
marmir serve --host 0.0.0.0 --port 8080
```

Open `http://localhost:8080/docs` for interactive Swagger documentation.

| Endpoint | Purpose |
| --- | --- |
| `POST /v1/spreadsheets` | spec in -> file stored, `download_url` out |
| `GET /v1/spreadsheets/{file_id}` | download it |
| `POST /v1/spreadsheets/render` | spec in -> file bytes out (nothing stored) |
| `POST /v1/spreadsheets/preview` | validate + Markdown preview |
| `POST /v1/spreadsheets/read` | upload a file -> Markdown/JSON |
| `GET /v1/schema` | the workbook spec JSON Schema |

## Try it without a server

FastAPI's test client calls the app in-process -- handy for this tutorial and for your
own tests:

```python
from fastapi.testclient import TestClient

from mm.ai import SpreadsheetTools
from mm.server import create_app

app = create_app(
    SpreadsheetTools(output_dir="api_files", read_dirs=[]),
    api_key="secret",
    public_url="https://sheets.acme-coffee.example",
)
client = TestClient(app)
auth = {"Authorization": "Bearer secret"}

spec = {
    "title": "Acme price list",
    "sheets": [{
        "name": "Prices",
        "columns": [{"name": "Coffee", "type": "string"}, {"name": "Per bag", "type": "currency"}],
        "rows": [["House blend", 13.75], ["Ethiopia Guji", 17.5], ["Decaf", 15]],
    }],
}
response = client.post("/v1/spreadsheets", json=spec, headers=auth)
body = response.json()
print(response.status_code, body["file_id"].endswith(".xlsx"))
print(body["download_url"].startswith("https://sheets.acme-coffee.example/v1/spreadsheets/"))
```

Output:

```text
200 True
True
```

Download it, as a client would:

```python
download = client.get(f"/v1/spreadsheets/{body['file_id']}", headers=auth)
print(download.status_code, download.headers["content-type"])
```

Output:

```text
200 application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
```

Bad specs get `422` with the same fix-it list the AI tools return; a missing key gets
`401`:

```python
bad = client.post("/v1/spreadsheets", json={"sheets": [{"rows": [["no columns"]]}]}, headers=auth)
print(bad.status_code, bad.json()["errors"])
print(client.post("/v1/spreadsheets", json=spec).status_code)
```

Output:

```text
422 ["sheets[0].rows[0]: array rows need 'columns' on the sheet"]
401
```

Need the file in the response instead of a link? Use `render` with any format:

```python
csv = client.post("/v1/spreadsheets/render", json={**spec, "format": "csv"}, headers=auth)
print(csv.text)
```

Output:

```text
Coffee,Per bag
House blend,13.75
Ethiopia Guji,17.5
Decaf,15
```

## From other languages

It is plain JSON over HTTP:

```bash
curl -s -X POST "$MARMIR_PUBLIC_URL/v1/spreadsheets" \
  -H "Authorization: Bearer $MARMIR_API_KEY" -H "Content-Type: application/json" \
  -d @examples/workbook_spec.json
```

```javascript
const res = await fetch(`${base}/v1/spreadsheets/render`, {
  method: "POST",
  headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json" },
  body: JSON.stringify(spec),
});
const xlsx = await res.arrayBuffer();
```

## Connect a custom GPT

1. Deploy the server somewhere with HTTPS (a container, Cloud Run, Fly.io, ...).
2. Export the OpenAPI document with your public URL:

   ```bash
   marmir openapi --url https://sheets.acme-coffee.example > openapi.json
   ```

3. In ChatGPT: *Explore GPTs -> Create -> Configure -> Actions -> Create new action*.
   Paste `openapi.json`. Under *Authentication* choose *API Key*, *Bearer*, and enter
   your `MARMIR_API_KEY`.
4. Add to the GPT's instructions:

   > When the user asks for a spreadsheet, table export, tracker or report, call
   > `createSpreadsheet` with a workbook spec. Use typed columns (currency, percent,
   > date), raw numbers and formulas for totals. Reply with the `download_url`.

5. Ask it: *"Make me a price list for our coffees with a 10% wholesale discount
   column."*

## Running it for real

- Put it behind HTTPS; keep `MARMIR_API_KEY` secret.
- `MARMIR_OUTPUT_DIR` grows over time -- clean it up with a cron job or use `render`.
- Uploads to `/v1/spreadsheets/read` are limited to 20 MB.
- To embed the API in an existing FastAPI app: `app.mount("/sheets", create_app(...))`.

## Recap

- `marmir serve` exposes create / download / render / preview / read over HTTP.
- `marmir openapi --url ...` gives a custom GPT everything it needs.
- The same validation messages reach every client.

Next: [7. Extending Marmir](07-extending.md).
