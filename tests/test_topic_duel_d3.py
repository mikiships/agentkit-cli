"""D3 tests for TopicDuelHTMLRenderer."""
from __future__ import annotations

import pytest

from agentkit_cli.engines.topic_duel import TopicDuelResult, TopicDuelDimension
from agentkit_cli.topic_rank import TopicRankEntry, TopicRankResult
from agentkit_cli.topic_duel_html import render_topic_duel_html


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _entry(rank, name, score, grade="B", stars=50):
    return TopicRankEntry(rank=rank, repo_full_name=name, score=score, grade=grade, stars=stars)


def _rank_result(topic, entries):
    return TopicRankResult(topic=topic, entries=entries, generated_at="2026-01-01", total_analyzed=len(entries))


def _duel_result(t1="fastapi", t2="django", winner="topic1", avg1=75.0, avg2=60.0):
    e1 = [_entry(1, f"{t1}/repo_a", avg1, "B"), _entry(2, f"{t1}/repo_b", avg1 - 5, "B")]
    e2 = [_entry(1, f"{t2}/repo_a", avg2, "C"), _entry(2, f"{t2}/repo_b", avg2 - 5, "C")]
    dims = [
        TopicDuelDimension("avg_score", avg1, avg2, winner),
        TopicDuelDimension("top_score", avg1, avg2, winner),
    ]
    return TopicDuelResult(
        topic1=t1,
        topic2=t2,
        topic1_result=_rank_result(t1, e1),
        topic2_result=_rank_result(t2, e2),
        dimensions=dims,
        overall_winner=winner,
        topic1_avg_score=avg1,
        topic2_avg_score=avg2,
        timestamp="2026-01-01 00:00 UTC",
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_render_returns_string():
    result = _duel_result()
    html = render_topic_duel_html(result)
    assert isinstance(html, str)
    assert len(html) > 500


def test_render_contains_topic_names():
    result = _duel_result("langchain", "llamaindex")
    html = render_topic_duel_html(result)
    assert "langchain" in html
    assert "llamaindex" in html


def test_render_winner_banner_topic1():
    result = _duel_result(winner="topic1", avg1=80.0, avg2=55.0)
    html = render_topic_duel_html(result)
    assert "fastapi wins" in html


def test_render_winner_banner_topic2():
    result = _duel_result(winner="topic2", avg1=55.0, avg2=80.0)
    html = render_topic_duel_html(result)
    assert "django wins" in html


def test_render_tie_banner():
    result = _duel_result(winner="tie", avg1=70.0, avg2=70.0)
    html = render_topic_duel_html(result)
    assert "Tie" in html or "tie" in html.lower()


def test_render_dark_theme_palette():
    result = _duel_result()
    html = render_topic_duel_html(result)
    assert "#0d1117" in html  # dark background
    assert "#161b22" in html  # card background
    assert "#58a6ff" in html  # accent color


def test_render_repo_links():
    result = _duel_result()
    html = render_topic_duel_html(result)
    assert "https://github.com/fastapi/repo_a" in html
    assert "https://github.com/django/repo_a" in html


def test_render_grade_colors():
    result = _duel_result()
    html = render_topic_duel_html(result)
    # Grade B color
    assert "#58a6ff" in html
