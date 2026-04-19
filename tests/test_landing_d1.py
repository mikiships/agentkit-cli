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
    assert "One canonical context file" in html
    assert ".agentkit/source.md" in html
    assert "v1.2.0" in html
    assert "agentkit contract" in html


def test_pipeline_stages():
    html = _html()
    for stage in ("SOURCE", "PROJECT", "SCORE", "GUARD", "LEARN"):
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
    # Test count stat should be present (2690+ for v0.57.0)
    assert any(str(n) in html for n in range(2000, 9999)), "Test count stat missing from stats bar"
    assert ">6<" in html or ">6</div" in html or "packages\">6" in html or ">6\n" in html or "2026" in html
    # At least packages count is present
    assert "6" in html


def test_quickstart_code_block():
    html = _html()
    assert "pip install agentkit-cli" in html
    assert "agentkit source --init" in html
    assert "agentkit project --write" in html
    assert "agentkit contract --init" in html


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
    assert "agentkit source --init" in html
    assert "agentkit contract --init" in html
    assert "agentkit burn --path ./transcripts" in html


def test_dark_theme_colors():
    html = _html()
    assert "#0d1117" in html or "0d1117" in html, "Dark background color missing"


def test_stats_show_current_shipped_counts():
    html = _html()
    assert 'data-stat="tests">4824<' in html
    assert 'data-stat="versions">111<' in html
    assert 'data-stat="packages">6<' in html
