"""Marmir tools with the OpenAI Chat Completions API (also works with most
OpenAI-compatible endpoints: Azure OpenAI, vLLM, Ollama, LM Studio ...).

    pip install marmir openai
    python examples/openai_chat_completions.py "Track my reading list"
"""

import os
import sys

from openai import OpenAI

from mm.ai import SYSTEM_PROMPT, SpreadsheetTools

MODEL = os.environ.get("OPENAI_MODEL", "gpt-5")


def main(prompt: str) -> None:
    client = OpenAI()
    tools = SpreadsheetTools(output_dir="marmir_output")
    messages: list = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}]

    while True:
        reply = client.chat.completions.create(
            model=MODEL, messages=messages, tools=tools.openai_tools("chat")
        ).choices[0].message
        messages.append(reply)
        if not reply.tool_calls:
            print(reply.content)
            return
        for call in reply.tool_calls:
            messages.append(tools.handle_openai_tool_call(call))


if __name__ == "__main__":
    main(" ".join(sys.argv[1:]) or "Make a spreadsheet comparing 3 cloud storage plans.")
