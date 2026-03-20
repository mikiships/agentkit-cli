"""Tests for D3: UserRankHTMLRenderer."""
from __future__ import annotations

import pytest

from agentkit_cli.user_rank import UserRankResult, UserRankEntry
from agentkit_cli.user_rank_html import UserRankHTMLRenderer, _grade_color


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_result(topic: str = "python", n: int = 3) -> UserRankResult:
    contributors = []
    for i in range(n):
        score = 90.0 - i * 10
        grade = "A" if score >= 80 else "B" if score >= 65 else "C" if score >= 50 else "D"
        contributors.append(UserRankEntry(
            rank=i + 1,
            username=f"user{i}",
            score=score,
            grade=grade,
            top_repo=f"repo{i}",
            avatar_url=f"https://github.com/user{i}.png?size=40",
        ))
    return UserRankResult(
        topic=topic,
        contributors=contributors,
        top_scorer="user0",
        mean_score=80.0,
        grade_distribution={"A": 2, "B": 1, "C": 0, "D": 0},
        timestamp="2026-03-20 00:00 UTC",
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_renderer_returns_string():
    renderer = UserRankHTMLRenderer()
    result = _make_result()
    html = renderer.render(result)
    assert isinstance(html, str)


def test_renderer_contains_doctype():
    renderer = UserRankHTMLRenderer()
    html = renderer.render(_make_result())
    assert "<!DOCTYPE html>" in html


def test_renderer_contains_topic():
    renderer = UserRankHTMLRenderer()
    html = renderer.render(_make_result("rust"))
    assert "rust" in html


def test_renderer_contains_contributor_usernames():
    renderer = UserRankHTMLRenderer()
    html = renderer.render(_make_result())
    assert "user0" in html
    assert "user1" in html


def test_renderer_contains_top_scorer_spotlight():
    renderer = UserRankHTMLRenderer()
    html = renderer.render(_make_result())
    assert "Top Scorer" in html
    assert "user0" in html


def test_renderer_contains_grade_distribution():
    renderer = UserRankHTMLRenderer()
    html = renderer.render(_make_result())
    # Grade distribution section
    assert "dist-bar" in html or "Grade Distribution" in html.replace("-", " ")


def test_renderer_dark_theme():
    renderer = UserRankHTMLRenderer()
    html = renderer.render(_make_result())
    assert "#0d1117" in html or "#161b22" in html


def test_renderer_contains_mean_score():
    renderer = UserRankHTMLRenderer()
    html = renderer.render(_make_result())
    assert "80.0" in html or "80" in html


def test_grade_color_returns_string():
    assert isinstance(_grade_color("A"), str)
    assert isinstance(_grade_color("D"), str)


def test_grade_color_a_is_green():
    color = _grade_color("A")
    assert color == "#3fb950"


def test_renderer_empty_contributors():
    renderer = UserRankHTMLRenderer()
    result = UserRankResult(
        topic="empty",
        contributors=[],
        top_scorer="",
        mean_score=0.0,
        grade_distribution={"A": 0, "B": 0, "C": 0, "D": 0},
        timestamp="2026-03-20 00:00 UTC",
    )
    html = renderer.render(result)
    assert "empty" in html
    assert isinstance(html, str)
