"""D2 tests for topic-league CLI wiring."""
from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.engines.topic_league import TopicLeagueResult, LeagueResult, ScoreDistribution
from agentkit_cli.topic_rank import TopicRankEntry, TopicRankResult

runner = CliRunner()


def _entry(rank, name, score, grade="B", stars=10):
    return TopicRankEntry(rank=rank, repo_full_name=name, score=score, grade=grade, stars=stars)


def _mock_result(topic, entries):
    return TopicRankResult(topic=topic, entries=entries, generated_at="", total_analyzed=len(entries))


def _mock_league_result(topics):
    standings = []
    topic_results = {}
    for i, t in enumerate(topics):
        score = 80.0 - i * 10
        entries = [_entry(1, f"{t}/repo", score, "A" if score >= 80 else "B")]
        topic_results[t] = _mock_result(t, entries)
        dist = ScoreDistribution(min_score=score, mean_score=score, max_score=score)
        standings.append(LeagueResult(
            rank=i + 1,
            topic=t,
            score=score,
            repo_count=1,
            top_repo=f"{t}/repo",
            score_distribution=dist,
            grade="A" if score >= 80 else "B",
        ))
    return TopicLeagueResult(
        topics=topics,
        standings=standings,
        topic_results=topic_results,
        timestamp="2026-01-01",
    )


def _factory_from_result(result: TopicLeagueResult):
    def factory(topic, limit):
        mock = MagicMock()
        mock.run.return_value = result.topic_results[topic]
        return mock
    return factory


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_cli_error_single_topic():
    r = runner.invoke(app, ["topic-league", "python"])
    assert r.exit_code != 0
    assert "at least 2" in r.output.lower() or "2 topics" in r.output.lower() or "require" in r.output.lower()


def test_cli_error_no_topics():
    r = runner.invoke(app, ["topic-league"])
    assert r.exit_code != 0


def test_cli_two_topics_rich():
    result = _mock_league_result(["python", "rust"])
    factory = _factory_from_result(result)

    from agentkit_cli.commands import topic_league_cmd
    orig = topic_league_cmd.TopicLeagueEngine

    class FakeEngine:
        def __init__(self, **kwargs):
            self._engine = orig(**{**kwargs, "_engine_factory": factory})
        def run(self, **kwargs):
            return self._engine.run(**kwargs)

    import agentkit_cli.commands.topic_league_cmd as cmd_mod
    orig_cls = cmd_mod.TopicLeagueEngine
    cmd_mod.TopicLeagueEngine = FakeEngine
    try:
        r = runner.invoke(app, ["topic-league", "python", "rust"])
        assert r.exit_code == 0
        assert "python" in r.output or "rust" in r.output
    finally:
        cmd_mod.TopicLeagueEngine = orig_cls


def test_cli_json_output():
    result = _mock_league_result(["python", "rust"])
    factory = _factory_from_result(result)

    import agentkit_cli.commands.topic_league_cmd as cmd_mod
    orig_cls = cmd_mod.TopicLeagueEngine

    class FakeEngine:
        def __init__(self, **kwargs):
            kwargs["_engine_factory"] = factory
            self._engine = orig_cls(**kwargs)
        def run(self, **kwargs):
            return self._engine.run(**kwargs)

    cmd_mod.TopicLeagueEngine = FakeEngine
    try:
        r = runner.invoke(app, ["topic-league", "python", "rust", "--json"])
        assert r.exit_code == 0
        data = json.loads(r.output)
        assert "standings" in data
        assert len(data["standings"]) == 2
    finally:
        cmd_mod.TopicLeagueEngine = orig_cls


def test_cli_quiet_output():
    result = _mock_league_result(["python", "rust"])
    factory = _factory_from_result(result)

    import agentkit_cli.commands.topic_league_cmd as cmd_mod
    orig_cls = cmd_mod.TopicLeagueEngine

    class FakeEngine:
        def __init__(self, **kwargs):
            kwargs["_engine_factory"] = factory
            self._engine = orig_cls(**kwargs)
        def run(self, **kwargs):
            return self._engine.run(**kwargs)

    cmd_mod.TopicLeagueEngine = FakeEngine
    try:
        r = runner.invoke(app, ["topic-league", "python", "rust", "--quiet"])
        assert r.exit_code == 0
        assert "winner:" in r.output
    finally:
        cmd_mod.TopicLeagueEngine = orig_cls


