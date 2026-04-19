from __future__ import annotations

from pathlib import Path

from agentkit_cli.burn import BurnAnalysisEngine
from agentkit_cli.renderers.burn_report import render_burn_html, render_burn_markdown

FIXTURES = Path(__file__).parent / "fixtures" / "burn"


def test_burn_report_has_required_sections():
    report = BurnAnalysisEngine().analyze(BurnAnalysisEngine().load(FIXTURES))
    html = render_burn_html(report).lower()
    assert "where spend goes" in html
    assert "what to fix first" in html
    assert "most expensive sessions" in html


def test_burn_report_dark_theme_markers():
    report = BurnAnalysisEngine().analyze(BurnAnalysisEngine().load(FIXTURES))
    html = render_burn_html(report)
    assert "#0d1117" in html
    assert "agentkit burn" in html.lower()


def test_burn_markdown_summary_contains_totals():
    report = BurnAnalysisEngine().analyze(BurnAnalysisEngine().load(FIXTURES))
    md = render_burn_markdown(report)
    assert "### Where spend goes" in md
    assert "Total cost" in md
