"""OpenAI Responses API calling a *remote* Marmir MCP server.

Start the server somewhere the OpenAI API can reach (behind HTTPS and your own auth):

    marmir-mcp --transport streamable-http --host 0.0.0.0 --port 8000   # serves /mcp

then point `server_url` at it.
"""

import os

from openai import OpenAI

client = OpenAI()
response = client.responses.create(
    model=os.environ.get("OPENAI_MODEL", "gpt-5"),
    tools=[
        {
            "type": "mcp",
            "server_label": "marmir",
            "server_url": os.environ.get("MARMIR_MCP_URL", "https://marmir.example.com/mcp"),
            "require_approval": "never",
        }
    ],
    input="Create a project tracker spreadsheet with owners, due dates and status.",
)
print(response.output_text)
