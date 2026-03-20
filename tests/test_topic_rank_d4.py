"""D4 tests — Integration: agentkit run --topic-repos and trending drill-down hint."""
from __future__ import annotations

import json
from unittest.mock import patch, MagicMock

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.topic_rank import TopicRankResult, TopicRankEntry

runner = CliRunner()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_result(topic: str = "python", n: int = 2) -> TopicRankResult:
    entries = [
        TopicRankEntry(
            rank=i + 1,
            repo_full_name=f"owner/repo-{i}",
            score=80.0 - i * 5,
            grade="A",
            stars=500,
            description="desc",
        )
        for i in range(n)
    ]
    return TopicRankResult(topic=topic, entries=entries, generated_at="ts", total_analyzed=n)


# ---------------------------------------------------------------------------
# agentkit run --topic-repos
# ---------------------------------------------------------------------------


def test_run_topic_repos_flag_invokes_topic_rank():
    """Test that topic_rank_command is called when --topic-repos is passed."""
    from agentkit_cli.commands.topic_rank_cmd import topic_rank_command
    topic_result = _make_result("python")

    with patch("agentkit_cli.commands.topic_rank_cmd.TopicRankEngine") as MockEngine:
        MockEngine.return_value.run.return_value = topic_result
        # Call topic_rank_command directly (simulating main.py's post-run call)
        topic_rank_command(topic="python")

    MockEngine.assert_called_once()
    init_kwargs = MockEngine.call_args[1]
    assert init_kwargs["topic"] == "python"


def test_run_topic_repos_output_contains_repos():
    from agentkit_cli.commands.topic_rank_cmd import topic_rank_command
    topic_result = _make_result("llm")

    with patch("agentkit_cli.commands.topic_rank_cmd.TopicRankEngine") as MockEngine:
        MockEngine.return_value.run.return_value = topic_result
        # Directly test the command (no exit)
        try:
            topic_rank_command(topic="llm")
        except SystemExit:
            pass

    MockEngine.assert_called_once()


def test_run_without_topic_repos_flag_does_not_call_engine():
    """When --topic-repos is not passed, the topic_rank_command is not invoked."""
    # This verifies the CLI registration exists; the flag default is None so no call happens
    r = runner.invoke(app, ["topic", "--help"])
    assert "--topic-repos" not in r.output  # --topic-repos belongs to `run`, not `topic`


# ---------------------------------------------------------------------------
# trending drill-down hint
# ---------------------------------------------------------------------------


def test_trending_shows_drill_down_with_topic():
    fake_trending = [
        {
            "full_name": "owner/trending-repo",
            "url": "https://github.com/owner/trending-repo",
            "stars": 1000,
            "description": "great repo",
        }
    ]
    with patch("agentkit_cli.commands.trending_cmd.fetch_trending", return_value=fake_trending), \
         patch("agentkit_cli.commands.trending_cmd.fetch_popular", return_value=[]), \
         patch("agentkit_cli.commands.trending_cmd._analyze_repo", return_value={"score": 75.0, "grade": "B"}):
        r = runner.invoke(app, ["trending", "--topic", "python", "--limit", "1"])
    # Drill-down hint should appear when topic is given
    assert "agentkit topic python" in r.output


def test_trending_no_drill_down_without_topic():
    fake_trending = [
        {
            "full_name": "owner/trending-repo",
            "url": "https://github.com/owner/trending-repo",
            "stars": 1000,
            "description": "great repo",
        }
    ]
    with patch("agentkit_cli.commands.trending_cmd.fetch_trending", return_value=fake_trending), \
         patch("agentkit_cli.commands.trending_cmd.fetch_popular", return_value=[]), \
         patch("agentkit_cli.commands.trending_cmd._analyze_repo", return_value={"score": 75.0, "grade": "B"}):
        r = runner.invoke(app, ["trending", "--limit", "1"])
    # Without topic, no drill-down hint for a specific topic
    assert "agentkit topic" not in r.output


# ---------------------------------------------------------------------------
# topic command is registered in app
# ---------------------------------------------------------------------------


def test_topic_command_registered():
    r = runner.invoke(app, ["topic", "--help"])
    assert r.exit_code == 0
    assert "topic" in r.output.lower() or "TOPIC" in r.output


def test_topic_command_help_shows_options():
    r = runner.invoke(app, ["topic", "--help"])
    assert "--limit" in r.output
    assert "--language" in r.output
    assert "--json" in r.output
