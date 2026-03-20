"""Tests for D3: TeamScorecardHTMLRenderer."""
from __future__ import annotations

import pytest

from agentkit_cli.user_team import TeamScorecardResult
from agentkit_cli.user_team_html import TeamScorecardHTMLRenderer
from agentkit_cli.user_scorecard import UserScorecardResult, score_to_grade


def _make_user_result(username: str, avg_score: float) -> UserScorecardResult:
    grade = score_to_grade(avg_score)
    return UserScorecardResult(
        username=username,
        total_repos=5,
        analyzed_repos=5,
        skipped_repos=0,
        avg_score=avg_score,
        grade=grade,
        context_coverage_pct=50.0,
        top_repos=[],
        bottom_repos=[],
        all_repos=[],
    )


def _make_result() -> TeamScorecardResult:
    results = [
        _make_user_result("alice", 85.0),
        _make_user_result("bob", 65.0),
        _make_user_result("charlie", 50.0),
    ]
    return TeamScorecardResult(
        org="pallets",
        contributor_results=results,
        aggregate_score=66.7,
        aggregate_grade="B",
        top_scorer="alice",
        contributor_count=3,
        timestamp="2026-03-20 00:00 UTC",
    )


def test_html_renderer_returns_valid_html():
    renderer = TeamScorecardHTMLRenderer()
    html = renderer.render(_make_result())
    assert isinstance(html, str)
    assert "<!DOCTYPE html>" in html
    assert "<html" in html
    assert "</html>" in html


def test_html_contains_org_name():
    renderer = TeamScorecardHTMLRenderer()
    html = renderer.render(_make_result())
    assert "pallets" in html


def test_html_contains_aggregate_grade():
    renderer = TeamScorecardHTMLRenderer()
    html = renderer.render(_make_result())
    assert "B" in html


def test_html_contains_contributor_rows():
    renderer = TeamScorecardHTMLRenderer()
    html = renderer.render(_make_result())
    assert "alice" in html
    assert "bob" in html
    assert "charlie" in html


def test_html_contains_avatar_img_tags():
    renderer = TeamScorecardHTMLRenderer()
    html = renderer.render(_make_result())
    assert "<img" in html
    assert "github.com/alice.png" in html


def test_html_contains_grade_pills():
    renderer = TeamScorecardHTMLRenderer()
    html = renderer.render(_make_result())
    assert "grade-pill" in html


def test_html_contains_grade_distribution():
    renderer = TeamScorecardHTMLRenderer()
    html = renderer.render(_make_result())
    assert "dist" in html or "Grade Distribution" in html or "dist-row" in html


def test_html_contains_footer():
    renderer = TeamScorecardHTMLRenderer()
    html = renderer.render(_make_result())
    assert "agentkit-cli" in html
    assert "footer" in html


def test_html_is_self_contained():
    """HTML should include embedded CSS, not external links."""
    renderer = TeamScorecardHTMLRenderer()
    html = renderer.render(_make_result())
    assert "<style>" in html
    assert "</style>" in html
    # Should not reference external CSS files
    assert 'href=' not in html or 'href="/' not in html


def test_html_dark_theme_colors():
    """HTML should contain dark theme background color."""
    renderer = TeamScorecardHTMLRenderer()
    html = renderer.render(_make_result())
    assert "#0d1117" in html or "0d1117" in html  # dark background


def test_html_grade_colors_present():
    """HTML should include grade color definitions."""
    renderer = TeamScorecardHTMLRenderer()
    html = renderer.render(_make_result())
    assert "#3fb950" in html  # A green
    assert "#f85149" in html  # D red
