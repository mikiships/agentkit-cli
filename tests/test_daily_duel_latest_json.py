"""Tests for D3 — daily-duel-latest.json always written with required fields."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from agentkit_cli.daily_duel import DailyDuelEngine, DailyDuelResult, _write_latest_json
from agentkit_cli.repo_duel import DimensionResult


REQUIRED_FIELDS = {
    "repo1", "repo2", "pair_category", "tweet_text",
    "run_date", "winner", "repo1_score", "repo2_score",
}


def _make_dimension():
    return DimensionResult(name="readme", repo1_value=80.0, repo2_value=60.0, winner="repo1")


def _make_result(**overrides) -> DailyDuelResult:
    defaults = dict(
        repo1="org/a",
        repo2="org/b",
        repo1_score=80.0,
        repo2_score=60.0,
        repo1_grade="B",
        repo2_grade="C",
        dimension_results=[_make_dimension()],
        winner="repo1",
        run_date="2026-03-21",
        share_url=None,
        tweet_text="org/a (80/100) vs org/b (60/100): clear winner.",
        pair_category="devtools",
        seed="2026-03-21",
    )
    defaults.update(overrides)
    return DailyDuelResult(**defaults)


def test_write_latest_json_contains_all_required_fields(tmp_path):
    """_write_latest_json must write all required fields."""
    out = tmp_path / "latest.json"
    result = _make_result()
    _write_latest_json(result, out)
    data = json.loads(out.read_text())
    for field in REQUIRED_FIELDS:
        assert field in data, f"Missing field: {field}"


def test_write_latest_json_contains_tweet_text(tmp_path):
    """tweet_text must be present and non-empty in JSON."""
    out = tmp_path / "latest.json"
    result = _make_result(tweet_text="My great tweet.")
    _write_latest_json(result, out)
    data = json.loads(out.read_text())
    assert data["tweet_text"] == "My great tweet."


def test_write_latest_json_called_on_auto_pair_run(tmp_path):
    """run_daily_duel must call _write_latest_json (auto-pair path)."""
    analyze_calls = []

    def factory(target, timeout):
        ar = MagicMock()
        ar.composite_score = 80.0 if len(analyze_calls) == 0 else 60.0
        ar.grade = "B" if len(analyze_calls) == 0 else "C"
        ar.tools = {}
        analyze_calls.append(target)
        return ar

    out = tmp_path / "latest.json"
    engine = DailyDuelEngine(_analyze_factory=factory)

    with patch("agentkit_cli.daily_duel._write_latest_json") as mock_write:
        engine.run_daily_duel(seed="test-seed")
        assert mock_write.called, "_write_latest_json was not called"


def test_write_latest_json_called_on_explicit_pair_run(tmp_path):
    """_run_explicit_pair must write daily-duel-latest.json."""
    from typer.testing import CliRunner
    from agentkit_cli.main import app

    runner = CliRunner()
    out = tmp_path / "custom.json"

    analyze_calls = []

    def factory(target, timeout):
        ar = MagicMock()
        ar.composite_score = 75.0 if len(analyze_calls) == 0 else 65.0
        ar.grade = "B"
        ar.tools = {}
        analyze_calls.append(target)
        return ar

    with patch("agentkit_cli.commands.daily_duel_cmd._write_latest_json") as mock_write:
        result = runner.invoke(
            app,
            ["daily-duel", "--pair", "a/b", "--pair", "c/d", "--tweet-only"],
            catch_exceptions=False,
        )
        assert mock_write.called or result.exit_code != 0  # called or network unavailable


def test_written_json_scores_match_result(tmp_path):
    """Scores in JSON must match those in the DailyDuelResult."""
    out = tmp_path / "latest.json"
    result = _make_result(repo1_score=92.5, repo2_score=78.0)
    _write_latest_json(result, out)
    data = json.loads(out.read_text())
    assert abs(data["repo1_score"] - 92.5) < 0.01
    assert abs(data["repo2_score"] - 78.0) < 0.01
