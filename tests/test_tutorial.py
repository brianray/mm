"""Execute every Python block in docs/tutorial (and the cookbook) and check the output.

Rules for tutorial Markdown:

* every ```python block runs, in order, in one namespace per chapter, inside a temporary
  working directory;
* a block preceded by ``<!-- skip -->`` (needs an API key, a server, ...) is not run;
* a block followed by a line ``Output:`` and a ```text block must print exactly that
  text (trailing whitespace ignored).
"""

from __future__ import annotations

import contextlib
import io
import re
from pathlib import Path

import pytest

DOCS = Path(__file__).resolve().parent.parent / "docs"
TUTORIAL = DOCS / "tutorial"
BLOCK = re.compile(
    r"(<!-- skip -->\s*\n)?```python\n(.*?)\n```(\s*\nOutput:\s*\n```text\n(.*?)\n```)?", re.S
)
CHAPTERS = [*sorted(TUTORIAL.glob("[0-9]*.md")), DOCS / "cookbook.md"]


def extract(path: Path) -> list[tuple[str, str | None, bool]]:
    """(code, expected output or None, skipped) for each python block."""
    return [(m.group(2), m.group(4), bool(m.group(1))) for m in BLOCK.finditer(path.read_text())]


def _clean(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.strip("\n").splitlines())


def test_chapters_found():
    assert len(CHAPTERS) >= 8
    assert all(extract(chapter) for chapter in CHAPTERS)


@pytest.mark.parametrize("chapter", CHAPTERS, ids=lambda p: p.stem)
def test_tutorial_chapter(chapter, tmp_path, monkeypatch):
    requirements = re.findall(r"<!-- requires: ([\w, ]+) -->", chapter.read_text())
    for group in requirements:
        for module in group.split(","):
            pytest.importorskip(module.strip())
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MARMIR_OUTPUT_DIR", str(tmp_path / "marmir_output"))
    namespace: dict = {"__name__": "__tutorial__"}
    for index, (code, expected, skipped) in enumerate(extract(chapter), start=1):
        if skipped:
            compile(code, f"{chapter.name}[{index}]", "exec")  # still must be valid Python
            continue
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exec(compile(code, f"{chapter.name}[{index}]", "exec"), namespace)
        if expected is not None:
            assert _clean(stdout.getvalue()) == _clean(expected), f"{chapter.name} block {index}"
