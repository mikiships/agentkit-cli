"""Tests for D2: `agentkit daily` CLI command."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.engines.daily_leaderboard import DailyLeaderboard, RankedRepo

runner = CliRunner()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_leaderboard(n: int = 3, date_val: date = date(2026, 3, 19)) -> DailyLeaderboard:
    from datetime import datetime, timezone
    repos = [
        RankedRepo(
            rank=i,
            full_name=f"org/repo-{i}",
            description=f"Repo {i}",
            stars=1000 * i,
            language="Python",
            url=f"https://github.com/org/repo-{i}",
            composite_score=float(90 - i * 5),
            top_finding=f"Finding {i}",
        )
        for i in range(1, n + 1)
    ]
    return DailyLeaderboard(
        date=date_val,
        repos=repos,
        generated_at=datetime(2026, 3, 19, 9, 0, 0, tzinfo=timezone.utc),
    )


def _patch_fetch(leaderboard: DailyLeaderboard):
    return patch(
        "agentkit_cli.commands.daily_cmd.fetch_trending_repos",
        return_value=leaderboard,
    )


# ---------------------------------------------------------------------------
# Basic invocation
# ---------------------------------------------------------------------------

class TestDailyCommandBasic:
    def test_runs_without_error(self):
        lb = _make_leaderboard()
        with _patch_fetch(lb):
            result = runner.invoke(app, ["daily"])
        assert result.exit_code == 0

    def test_shows_repo_names(self):
        lb = _make_leaderboard()
        with _patch_fetch(lb):
            result = runner.invoke(app, ["daily"])
        assert "org/repo-1" in result.output

    def test_shows_date_in_output(self):
        lb = _make_leaderboard()
        with _patch_fetch(lb):
            result = runner.invoke(app, ["daily"])
        assert "2026" in result.output

    def test_shows_scores(self):
        lb = _make_leaderboard()
        with _patch_fetch(lb):
            result = runner.invoke(app, ["daily"])
        assert "85" in result.output or "80" in result.output

    def test_default_limit_is_20(self):
        lb = _make_leaderboard()
        with patch("agentkit_cli.commands.daily_cmd.fetch_trending_repos", return_value=lb) as mock_fetch:
            runner.invoke(app, ["daily"])
        mock_fetch.assert_called_once()
        call_kwargs = mock_fetch.call_args
        assert call_kwargs.kwargs.get("limit", 20) == 20


# ---------------------------------------------------------------------------
# --date flag
# ---------------------------------------------------------------------------

class TestDailyDateFlag:
    def test_valid_date_passed_through(self):
        lb = _make_leaderboard()
        with patch("agentkit_cli.commands.daily_cmd.fetch_trending_repos", return_value=lb) as mock_fetch:
            result = runner.invoke(app, ["daily", "--date", "2026-01-15"])
        assert result.exit_code == 0
        call_kwargs = mock_fetch.call_args
        assert call_kwargs.kwargs.get("for_date") == date(2026, 1, 15)

    def test_invalid_date_exits_nonzero(self):
        result = runner.invoke(app, ["daily", "--date", "notadate"])
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# --json flag
# ---------------------------------------------------------------------------

class TestDailyJsonFlag:
    def test_json_output_valid(self):
        lb = _make_leaderboard()
        with _patch_fetch(lb):
            result = runner.invoke(app, ["daily", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "repos" in data
        assert "date" in data

    def test_json_repos_have_required_fields(self):
        lb = _make_leaderboard()
        with _patch_fetch(lb):
            result = runner.invoke(app, ["daily", "--json"])
        data = json.loads(result.output)
        for repo in data["repos"]:
            assert "rank" in repo
            assert "full_name" in repo
            assert "composite_score" in repo

    def test_json_no_rich_output(self):
        lb = _make_leaderboard()
        with _patch_fetch(lb):
            result = runner.invoke(app, ["daily", "--json"])
        # Should not contain ANSI/Rich table artifacts
        assert "┐" not in result.output


# ---------------------------------------------------------------------------
# --quiet flag
# ---------------------------------------------------------------------------

class TestDailyQuietFlag:
    def test_quiet_suppresses_banner(self):
        lb = _make_leaderboard()
        with _patch_fetch(lb):
            result = runner.invoke(app, ["daily", "--quiet"])
        assert "agentkit daily" not in result.output

    def test_quiet_and_share_outputs_only_url(self):
        lb = _make_leaderboard()
        with _patch_fetch(lb):
            with patch("agentkit_cli.commands.daily_cmd.publish_report", return_value="https://here.now/abc"):
                result = runner.invoke(app, ["daily", "--quiet", "--share"])
        assert result.exit_code == 0
        assert result.output.strip() == "https://here.now/abc"


# ---------------------------------------------------------------------------
# --share flag
# ---------------------------------------------------------------------------

class TestDailyShareFlag:
    def test_share_prints_url(self):
        lb = _make_leaderboard()
        with _patch_fetch(lb):
            with patch("agentkit_cli.commands.daily_cmd.publish_report", return_value="https://here.now/xyz"):
                result = runner.invoke(app, ["daily", "--share"])
        assert result.exit_code == 0
        assert "https://here.now/xyz" in result.output

    def test_share_failure_saves_locally(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        lb = _make_leaderboard()
        from agentkit_cli.publish import PublishError
        with _patch_fetch(lb):
            with patch("agentkit_cli.commands.daily_cmd.publish_report", side_effect=PublishError("fail")):
                result = runner.invoke(app, ["daily", "--share"])
        assert result.exit_code == 0
        assert (tmp_path / "daily-leaderboard.html").exists()


# ---------------------------------------------------------------------------
# --output flag
# ---------------------------------------------------------------------------

class TestDailyOutputFlag:
    def test_output_creates_html_file(self, tmp_path):
        out_file = tmp_path / "report.html"
        lb = _make_leaderboard()
        with _patch_fetch(lb):
            result = runner.invoke(app, ["daily", "--output", str(out_file)])
        assert result.exit_code == 0
        assert out_file.exists()
        content = out_file.read_text()
        assert "<!DOCTYPE html>" in content


# ---------------------------------------------------------------------------
# --min-score flag
# ---------------------------------------------------------------------------

class TestDailyMinScoreFlag:
    def test_min_score_filters_repos(self):
        lb = _make_leaderboard(5)
        with _patch_fetch(lb):
            result = runner.invoke(app, ["daily", "--min-score", "88"])
        assert result.exit_code == 0
        # Only repos with score >= 88 should appear: repo-1 (85) excluded
        assert "repo-3" not in result.output or "85" not in result.output
