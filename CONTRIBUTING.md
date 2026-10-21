# Contributing

```bash
git clone https://github.com/brianray/mm && cd mm
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"

pytest                       # tests (optional features skip when their extra is missing)
pytest --cov=mm              # with coverage
ruff check src tests && ruff format src tests
mypy
```

Layout:

```
src/mm/            library (import name: mm)
  types.py         cell field types          model.py    input normalisation + DataModel
  grid.py          Grid + Serializer         document.py Document / DocumentWriter
  composers/       output formats            reader.py   reading files
  spec.py          workbook spec + validator style.py, colors.py, formats.py, fonts.py
  ai/              LLM tools + MCP server    server.py   HTTP API     cli.py  CLI
  contrib/         Django, Google Sheets, PrettyTable
tests/             pytest suite
docs/              documentation (mkdocs.yml)
examples/          runnable examples and client configs
skills/            Claude Agent Skill
.claude-plugin/    Claude Code plugin + marketplace manifests
```

Guidelines: keep the core dependency-free beyond openpyxl (optional features go behind
extras and lazy imports); every change needs tests; tool-facing errors should say what
to fix and where, because models read them.
