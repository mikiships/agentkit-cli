"""Tests for DailyDuelEngine (D1) — preset pairs, pick_pair, run_daily_duel, JSON output."""
from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from agentkit_cli.daily_duel import (
    PRESET_PAIRS,
    DailyDuelEngine,
    DailyDuelResult,
    _write_latest_json,
)
from agentkit_cli.repo_duel import DimensionResult, RepoDuelResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_analyze_result(score: float = 75.0, grade: str = "B"):
    ar = MagicMock()
    ar.composite_score = score
    ar.grade = grade
    ar.tools = {}
    return ar


def _make_analyze_factory(score1=75.0, grade1="B", score2=60.0, grade2="C"):
    calls = []

    def factory(target, timeout):
        if len(calls) == 0:
            calls.append(target)
            return _make_analyze_result(score1, grade1)
        else:
            calls.append(target)
            return _make_analyze_result(score2, grade2)

    return factory


# ---------------------------------------------------------------------------
# Preset pairs
# ---------------------------------------------------------------------------

def test_preset_pairs_count():
    assert len(PRESET_PAIRS) >= 20


def test_preset_pairs_structure():
    for item in PRESET_PAIRS:
        assert len(item) == 3, f"Expected (repo1, repo2, category) but got {item}"
        repo1, repo2, category = item
        assert "/" in repo1, f"repo1 missing slash: {repo1}"
        assert "/" in repo2, f"repo2 missing slash: {repo2}"
        assert len(category) > 0


def test_preset_pairs_categories():
    categories = {p[2] for p in PRESET_PAIRS}
    assert "web-frameworks" in categories
    assert "http-clients" in categories
    assert "ml-ai" in categories
    assert "devtools" in categories


def test_preset_pairs_no_duplicates():
    seen = set()
    for repo1, repo2, _ in PRESET_PAIRS:
        key = frozenset([repo1, repo2])
        assert key not in seen, f"Duplicate pair: {repo1} vs {repo2}"
        seen.add(key)


# ---------------------------------------------------------------------------
# pick_pair
# ---------------------------------------------------------------------------

def test_pick_pair_default_is_deterministic():
    engine = DailyDuelEngine()
    r1 = engine.pick_pair()
    r2 = engine.pick_pair()
    assert r1 == r2


def test_pick_pair_same_seed_same_result():
    engine = DailyDuelEngine()
    r1 = engine.pick_pair(seed="2026-01-01")
    r2 = engine.pick_pair(seed="2026-01-01")
    assert r1 == r2


def test_pick_pair_different_seeds_may_differ():
    engine = DailyDuelEngine()
    results = {engine.pick_pair(seed=f"2026-01-{d:02d}") for d in range(1, 8)}
    # Not all 7 days need different pairs but at least the function accepts varied seeds
    assert all(len(r) == 3 for r in results)


def test_pick_pair_returns_preset_triple():
    engine = DailyDuelEngine()
    result = engine.pick_pair(seed="test-seed")
    assert result in PRESET_PAIRS


def test_pick_pair_today_seed_is_isoformat():
    """Default seed should yield the same result as today's date."""
    engine = DailyDuelEngine()
    today = date.today().isoformat()
    assert engine.pick_pair() == engine.pick_pair(seed=today)


# ---------------------------------------------------------------------------
# DailyDuelResult
# ---------------------------------------------------------------------------

def test_daily_duel_result_extends_repo_duel_result():
    result = DailyDuelResult(
        repo1="a/b",
        repo2="c/d",
        repo1_score=80.0,
        repo2_score=70.0,
        repo1_grade="B",
        repo2_grade="C",
    )
    assert isinstance(result, RepoDuelResult)
    assert result.tweet_text == ""
    assert result.pair_category == ""
    assert result.seed == ""


def test_daily_duel_result_to_dict():
    result = DailyDuelResult(
        repo1="a/b",
        repo2="c/d",
        repo1_score=80.0,
        repo2_score=70.0,
        repo1_grade="B",
        repo2_grade="C",
        tweet_text="hello",
        pair_category="web-frameworks",
        seed="2026-01-01",
    )
    d = result.to_dict()
    assert d["tweet_text"] == "hello"
    assert d["pair_category"] == "web-frameworks"
    assert d["seed"] == "2026-01-01"
    assert "repo1" in d
    assert "repo2" in d


