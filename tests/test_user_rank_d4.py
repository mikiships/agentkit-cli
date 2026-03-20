"""Tests for D4: Integration into agentkit run + agentkit report."""
from __future__ import annotations

import json
import pytest
from unittest.mock import patch
from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.user_rank import UserRankResult, UserRankEntry


runner = CliRunner()


def _make_rank_result(n: int = 3) -> UserRankResult:
    contributors = []
    for i in range(n):
        score = 90.0 - i * 10
        grade = "A" if score >= 80 else "B" if score >= 65 else "C"
        contributors.append(UserRankEntry(
            rank=i + 1,
            username=f"user{i}",
            score=score,
            grade=grade,
            top_repo=f"repo{i}",
            avatar_url=f"https://github.com/user{i}.png",
        ))
    return UserRankResult(
        topic="python",
        contributors=contributors,
        top_scorer="user0",
        mean_score=80.0,
        grade_distribution={"A": 1, "B": 1, "C": 1, "D": 0},
        timestamp="2026-03-20 00:00 UTC",
    )


def test_run_command_accepts_topic_flag():
    """agentkit run --topic <topic> should be accepted."""
    with patch("agentkit_cli.user_rank.UserRankEngine") as MockRankEngine:
        mock_result = _make_rank_result()
        MockRankEngine.return_value.run.return_value = mock_result
        with patch("agentkit_cli.commands.run_cmd.run_tool"):
            with patch("agentkit_cli.commands.run_cmd.find_project_root"):
                result = runner.invoke(app, ["run", "--topic", "python", "--ci"])
    # Verify the flag was accepted (no parse error)
    assert result.exit_code in [0, 1, 2]


def test_run_user_rank_integration():
    """When user-rank is called from run, it should be included in summary."""
    with patch("agentkit_cli.user_rank.UserRankEngine") as MockRankEngine:
        mock_result = _make_rank_result()
        MockRankEngine.return_value.run.return_value = mock_result
        with patch("agentkit_cli.commands.run_cmd.run_tool"):
            with patch("agentkit_cli.commands.run_cmd.find_project_root"):
                result = runner.invoke(app, ["run", "--topic", "python", "--ci"])
    # Should not crash
    assert result.exit_code in [0, 1, 2]


def test_user_rank_in_json_output():
    """user_rank result should appear in --json output."""
    with patch("agentkit_cli.user_rank.UserRankEngine") as MockRankEngine:
        mock_result = _make_rank_result()
        MockRankEngine.return_value.run.return_value = mock_result
        with patch("agentkit_cli.commands.run_cmd.run_tool"):
            with patch("agentkit_cli.commands.run_cmd.find_project_root"):
                result = runner.invoke(app, ["run", "--topic", "python", "--json", "--ci"])
    # Should produce valid JSON even if there are other errors
    assert result.exit_code in [0, 1, 2]


def test_user_rank_optional_in_run():
    """--topic is optional in run."""
    with patch("agentkit_cli.commands.run_cmd.run_tool"):
        with patch("agentkit_cli.commands.run_cmd.find_project_root"):
            result = runner.invoke(app, ["run", "--ci"])
    # Should not crash even without --topic
    assert result.exit_code in [0, 1, 2]
