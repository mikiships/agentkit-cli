"""D1 tests for EcosystemEngine."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from agentkit_cli.engines.ecosystem import (
    EcosystemEngine,
    EcosystemResult,
    PRESETS,
    LANG_EMOJI,
    get_preset_topics,
)
from agentkit_cli.engines.topic_league import (
    TopicLeagueResult,
    LeagueResult,
    ScoreDistribution,
)
from agentkit_cli.topic_rank import TopicRankEntry, TopicRankResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_league_result(topics, scores):
    """Build a minimal TopicLeagueResult with given topics and scores."""
    standings = []
    topic_results = {}
    for i, (topic, score) in enumerate(zip(topics, scores), 1):
        dist = ScoreDistribution(min_score=score - 5, mean_score=score, max_score=score + 5)
        standings.append(LeagueResult(
            rank=i, topic=topic, score=score, repo_count=3,
            top_repo=f"org/{topic}-kit", score_distribution=dist, grade="B",
        ))
        entry = TopicRankEntry(rank=1, repo_full_name=f"org/{topic}-kit", score=score,
                               grade="B", stars=100, description="")
        topic_results[topic] = TopicRankResult(
            topic=topic, entries=[entry], generated_at="2026-01-01", total_analyzed=1
        )
    # re-sort by score desc
    standings.sort(key=lambda s: s.score, reverse=True)
    for i, s in enumerate(standings, 1):
        s.rank = i
    return TopicLeagueResult(
        topics=topics,
        standings=standings,
        topic_results=topic_results,
        timestamp="2026-01-01 00:00 UTC",
    )


def _make_league_factory(topics, scores):
    """Return a _league_factory callable that yields a mock TopicLeagueEngine."""
    lr = _make_league_result(topics, scores)
    def factory(**kwargs):
        mock = MagicMock()
        mock.run.return_value = lr
        return mock
    return factory


# ---------------------------------------------------------------------------
# Preset tests
# ---------------------------------------------------------------------------

def test_default_preset_topics():
    topics = get_preset_topics("default")
    assert "python" in topics
    assert "rust" in topics
    assert len(topics) == 5


def test_extended_preset_topics():
    topics = get_preset_topics("extended")
    assert len(topics) == 12
    assert "elixir" in topics
    assert "kotlin" in topics


def test_unknown_preset_raises():
    with pytest.raises(ValueError, match="Unknown preset"):
        get_preset_topics("nope")


def test_preset_keys():
    assert set(PRESETS.keys()) == {"default", "extended"}


# ---------------------------------------------------------------------------
# EcosystemEngine init
# ---------------------------------------------------------------------------

def test_init_default_preset():
    engine = EcosystemEngine(preset="default")
    assert engine.preset == "default"
    assert len(engine.topics) == 5
    assert engine.parallel is True


def test_init_extended_preset():
    engine = EcosystemEngine(preset="extended")
    assert len(engine.topics) == 12


def test_init_custom_preset():
    engine = EcosystemEngine(preset="custom", topics=["python", "rust"])
    assert engine.preset == "custom"
    assert engine.topics == ["python", "rust"]


def test_init_custom_too_few_raises():
    with pytest.raises(ValueError, match="at least 2"):
        EcosystemEngine(preset="custom", topics=["python"])


def test_init_custom_empty_raises():
    with pytest.raises(ValueError, match="at least 2"):
        EcosystemEngine(preset="custom", topics=[])


def test_init_repos_per_topic_capped():
    engine = EcosystemEngine(preset="default", repos_per_topic=99)
    assert engine.repos_per_topic == EcosystemEngine.MAX_REPOS_PER_TOPIC


def test_init_repos_per_topic_minimum():
    engine = EcosystemEngine(preset="default", repos_per_topic=0)
    assert engine.repos_per_topic == 1


# ---------------------------------------------------------------------------
# EcosystemEngine.run — mocked
# ---------------------------------------------------------------------------

def test_run_returns_ecosystem_result():
    topics = ["python", "rust", "go", "java", "typescript"]
    scores = [80.0, 75.0, 70.0, 65.0, 60.0]
    factory = _make_league_factory(topics, scores)
    engine = EcosystemEngine(preset="default", _league_factory=factory)
    result = engine.run()
    assert isinstance(result, EcosystemResult)


def test_run_winner_is_highest_score():
    topics = ["python", "rust", "go", "java", "typescript"]
    scores = [80.0, 90.0, 70.0, 65.0, 60.0]
    factory = _make_league_factory(topics, scores)
    engine = EcosystemEngine(preset="default", _league_factory=factory)
    result = engine.run()
    assert result.winner is not None
    assert result.winner.score == max(scores)


def test_run_total_repos():
    topics = ["python", "rust", "go", "java", "typescript"]
    scores = [80.0, 75.0, 70.0, 65.0, 60.0]
    factory = _make_league_factory(topics, scores)
    engine = EcosystemEngine(preset="default", _league_factory=factory)
    result = engine.run()
    # each has repo_count=3
    assert result.total_repos == 15


def test_run_timestamp_set():
    topics = ["python", "rust", "go", "java", "typescript"]
    scores = [80.0, 75.0, 70.0, 65.0, 60.0]
    factory = _make_league_factory(topics, scores)
    engine = EcosystemEngine(preset="default", _league_factory=factory)
    result = engine.run()
    assert result.timestamp


def test_run_preset_in_result():
    topics = ["python", "rust", "go", "java", "typescript"]
    scores = [80.0, 75.0, 70.0, 65.0, 60.0]
    factory = _make_league_factory(topics, scores)
    engine = EcosystemEngine(preset="default", _league_factory=factory)
    result = engine.run()
    assert result.preset == "default"


# ---------------------------------------------------------------------------
# EcosystemResult.to_dict
# ---------------------------------------------------------------------------

def test_to_dict_required_keys():
    topics = ["python", "rust", "go", "java", "typescript"]
    scores = [80.0, 75.0, 70.0, 65.0, 60.0]
    factory = _make_league_factory(topics, scores)
    engine = EcosystemEngine(preset="default", _league_factory=factory)
    result = engine.run()
    d = result.to_dict()
    for key in ("preset", "topics", "standings", "winner", "total_repos", "timestamp"):
        assert key in d, f"Missing key: {key}"


def test_to_dict_standings_are_dicts():
    topics = ["python", "rust", "go", "java", "typescript"]
    scores = [80.0, 75.0, 70.0, 65.0, 60.0]
    factory = _make_league_factory(topics, scores)
    engine = EcosystemEngine(preset="default", _league_factory=factory)
    result = engine.run()
    d = result.to_dict()
    assert all(isinstance(s, dict) for s in d["standings"])


# ---------------------------------------------------------------------------
# LANG_EMOJI map
# ---------------------------------------------------------------------------

def test_lang_emoji_python():
    assert LANG_EMOJI["python"] == "🐍"


def test_lang_emoji_rust():
    assert LANG_EMOJI["rust"] == "🦀"


def test_lang_emoji_go():
    assert LANG_EMOJI["go"] == "🐹"
