"""D2 tests for ecosystem CLI command."""
from __future__ import annotations

import json
from typing import List
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.engines.ecosystem import EcosystemResult, PRESETS
from agentkit_cli.engines.topic_league import (
    TopicLeagueResult, LeagueResult, ScoreDistribution, TopicLeagueEngine
)
from agentkit_cli.topic_rank import TopicRankEntry, TopicRankResult


runner = CliRunner()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_eco_result(topics=None, preset="default"):
    if topics is None:
        topics = ["python", "rust", "go", "java", "typescript"]
    scores = [80.0, 75.0, 70.0, 65.0, 60.0]
    standings = []
    topic_results = {}
    for i, (t, s) in enumerate(zip(topics, scores[:len(topics)]), 1):
        dist = ScoreDistribution(min_score=s - 5, mean_score=s, max_score=s + 5)
        standings.append(LeagueResult(rank=i, topic=t, score=s, repo_count=3,
                                      top_repo=f"org/{t}-kit", score_distribution=dist, grade="B"))
        entry = TopicRankEntry(rank=1, repo_full_name=f"org/{t}-kit", score=s,
                               grade="B", stars=100, description="")
        topic_results[t] = TopicRankResult(
            topic=t, entries=[entry], generated_at="2026-01-01", total_analyzed=1
        )
    lr = TopicLeagueResult(topics=topics, standings=standings,
                           topic_results=topic_results, timestamp="2026-01-01")
    return EcosystemResult(preset=preset, topics=topics, standings=standings,
                           league_result=lr, timestamp="2026-01-01 00:00 UTC")


def _mock_factory(eco_result):
    """Return _league_factory that yields a mock engine returning eco_result.league_result."""
    lr = eco_result.league_result
    def factory(**kwargs):
        mock = MagicMock()
        mock.run.return_value = lr
        return mock
    return factory


# ---------------------------------------------------------------------------
# CLI: basic invocation
# ---------------------------------------------------------------------------

def test_ecosystem_json_output():
    eco = _make_eco_result()
    factory = _mock_factory(eco)
    with patch("agentkit_cli.engines.ecosystem.EcosystemEngine._make_league_engine") as mock_make:
        mock_eng = MagicMock()
        mock_eng.run.return_value = eco.league_result
        mock_make.return_value = mock_eng
        result = runner.invoke(app, ["ecosystem", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "standings" in data
    assert "winner" in data


def test_ecosystem_custom_topics_json():
    eco = _make_eco_result(topics=["python", "rust"])
    with patch("agentkit_cli.engines.ecosystem.EcosystemEngine._make_league_engine") as mock_make:
        mock_eng = MagicMock()
        mock_eng.run.return_value = eco.league_result
        mock_make.return_value = mock_eng
        result = runner.invoke(app, ["ecosystem", "--preset", "custom", "--topics", "python,rust", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "standings" in data


def test_ecosystem_invalid_preset_error():
    result = runner.invoke(app, ["ecosystem", "--preset", "bogus", "--json"])
    assert result.exit_code != 0
    data = json.loads(result.output)
    assert "error" in data


def test_ecosystem_custom_too_few_topics_error():
    result = runner.invoke(app, ["ecosystem", "--preset", "custom", "--topics", "python", "--json"])
    assert result.exit_code != 0
    data = json.loads(result.output)
    assert "error" in data


def test_ecosystem_json_has_preset():
    eco = _make_eco_result()
    with patch("agentkit_cli.engines.ecosystem.EcosystemEngine._make_league_engine") as mock_make:
        mock_eng = MagicMock()
        mock_eng.run.return_value = eco.league_result
        mock_make.return_value = mock_eng
        result = runner.invoke(app, ["ecosystem", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["preset"] == "default"


def test_ecosystem_json_has_total_repos():
    eco = _make_eco_result()
    with patch("agentkit_cli.engines.ecosystem.EcosystemEngine._make_league_engine") as mock_make:
        mock_eng = MagicMock()
        mock_eng.run.return_value = eco.league_result
        mock_make.return_value = mock_eng
        result = runner.invoke(app, ["ecosystem", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "total_repos" in data


def test_ecosystem_json_winner_present():
    eco = _make_eco_result()
    with patch("agentkit_cli.engines.ecosystem.EcosystemEngine._make_league_engine") as mock_make:
        mock_eng = MagicMock()
        mock_eng.run.return_value = eco.league_result
        mock_make.return_value = mock_eng
        result = runner.invoke(app, ["ecosystem", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["winner"] is not None
    assert "topic" in data["winner"]


# ---------------------------------------------------------------------------
# ecosystem_command function direct
# ---------------------------------------------------------------------------

def test_ecosystem_command_quiet():
    from agentkit_cli.commands.ecosystem_cmd import ecosystem_command
    eco = _make_eco_result()
    factory = _mock_factory(eco)
    import io, sys
    # should not raise
    ecosystem_command(
        preset="default",
        quiet=True,
        json_output=False,
        _league_factory=factory,
    )


def test_ecosystem_command_json_direct():
    from agentkit_cli.commands.ecosystem_cmd import ecosystem_command
    eco = _make_eco_result()
    factory = _mock_factory(eco)
    import io
    from contextlib import redirect_stdout
    buf = io.StringIO()
    with redirect_stdout(buf):
        ecosystem_command(
            preset="default",
            json_output=True,
            _league_factory=factory,
        )
    data = json.loads(buf.getvalue())
    assert "standings" in data


# ---------------------------------------------------------------------------
# run --ecosystem integration
# ---------------------------------------------------------------------------

def test_run_ecosystem_flag_in_json():
    eco = _make_eco_result()
    with patch("agentkit_cli.commands.run_cmd.run_command") as mock_run:
        mock_run.return_value = None
        with patch("agentkit_cli.engines.ecosystem.EcosystemEngine._make_league_engine") as mock_make:
            mock_eng = MagicMock()
            mock_eng.run.return_value = eco.league_result
            mock_make.return_value = mock_eng
            result = runner.invoke(app, ["run", "--ecosystem", "default", "--json"])
    # run_command is mocked so it doesn't produce output; just verify no crash
    assert result.exit_code == 0
