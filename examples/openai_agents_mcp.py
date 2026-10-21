"""OpenAI Agents SDK agent using the Marmir MCP server over stdio.

    pip install 'marmir[mcp]' openai-agents
    python examples/openai_agents_mcp.py
"""

import asyncio

from agents import Agent, Runner
from agents.mcp import MCPServerStdio

from mm.ai import SYSTEM_PROMPT


async def main() -> None:
    async with MCPServerStdio(
        name="marmir",
        params={"command": "marmir-mcp", "args": ["--output-dir", "marmir_output"]},
    ) as server:
        agent = Agent(name="Spreadsheet analyst", instructions=SYSTEM_PROMPT, mcp_servers=[server])
        result = await Runner.run(agent, "Create a weekly meal-plan spreadsheet with a shopping list sheet.")
        print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
