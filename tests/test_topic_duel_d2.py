"""D2 tests for topic-duel CLI command."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.engines.topic_duel import TopicDuelResult, TopicDuelDimension
from agentkit_cli.topic_rank import TopicRankEntry, TopicRankResult

runner = CliRunner()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _entry(rank, name, score, grade="B"):
    return TopicRankEntry(rank=rank, repo_full_name=name, score=score, grade=grade, stars=100)


def _rank_result(topic, entries):
    return TopicRankResult(topic=topic, entries=entries, generated_at="2026-01-01 00:00 UTC", total_analyzed=len(entries))


def _duel_result(t1="fastapi", t2="django", winner="topic1", avg1=75.0, avg2=60.0):
    e1 = [_entry(1, f"{t1}/repo", avg1, "B")]
    e2 = [_entry(1, f"{t2}/repo", avg2, "C")]
    dims = [TopicDuelDimension(name="avg_score", topic1_value=avg1, topic2_value=avg2, winner=winner)]
    return TopicDuelResult(
        topic1=t1,
        topic2=t2,
        topic1_result=_rank_result(t1, e1),
        topic2_result=_rank_result(t2, e2),
        dimensions=dims,
        overall_winner=winner,
        topic1_avg_score=avg1,
        topic2_avg_score=avg2,
        timestamp="2026-01-01 00:00 UTC",
    )


def _mock_engine_factory(result):
    def _factory(*a, **kw):
        mock = MagicMock()
        mock.run.return_value = result
        return mock
    return _factory


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_topic_duel_basic_output():
    result = _duel_result()
    with patch("agentkit_cli.commands.topic_duel_cmd.TopicDuelEngine") as MockEngine:
        MockEngine.return_value.run.return_value = result
        r = runner.invoke(app, ["topic-duel", "fastapi", "django", "--quiet"])
    assert r.exit_code == 0
    assert "fastapi" in r.output


def test_topic_duel_quiet_prints_winner():
    result = _duel_result(winner="topic1")
    with patch("agentkit_cli.commands.topic_duel_cmd.TopicDuelEngine") as MockEngine:
        MockEngine.return_value.run.return_value = result
        r = runner.invoke(app, ["topic-duel", "fastapi", "django", "--quiet"])
    assert r.exit_code == 0
    assert "fastapi" in r.output


def test_topic_duel_quiet_topic2_wins():
    result = _duel_result(winner="topic2")
    with patch("agentkit_cli.commands.topic_duel_cmd.TopicDuelEngine") as MockEngine:
        MockEngine.return_value.run.return_value = result
        r = runner.invoke(app, ["topic-duel", "fastapi", "django", "--quiet"])
    assert r.exit_code == 0
    assert "django" in r.output


def test_topic_duel_quiet_tie():
    result = _duel_result(winner="tie", avg1=70.0, avg2=70.0)
    with patch("agentkit_cli.commands.topic_duel_cmd.TopicDuelEngine") as MockEngine:
        MockEngine.return_value.run.return_value = result
        r = runner.invoke(app, ["topic-duel", "a", "b", "--quiet"])
    assert r.exit_code == 0
    assert "tie" in r.output


def test_topic_duel_json_output():
    result = _duel_result()
    with patch("agentkit_cli.commands.topic_duel_cmd.TopicDuelEngine") as MockEngine:
        MockEngine.return_value.run.return_value = result
        r = runner.invoke(app, ["topic-duel", "fastapi", "django", "--json"])
    assert r.exit_code == 0
    data = json.loads(r.output)
    assert data["topic1"] == "fastapi"
    assert data["topic2"] == "django"
    assert "overall_winner" in data
    assert "dimensions" in data


def test_topic_duel_repos_per_topic_passed():
    result = _duel_result()
    with patch("agentkit_cli.commands.topic_duel_cmd.TopicDuelEngine") as MockEngine:
        MockEngine.return_value.run.return_value = result
        r = runner.invoke(app, ["topic-duel", "fastapi", "django", "--repos-per-topic", "3", "--quiet"])
    assert r.exit_code == 0
    # Verify engine was called with repos_per_topic=3
    call_kwargs = MockEngine.call_args[1]
    assert call_kwargs.get("repos_per_topic") == 3


def test_topic_duel_error_on_empty_topics():
    r = runner.invoke(app, ["topic-duel", "", "django"])
    assert r.exit_code != 0


def test_topic_duel_command_is_registered():
    """Verify topic-duel is registered in the app."""
    result = runner.invoke(app, ["--help"])
    assert "topic-duel" in result.output


def test_topic_duel_engine_exception_handled():
    with patch("agentkit_cli.commands.topic_duel_cmd.TopicDuelEngine") as MockEngine:
        MockEngine.return_value.run.side_effect = RuntimeError("API failure")
        r = runner.invoke(app, ["topic-duel", "fastapi", "django", "--quiet"])
    assert r.exit_code != 0


def test_topic_duel_json_share_url_in_to_dict():
    """share_url can be added to the to_dict output."""
    result = _duel_result()
    out = result.to_dict()
    out["share_url"] = "https://here.now/abc"
    assert out.get("share_url") == "https://here.now/abc"
    assert out["topic1"] == "fastapi"
    assert "dimensions" in out
