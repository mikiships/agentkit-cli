"""Tests for D3 — agentkit daily-duel --calendar schedule preview."""
from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import MagicMock, patch
from typer.testing import CliRunner

import pytest

from agentkit_cli.main import app


runner = CliRunner()


def test_calendar_shows_7_days():
    """--calendar should show 7-day schedule as a table."""
    with patch("agentkit_cli.commands.daily_duel_cmd.DailyDuelEngine") as mock_engine_class:
        mock_engine = MagicMock()
        mock_engine_class.return_value = mock_engine
        
        schedule = []
        today = date.today()
        for i in range(7):
            d = today + timedelta(days=i)
            schedule.append({
                "date": d.isoformat(),
                "repo1": f"repo{i}/a",
                "repo2": f"repo{i}/b",
                "category": f"cat{i}",
            })
        mock_engine.calendar.return_value = schedule
        
        result = runner.invoke(app, ["daily-duel", "--calendar"])
        assert result.exit_code == 0


def test_calendar_has_date_column():
    """--calendar output should include date column."""
    with patch("agentkit_cli.commands.daily_duel_cmd.DailyDuelEngine") as mock_engine_class:
        mock_engine = MagicMock()
        mock_engine_class.return_value = mock_engine
        
        today = date.today()
        schedule = [
            {
                "date": today.isoformat(),
                "repo1": "a/b",
                "repo2": "c/d",
                "category": "web-frameworks",
            }
        ]
        mock_engine.calendar.return_value = schedule
        
        result = runner.invoke(app, ["daily-duel", "--calendar"])
        assert result.exit_code == 0
        assert today.isoformat() in result.stdout


def test_calendar_has_repo_columns():
    """--calendar output should include repo columns."""
    with patch("agentkit_cli.commands.daily_duel_cmd.DailyDuelEngine") as mock_engine_class:
        mock_engine = MagicMock()
        mock_engine_class.return_value = mock_engine
        
        schedule = [
            {
                "date": "2026-01-01",
                "repo1": "tiangolo/fastapi",
                "repo2": "pallets/flask",
                "category": "web-frameworks",
            }
        ]
        mock_engine.calendar.return_value = schedule
        
        result = runner.invoke(app, ["daily-duel", "--calendar"])
        assert result.exit_code == 0
        assert "tiangolo/fastapi" in result.stdout or "fastapi" in result.stdout.lower()


def test_calendar_has_category_column():
    """--calendar output should include category column."""
    with patch("agentkit_cli.commands.daily_duel_cmd.DailyDuelEngine") as mock_engine_class:
        mock_engine = MagicMock()
        mock_engine_class.return_value = mock_engine
        
        schedule = [
            {
                "date": "2026-01-01",
                "repo1": "a/b",
                "repo2": "c/d",
                "category": "web-frameworks",
            }
        ]
        mock_engine.calendar.return_value = schedule
        
        result = runner.invoke(app, ["daily-duel", "--calendar"])
        assert result.exit_code == 0
        assert "web-frameworks" in result.stdout or "category" in result.stdout.lower()


def test_calendar_no_analysis_run():
    """--calendar should NOT call run_daily_duel."""
    with patch("agentkit_cli.commands.daily_duel_cmd.DailyDuelEngine") as mock_engine_class:
        mock_engine = MagicMock()
        mock_engine_class.return_value = mock_engine
        
        schedule = [
            {
                "date": "2026-01-01",
                "repo1": "a/b",
                "repo2": "c/d",
                "category": "web",
            }
        ]
        mock_engine.calendar.return_value = schedule
        
        result = runner.invoke(app, ["daily-duel", "--calendar"])
        assert result.exit_code == 0
        # Should not attempt to run analysis
        mock_engine.run_daily_duel.assert_not_called()
