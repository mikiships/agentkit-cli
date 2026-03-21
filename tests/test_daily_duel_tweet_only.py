"""Tests for D2 — --tweet-only flag on agentkit daily-duel."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from agentkit_cli.daily_duel import DailyDuelResult
from agentkit_cli.main import app
from agentkit_cli.repo_duel import DimensionResult

runner = CliRunner()


def _make_result(tweet="Test tweet text.", winner="repo1") -> DailyDuelResult:
    dim = DimensionResult(
        name="readme",
        repo1_value=75.0,
        repo2_value=60.0,
        winner="repo1",
    )
    return DailyDuelResult(
        repo1="org/repo1",
        repo2="org/repo2",
        repo1_score=75.0,
        repo2_score=60.0,
        repo1_grade="B",
        repo2_grade="C",
        dimension_results=[dim],
        winner=winner,
        run_date="2026-03-21",
        share_url=None,
        tweet_text=tweet,
        pair_category="devtools",
        seed="2026-03-21",
    )


def _patch_engine(result: DailyDuelResult):
    mock_engine = MagicMock()
    mock_engine.pick_pair.return_value = ("org/repo1", "org/repo2", "devtools")
    mock_engine.run_daily_duel.return_value = result
    return mock_engine


def test_tweet_only_prints_only_tweet_text():
    """--tweet-only should print ONLY tweet text, nothing else."""
    expected = "org/repo1 beats org/repo2 in devtools agent-readiness."
    result = _make_result(tweet=expected)

    with patch("agentkit_cli.commands.daily_duel_cmd.DailyDuelEngine") as mock_cls:
        with patch("agentkit_cli.commands.daily_duel_cmd._write_latest_json"):
            mock_cls.return_value = _patch_engine(result)
            out = runner.invoke(app, ["daily-duel", "--tweet-only", "--seed", "test"])

    assert out.exit_code == 0
    assert out.output.strip() == expected


def test_tweet_only_no_rich_output():
    """--tweet-only output must not contain Rich markup artifacts or table borders."""
    result = _make_result(tweet="Simple tweet text.")

    with patch("agentkit_cli.commands.daily_duel_cmd.DailyDuelEngine") as mock_cls:
        with patch("agentkit_cli.commands.daily_duel_cmd._write_latest_json"):
            mock_cls.return_value = _patch_engine(result)
            out = runner.invoke(app, ["daily-duel", "--tweet-only", "--seed", "test"])

    assert out.exit_code == 0
    # Should NOT contain Panel/table border characters or Rich markup
    assert "Tweet-ready" not in out.output
    assert "Daily Duel" not in out.output


def test_tweet_only_with_pair_flag():
    """--tweet-only should work with --pair."""
    tweet = "pair tweet text"
    with patch("agentkit_cli.commands.daily_duel_cmd._run_explicit_pair") as mock_run:
        # _run_explicit_pair prints and returns
        def side_effect(**kwargs):
            print(tweet)

        mock_run.side_effect = side_effect
        out = runner.invoke(app, ["daily-duel", "--tweet-only", "--pair", "a/b", "--pair", "c/d"])

    # tweet_only was passed to _run_explicit_pair
    assert mock_run.called
    call_kwargs = mock_run.call_args[1]
    assert call_kwargs.get("tweet_only") is True


def test_tweet_only_output_within_280_chars():
    """Tweet from --tweet-only must be <= 280 chars."""
    tweet = "A" * 140 + " vs B/b: both score 100/100."
    result = _make_result(tweet=tweet[:280])

    with patch("agentkit_cli.commands.daily_duel_cmd.DailyDuelEngine") as mock_cls:
        with patch("agentkit_cli.commands.daily_duel_cmd._write_latest_json"):
            mock_cls.return_value = _patch_engine(result)
            out = runner.invoke(app, ["daily-duel", "--tweet-only", "--seed", "test"])

    assert out.exit_code == 0
    assert len(out.output.strip()) <= 280


def test_tweet_only_flag_exists_in_help():
    """--tweet-only should appear in daily-duel help."""
    out = runner.invoke(app, ["daily-duel", "--help"])
    assert "--tweet-only" in out.output
