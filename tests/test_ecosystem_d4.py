"""D4 tests: ecosystem integration — run --ecosystem, doctor check, JSON structure."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.engines.ecosystem import EcosystemResult
from agentkit_cli.engines.topic_league import (
    TopicLeagueResult, LeagueResult, ScoreDistribution
)
from agentkit_cli.topic_rank import TopicRankEntry, TopicRankResult
from agentkit_cli.doctor import check_ecosystem_available


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
        dist = ScoreDistribution(min_score=s-5, mean_score=s, max_score=s+5)
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


# ---------------------------------------------------------------------------
# Doctor check
# ---------------------------------------------------------------------------

def test_doctor_ecosystem_check_passes():
    result = check_ecosystem_available()
    assert result.status == "pass"
    assert result.id == "toolchain.ecosystem"


def test_doctor_ecosystem_check_name():
    result = check_ecosystem_available()
    assert "ecosystem" in result.name.lower()


def test_doctor_ecosystem_check_category():
    result = check_ecosystem_available()
    assert result.category == "toolchain"


# ---------------------------------------------------------------------------
# JSON output structure
# ---------------------------------------------------------------------------

def test_json_output_required_keys():
    eco = _make_eco_result()
    with patch("agentkit_cli.engines.ecosystem.EcosystemEngine._make_league_engine") as mock_make:
        mock_eng = MagicMock()
        mock_eng.run.return_value = eco.league_result
        mock_make.return_value = mock_eng
        result = runner.invoke(app, ["ecosystem", "--json"])
    data = json.loads(result.output)
    for key in ("preset", "topics", "standings", "winner", "total_repos", "timestamp"):
        assert key in data, f"Missing key: {key}"


def test_json_standings_have_required_fields():
    eco = _make_eco_result()
    with patch("agentkit_cli.engines.ecosystem.EcosystemEngine._make_league_engine") as mock_make:
        mock_eng = MagicMock()
        mock_eng.run.return_value = eco.league_result
        mock_make.return_value = mock_eng
        result = runner.invoke(app, ["ecosystem", "--json"])
    data = json.loads(result.output)
    for s in data["standings"]:
        for key in ("rank", "topic", "score", "grade", "repo_count", "top_repo"):
            assert key in s, f"Standings entry missing: {key}"


def test_json_winner_has_topic():
    eco = _make_eco_result()
    with patch("agentkit_cli.engines.ecosystem.EcosystemEngine._make_league_engine") as mock_make:
        mock_eng = MagicMock()
        mock_eng.run.return_value = eco.league_result
        mock_make.return_value = mock_eng
        result = runner.invoke(app, ["ecosystem", "--json"])
    data = json.loads(result.output)
    assert "topic" in data["winner"]


# ---------------------------------------------------------------------------
# GITHUB_TOKEN guard
# ---------------------------------------------------------------------------

def test_no_token_warns_but_does_not_crash(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    eco = _make_eco_result()
    with patch("agentkit_cli.engines.ecosystem.EcosystemEngine._make_league_engine") as mock_make:
        mock_eng = MagicMock()
        mock_eng.run.return_value = eco.league_result
        mock_make.return_value = mock_eng
        result = runner.invoke(app, ["ecosystem", "--json"])
    # Should still produce JSON output
    data = json.loads(result.output)
    assert "standings" in data


# ---------------------------------------------------------------------------
# run --ecosystem integration
# ---------------------------------------------------------------------------

def test_run_command_accepts_ecosystem_param():
    """Verify run_command signature accepts ecosystem parameter."""
    import inspect
    from agentkit_cli.commands.run_cmd import run_command
    sig = inspect.signature(run_command)
    assert "ecosystem" in sig.parameters


def test_run_ecosystem_extended_preset_param():
    """Verify run_command ecosystem param has default None."""
    import inspect
    from agentkit_cli.commands.run_cmd import run_command
    sig = inspect.signature(run_command)
    param = sig.parameters["ecosystem"]
    assert param.default is None


def test_ecosystem_json_parseable_by_run_consumer():
    """Verify ecosystem to_dict output is JSON serializable (parseable by report consumers)."""
    eco = _make_eco_result()
    d = eco.to_dict()
    serialized = json.dumps(d)
    parsed = json.loads(serialized)
    assert parsed["preset"] == "default"
    assert len(parsed["standings"]) == 5
