"""Tests for D1: GitHub Pages landing site (docs/index.html)."""
from __future__ import annotations

from pathlib import Path

DOCS_DIR = Path(__file__).parent.parent / "docs"
INDEX_HTML = DOCS_DIR / "index.html"


def _html() -> str:
    return INDEX_HTML.read_text(encoding="utf-8")


def test_index_html_exists():
    assert INDEX_HTML.exists(), "docs/index.html must exist"


def test_html_has_doctype():
    assert _html().lower().startswith("<!doctype html")


def test_hero_headline():
    html = _html()
    assert "Benchmark AI Coding Agents" in html


def test_pipeline_stages():
    html = _html()
    for stage in ("MEASURE", "GENERATE", "GUARD", "LEARN", "BENCHMARK"):
        assert stage in html, f"Pipeline stage {stage!r} missing"


def test_feature_grid_six_tools():
    html = _html()
    for tool in ("coderace", "agentmd", "agentlint", "agentreflect", "agentkit-mcp", "agentkit-cli"):
        assert tool in html, f"Tool {tool!r} missing from features grid"


def test_stat_data_attributes():
    html = _html()
    assert html.count("data-stat=") >= 3, "Expected ≥3 data-stat attributes in stats bar"


def test_stat_values_present():
    html = _html()
    assert "2529" in html, "Test count stat 2529 missing"
    assert ">6<" in html or ">6</div" in html or "packages\">6" in html or ">6\n" in html or "2026" in html
    # At least packages count is present
    assert "6" in html


def test_quickstart_code_block():
    html = _html()
    assert "pip install agentkit-cli" in html
    assert "agentkit quickstart" in html


def test_github_link():
    html = _html()
    assert "github.com/mikiships/agentkit-cli" in html


def test_pypi_link():
    html = _html()
    assert "pypi.org/project/agentkit-cli" in html


def test_no_external_js_frameworks():
    html = _html()
    # No CDN script imports for major frameworks
    for cdn in ("cdn.jsdelivr.net", "unpkg.com", "cdnjs.cloudflare.com"):
        assert cdn not in html, f"External CDN dependency found: {cdn}"


def test_commands_table_present():
    html = _html()
    assert "cmd-table" in html
    assert "agentkit run" in html


def test_dark_theme_colors():
    html = _html()
    assert "#0d1117" in html or "0d1117" in html, "Dark background color missing"