# ---------------------------------------------------------------------------
# run_daily_duel
# ---------------------------------------------------------------------------

def test_run_daily_duel_returns_daily_duel_result():
    engine = DailyDuelEngine(_analyze_factory=_make_analyze_factory())
    with patch("agentkit_cli.daily_duel._write_latest_json"):
        result = engine.run_daily_duel(seed="2026-01-01")
    assert isinstance(result, DailyDuelResult)


def test_run_daily_duel_tweet_text_within_280():
    engine = DailyDuelEngine(_analyze_factory=_make_analyze_factory())
    with patch("agentkit_cli.daily_duel._write_latest_json"):
        result = engine.run_daily_duel(seed="2026-01-01")
    assert len(result.tweet_text) <= 280


def test_run_daily_duel_has_seed():
    engine = DailyDuelEngine(_analyze_factory=_make_analyze_factory())
    with patch("agentkit_cli.daily_duel._write_latest_json"):
        result = engine.run_daily_duel(seed="custom-seed")
    assert result.seed == "custom-seed"


def test_run_daily_duel_has_pair_category():
    engine = DailyDuelEngine(_analyze_factory=_make_analyze_factory())
    with patch("agentkit_cli.daily_duel._write_latest_json"):
        result = engine.run_daily_duel(seed="2026-01-01")
    assert result.pair_category != ""


def test_run_daily_duel_tweet_text_contains_repos():
    engine = DailyDuelEngine(_analyze_factory=_make_analyze_factory())
    with patch("agentkit_cli.daily_duel._write_latest_json"):
        result = engine.run_daily_duel(seed="2026-01-01")
    assert result.repo1 in result.tweet_text or result.repo2 in result.tweet_text


def test_run_daily_duel_default_seed_is_today():
    engine = DailyDuelEngine(_analyze_factory=_make_analyze_factory())
    with patch("agentkit_cli.daily_duel._write_latest_json"):
        result = engine.run_daily_duel()
    assert result.seed == date.today().isoformat()


# ---------------------------------------------------------------------------
# JSON output file
# ---------------------------------------------------------------------------

def test_write_latest_json_creates_file(tmp_path):
    result = DailyDuelResult(
        repo1="a/b",
        repo2="c/d",
        repo1_score=80.0,
        repo2_score=70.0,
        repo1_grade="B",
        repo2_grade="C",
        tweet_text="test tweet",
        pair_category="web-frameworks",
        seed="2026-01-01",
    )
    target = tmp_path / "daily-duel-latest.json"
    _write_latest_json(result, path=target)
    assert target.exists()
    data = json.loads(target.read_text())
    assert data["tweet_text"] == "test tweet"
    assert data["repo1"] == "a/b"


def test_run_daily_duel_writes_json(tmp_path):
    target = tmp_path / "daily-duel-latest.json"
    engine = DailyDuelEngine(_analyze_factory=_make_analyze_factory())
    with patch("agentkit_cli.daily_duel._LATEST_JSON", target):
        result = engine.run_daily_duel(seed="2026-01-01")
    assert target.exists()
    data = json.loads(target.read_text())
    assert "tweet_text" in data


def test_write_latest_json_atomic(tmp_path):
    """Verify the file is fully written (atomic replace semantics)."""
    result = DailyDuelResult(
        repo1="x/y",
        repo2="z/w",
        repo1_score=50.0,
        repo2_score=60.0,
        repo1_grade="C",
        repo2_grade="B",
        tweet_text="atomic test",
        pair_category="devtools",
        seed="2026-01-02",
    )
    target = tmp_path / "latest.json"
    _write_latest_json(result, path=target)
    raw = target.read_text()
    # Should be valid JSON (atomic write completed)
    parsed = json.loads(raw)
    assert parsed["seed"] == "2026-01-02"


# ---------------------------------------------------------------------------
# calendar
# ---------------------------------------------------------------------------

def test_calendar_returns_7_days():
    engine = DailyDuelEngine()
    schedule = engine.calendar(days=7)
    assert len(schedule) == 7


def test_calendar_entries_have_required_keys():
    engine = DailyDuelEngine()
    schedule = engine.calendar(days=3)
    for entry in schedule:
        assert "date" in entry
        assert "repo1" in entry
        assert "repo2" in entry
        assert "category" in entry
