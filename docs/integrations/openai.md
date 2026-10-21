# OpenAI: Responses API, Chat Completions, Agents SDK, ChatGPT

## Responses API (function calling)

```python
from openai import OpenAI
from mm.ai import SYSTEM_PROMPT, SpreadsheetTools

client = OpenAI()
tools = SpreadsheetTools(output_dir="marmir_output")
items = [{"role": "user", "content": "Build a 12-month budget for a 5-person startup"}]

while True:
    response = client.responses.create(
        model="gpt-5", instructions=SYSTEM_PROMPT, tools=tools.openai_tools(), input=items
    )
    items += response.output
    calls = [i for i in response.output if i.type == "function_call"]
    if not calls:
        print(response.output_text)
        break
    items += [tools.handle_openai_tool_call(c) for c in calls]
```

`tools.openai_tools()` returns Responses-style definitions (`{"type": "function",
"name", "parameters", "strict": false}`); `handle_openai_tool_call` returns the matching
`function_call_output` item. Strict mode is off because rows are free-form; Marmir
validates the arguments itself and returns errors the model can act on.

Scripts: [`examples/openai_responses.py`](../../examples/openai_responses.py).

## Chat Completions (and OpenAI-compatible servers)

```python
tools_list = tools.openai_tools("chat")      # {"type": "function", "function": {...}}
...
for call in message.tool_calls:
    messages.append(tools.handle_openai_tool_call(call))   # {"role": "tool", ...}
```

This also works with Azure OpenAI, vLLM, Ollama, LM Studio and other servers that speak
the Chat Completions tool protocol. See
[`examples/openai_chat_completions.py`](../../examples/openai_chat_completions.py).

## Agents SDK (MCP)

```python
from agents import Agent, Runner
from agents.mcp import MCPServerStdio

async with MCPServerStdio(name="marmir", params={"command": "marmir-mcp"}) as server:
    agent = Agent(name="Analyst", instructions=SYSTEM_PROMPT, mcp_servers=[server])
    result = await Runner.run(agent, "Create a meal-plan spreadsheet")
```

See [`examples/openai_agents_mcp.py`](../../examples/openai_agents_mcp.py).

## Remote MCP (Responses API, ChatGPT connectors)

Host the server over streamable HTTP, behind HTTPS and authentication you control:

```bash
marmir-mcp --transport streamable-http --host 0.0.0.0 --port 8000   # endpoint: /mcp
```

```python
client.responses.create(
    model="gpt-5",
    tools=[{"type": "mcp", "server_label": "marmir",
            "server_url": "https://marmir.example.com/mcp", "require_approval": "never"}],
    input="Create a project tracker spreadsheet",
)
```

## Custom GPTs (Actions)

Use the [HTTP API](http-api.md): run `marmir serve`, export the OpenAPI document with
`marmir openapi --url https://your-host`, and paste it into the GPT's Actions editor
with Bearer authentication. The model receives a `download_url` for every file it
creates.
