"""Shipped examples, manifests and docs stay valid."""

from __future__ import annotations

import json
import re
from pathlib import Path

import mm

ROOT = Path(__file__).resolve().parent.parent


def test_example_spec_is_valid():
    spec = json.loads((ROOT / "examples" / "workbook_spec.json").read_text())
    assert mm.validate_spec(spec) == []
    doc = mm.from_spec(spec)
    assert [d.name for d in doc.sheets] == ["Summary", "Deals"]


def test_plugin_and_mcp_manifests():
    plugin = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
    assert plugin["name"] == "marmir"
    assert plugin["version"] == mm.__version__
    market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
    assert market["plugins"][0]["name"] == plugin["name"]
    for path in (
        ROOT / ".mcp.json",
        ROOT / "examples" / "integrations" / "claude_desktop_config.json",
    ):
        server = json.loads(path.read_text())["mcpServers"]["marmir"]
        assert "marmir-mcp" in server["args"]


def test_skill_frontmatter():
    text = (ROOT / "skills" / "marmir-spreadsheets" / "SKILL.md").read_text()
    match = re.match(r"^---\nname: ([a-z0-9-]+)\ndescription: (.+?)\n---\n", text, re.S)
    assert match
    assert match.group(1) == "marmir-spreadsheets"
    assert len(match.group(2)) <= 1024
    # the spec embedded in the skill must be valid
    block = re.search(r"```json\n(.*?)\n```", text, re.S).group(1)
    assert mm.validate_spec(json.loads(block)) == []


def test_docs_links_resolve():
    for md in [ROOT / "README.md", *ROOT.joinpath("docs").rglob("*.md")]:
        for target in re.findall(r"\]\(([^)#:]+\.(?:md|py|json))(?:#[^)]*)?\)", md.read_text()):
            assert (md.parent / target).resolve().exists(), f"{md.name}: broken link {target}"


def test_version_matches_pyproject():
    assert 'path = "src/mm/__init__.py"' in (ROOT / "pyproject.toml").read_text()
    assert re.match(r"^\d+\.\d+\.\d+$", mm.__version__)
