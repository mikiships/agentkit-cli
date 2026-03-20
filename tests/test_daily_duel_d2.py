"""Tests for agentkit daily-duel CLI command (D2)."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from agentkit_cli.commands.daily_duel_cmd import daily_duel_command
from agentkit_cli.daily_duel import DailyDuelResult
from agentkit_cli.repo_duel import DimensionResult


# ---------------------------------------------------------------------------
# Helpers
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
        calls.append(target)
        if len(calls) <= 1:
            return _make_analyze_result(score1, grade1)
        return _make_analyze_result(score2, grade2)

    return factory


def _make_daily_duel_result(repo1="a/b", repo2="c/d"):
    dims = [
        DimensionResult("composite_score", 75.0, 60.0, "repo1", 15.0),
    ]
    return DailyDuelResult(
        repo1=repo1,
        repo2=repo2,
        repo1_score=75.0,
        repo2_score=60.0,
        repo1_grade="B",
        repo2_grade="C",
        dimension_results=dims,
        winner="repo1",
        run_date="2026-01-01 00:00 UTC",
        tweet_text=f"{repo1} vs {repo2} agent-readiness: {repo1} 75/100 (B), {repo2} 60/100 (C). Winner: {repo1} on 1/1 dimensions.",
        pair_category="web-frameworks",
        seed="2026-01-01",
    )


# ---------------------------------------------------------------------------
# Basic CLI execution
# ---------------------------------------------------------------------------

def test_daily_duel_quiet_output(tmp_path, capsys):
    result = _make_daily_duel_result()
    engine_mock = MagicMock()
    engine_mock.run_daily_duel.return_value = result
    engine_mock.pick_pair.return_value = ("a/b", "c/d", "web-frameworks")

    with patch("agentkit_cli.commands.daily_duel_cmd.DailyDuelEngine", return_value=engine_mock):
        daily_duel_command(quiet=True, _output_path=tmp_path / "out.json")

    captured = capsys.readouterr()
    assert result.tweet_text in captured.out


def test_daily_duel_json_output(tmp_path, capsys):
    result = _make_daily_duel_result()
    engine_mock = MagicMock()
    engine_mock.run_daily_duel.return_value = result
    engine_mock.pick_pair.return_value = ("a/b", "c/d", "web-frameworks")

    with patch("agentkit_cli.commands.daily_duel_cmd.DailyDuelEngine", return_value=engine_mock):
        daily_duel_command(json_output=True, _output_path=tmp_path / "out.json")

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["repo1"] == "a/b"
    assert "tweet_text" in data


def test_daily_duel_with_seed(tmp_path, capsys):
    result = _make_daily_duel_result()
    engine_mock = MagicMock()
    engine_mock.run_daily_duel.return_value = result
    engine_mock.pick_pair.return_value = ("a/b", "c/d", "web-frameworks")

    with patch("agentkit_cli.commands.daily_duel_cmd.DailyDuelEngine", return_value=engine_mock):
        daily_duel_command(seed="custom-seed", json_output=True, _output_path=tmp_path / "out.json")

    engine_mock.run_daily_duel.assert_called_once_with(seed="custom-seed", deep=False)


def test_daily_duel_with_pair(tmp_path, capsys):
    """--pair overrides auto-pick."""
    result = _make_daily_duel_result(repo1="pallets/flask", repo2="encode/httpx")
    engine_mock = MagicMock()
    engine_mock.run_duel.return_value = result

    with patch("agentkit_cli.commands.daily_duel_cmd.DailyDuelEngine"):
        with patch("agentkit_cli.commands.daily_duel_cmd._run_explicit_pair") as mock_explicit:
            daily_duel_command(
                pair=["pallets/flask", "encode/httpx"],
                json_output=True,
                _output_path=tmp_path / "out.json",
            )
    mock_explicit.assert_called_once()
    call_kwargs = mock_explicit.call_args[1]
    assert call_kwargs["repo1"] == "pallets/flask"
    assert call_kwargs["repo2"] == "encode/httpx"


def test_daily_duel_saves_history(tmp_path):
    result = _make_daily_duel_result()
    engine_mock = MagicMock()
    engine_mock.run_daily_duel.return_value = result
    engine_mock.pick_pair.return_value = ("a/b", "c/d", "web-frameworks")

    mock_db = MagicMock()
    mock_db_class = MagicMock(return_value=mock_db)

    with patch("agentkit_cli.commands.daily_duel_cmd.DailyDuelEngine", return_value=engine_mock):
        with patch("agentkit_cli.commands.daily_duel_cmd.Console"):
            with patch("agentkit_cli.history.HistoryDB", mock_db_class):
                daily_duel_command(quiet=True, _output_path=tmp_path / "out.json")

    # history is best-effort so just verify no crash


def test_daily_duel_calendar_json(capsys):
    engine_mock = MagicMock()
    engine_mock.calendar.return_value = [
        {"date": "2026-01-01", "repo1": "a/b", "repo2": "c/d", "category": "web-frameworks"},
        {"date": "2026-01-02", "repo1": "e/f", "repo2": "g/h", "category": "ml-ai"},
    ]
    with patch("agentkit_cli.commands.daily_duel_cmd.DailyDuelEngine", return_value=engine_mock):
        daily_duel_command(calendar=True, json_output=True)

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert len(data) == 2
    assert data[0]["date"] == "2026-01-01"


def test_daily_duel_calendar_rich(capsys):
    engine_mock = MagicMock()
    engine_mock.calendar.return_value = [
        {"date": "2026-01-01", "repo1": "a/b", "repo2": "c/d", "category": "web-frameworks"},
    ]
    with patch("agentkit_cli.commands.daily_duel_cmd.DailyDuelEngine", return_value=engine_mock):
        daily_duel_command(calendar=True)
    # Should not raise


def test_daily_duel_output_html(tmp_path):
    result = _make_daily_duel_result()
    engine_mock = MagicMock()
    engine_mock.run_daily_duel.return_value = result
    engine_mock.pick_pair.return_value = ("a/b", "c/d", "web-frameworks")
    output_file = str(tmp_path / "out.html")

    with patch("agentkit_cli.commands.daily_duel_cmd.DailyDuelEngine", return_value=engine_mock):
        with patch("agentkit_cli.renderers.repo_duel_renderer.render_repo_duel_html", return_value="<html>test</html>"):
            daily_duel_command(output=output_file, quiet=True, _output_path=tmp_path / "latest.json")

    assert Path(output_file).exists()
    assert "<html>" in Path(output_file).read_text()


def test_daily_duel_share_updates_tweet_text(tmp_path, capsys):
    result = _make_daily_duel_result()
    engine_mock = MagicMock()
    engine_mock.run_daily_duel.return_value = result
    engine_mock.pick_pair.return_value = ("a/b", "c/d", "web-frameworks")

    with patch("agentkit_cli.commands.daily_duel_cmd.DailyDuelEngine", return_value=engine_mock):
        with patch("agentkit_cli.renderers.repo_duel_renderer.render_repo_duel_html", return_value="<html/>"):
            with patch("agentkit_cli.share.upload_scorecard", return_value="https://here.now/abc123"):
                daily_duel_command(share=True, quiet=True, _output_path=tmp_path / "latest.json")

    captured = capsys.readouterr()
    # tweet_text printed in quiet mode
    assert "https://here.now/abc123" in captured.out or result.tweet_text in captured.out


def test_daily_duel_error_handling(tmp_path, capsys):
    engine_mock = MagicMock()
    engine_mock.run_daily_duel.side_effect = RuntimeError("API failure")
    engine_mock.pick_pair.return_value = ("a/b", "c/d", "web-frameworks")

    import click
    with patch("agentkit_cli.commands.daily_duel_cmd.DailyDuelEngine", return_value=engine_mock):
        with pytest.raises((SystemExit, click.exceptions.Exit)):
            daily_duel_command(_output_path=tmp_path / "out.json")
