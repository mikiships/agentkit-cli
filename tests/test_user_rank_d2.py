"""Tests for D2: user-rank CLI command."""
from __future__ import annotations

import json
import pytest
from unittest.mock import MagicMock, patch
from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.user_rank import UserRankResult, UserRankEntry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_result(topic: str = "python", n: int = 3) -> UserRankResult:
    contributors = []
    for i in range(n):
        score = 90.0 - i * 10
        grade = "A" if score >= 80 else "B" if score >= 65 else "C" if score >= 50 else "D"
        contributors.append(UserRankEntry(
            rank=i + 1,
            username=f"user{i}",
            score=score,
            grade=grade,
            top_repo=f"repo{i}",
            avatar_url=f"https://github.com/user{i}.png",
        ))
    return UserRankResult(
        topic=topic,
        contributors=contributors,
        top_scorer="user0",
        mean_score=80.0,
        grade_distribution={"A": 1, "B": 1, "C": 1, "D": 0},
        timestamp="2026-03-20 00:00 UTC",
    )


runner = CliRunner()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_user_rank_help():
    result = runner.invoke(app, ["user-rank", "--help"])
    assert result.exit_code == 0
    assert "topic" in result.output.lower() or "rank" in result.output.lower()


def test_user_rank_json_output():
    mock_result = _make_result()
    with patch("agentkit_cli.commands.user_rank_cmd.UserRankEngine") as MockEngine:
        MockEngine.return_value.run.return_value = mock_result
        result = runner.invoke(app, ["user-rank", "python", "--json", "--quiet"])
    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert parsed["topic"] == "python"
    assert isinstance(parsed["contributors"], list)


def test_user_rank_json_has_required_fields():
    mock_result = _make_result()
    with patch("agentkit_cli.commands.user_rank_cmd.UserRankEngine") as MockEngine:
        MockEngine.return_value.run.return_value = mock_result
        result = runner.invoke(app, ["user-rank", "python", "--json", "--quiet"])
    parsed = json.loads(result.output)
    assert "top_scorer" in parsed
    assert "mean_score" in parsed
    assert "grade_distribution" in parsed


def test_user_rank_limit_flag():
    mock_result = _make_result()
    with patch("agentkit_cli.commands.user_rank_cmd.UserRankEngine") as MockEngine:
        MockEngine.return_value.run.return_value = mock_result
        result = runner.invoke(app, ["user-rank", "python", "--limit", "5", "--json", "--quiet"])
    assert result.exit_code == 0
    # Verify limit was passed
    MockEngine.assert_called_once()
    call_kwargs = MockEngine.call_args
    assert call_kwargs.kwargs.get("limit") == 5 or (call_kwargs.args and 5 in call_kwargs.args)


def test_user_rank_quiet_flag():
    mock_result = _make_result()
    with patch("agentkit_cli.commands.user_rank_cmd.UserRankEngine") as MockEngine:
        MockEngine.return_value.run.return_value = mock_result
        result = runner.invoke(app, ["user-rank", "python", "--quiet"])
    assert result.exit_code == 0
    # Quiet mode should produce minimal output
    assert "Warning" not in result.output or "GITHUB_TOKEN" in result.output


def test_user_rank_output_file(tmp_path):
    mock_result = _make_result()
    out_file = tmp_path / "report.html"
    with patch("agentkit_cli.commands.user_rank_cmd.UserRankEngine") as MockEngine:
        MockEngine.return_value.run.return_value = mock_result
        result = runner.invoke(app, ["user-rank", "python", "--output", str(out_file), "--quiet"])
    assert result.exit_code == 0
    assert out_file.exists()
    content = out_file.read_text()
    assert "python" in content.lower()


def test_user_rank_share_graceful_failure():
    """--share fails gracefully if share module unavailable."""
    mock_result = _make_result()
    with patch("agentkit_cli.commands.user_rank_cmd.UserRankEngine") as MockEngine:
        MockEngine.return_value.run.return_value = mock_result
        with patch("agentkit_cli.commands.user_rank_cmd.UserRankHTMLRenderer") as MockRenderer:
            MockRenderer.return_value.render.return_value = "<html></html>"
            with patch("agentkit_cli.share.upload_scorecard", side_effect=Exception("no key")):
                result = runner.invoke(app, ["user-rank", "python", "--share"])
    # Should not crash
    assert result.exit_code == 0


def test_user_rank_rich_table_output():
    mock_result = _make_result()
    with patch("agentkit_cli.commands.user_rank_cmd.UserRankEngine") as MockEngine:
        MockEngine.return_value.run.return_value = mock_result
        result = runner.invoke(app, ["user-rank", "python"])
    assert result.exit_code == 0
    assert "user0" in result.output


def test_user_rank_no_contributors():
    mock_result = UserRankResult(
        topic="obscuretopic",
        contributors=[],
        top_scorer="",
        mean_score=0.0,
        grade_distribution={"A": 0, "B": 0, "C": 0, "D": 0},
        timestamp="2026-03-20 00:00 UTC",
    )
    with patch("agentkit_cli.commands.user_rank_cmd.UserRankEngine") as MockEngine:
        MockEngine.return_value.run.return_value = mock_result
        result = runner.invoke(app, ["user-rank", "obscuretopic", "--quiet"])
    assert result.exit_code == 0


def test_user_rank_wired_in_main():
    """Verify user-rank is registered in main app."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "user-rank" in result.output