def test_cli_repos_per_topic_flag():
    """--repos-per-topic is accepted without error."""
    result = _mock_league_result(["python", "rust"])
    factory = _factory_from_result(result)

    import agentkit_cli.commands.topic_league_cmd as cmd_mod
    orig_cls = cmd_mod.TopicLeagueEngine

    class FakeEngine:
        def __init__(self, **kwargs):
            self._rpt = kwargs.get("repos_per_topic")
            kwargs["_engine_factory"] = factory
            self._engine = orig_cls(**kwargs)
        def run(self, **kwargs):
            return self._engine.run(**kwargs)

    cmd_mod.TopicLeagueEngine = FakeEngine
    try:
        r = runner.invoke(app, ["topic-league", "python", "rust", "--repos-per-topic", "3"])
        assert r.exit_code == 0
    finally:
        cmd_mod.TopicLeagueEngine = orig_cls


def test_cli_parallel_flag():
    result = _mock_league_result(["python", "rust", "go"])
    factory = _factory_from_result(result)

    import agentkit_cli.commands.topic_league_cmd as cmd_mod
    orig_cls = cmd_mod.TopicLeagueEngine

    class FakeEngine:
        def __init__(self, **kwargs):
            kwargs["_engine_factory"] = factory
            self._engine = orig_cls(**kwargs)
        def run(self, **kwargs):
            return self._engine.run(**kwargs)

    cmd_mod.TopicLeagueEngine = FakeEngine
    try:
        r = runner.invoke(app, ["topic-league", "python", "rust", "go", "--parallel"])
        assert r.exit_code == 0
    finally:
        cmd_mod.TopicLeagueEngine = orig_cls


def test_cli_output_flag(tmp_path):
    result = _mock_league_result(["python", "rust"])
    factory = _factory_from_result(result)
    out_file = str(tmp_path / "league.html")

    import agentkit_cli.commands.topic_league_cmd as cmd_mod
    orig_cls = cmd_mod.TopicLeagueEngine

    class FakeEngine:
        def __init__(self, **kwargs):
            kwargs["_engine_factory"] = factory
            self._engine = orig_cls(**kwargs)
        def run(self, **kwargs):
            return self._engine.run(**kwargs)

    cmd_mod.TopicLeagueEngine = FakeEngine
    try:
        r = runner.invoke(app, ["topic-league", "python", "rust", "--output", out_file])
        assert r.exit_code == 0
        import os
        assert os.path.exists(out_file)
        with open(out_file) as f:
            html = f.read()
        assert "<!DOCTYPE html>" in html
    finally:
        cmd_mod.TopicLeagueEngine = orig_cls


def test_json_standings_schema():
    result = _mock_league_result(["python", "rust", "go"])
    factory = _factory_from_result(result)

    import agentkit_cli.commands.topic_league_cmd as cmd_mod
    orig_cls = cmd_mod.TopicLeagueEngine

    class FakeEngine:
        def __init__(self, **kwargs):
            kwargs["_engine_factory"] = factory
            self._engine = orig_cls(**kwargs)
        def run(self, **kwargs):
            return self._engine.run(**kwargs)

    cmd_mod.TopicLeagueEngine = FakeEngine
    try:
        r = runner.invoke(app, ["topic-league", "python", "rust", "go", "--json"])
        assert r.exit_code == 0
        data = json.loads(r.output)
        s = data["standings"][0]
        assert "rank" in s
        assert "topic" in s
        assert "score" in s
        assert "score_distribution" in s
        assert "top_repo" in s
    finally:
        cmd_mod.TopicLeagueEngine = orig_cls


def test_cli_three_topics_rich():
    result = _mock_league_result(["python", "rust", "go"])
    factory = _factory_from_result(result)

    import agentkit_cli.commands.topic_league_cmd as cmd_mod
    orig_cls = cmd_mod.TopicLeagueEngine

    class FakeEngine:
        def __init__(self, **kwargs):
            kwargs["_engine_factory"] = factory
            self._engine = orig_cls(**kwargs)
        def run(self, **kwargs):
            return self._engine.run(**kwargs)

    cmd_mod.TopicLeagueEngine = FakeEngine
    try:
        r = runner.invoke(app, ["topic-league", "python", "rust", "go"])
        assert r.exit_code == 0
        assert "python" in r.output
    finally:
        cmd_mod.TopicLeagueEngine = orig_cls


def test_cli_too_many_topics():
    topics = [f"t{i}" for i in range(11)]
    r = runner.invoke(app, ["topic-league"] + topics)
    assert r.exit_code != 0
