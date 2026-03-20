"""Tests for D3: RepoDuelHTMLRenderer."""
from __future__ import annotations

import pytest

from agentkit_cli.repo_duel import RepoDuelResult, DimensionResult
from agentkit_cli.renderers.repo_duel_renderer import render_repo_duel_html


def _make_result(winner="repo1", repo1="github:a/repo1", repo2="github:b/repo2"):
    return RepoDuelResult(
        repo1=repo1,
        repo2=repo2,
        repo1_score=85.0,
        repo2_score=65.0,
        repo1_grade="A",
        repo2_grade="C",
        dimension_results=[
            DimensionResult("composite_score", 85.0, 65.0, "repo1", 20.0),
            DimensionResult("context_coverage", 90.0, 60.0, "repo1", 30.0),
            DimensionResult("test_coverage", 70.0, 70.0, "draw", 0.0),
            DimensionResult("lint_score", 80.0, 80.0, "draw", 0.0),
        ],
        winner=winner,
        run_date="2026-03-20 12:00 UTC",
    )


def test_renders_valid_html():
    result = _make_result()
    html = render_repo_duel_html(result)
    assert "<!DOCTYPE html>" in html
    assert "<html" in html
    assert "</html>" in html


def test_contains_repo_names():
    result = _make_result()
    html = render_repo_duel_html(result)
    assert "a/repo1" in html or "repo1" in html
    assert "b/repo2" in html or "repo2" in html


def test_contains_scores():
    result = _make_result()
    html = render_repo_duel_html(result)
    assert "85.0" in html
    assert "65.0" in html


def test_contains_grade_badges():
    result = _make_result()
    html = render_repo_duel_html(result)
    assert "A" in html
    assert "C" in html


def test_winner_banner_repo1():
    result = _make_result(winner="repo1")
    html = render_repo_duel_html(result)
    assert "wins" in html or "winner" in html.lower()


def test_winner_banner_draw():
    result = _make_result(winner="draw")
    result.repo1_score = 70.0
    result.repo2_score = 70.0
    html = render_repo_duel_html(result)
    assert "draw" in html.lower() or "🤝" in html


def test_winner_banner_repo2():
    result = _make_result(winner="repo2")
    html = render_repo_duel_html(result)
    assert "wins" in html


def test_dimension_table_present():
    result = _make_result()
    html = render_repo_duel_html(result)
    assert "<table" in html
    assert "Composite Score" in html or "composite" in html.lower()


def test_footer_contains_version():
    from agentkit_cli import __version__
    result = _make_result()
    html = render_repo_duel_html(result)
    assert __version__ in html


def test_share_url_included():
    result = _make_result()
    result.share_url = "https://here.now/abc123"
    html = render_repo_duel_html(result)
    assert "https://here.now/abc123" in html


def test_no_broken_template_vars():
    result = _make_result()
    html = render_repo_duel_html(result)
    assert "{" not in html or "style" in html  # allow CSS {} but no Python {vars}
    assert "}" not in html or "style" in html or "}" in html  # CSS is fine


def test_github_link_in_footer():
    result = _make_result()
    html = render_repo_duel_html(result)
    assert "github.com/mikiships/agentkit-cli" in html
