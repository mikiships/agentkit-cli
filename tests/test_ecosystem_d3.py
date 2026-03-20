"""D3 tests for EcosystemHTMLRenderer."""
from __future__ import annotations

import pytest

from agentkit_cli.engines.ecosystem import EcosystemResult, LANG_EMOJI
from agentkit_cli.engines.topic_league import (
    TopicLeagueResult, LeagueResult, ScoreDistribution
)
from agentkit_cli.renderers.ecosystem_html import EcosystemHTMLRenderer
from agentkit_cli.topic_rank import TopicRankEntry, TopicRankResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_eco_result(topics=None, scores=None, preset="default"):
    if topics is None:
        topics = ["python", "rust", "go", "java", "typescript"]
    if scores is None:
        scores = [80.0, 75.0, 70.0, 65.0, 60.0]
    standings = []
    topic_results = {}
    for i, (t, s) in enumerate(zip(topics, scores), 1):
        dist = ScoreDistribution(min_score=s - 5, mean_score=s, max_score=s + 5)
        grade = "A" if s >= 80 else "B" if s >= 60 else "C"
        standings.append(LeagueResult(rank=i, topic=t, score=s, repo_count=3,
                                      top_repo=f"org/{t}-kit", score_distribution=dist, grade=grade))
        entry = TopicRankEntry(rank=1, repo_full_name=f"org/{t}-kit", score=s,
                               grade=grade, stars=500, description="")
        topic_results[t] = TopicRankResult(
            topic=t, entries=[entry], generated_at="2026-01-01", total_analyzed=1
        )
    lr = TopicLeagueResult(topics=topics, standings=standings,
                           topic_results=topic_results, timestamp="2026-01-01 00:00 UTC")
    return EcosystemResult(preset=preset, topics=topics, standings=standings,
                           league_result=lr, timestamp="2026-01-01 00:00 UTC")


# ---------------------------------------------------------------------------
# Renderer tests
# ---------------------------------------------------------------------------

def test_render_returns_string():
    eco = _make_eco_result()
    renderer = EcosystemHTMLRenderer()
    html = renderer.render(eco)
    assert isinstance(html, str)
    assert len(html) > 500


def test_render_has_doctype():
    eco = _make_eco_result()
    html = EcosystemHTMLRenderer().render(eco)
    assert html.strip().startswith("<!DOCTYPE html>")


def test_render_has_title():
    eco = _make_eco_result()
    html = EcosystemHTMLRenderer().render(eco)
    assert "State of AI Agent Readiness" in html


def test_render_has_winner_banner():
    eco = _make_eco_result()
    html = EcosystemHTMLRenderer().render(eco)
    assert "winner-banner" in html
    assert "python" in html  # highest score


def test_render_has_standings_table():
    eco = _make_eco_result()
    html = EcosystemHTMLRenderer().render(eco)
    assert "standings-table" in html
    assert "rust" in html


def test_render_has_detail_cards():
    eco = _make_eco_result()
    html = EcosystemHTMLRenderer().render(eco)
    assert "detail-card" in html


def test_render_has_insight_panel():
    eco = _make_eco_result()
    html = EcosystemHTMLRenderer().render(eco)
    assert "insight-panel" in html
    assert "Closest to Agent-Ready" in html


def test_render_has_footer_version():
    eco = _make_eco_result()
    html = EcosystemHTMLRenderer().render(eco)
    assert "agentkit-cli" in html


def test_render_lang_emojis():
    eco = _make_eco_result()
    html = EcosystemHTMLRenderer().render(eco)
    assert "🐍" in html  # python
    assert "🦀" in html  # rust


def test_render_grade_pills():
    eco = _make_eco_result()
    html = EcosystemHTMLRenderer().render(eco)
    assert "grade-pill" in html


def test_render_custom_timestamp():
    eco = _make_eco_result()
    html = EcosystemHTMLRenderer().render(eco, timestamp="2099-01-01 00:00 UTC")
    assert "2099-01-01" in html


def test_render_no_winner_content_empty_standings():
    lr = TopicLeagueResult(topics=[], standings=[], topic_results={}, timestamp="")
    eco = EcosystemResult(preset="custom", topics=[], standings=[], league_result=lr)
    html = EcosystemHTMLRenderer().render(eco)
    # With no standings, the winner-banner div should not be rendered
    assert '<div class="winner-banner">' not in html
