"""D3 tests — TopicRankHTMLRenderer."""
from __future__ import annotations

import pytest
from agentkit_cli.topic_rank import TopicRankEntry, TopicRankResult
from agentkit_cli.topic_rank_html import TopicRankHTMLRenderer, _grade_color, _score_to_grade


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_result(n: int = 3, topic: str = "python") -> TopicRankResult:
    entries = [
        TopicRankEntry(
            rank=i + 1,
            repo_full_name=f"owner/repo-{i}",
            score=round(85.0 - i * 10, 1),
            grade="A" if i == 0 else ("B" if i == 1 else "C"),
            stars=1000 - i * 100,
            description=f"Repo description {i}",
        )
        for i in range(n)
    ]
    return TopicRankResult(
        topic=topic,
        entries=entries,
        generated_at="2026-03-20 00:00 UTC",
        total_analyzed=n,
    )


renderer = TopicRankHTMLRenderer()


# ---------------------------------------------------------------------------
# Grade color helpers
# ---------------------------------------------------------------------------


def test_grade_color_A():
    assert _grade_color("A") == "#3fb950"


def test_grade_color_B():
    assert _grade_color("B") == "#58a6ff"


def test_grade_color_C():
    assert _grade_color("C") == "#d29922"


def test_grade_color_D():
    assert _grade_color("D") == "#f85149"


def test_grade_color_unknown():
    color = _grade_color("Z")
    assert color.startswith("#")


def test_score_to_grade_A():
    assert _score_to_grade(85.0) == "A"


def test_score_to_grade_B():
    assert _score_to_grade(70.0) == "B"


def test_score_to_grade_C():
    assert _score_to_grade(55.0) == "C"


def test_score_to_grade_D():
    assert _score_to_grade(40.0) == "D"


# ---------------------------------------------------------------------------
# HTML rendering
# ---------------------------------------------------------------------------


def test_render_returns_string():
    result = _make_result()
    html = renderer.render(result)
    assert isinstance(html, str)


def test_render_has_doctype():
    result = _make_result()
    html = renderer.render(result)
    assert "<!DOCTYPE html>" in html


def test_render_contains_topic():
    result = _make_result(topic="agents")
    html = renderer.render(result)
    assert "agents" in html


def test_render_contains_repo_names():
    result = _make_result(n=2)
    html = renderer.render(result)
    assert "owner/repo-0" in html
    assert "owner/repo-1" in html


def test_render_contains_scores():
    result = _make_result(n=2)
    html = renderer.render(result)
    assert "85.0" in html


def test_render_contains_grade_badges():
    result = _make_result(n=2)
    html = renderer.render(result)
    assert "grade-pill" in html


def test_render_top_scorer_spotlight():
    result = _make_result(n=3)
    html = renderer.render(result)
    assert "Top Repo" in html
    assert "owner/repo-0" in html


def test_render_grade_distribution_bars():
    result = _make_result(n=3)
    html = renderer.render(result)
    assert "dist-bar" in html


def test_render_custom_timestamp():
    result = _make_result()
    html = renderer.render(result, timestamp="2099-01-01 00:00 UTC")
    assert "2099-01-01" in html


def test_render_empty_entries():
    result = TopicRankResult(topic="empty", entries=[], generated_at="ts", total_analyzed=0)
    html = renderer.render(result)
    assert "<!DOCTYPE html>" in html
    assert "empty" in html


def test_render_contains_agentkit_footer():
    result = _make_result()
    html = renderer.render(result)
    assert "agentkit-cli" in html


def test_render_dark_background():
    result = _make_result()
    html = renderer.render(result)
    assert "#0d1117" in html


def test_render_repo_links():
    result = _make_result(n=1)
    html = renderer.render(result)
    assert "https://github.com/owner/repo-0" in html
