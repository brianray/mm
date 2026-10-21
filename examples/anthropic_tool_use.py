"""Claude builds a spreadsheet with Marmir's tools (Anthropic Messages API).

    pip install marmir anthropic
    export ANTHROPIC_API_KEY=...        # or `ant auth login`
    python examples/anthropic_tool_use.py "Build a 12-month budget for a 5-person startup"

The loop is the standard manual tool-use loop: send tools, run each tool_use block with
SpreadsheetTools, return every tool_result in one user message, repeat until Claude stops.
"""

import sys

import anthropic

from mm.ai import SYSTEM_PROMPT, SpreadsheetTools

MODEL = "claude-opus-5-5"


def main(prompt: str) -> None:
    client = anthropic.Anthropic()
    tools = SpreadsheetTools(output_dir="marmir_output")
    messages = [{"role": "user", "content": prompt}]

    while True:
        # fallbacks="default" re-runs a request that hits a safety refusal on a
        # fallback model inside the same call (beta server-side-fallback-2026-07-01).
        response = client.beta.messages.create(
            model=MODEL,
            max_tokens=16000,
            system=SYSTEM_PROMPT,
            tools=tools.anthropic_tools(),
            messages=messages,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
        if response.stop_reason == "refusal":
            print("Claude declined this request.")
            return
        # keep the full content (thinking and tool_use blocks included)
        messages.append({"role": "assistant", "content": response.content})

        tool_uses = [block for block in response.content if block.type == "tool_use"]
        if response.stop_reason != "tool_use" or not tool_uses:
            for block in response.content:
                if block.type == "text":
                    print(block.text)
            return

        results = [tools.handle_anthropic_tool_use(block) for block in tool_uses]
        for block, result in zip(tool_uses, results):
            print(f"[{block.name}] error={result['is_error']}")
        messages.append({"role": "user", "content": results})


if __name__ == "__main__":
    main(" ".join(sys.argv[1:]) or "Make a spreadsheet comparing 3 cloud storage plans.")
