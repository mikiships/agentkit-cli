"""Tests for D2: agentkit pages-trending CLI command."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.engines.trending_pages import TrendingPagesResult

runner = CliRunner()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_result(published: bool = True, repos_scored: int = 10, error: str = None) -> TrendingPagesResult:
    return TrendingPagesResult(
        pages_url="https://owner.github.io/agentkit-trending/trending.html",
        repos_scored=repos_scored,
        period="today",
        language=None,
        published=published,
        error=error,
        leaderboard_json={"repos": [], "period": "today", "generated": "2026-03-19"},
    )


# ---------------------------------------------------------------------------
# Command wiring
# ---------------------------------------------------------------------------

def test_command_is_registered():
    result = runner.invoke(app, ["pages-trending", "--help"])
    assert result.exit_code == 0
    assert "pages-trending" in result.output or "trending" in result.output.lower()

def test_command_help_shows_flags():
    result = runner.invoke(app, ["pages-trending", "--help"])
    assert "--limit" in result.output
    assert "--language" in result.output
    assert "--period" in result.output
    assert "--dry-run" in result.output
    assert "--quiet" in result.output
    assert "--share" in result.output


# ---------------------------------------------------------------------------
# --dry-run
# ---------------------------------------------------------------------------

def test_dry_run_no_push():
    mock_result = _make_result(published=False, repos_scored=5)
    with patch("agentkit_cli.commands.pages_trending_cmd.TrendingPagesEngine") as mock_cls:
        mock_instance = MagicMock()
        mock_instance.run.return_value = mock_result
        mock_cls.return_value = mock_instance
        result = runner.invoke(app, ["pages-trending", "--dry-run", "--pages-repo", "owner/repo"])
    assert result.exit_code == 0
    assert "dry" in result.output.lower() or "not published" in result.output.lower() or "5" in result.output

def test_dry_run_engine_receives_dry_run():
    mock_result = _make_result(published=False)
    with patch("agentkit_cli.commands.pages_trending_cmd.TrendingPagesEngine") as mock_cls:
        mock_instance = MagicMock()
        mock_instance.run.return_value = mock_result
        mock_cls.return_value = mock_instance
        runner.invoke(app, ["pages-trending", "--dry-run", "--pages-repo", "owner/repo"])
        _, kwargs = mock_cls.call_args
        assert kwargs.get("dry_run") is True


# ---------------------------------------------------------------------------
# --limit
# ---------------------------------------------------------------------------

def test_limit_passed_to_engine():
    mock_result = _make_result()
    with patch("agentkit_cli.commands.pages_trending_cmd.TrendingPagesEngine") as mock_cls:
        mock_instance = MagicMock()
        mock_instance.run.return_value = mock_result
        mock_cls.return_value = mock_instance
        runner.invoke(app, ["pages-trending", "--dry-run", "--pages-repo", "owner/repo", "--limit", "15"])
        _, kwargs = mock_cls.call_args
        assert kwargs.get("limit") == 15

def test_limit_invalid_over_50():
    result = runner.invoke(app, ["pages-trending", "--dry-run", "--pages-repo", "owner/repo", "--limit", "100"])
    assert result.exit_code != 0

def test_limit_invalid_zero():
    result = runner.invoke(app, ["pages-trending", "--dry-run", "--pages-repo", "owner/repo", "--limit", "0"])
    assert result.exit_code != 0


# ---------------------------------------------------------------------------
# --language
# ---------------------------------------------------------------------------

def test_language_passed_to_engine():
    mock_result = _make_result()
    with patch("agentkit_cli.commands.pages_trending_cmd.TrendingPagesEngine") as mock_cls:
        mock_instance = MagicMock()
        mock_instance.run.return_value = mock_result
        mock_cls.return_value = mock_instance
        runner.invoke(app, ["pages-trending", "--dry-run", "--pages-repo", "owner/repo", "--language", "python"])
        _, kwargs = mock_cls.call_args
        assert kwargs.get("language") == "python"

def test_language_none_by_default():
    mock_result = _make_result()
    with patch("agentkit_cli.commands.pages_trending_cmd.TrendingPagesEngine") as mock_cls:
        mock_instance = MagicMock()
        mock_instance.run.return_value = mock_result
        mock_cls.return_value = mock_instance
        runner.invoke(app, ["pages-trending", "--dry-run", "--pages-repo", "owner/repo"])
        _, kwargs = mock_cls.call_args
        assert kwargs.get("language") is None


# ---------------------------------------------------------------------------
# --period
# ---------------------------------------------------------------------------

def test_period_today():
    mock_result = _make_result()
    with patch("agentkit_cli.commands.pages_trending_cmd.TrendingPagesEngine") as mock_cls:
        mock_instance = MagicMock()
        mock_instance.run.return_value = mock_result
        mock_cls.return_value = mock_instance
        runner.invoke(app, ["pages-trending", "--dry-run", "--pages-repo", "owner/repo", "--period", "today"])
        _, kwargs = mock_cls.call_args
        assert kwargs.get("period") == "today"

def test_period_week():
    mock_result = _make_result()
    with patch("agentkit_cli.commands.pages_trending_cmd.TrendingPagesEngine") as mock_cls:
        mock_instance = MagicMock()
        mock_instance.run.return_value = mock_result
        mock_cls.return_value = mock_instance
        runner.invoke(app, ["pages-trending", "--dry-run", "--pages-repo", "owner/repo", "--period", "week"])
        _, kwargs = mock_cls.call_args
        assert kwargs.get("period") == "week"

def test_period_month():
    mock_result = _make_result()
    with patch("agentkit_cli.commands.pages_trending_cmd.TrendingPagesEngine") as mock_cls:
        mock_instance = MagicMock()
        mock_instance.run.return_value = mock_result
        mock_cls.return_value = mock_instance
        runner.invoke(app, ["pages-trending", "--dry-run", "--pages-repo", "owner/repo", "--period", "month"])
        _, kwargs = mock_cls.call_args
        assert kwargs.get("period") == "month"

def test_period_invalid():
    result = runner.invoke(app, ["pages-trending", "--dry-run", "--pages-repo", "owner/repo", "--period", "year"])
    assert result.exit_code != 0


# ---------------------------------------------------------------------------
# --quiet
# ---------------------------------------------------------------------------

def test_quiet_prints_only_url():
    mock_result = _make_result()
    with patch("agentkit_cli.commands.pages_trending_cmd.TrendingPagesEngine") as mock_cls:
        mock_instance = MagicMock()
        mock_instance.run.return_value = mock_result
        mock_cls.return_value = mock_instance
        result = runner.invoke(app, ["pages-trending", "--quiet", "--pages-repo", "owner/repo", "--dry-run"])
    assert result.exit_code == 0
    lines = [l for l in result.output.strip().split("\n") if l.strip()]
    assert len(lines) == 1
    assert "github.io" in lines[0] or "trending" in lines[0]


# ---------------------------------------------------------------------------
# --json
# ---------------------------------------------------------------------------

def test_json_output():
    mock_result = _make_result()
    with patch("agentkit_cli.commands.pages_trending_cmd.TrendingPagesEngine") as mock_cls:
        mock_instance = MagicMock()
        mock_instance.run.return_value = mock_result
        mock_cls.return_value = mock_instance
        result = runner.invoke(app, ["pages-trending", "--json", "--pages-repo", "owner/repo", "--dry-run"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "pages_url" in data
    assert "repos_scored" in data


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

def test_publish_failure_shown():
    mock_result = _make_result(published=False, error="git push failed")
    with patch("agentkit_cli.commands.pages_trending_cmd.TrendingPagesEngine") as mock_cls:
        mock_instance = MagicMock()
        mock_instance.run.return_value = mock_result
        mock_cls.return_value = mock_instance
        result = runner.invoke(app, ["pages-trending", "--pages-repo", "owner/repo"])
    assert "failed" in result.output.lower() or "git push failed" in result.output

def test_publish_success_shown():
    mock_result = _make_result(published=True)
    with patch("agentkit_cli.commands.pages_trending_cmd.TrendingPagesEngine") as mock_cls:
        mock_instance = MagicMock()
        mock_instance.run.return_value = mock_result
        mock_cls.return_value = mock_instance
        result = runner.invoke(app, ["pages-trending", "--pages-repo", "owner/repo"])
    assert result.exit_code == 0
    assert "trending" in result.output.lower() or "github.io" in result.output


# ---------------------------------------------------------------------------
# --share
# ---------------------------------------------------------------------------

def test_share_passed_to_engine():
    mock_result = _make_result()
    mock_result.share_url = "https://here.now/abc123"
    with patch("agentkit_cli.commands.pages_trending_cmd.TrendingPagesEngine") as mock_cls:
        mock_instance = MagicMock()
        mock_instance.run.return_value = mock_result
        mock_cls.return_value = mock_instance
        result = runner.invoke(app, ["pages-trending", "--share", "--pages-repo", "owner/repo"])
        _, kwargs = mock_cls.call_args
        assert kwargs.get("share") is True
