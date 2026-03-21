"""Tests for D1 — improved tweet_text generation for draws, near-draws, and winners."""
from __future__ import annotations

import pytest

from agentkit_cli.daily_duel import (
    CATEGORY_INSIGHTS,
    _build_tweet_text,
    _category_insight,
    _DEFAULT_INSIGHTS,
)


# ---------------------------------------------------------------------------
# CATEGORY_INSIGHTS structure
# ---------------------------------------------------------------------------

def test_category_insights_has_required_categories():
    required = {"web-frameworks", "devtools", "ml-ai", "databases"}
    assert required.issubset(set(CATEGORY_INSIGHTS.keys()))


def test_category_insights_each_has_multiple_phrases():
    for cat, phrases in CATEGORY_INSIGHTS.items():
        assert len(phrases) >= 3, f"{cat} has fewer than 3 phrases"


# ---------------------------------------------------------------------------
# _category_insight determinism
# ---------------------------------------------------------------------------

def test_category_insight_is_deterministic():
    result1 = _category_insight("web-frameworks", "2026-03-21")
    result2 = _category_insight("web-frameworks", "2026-03-21")
    assert result1 == result2


def test_category_insight_varies_by_seed():
    results = {_category_insight("devtools", str(i)) for i in range(20)}
    # At least 2 distinct phrases should appear across 20 seeds
    assert len(results) >= 2


def test_category_insight_unknown_category_uses_default():
    phrase = _category_insight("unknown-category-xyz", "seed-abc")
    assert phrase in _DEFAULT_INSIGHTS


# ---------------------------------------------------------------------------
# Draw case
# ---------------------------------------------------------------------------

def test_draw_tweet_no_boring_draw_language():
    text = _build_tweet_text(
        repo1="expressjs/express",
        repo2="fastify/fastify",
        repo1_score=100,
        repo2_score=100,
        repo1_grade="A",
        repo2_grade="A",
        winner="draw",
        n_dims=4,
        winner_wins=0,
        pair_category="web-frameworks",
        seed="2026-03-21",
    )
    assert "draw on 0/4 dimensions" not in text
    assert "Winner:" not in text


def test_draw_tweet_contains_both_repos():
    text = _build_tweet_text(
        repo1="expressjs/express",
        repo2="fastify/fastify",
        repo1_score=100,
        repo2_score=100,
        repo1_grade="A",
        repo2_grade="A",
        winner="draw",
        n_dims=4,
        winner_wins=0,
        pair_category="web-frameworks",
        seed="2026-03-21",
    )
    assert "expressjs/express" in text
    assert "fastify/fastify" in text


def test_draw_tweet_contains_category_insight():
    cat = "web-frameworks"
    seed = "2026-03-21"
    insight = _category_insight(cat, seed)
    text = _build_tweet_text(
        repo1="expressjs/express",
        repo2="fastify/fastify",
        repo1_score=100,
        repo2_score=100,
        repo1_grade="A",
        repo2_grade="A",
        winner="draw",
        n_dims=4,
        winner_wins=0,
        pair_category=cat,
        seed=seed,
    )
    assert insight in text


def test_draw_tweet_within_280_chars():
    text = _build_tweet_text(
        repo1="a-very-long-org-name/a-very-long-repo-name",
        repo2="another-long-org/another-long-repo-name",
        repo1_score=100,
        repo2_score=100,
        repo1_grade="A",
        repo2_grade="A",
        winner="draw",
        n_dims=4,
        winner_wins=0,
        pair_category="web-frameworks",
        seed="2026-03-21",
    )
    assert len(text) <= 280


# ---------------------------------------------------------------------------
# Near-draw case (score_diff <= 5)
# ---------------------------------------------------------------------------

def test_near_draw_tweet_leads_with_margin():
    text = _build_tweet_text(
        repo1="django/django",
        repo2="tiangolo/fastapi",
        repo1_score=98,
        repo2_score=95,
        repo1_grade="A",
        repo2_grade="A",
        winner="repo1",
        n_dims=4,
        winner_wins=3,
        pair_category="web-frameworks",
        seed="2026-03-21",
    )
    assert "extremely close" in text
    assert "3 point" in text


def test_near_draw_tweet_names_winner():
    text = _build_tweet_text(
        repo1="django/django",
        repo2="tiangolo/fastapi",
        repo1_score=98,
        repo2_score=95,
        repo1_grade="A",
        repo2_grade="A",
        winner="repo1",
        n_dims=4,
        winner_wins=3,
        pair_category="web-frameworks",
        seed="2026-03-21",
    )
    assert "django" in text.lower()


def test_near_draw_tweet_within_280():
    text = _build_tweet_text(
        repo1="huggingface/transformers",
        repo2="openai/openai-python",
        repo1_score=97,
        repo2_score=94,
        repo1_grade="A",
        repo2_grade="A",
        winner="repo1",
        n_dims=4,
        winner_wins=3,
        pair_category="ml-ai",
        seed="2026-03-21",
    )
    assert len(text) <= 280


# ---------------------------------------------------------------------------
# Clear winner case (score_diff > 5)
# ---------------------------------------------------------------------------

def test_clear_winner_tweet_contains_winner_label():
    text = _build_tweet_text(
        repo1="astral-sh/ruff",
        repo2="PyCQA/flake8",
        repo1_score=95,
        repo2_score=60,
        repo1_grade="A",
        repo2_grade="C",
        winner="repo1",
        n_dims=4,
        winner_wins=4,
        pair_category="devtools",
        seed="2026-03-21",
    )
    assert "Winner:" in text
    assert "astral-sh/ruff" in text


def test_clear_winner_tweet_within_280():
    text = _build_tweet_text(
        repo1="astral-sh/ruff",
        repo2="PyCQA/flake8",
        repo1_score=95,
        repo2_score=60,
        repo1_grade="A",
        repo2_grade="C",
        winner="repo1",
        n_dims=4,
        winner_wins=4,
        pair_category="devtools",
        seed="2026-03-21",
    )
    assert len(text) <= 280


# ---------------------------------------------------------------------------
# Truncation
# ---------------------------------------------------------------------------

def test_tweet_truncated_at_280():
    text = _build_tweet_text(
        repo1="x" * 60 + "/y",
        repo2="z" * 60 + "/w",
        repo1_score=100,
        repo2_score=100,
        repo1_grade="A",
        repo2_grade="A",
        winner="draw",
        n_dims=4,
        winner_wins=0,
        pair_category="web-frameworks",
        seed="seed",
    )
    assert len(text) <= 280
