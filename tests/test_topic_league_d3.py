"""D3 tests for TopicLeagueHTMLRenderer."""
from __future__ import annotations

import pytest

from agentkit_cli.renderers.topic_league_html import TopicLeagueHTMLRenderer, _grade_color, _score_bar_width
from agentkit_cli.engines.topic_league import TopicLeagueResult, LeagueResult, ScoreDistribution
from agentkit_cli.topic_rank import TopicRankEntry, TopicRankResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _entry(rank, name, score, grade="B", stars=10):
    return TopicRankEntry(rank=rank, repo_full_name=name, score=score, grade=grade, stars=stars)


def _mock_topic_result(topic, scores):
    entries = [_entry(i + 1, f"{topic}/repo{i}", s, "A" if s >= 80 else "B") for i, s in enumerate(scores)]
    return TopicRankResult(topic=topic, entries=entries, generated_at="", total_analyzed=len(entries))


def _make_result(topics_scores):
    """topics_scores: dict of topic -> [scores]"""
    standings = []
    topic_results = {}
    for rank, (topic, scores) in enumerate(topics_scores.items(), 1):
        tr = _mock_topic_result(topic, scores)
        topic_results[topic] = tr
        mean = sum(scores) / len(scores) if scores else 0.0
        dist = ScoreDistribution(min(scores) if scores else 0, mean, max(scores) if scores else 0)
        grade = "A" if mean >= 80 else "B" if mean >= 65 else "C"
        standings.append(LeagueResult(
            rank=rank,
            topic=topic,
            score=round(mean, 2),
            repo_count=len(scores),
            top_repo=f"{topic}/repo0",
            score_distribution=dist,
            grade=grade,
        ))
    return TopicLeagueResult(
        topics=list(topics_scores.keys()),
        standings=standings,
        topic_results=topic_results,
        timestamp="2026-01-01 00:00 UTC",
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_grade_color_a():
    assert _grade_color("A") == "#3fb950"


def test_grade_color_b():
    assert _grade_color("B") == "#58a6ff"


def test_grade_color_unknown():
    assert _grade_color("Z") == "#8b949e"


def test_score_bar_width_full():
    assert _score_bar_width(100.0) == 100


def test_score_bar_width_zero():
    assert _score_bar_width(0.0) == 0


def test_score_bar_width_half():
    assert _score_bar_width(50.0) == 50


def test_render_returns_html():
    result = _make_result({"python": [80.0, 70.0], "rust": [60.0]})
    html = TopicLeagueHTMLRenderer().render(result)
    assert "<!DOCTYPE html>" in html
    assert "<html" in html
    assert "</html>" in html


def test_render_contains_topics():
    result = _make_result({"python": [80.0], "rust": [70.0], "go": [65.0]})
    html = TopicLeagueHTMLRenderer().render(result)
    assert "python" in html
    assert "rust" in html
    assert "go" in html


def test_render_contains_standings_header():
    result = _make_result({"python": [80.0], "rust": [70.0]})
    html = TopicLeagueHTMLRenderer().render(result)
    assert "Standings" in html or "standings" in html.lower()


def test_render_contains_scores():
    result = _make_result({"python": [80.0], "rust": [60.0]})
    html = TopicLeagueHTMLRenderer().render(result)
    assert "80.0" in html
    assert "60.0" in html


def test_render_contains_repo_links():
    result = _make_result({"python": [80.0]})
    html = TopicLeagueHTMLRenderer().render(result)
    assert "github.com" in html


def test_render_contains_grade_pills():
    result = _make_result({"python": [90.0], "rust": [50.0]})
    html = TopicLeagueHTMLRenderer().render(result)
    assert "grade-pill" in html


def test_render_contains_footer():
    result = _make_result({"python": [80.0], "rust": [70.0]})
    html = TopicLeagueHTMLRenderer().render(result)
    assert "agentkit-cli" in html
    assert "footer" in html


def test_render_dark_theme():
    result = _make_result({"python": [80.0], "rust": [70.0]})
    html = TopicLeagueHTMLRenderer().render(result)
    assert "#0d1117" in html  # dark background


def test_render_custom_timestamp():
    result = _make_result({"python": [80.0], "rust": [70.0]})
    html = TopicLeagueHTMLRenderer().render(result, timestamp="2030-01-01 12:00 UTC")
    assert "2030-01-01" in html
