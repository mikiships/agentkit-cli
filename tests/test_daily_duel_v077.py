"""Tests for agentkit-cli v0.77.0 daily-duel features:
- Asymmetric pairs
- _diff_tier helper
- Narrative tweet templates (large/medium diff)
- PRESET_PAIRS structure (4-tuple)
- Calendar narrative_type column
- DailyDuelResult.narrative_type field
"""
from __future__ import annotations

import json
from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from agentkit_cli.daily_duel import (
    ASYMMETRIC_PAIRS,
    BALANCED_PAIRS,
    PRESET_PAIRS,
    DailyDuelEngine,
    DailyDuelResult,
    _build_tweet_text,
    _diff_tier,
    _pick_template,
    _LARGE_DIFF_TEMPLATES,
    _MEDIUM_DIFF_TEMPLATES,
)
from agentkit_cli.main import app
import re

runner = CliRunner()


# ---------------------------------------------------------------------------
# _diff_tier
# ---------------------------------------------------------------------------

def test_diff_tier_large():
    assert _diff_tier(31) == "large"
    assert _diff_tier(50) == "large"
    assert _diff_tier(100) == "large"


def test_diff_tier_medium():
    assert _diff_tier(15) == "medium"
    assert _diff_tier(20) == "medium"
    assert _diff_tier(30) == "medium"


def test_diff_tier_small():
    assert _diff_tier(14) == "small"
    assert _diff_tier(5) == "small"
    assert _diff_tier(1) == "small"


def test_diff_tier_boundary_medium_large():
    assert _diff_tier(30) == "medium"
    assert _diff_tier(30.1) == "large"


def test_diff_tier_boundary_small_medium():
    assert _diff_tier(14.9) == "small"
    assert _diff_tier(15) == "medium"


# ---------------------------------------------------------------------------
# PRESET_PAIRS 4-tuple structure
# ---------------------------------------------------------------------------

def test_preset_pairs_all_four_tuple():
    for item in PRESET_PAIRS:
        assert len(item) == 4, f"Expected 4-tuple but got {len(item)}-tuple: {item}"


def test_preset_pairs_narrative_type_valid():
    valid = {"asymmetric", "balanced"}
    for r1, r2, cat, nt in PRESET_PAIRS:
        assert nt in valid, f"Invalid narrative_type '{nt}' for {r1} vs {r2}"


def test_preset_pairs_count_gte_42():
    assert len(PRESET_PAIRS) >= 42, f"Expected >=42 pairs, got {len(PRESET_PAIRS)}"


def test_asymmetric_pairs_count_gte_20():
    assert len(ASYMMETRIC_PAIRS) >= 20, f"Expected >=20 asymmetric pairs, got {len(ASYMMETRIC_PAIRS)}"


def test_balanced_pairs_count_gte_20():
    assert len(BALANCED_PAIRS) >= 20, f"Expected >=20 balanced pairs, got {len(BALANCED_PAIRS)}"


def test_asymmetric_pairs_all_tagged():
    for r1, r2, cat, nt in ASYMMETRIC_PAIRS:
        assert nt == "asymmetric", f"Expected 'asymmetric' for {r1} vs {r2}, got '{nt}'"


def test_balanced_pairs_all_tagged():
    for r1, r2, cat, nt in BALANCED_PAIRS:
        assert nt == "balanced", f"Expected 'balanced' for {r1} vs {r2}, got '{nt}'"


def test_preset_pairs_is_union_of_sub_lists():
    all_pairs = set(ASYMMETRIC_PAIRS) | set(BALANCED_PAIRS)
    assert set(PRESET_PAIRS) == all_pairs


def test_preset_pairs_no_duplicates():
    seen = set()
    for r1, r2, cat, nt in PRESET_PAIRS:
        key = frozenset([r1, r2])
        assert key not in seen, f"Duplicate pair: {r1} vs {r2}"
        seen.add(key)


# ---------------------------------------------------------------------------
# Specific asymmetric pairs verification (real GitHub repos)
# ---------------------------------------------------------------------------

def test_asymmetric_pair_fastapi_bottle():
    pairs = [(r1, r2) for r1, r2, cat, nt in ASYMMETRIC_PAIRS]
    assert ("tiangolo/fastapi", "bottlepy/bottle") in pairs, "fastapi vs bottle missing"


def test_asymmetric_pair_ruff_pylint():
    pairs = [(r1, r2) for r1, r2, cat, nt in ASYMMETRIC_PAIRS]
    assert ("astral-sh/ruff", "PyCQA/pylint") in pairs, "ruff vs pylint missing"


def test_asymmetric_pair_uvicorn_tornado():
    pairs = [(r1, r2) for r1, r2, cat, nt in ASYMMETRIC_PAIRS]
    assert ("encode/uvicorn", "tornadoweb/tornado") in pairs, "uvicorn vs tornado missing"


