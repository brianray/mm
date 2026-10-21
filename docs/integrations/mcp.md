# MCP server

`marmir-mcp` is a [Model Context Protocol](https://modelcontextprotocol.io) server
(`pip install "marmir[mcp]"`; works with the `mcp` SDK 1.x and 2.x).

```bash
marmir-mcp                                              # stdio
marmir-mcp --transport streamable-http --port 8000      # http://127.0.0.1:8000/mcp
marmir-mcp --transport sse --port 8000
uvx --from "marmir[mcp]" marmir-mcp                     # without installing
```

| Flag | Env var | Default |
| --- | --- | --- |
| `--output-dir` | `MARMIR_OUTPUT_DIR` | `./marmir_output` |
| `--read-dir` (repeatable) | `MARMIR_READ_DIRS` (`os.pathsep`-separated) | the working directory |
| `--allow-images` | | off |
| `--no-read` | | read tool enabled |
| `--host`, `--port` | | `127.0.0.1`, `8000` |

## Tools

| Tool | Input | Result |
| --- | --- | --- |
| `create_spreadsheet` | `sheets`, `format?`, `filename?`, `title?`, `options?` | `{ok, path, filename, format, size_bytes, sheets, preview}` or `{ok: false, errors}` |
| `preview_spreadsheet` | `sheets`, `title?`, `options?` | `{ok, sheets, preview}` (Markdown, no file written) |
| `read_spreadsheet` | `path`, `sheet?`, `max_rows?`, `output?` | `{ok, sheets, content}` (Markdown) or `data` (JSON) |

Resource: `marmir://schema/workbook` -- the workbook spec JSON Schema.

## Clients

- Claude Code / Claude Desktop: see [Anthropic](anthropic.md).
- OpenAI Agents SDK, Responses API remote MCP, ChatGPT connectors: see [OpenAI](openai.md).
- Cursor, VS Code, Windsurf and others: register the command `marmir-mcp` (or the
  `uvx` form) as a stdio server in the client's MCP settings.

## Embedding

```python
from mm.ai import SpreadsheetTools
from mm.ai.mcp_server import build_server

server = build_server(SpreadsheetTools(output_dir="/srv/files", read_dirs=["/srv/files"]))
server.run("stdio")
```

When exposing the HTTP transports beyond localhost, put the server behind TLS and an
authenticating proxy; the server itself does not authenticate callers.
