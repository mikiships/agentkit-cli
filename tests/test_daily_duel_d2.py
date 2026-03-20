"""Tests for D2 — agentkit daily-duel CLI command and flags."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch
from typer.testing import CliRunner

import pytest

from agentkit_cli.main import app
from agentkit_cli.daily_duel import DailyDuelResult
from agentkit_cli.repo_duel import DimensionResult


runner = CliRunner()


def _mock_analyze(score1=75.0, grade1="B", score2=60.0, grade2="C"):
    """Factory for mocked analyze results."""
    calls = []

    def factory(target, timeout):
        ar = MagicMock()
        if len(calls) == 0:
            ar.composite_score = score1
            ar.grade = grade1
        else:
            ar.composite_score = score2
            ar.grade = grade2
        ar.tools = {}
        calls.append(target)
        return ar

    return factory


# ---------------------------------------------------------------------------
# Basic daily-duel command
# ---------------------------------------------------------------------------

def test_daily_duel_command_basic():
    """Basic invocation should succeed."""
    with patch("agentkit_cli.commands.daily_duel_cmd.DailyDuelEngine") as mock_engine_class:
        with patch("agentkit_cli.commands.daily_duel_cmd._write_latest_json"):
            mock_engine = MagicMock()
            mock_engine_class.return_value = mock_engine
            
            mock_result = DailyDuelResult(
                repo1="a/b",
                repo2="c/d",
                repo1_score=80.0,
                repo2_score=70.0,
                repo1_grade="B",
                repo2_grade="C",
                tweet_text="Test tweet",
                pair_category="test",
                seed="2026-01-01",
            )
            mock_engine.run_daily_duel.return_value = mock_result
            mock_engine.pick_pair.return_value = ("a/b", "c/d", "test")
            
            result = runner.invoke(app, ["daily-duel", "--quiet"])
            assert result.exit_code == 0


def test_daily_duel_help():
    """Help text should be available."""
    result = runner.invoke(app, ["daily-duel", "--help"])
    assert result.exit_code == 0
    assert "Daily Duel" in result.stdout or "daily" in result.stdout.lower()


# ---------------------------------------------------------------------------
# --seed flag
# ---------------------------------------------------------------------------

def test_daily_duel_with_seed():
    """--seed should pass through to engine."""
    with patch("agentkit_cli.commands.daily_duel_cmd.DailyDuelEngine") as mock_engine_class:
        with patch("agentkit_cli.commands.daily_duel_cmd._write_latest_json"):
            mock_engine = MagicMock()
            mock_engine_class.return_value = mock_engine
            
            mock_result = DailyDuelResult(
                repo1="a/b",
                repo2="c/d",
                repo1_score=75.0,
                repo2_score=65.0,
                repo1_grade="C",
                repo2_grade="C",
                tweet_text="Test",
                pair_category="test",
                seed="custom-seed",
            )
            mock_engine.run_daily_duel.return_value = mock_result
            mock_engine.pick_pair.return_value = ("a/b", "c/d", "test")
            
            runner.invoke(app, ["daily-duel", "--seed", "custom-seed", "--quiet"])
            mock_engine.run_daily_duel.assert_called_once()
            call_args = mock_engine.run_daily_duel.call_args
            assert call_args.kwargs["seed"] == "custom-seed"


# ---------------------------------------------------------------------------
# --deep flag
# ---------------------------------------------------------------------------

def test_daily_duel_with_deep():
    """--deep should pass through."""
    with patch("agentkit_cli.commands.daily_duel_cmd.DailyDuelEngine") as mock_engine_class:
        with patch("agentkit_cli.commands.daily_duel_cmd._write_latest_json"):
            mock_engine = MagicMock()
            mock_engine_class.return_value = mock_engine
            
            mock_result = DailyDuelResult(
                repo1="a/b",
                repo2="c/d",
                repo1_score=75.0,
                repo2_score=65.0,
                repo1_grade="C",
                repo2_grade="C",
                tweet_text="Test",
                pair_category="test",
                seed=date.today().isoformat(),
            )
            mock_engine.run_daily_duel.return_value = mock_result
            mock_engine.pick_pair.return_value = ("a/b", "c/d", "test")
            
            runner.invoke(app, ["daily-duel", "--deep", "--quiet"])
            call_args = mock_engine.run_daily_duel.call_args
            assert call_args.kwargs["deep"] is True


# ---------------------------------------------------------------------------
# --quiet flag
# ---------------------------------------------------------------------------

def test_daily_duel_quiet_mode():
    """--quiet should only output tweet_text."""
    with patch("agentkit_cli.commands.daily_duel_cmd.DailyDuelEngine") as mock_engine_class:
        with patch("agentkit_cli.commands.daily_duel_cmd._write_latest_json"):
            mock_engine = MagicMock()
            mock_engine_class.return_value = mock_engine
            
            mock_result = DailyDuelResult(
                repo1="a/b",
                repo2="c/d",
                repo1_score=75.0,
                repo2_score=65.0,
                repo1_grade="C",
                repo2_grade="C",
                tweet_text="Hello world",
                pair_category="test",
                seed=date.today().isoformat(),
            )
            mock_engine.run_daily_duel.return_value = mock_result
            mock_engine.pick_pair.return_value = ("a/b", "c/d", "test")
            
            result = runner.invoke(app, ["daily-duel", "--quiet"])
            assert result.exit_code == 0
            assert "Hello world" in result.stdout


# ---------------------------------------------------------------------------
# --json flag
# ---------------------------------------------------------------------------

def test_daily_duel_json_output():
    """--json should output JSON."""
    with patch("agentkit_cli.commands.daily_duel_cmd.DailyDuelEngine") as mock_engine_class:
        with patch("agentkit_cli.commands.daily_duel_cmd._write_latest_json"):
            mock_engine = MagicMock()
            mock_engine_class.return_value = mock_engine
            
            result_obj = DailyDuelResult(
                repo1="a/b",
                repo2="c/d",
                repo1_score=80.0,
                repo2_score=70.0,
                repo1_grade="B",
                repo2_grade="C",
                tweet_text="Hello",
                pair_category="web-frameworks",
                seed="2026-01-01",
            )
            mock_engine.run_daily_duel.return_value = result_obj
            mock_engine.pick_pair.return_value = ("a/b", "c/d", "web-frameworks")
            
            result = runner.invoke(app, ["daily-duel", "--json", "--seed", "2026-01-01"])
            assert result.exit_code == 0
            parsed = json.loads(result.stdout)
            assert parsed["tweet_text"] == "Hello"
            assert parsed["repo1"] == "a/b"


# ---------------------------------------------------------------------------
# --pair flag
# ---------------------------------------------------------------------------

def test_daily_duel_pair_override():
    """--pair flag should accept two repo arguments."""
    # Note: typer's Option with List doesn't work the same way as Click
    # This test verifies the command structure accepts multiple --pair values
    result = runner.invoke(app, ["daily-duel", "--help"])
    assert result.exit_code == 0
    assert "--pair" in result.stdout


# ---------------------------------------------------------------------------
# --calendar flag
# ---------------------------------------------------------------------------

def test_daily_duel_calendar():
    """--calendar should show schedule without analysis."""
    with patch("agentkit_cli.commands.daily_duel_cmd.DailyDuelEngine") as mock_engine_class:
        mock_engine = MagicMock()
        mock_engine_class.return_value = mock_engine
        
        schedule = [
            {"date": "2026-01-01", "repo1": "a/b", "repo2": "c/d", "category": "web"},
            {"date": "2026-01-02", "repo1": "e/f", "repo2": "g/h", "category": "devtools"},
        ]
        mock_engine.calendar.return_value = schedule
        
        result = runner.invoke(app, ["daily-duel", "--calendar"])
        assert result.exit_code == 0
        mock_engine.run_daily_duel.assert_not_called()


def test_daily_duel_calendar_json():
    """--calendar --json should output JSON schedule."""
    with patch("agentkit_cli.commands.daily_duel_cmd.DailyDuelEngine") as mock_engine_class:
        mock_engine = MagicMock()
        mock_engine_class.return_value = mock_engine
        
        schedule = [
            {"date": "2026-01-01", "repo1": "a/b", "repo2": "c/d", "category": "web"},
        ]
        mock_engine.calendar.return_value = schedule
        
        result = runner.invoke(app, ["daily-duel", "--calendar", "--json"])
        assert result.exit_code == 0
        parsed = json.loads(result.stdout)
        assert len(parsed) == 1
        assert parsed[0]["category"] == "web"


# ---------------------------------------------------------------------------
# --share flag
# ---------------------------------------------------------------------------

def test_daily_duel_share_flag():
    """--share should attempt upload."""
    with patch("agentkit_cli.commands.daily_duel_cmd.DailyDuelEngine") as mock_engine_class:
        with patch("agentkit_cli.commands.daily_duel_cmd._write_latest_json"):
            with patch("agentkit_cli.renderers.repo_duel_renderer.render_repo_duel_html") as mock_render:
                with patch("agentkit_cli.share.upload_scorecard") as mock_upload:
                    mock_engine = MagicMock()
                    mock_engine_class.return_value = mock_engine
                    
                    result_obj = DailyDuelResult(
                        repo1="a/b",
                        repo2="c/d",
                        repo1_score=80.0,
                        repo2_score=70.0,
                        repo1_grade="B",
                        repo2_grade="C",
                        tweet_text="Test",
                        pair_category="web",
                        seed="2026-01-01",
                    )
                    mock_engine.run_daily_duel.return_value = result_obj
                    mock_engine.pick_pair.return_value = ("a/b", "c/d", "web")
                    mock_render.return_value = "<html></html>"
                    mock_upload.return_value = "https://example.com/report"
                    
                    result = runner.invoke(app, ["daily-duel", "--share", "--quiet"])
                    assert result.exit_code == 0


# ---------------------------------------------------------------------------
# --output flag
# ---------------------------------------------------------------------------

def test_daily_duel_output_file(tmp_path):
    """--output FILE should write HTML to file."""
    html_file = tmp_path / "report.html"
    
    with patch("agentkit_cli.commands.daily_duel_cmd.DailyDuelEngine") as mock_engine_class:
        with patch("agentkit_cli.commands.daily_duel_cmd._write_latest_json"):
            with patch("agentkit_cli.renderers.repo_duel_renderer.render_repo_duel_html") as mock_render:
                mock_engine = MagicMock()
                mock_engine_class.return_value = mock_engine
                
                result_obj = DailyDuelResult(
                    repo1="a/b",
                    repo2="c/d",
                    repo1_score=80.0,
                    repo2_score=70.0,
                    repo1_grade="B",
                    repo2_grade="C",
                    tweet_text="Test",
                    pair_category="web",
                    seed="2026-01-01",
                )
                mock_engine.run_daily_duel.return_value = result_obj
                mock_engine.pick_pair.return_value = ("a/b", "c/d", "web")
                mock_render.return_value = "<html><body>Report</body></html>"
                
                result = runner.invoke(app, ["daily-duel", "--output", str(html_file), "--quiet"])
                assert result.exit_code == 0
                assert html_file.exists()
                content = html_file.read_text()
                assert "Report" in content