def test_asymmetric_pair_pytest_nose():
    pairs = [(r1, r2) for r1, r2, cat, nt in ASYMMETRIC_PAIRS]
    assert ("pytest-dev/pytest", "nose-devs/nose") in pairs, "pytest vs nose missing"


def test_asymmetric_pair_react_backbone():
    pairs = [(r1, r2) for r1, r2, cat, nt in ASYMMETRIC_PAIRS]
    assert ("facebook/react", "jashkenas/backbone") in pairs, "react vs backbone missing"


def test_asymmetric_pairs_have_legacy_vs_modern_coverage():
    categories = {cat for _, _, cat, _ in ASYMMETRIC_PAIRS}
    assert "web-frameworks" in categories
    assert "devtools" in categories
    assert "testing" in categories
    assert "async-networking" in categories


# ---------------------------------------------------------------------------
# Tweet templates: large diff (score_diff > 30)
# ---------------------------------------------------------------------------

def test_large_diff_tweet_not_boring():
    text = _build_tweet_text(
        repo1="tiangolo/fastapi",
        repo2="bottlepy/bottle",
        repo1_score=100,
        repo2_score=45,
        repo1_grade="A",
        repo2_grade="D",
        winner="repo1",
        n_dims=4,
        winner_wins=4,
        pair_category="web-frameworks",
        seed="test-large-diff",
    )
    assert len(text) <= 280
    # Should NOT use the old boring format
    assert "Winner:" not in text
    # Should reference both repos (short names)
    assert "fastapi" in text.lower() or "bottle" in text.lower()


def test_large_diff_tweet_within_280():
    for seed in ["seed1", "seed2", "seed3", "seed4"]:
        text = _build_tweet_text(
            repo1="tiangolo/fastapi",
            repo2="bottlepy/bottle",
            repo1_score=100,
            repo2_score=45,
            repo1_grade="A",
            repo2_grade="D",
            winner="repo1",
            n_dims=4,
            winner_wins=4,
            pair_category="web-frameworks",
            seed=seed,
        )
        assert len(text) <= 280, f"Tweet too long ({len(text)}) for seed={seed}: {text}"


def test_large_diff_all_templates_valid_length():
    """All large-diff templates must produce ≤280-char tweets."""
    for i, tmpl in enumerate(_LARGE_DIFF_TEMPLATES):
        text = tmpl.format(
            winner="fastapi", loser="bottle",
            ws=100, ls=45, ww=4, nd=4, diff=55,
        )
        assert len(text) <= 280, f"Template {i} too long: {len(text)} chars"


def test_medium_diff_all_templates_valid_length():
    """All medium-diff templates must produce ≤280-char tweets."""
    for i, tmpl in enumerate(_MEDIUM_DIFF_TEMPLATES):
        text = tmpl.format(
            winner="uvicorn", loser="tornado",
            ws=85, ls=62, ww=3, nd=4, diff=23,
        )
        assert len(text) <= 280, f"Template {i} too long: {len(text)} chars"


# ---------------------------------------------------------------------------
# Tweet templates: medium diff (15-30)
# ---------------------------------------------------------------------------

def test_medium_diff_tweet():
    text = _build_tweet_text(
        repo1="encode/uvicorn",
        repo2="tornadoweb/tornado",
        repo1_score=85,
        repo2_score=62,
        repo1_grade="A",
        repo2_grade="C",
        winner="repo1",
        n_dims=4,
        winner_wins=3,
        pair_category="async-networking",
        seed="test-medium-diff",
    )
    assert len(text) <= 280
    assert "Winner:" not in text


def test_medium_diff_tweet_within_280_multiple_seeds():
    for seed in ["alpha", "beta", "gamma", "delta"]:
        text = _build_tweet_text(
            repo1="encode/uvicorn",
            repo2="tornadoweb/tornado",
            repo1_score=85,
            repo2_score=62,
            repo1_grade="A",
            repo2_grade="C",
            winner="repo1",
            n_dims=4,
            winner_wins=3,
            pair_category="async-networking",
            seed=seed,
        )
        assert len(text) <= 280, f"Tweet too long for seed={seed}"


# ---------------------------------------------------------------------------
# Tweet templates: small diff and near-draw (unchanged behavior)
# ---------------------------------------------------------------------------

def test_small_diff_tweet_format():
    """Small diff (5-14) should still work and be ≤280."""
    text = _build_tweet_text(
        repo1="pallets/flask",
        repo2="tiangolo/fastapi",
        repo1_score=80,
        repo2_score=72,
        repo1_grade="B",
        repo2_grade="B",
        winner="repo1",
        n_dims=4,
        winner_wins=3,
        pair_category="web-frameworks",
        seed="small-diff-seed",
    )
    assert len(text) <= 280


def test_near_draw_tweet_format():
    """Near-draw (≤5) should keep existing 'extremely close' format."""
    text = _build_tweet_text(
        repo1="pallets/flask",
        repo2="tiangolo/fastapi",
        repo1_score=80,
        repo2_score=78,
        repo1_grade="B",
        repo2_grade="B",
        winner="repo1",
        n_dims=4,
        winner_wins=2,
        pair_category="web-frameworks",
        seed="near-draw-seed",
    )
    assert "extremely close" in text
    assert len(text) <= 280


