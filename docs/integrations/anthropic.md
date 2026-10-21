# Anthropic: Claude Desktop, Claude Code, the Claude API and Skills

Marmir plugs into Claude four ways. All of them use the same three tools --
`create_spreadsheet`, `preview_spreadsheet`, `read_spreadsheet` -- and the same
[workbook spec](../workbook-spec.md).

## Claude Code

Add the MCP server (needs [uv](https://docs.astral.sh/uv/); or replace the command with
`marmir-mcp` after `pip install "marmir[mcp]"`):

```bash
claude mcp add marmir -- uvx --from "marmir[mcp]" marmir-mcp
```

Or install this repository as a **plugin** -- it bundles the MCP server (`.mcp.json`)
and the `marmir-spreadsheets` skill:

```text
/plugin marketplace add brianray/mm
/plugin install marmir@marmir
```

Then ask: *"Turn data/orders.csv into a formatted Excel report with a summary sheet."*

## Claude Desktop

Edit `claude_desktop_config.json` (Settings -> Developer -> Edit Config):

```json
{
  "mcpServers": {
    "marmir": {
      "command": "uvx",
      "args": ["--from", "marmir[mcp]", "marmir-mcp"],
      "env": {
        "MARMIR_OUTPUT_DIR": "/Users/you/Documents/Marmir",
        "MARMIR_READ_DIRS": "/Users/you/Documents:/Users/you/Downloads"
      }
    }
  }
}
```

Restart Claude Desktop. Files are written to `MARMIR_OUTPUT_DIR`; the read tool can
only open files under `MARMIR_READ_DIRS` (default: the server's working directory) and
the output directory.

## Claude API (Messages API tool use)

```python
import anthropic
from mm.ai import SYSTEM_PROMPT, SpreadsheetTools

client = anthropic.Anthropic()
tools = SpreadsheetTools(output_dir="marmir_output")
messages = [{"role": "user", "content": "Build a 12-month budget for a 5-person startup"}]

while True:
    response = client.beta.messages.create(
        model="claude-opus-5-5",
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        tools=tools.anthropic_tools(),
        messages=messages,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",   # re-run a refused request on a fallback model
    )
    if response.stop_reason == "refusal":
        break
    messages.append({"role": "assistant", "content": response.content})
    tool_uses = [b for b in response.content if b.type == "tool_use"]
    if response.stop_reason != "tool_use" or not tool_uses:
        break
    # every tool_result goes back in ONE user message
    messages.append({"role": "user", "content": [tools.handle_anthropic_tool_use(b) for b in tool_uses]})
```

The full script is [`examples/anthropic_tool_use.py`](../../examples/anthropic_tool_use.py).
Notes:

- `handle_anthropic_tool_use` returns a `tool_result` block with `is_error: true` when the
  spec is invalid; the content lists every problem so Claude can correct itself.
- `SYSTEM_PROMPT` is a short, optional instruction block that improves results (raw
  numbers with currency/percent types, formulas for totals, ISO dates).
- Use `SpreadsheetTools(include_base64=True)` when the caller cannot reach the server's
  disk and you want the file bytes in the tool result.
- Remote MCP: run `marmir-mcp --transport streamable-http` behind HTTPS and use it with
  the Messages API MCP connector or a Claude.ai custom connector (see [MCP](mcp.md)).

## Agent Skill

`skills/marmir-spreadsheets/SKILL.md` teaches Claude to use the Python library and CLI
directly, which suits environments where Claude runs code (Claude Code, Claude.ai with
code execution, the Agent SDK, or Agent Skills on the API). Install it by copying the
folder into `~/.claude/skills/` (personal) or `.claude/skills/` (project), uploading it
as a custom skill in Claude.ai, or through the plugin above. The environment needs
`pip install marmir`.
