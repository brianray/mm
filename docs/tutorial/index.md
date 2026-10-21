# Tutorial

This tutorial builds one realistic project from start to finish: the quarterly
reporting for **Acme Coffee Roasters**, a small wholesale roaster that sells bags of
coffee to cafes. Along the way you will use every major part of Marmir.

| Chapter | You will learn | Time |
| --- | --- | --- |
| [1. Your first spreadsheet](01-first-spreadsheet.md) | `Document`, type inference, options, reading files back | 10 min |
| [2. Formatting, formulas and styles](02-formatting-and-formulas.md) | currency/percent/date formats, live formulas, CSS styles | 15 min |
| [3. Multi-sheet reports from real data](03-multi-sheet-reports.md) | DataFrames, SQL, several sheets, other formats, the CLI | 15 min |
| [4. The workbook spec](04-workbook-spec.md) | describing a workbook as JSON, validation, round-trips | 15 min |
| [5. Let an AI agent build spreadsheets](05-ai-agents.md) | tool calls, Claude, OpenAI, MCP, prompts that work | 20 min |
| [6. A spreadsheet API for GPTs and apps](06-http-api.md) | the HTTP API, auth, custom GPT Actions | 10 min |
| [7. Extending Marmir](07-extending.md) | custom output formats, custom grids, Django | 15 min |

## Before you start

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install "marmir[all]"
mkdir acme && cd acme
```

`marmir[all]` installs every optional feature. Chapters say which extra they need if you
prefer a smaller install.

Every Python block in these chapters is executed by the project's test suite
(`tests/test_tutorial.py`), and every "Output" block is compared against what the code
really prints -- so what you read is what you will see. Blocks that need an API key or a
running server are marked as such and skipped by the tests.

Run each chapter's blocks in order in one Python session (a script, a REPL or a
notebook); later blocks reuse variables from earlier ones.