def test_draw_tweet_format():
    """Draw case should still use champion framing."""
    text = _build_tweet_text(
        repo1="pallets/flask",
        repo2="tiangolo/fastapi",
        repo1_score=80,
        repo2_score=80,
        repo1_grade="B",
        repo2_grade="B",
        winner="draw",
        n_dims=4,
        winner_wins=2,
        pair_category="web-frameworks",
        seed="draw-seed",
    )
    assert "draw of champions" in text
    assert len(text) <= 280


# ---------------------------------------------------------------------------
# pick_pair_full
# ---------------------------------------------------------------------------

def test_pick_pair_full_returns_4_tuple():
    engine = DailyDuelEngine()
    result = engine.pick_pair_full(seed="test-seed")
    assert len(result) == 4
    r1, r2, cat, nt = result
    assert "/" in r1
    assert "/" in r2
    assert len(cat) > 0
    assert nt in {"asymmetric", "balanced"}


def test_pick_pair_full_deterministic():
    engine = DailyDuelEngine()
    r1 = engine.pick_pair_full(seed="fixed-seed")
    r2 = engine.pick_pair_full(seed="fixed-seed")
    assert r1 == r2


def test_pick_pair_backward_compat_3_tuple():
    """pick_pair still returns 3-tuple for backward compat."""
    engine = DailyDuelEngine()
    result = engine.pick_pair(seed="test-seed")
    assert len(result) == 3


# ---------------------------------------------------------------------------
# DailyDuelResult.narrative_type
# ---------------------------------------------------------------------------

def test_daily_duel_result_narrative_type_default():
    result = DailyDuelResult(
        repo1="a/b", repo2="c/d",
        repo1_score=80, repo2_score=70,
        repo1_grade="B", repo2_grade="C",
    )
    assert result.narrative_type == ""


def test_daily_duel_result_narrative_type_in_dict():
    result = DailyDuelResult(
        repo1="a/b", repo2="c/d",
        repo1_score=80, repo2_score=70,
        repo1_grade="B", repo2_grade="C",
        narrative_type="asymmetric",
    )
    d = result.to_dict()
    assert d["narrative_type"] == "asymmetric"


def test_run_daily_duel_sets_narrative_type():
    calls = []

    def factory(target, timeout):
        ar = MagicMock()
        if len(calls) == 0:
            ar.composite_score = 100.0
            ar.grade = "A"
        else:
            ar.composite_score = 55.0
            ar.grade = "D"
        ar.tools = {}
        calls.append(target)
        return ar

    engine = DailyDuelEngine(_analyze_factory=factory)
    with patch("agentkit_cli.daily_duel._write_latest_json"):
        result = engine.run_daily_duel(seed="2026-03-21")
    assert result.narrative_type in {"asymmetric", "balanced"}


# ---------------------------------------------------------------------------
# Calendar narrative_type
# ---------------------------------------------------------------------------

def test_calendar_has_narrative_type():
    engine = DailyDuelEngine()
    schedule = engine.calendar(days=7)
    for entry in schedule:
        assert "narrative_type" in entry, f"narrative_type missing for {entry['date']}"
        assert entry["narrative_type"] in {"asymmetric", "balanced"}


def test_calendar_json_has_narrative_type():
    with patch("agentkit_cli.commands.daily_duel_cmd.DailyDuelEngine") as mock_cls:
        mock_engine = MagicMock()
        mock_cls.return_value = mock_engine
        schedule = [
            {"date": "2026-01-01", "repo1": "a/b", "repo2": "c/d",
             "category": "web", "narrative_type": "asymmetric"},
        ]
        mock_engine.calendar.return_value = schedule
        result = runner.invoke(app, ["daily-duel", "--calendar", "--json"])
        assert result.exit_code == 0
        parsed = json.loads(result.stdout)
        assert parsed[0]["narrative_type"] == "asymmetric"


def test_calendar_table_shows_narrative_column():
    with patch("agentkit_cli.commands.daily_duel_cmd.DailyDuelEngine") as mock_cls:
        mock_engine = MagicMock()
        mock_cls.return_value = mock_engine
        schedule = [
            {"date": "2026-01-01", "repo1": "a/b", "repo2": "c/d",
             "category": "web", "narrative_type": "asymmetric"},
        ]
        mock_engine.calendar.return_value = schedule
        result = runner.invoke(app, ["daily-duel", "--calendar"])
        assert result.exit_code == 0
        assert "asymmetric" in result.stdout or "Narrative" in result.stdout


# ---------------------------------------------------------------------------
# Version
# ---------------------------------------------------------------------------

def test_version_is_077():
    from agentkit_cli import __version__
    assert tuple(int(x) for x in __version__.split(".")) >= tuple(int(x) for x in "0.80.0".split("."))
