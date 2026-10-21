"""An OpenAI model builds a spreadsheet with Marmir's tools (Responses API).

    pip install marmir openai
    export OPENAI_API_KEY=...
    python examples/openai_responses.py "Build a 12-month budget for a 5-person startup"
"""

import os
import sys

from openai import OpenAI

from mm.ai import SYSTEM_PROMPT, SpreadsheetTools

MODEL = os.environ.get("OPENAI_MODEL", "gpt-5")


def main(prompt: str) -> None:
    client = OpenAI()
    tools = SpreadsheetTools(output_dir="marmir_output")
    items: list = [{"role": "user", "content": prompt}]

    while True:
        response = client.responses.create(
            model=MODEL,
            instructions=SYSTEM_PROMPT,
            tools=tools.openai_tools("responses"),
            input=items,
        )
        items += response.output
        calls = [item for item in response.output if item.type == "function_call"]
        if not calls:
            print(response.output_text)
            return
        for call in calls:
            items.append(tools.handle_openai_tool_call(call))
            print(f"[{call.name}] done")


if __name__ == "__main__":
    main(" ".join(sys.argv[1:]) or "Make a spreadsheet comparing 3 cloud storage plans.")
