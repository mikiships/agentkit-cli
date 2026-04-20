"""Tests for D3 — Tweet text is NOT "both score 100/100" for ruff vs pylint (≥8 tests).

Verifies:
- _build_tweet_text produces real score differences
- Tweet text for ruff vs pylint does NOT say "both score 100/100"
- Tweet text shows winner clearly when score diff > 5
- DailyDuelEngine with existing mode produces non-draw tweet
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from agentkit_cli.daily_duel import (
    DailyDuelEngine,
    _build_tweet_text,
)


# ---------------------------------------------------------------------------
# D3: _build_tweet_text with real score differences
# ---------------------------------------------------------------------------

def test_tweet_text_shows_winner_not_draw():
    tweet = _build_tweet_text(
        repo1="astral-sh/ruff",
        repo2="PyCQA/pylint",
        repo1_score=78.0,
        repo2_score=42.0,
        repo1_grade="A",
        repo2_grade="C",
        winner="repo1",
        n_dims=4,
        winner_wins=3,
        pair_category="devtools",
        seed="2026-03-21",
    )
    assert "100/100" not in tweet
    assert "draw" not in tweet.lower()


def test_tweet_text_not_both_100():
    tweet = _build_tweet_text(
        repo1="astral-sh/ruff",
        repo2="PyCQA/pylint",
        repo1_score=80.0,
        repo2_score=45.0,
        repo1_grade="A",
        repo2_grade="C",
        winner="repo1",
        n_dims=4,
        winner_wins=4,
        pair_category="devtools",
        seed="ruff-pylint-test",
    )
    assert "both score" not in tweet.lower()
    assert "100/100" not in tweet


def test_tweet_text_shows_ruff_winning():
    tweet = _build_tweet_text(
        repo1="astral-sh/ruff",
        repo2="PyCQA/pylint",
        repo1_score=85.0,
        repo2_score=40.0,
        repo1_grade="A",
        repo2_grade="C",
        winner="repo1",
        n_dims=4,
        winner_wins=4,
        pair_category="devtools",
        seed="test-ruff-wins",
    )
    # Should mention ruff (or winner score)
    assert "85" in tweet or "ruff" in tweet.lower()


def test_tweet_text_shows_score_diff_large():
    tweet = _build_tweet_text(
        repo1="astral-sh/ruff",
        repo2="PyCQA/pylint",
        repo1_score=90.0,
        repo2_score=45.0,
        repo1_grade="A",
        repo2_grade="C",
        winner="repo1",
        n_dims=4,
        winner_wins=4,
        pair_category="devtools",
        seed="big-diff-test",
    )
    assert "100/100" not in tweet
    # Should mention both scores
    assert "90" in tweet or "45" in tweet


def test_tweet_text_near_draw_not_100():
    """Near-draw (diff <= 5) should NOT say 100/100."""
    tweet = _build_tweet_text(
        repo1="astral-sh/ruff",
        repo2="PyCQA/pylint",
        repo1_score=72.0,
        repo2_score=70.0,
        repo1_grade="B",
        repo2_grade="B",
        winner="repo1",
        n_dims=4,
        winner_wins=2,
        pair_category="devtools",
        seed="near-draw-test",
    )
    assert "100/100" not in tweet


def test_daily_duel_engine_existing_mode_tweet_not_100(monkeypatch):
    """Full DailyDuelEngine with existing mode should not produce 100/100 tweet."""
    def fake_factory(target, timeout):
        score = 78.0 if "ruff" in target else 40.0
        r = MagicMock()
        r.composite_score = score
        r.grade = "A" if score > 60 else "D"
        r.tools = {}
        return r

    engine = DailyDuelEngine(existing=True, _analyze_factory=fake_factory)
    with patch("agentkit_cli.daily_duel._write_latest_json"):
        result = engine.run_daily_duel(seed="2026-03-21")
    assert "100/100" not in result.tweet_text
    assert "both score" not in result.tweet_text.lower()


def test_daily_duel_existing_mode_tweet_shows_winner():
    """Tweet should name a winner, not say draw."""
    def fake_factory(target, timeout):
        score = 75.0 if "ruff" in target else 35.0
        r = MagicMock()
        r.composite_score = score
        r.grade = "B" if score > 50 else "D"
        r.tools = {}
        return r

    engine = DailyDuelEngine(existing=True, _analyze_factory=fake_factory)
    with patch("agentkit_cli.daily_duel._write_latest_json"):
        result = engine.run_daily_duel(seed="2026-03-21")
    assert result.winner != "draw"
    assert "draw of champions" not in result.tweet_text


def test_tweet_text_fits_twitter_limit():
    """Tweet text should be ≤280 characters."""
    tweet = _build_tweet_text(
        repo1="astral-sh/ruff",
        repo2="PyCQA/pylint",
        repo1_score=88.0,
        repo2_score=44.0,
        repo1_grade="A",
        repo2_grade="C",
        winner="repo1",
        n_dims=4,
        winner_wins=4,
        pair_category="devtools",
        seed="length-test-seed",
    )
    assert len(tweet) <= 280
