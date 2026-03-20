"""D1 tests — TopicRankEngine and helper functions."""
from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

from agentkit_cli.topic_rank import (
    TopicRankEntry,
    TopicRankResult,
    TopicRankEngine,
    search_topic_repos,
    _heuristic_score,
    _score_repo,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

REPO_A = {
    "full_name": "owner/repo-a",
    "description": "A great AI agent library",
    "stargazers_count": 1500,
    "pushed_at": "2026-03-01T12:00:00Z",
    "license": {"key": "mit"},
    "has_wiki": True,
    "homepage": "https://example.com",
    "archived": False,
    "topics": ["agents", "llm", "python"],
}

REPO_B = {
    "full_name": "owner/repo-b",
    "description": "Another useful tool",
    "stargazers_count": 200,
    "pushed_at": "2026-02-01T12:00:00Z",
    "license": None,
    "has_wiki": False,
    "homepage": "",
    "archived": False,
    "topics": ["tool"],
}

REPO_C = {
    "full_name": "owner/repo-c",
    "description": "",
    "stargazers_count": 5,
    "pushed_at": "",
    "license": None,
    "has_wiki": False,
    "homepage": "",
    "archived": True,
    "topics": [],
}


# ---------------------------------------------------------------------------
# TopicRankEntry
# ---------------------------------------------------------------------------


def test_topic_rank_entry_to_dict():
    entry = TopicRankEntry(rank=1, repo_full_name="owner/repo", score=85.0, grade="A", stars=100, description="desc")
    d = entry.to_dict()
    assert d["rank"] == 1
    assert d["repo_full_name"] == "owner/repo"
    assert d["score"] == 85.0
    assert d["grade"] == "A"
    assert d["stars"] == 100
    assert d["description"] == "desc"


def test_topic_rank_entry_defaults():
    entry = TopicRankEntry(rank=2, repo_full_name="x/y", score=50.0, grade="C")
    assert entry.stars == 0
    assert entry.description == ""


# ---------------------------------------------------------------------------
# TopicRankResult
# ---------------------------------------------------------------------------


def test_topic_rank_result_to_dict_empty():
    result = TopicRankResult(topic="python", entries=[], generated_at="2026-03-20 00:00 UTC", total_analyzed=0)
    d = result.to_dict()
    assert d["topic"] == "python"
    assert d["entries"] == []
    assert d["total_analyzed"] == 0


def test_topic_rank_result_to_dict_with_entries():
    entry = TopicRankEntry(rank=1, repo_full_name="a/b", score=90.0, grade="A", stars=500, description="cool")
    result = TopicRankResult(topic="llm", entries=[entry], generated_at="ts", total_analyzed=1)
    d = result.to_dict()
    assert len(d["entries"]) == 1
    assert d["entries"][0]["repo_full_name"] == "a/b"


# ---------------------------------------------------------------------------
# _heuristic_score
# ---------------------------------------------------------------------------


def test_heuristic_score_rich_repo():
    score = _heuristic_score(REPO_A)
    assert score > 50.0
    assert score <= 100.0


def test_heuristic_score_bare_repo():
    score = _heuristic_score(REPO_C)
    assert score < 50.0


def test_heuristic_score_archived_penalty():
    score_archived = _heuristic_score(REPO_C)
    unarchived = dict(REPO_C)
    unarchived["archived"] = False
    score_live = _heuristic_score(unarchived)
    assert score_live >= score_archived


def test_heuristic_score_caps_at_100():
    rich = dict(REPO_A)
    rich["stargazers_count"] = 999999
    rich["topics"] = ["a"] * 100
    score = _heuristic_score(rich)
    assert score <= 100.0


def test_heuristic_score_none_stars():
    repo = dict(REPO_B)
    repo["stargazers_count"] = None
    score = _heuristic_score(repo)
    assert score >= 0.0


# ---------------------------------------------------------------------------
# search_topic_repos
# ---------------------------------------------------------------------------


def test_search_topic_repos_returns_items():
    fake_response = {"items": [REPO_A, REPO_B]}
    with patch("agentkit_cli.topic_rank._fetch_page", return_value=(fake_response, {}, None)):
        repos = search_topic_repos("python", limit=5)
    assert len(repos) == 2
    assert repos[0]["full_name"] == "owner/repo-a"


def test_search_topic_repos_with_language():
    fake_response = {"items": [REPO_A]}
    with patch("agentkit_cli.topic_rank._fetch_page") as mock_fp:
        mock_fp.return_value = (fake_response, {}, None)
        repos = search_topic_repos("python", limit=5, language="python")
    call_url = mock_fp.call_args[0][0]
    assert "language:python" in call_url


def test_search_topic_repos_respects_limit():
    items = [{"full_name": f"owner/repo-{i}"} for i in range(20)]
    fake_response = {"items": items}
    with patch("agentkit_cli.topic_rank._fetch_page", return_value=(fake_response, {}, None)):
        repos = search_topic_repos("python", limit=5)
    assert len(repos) == 5


def test_search_topic_repos_handles_exception():
    with patch("agentkit_cli.topic_rank._fetch_page", side_effect=Exception("network error")):
        repos = search_topic_repos("python")
    assert repos == []


def test_search_topic_repos_list_response():
    """Handle case where _fetch_page returns a list directly."""
    with patch("agentkit_cli.topic_rank._fetch_page", return_value=([REPO_A], {}, None)):
        repos = search_topic_repos("python", limit=5)
    assert repos == [REPO_A]


# ---------------------------------------------------------------------------
# TopicRankEngine
# ---------------------------------------------------------------------------


def test_engine_fetch_repos_override():
    engine = TopicRankEngine(topic="python", _repos_override=[REPO_A, REPO_B])
    repos = engine.fetch_repos()
    assert len(repos) == 2


def test_engine_fetch_repos_override_respects_limit():
    repos_list = [{"full_name": f"x/y-{i}"} for i in range(20)]
    engine = TopicRankEngine(topic="python", limit=3, _repos_override=repos_list)
    repos = engine.fetch_repos()
    assert len(repos) == 3


def test_engine_score_repo_uses_custom_fn():
    called = []

    def fake_score(repo, token, timeout):
        called.append(repo["full_name"])
        return 77.0

    engine = TopicRankEngine(topic="python", _repos_override=[REPO_A], _score_fn=fake_score)
    score = engine.score_repo(REPO_A)
    assert score == 77.0
    assert "owner/repo-a" in called


def test_engine_rank_repos_sorted_descending():
    engine = TopicRankEngine(topic="python", _repos_override=[], _score_fn=lambda r, t, to: 0.0)
    repo_scores = [(REPO_A, 90.0), (REPO_B, 50.0), (REPO_C, 70.0)]
    entries = engine.rank_repos(repo_scores)
    assert entries[0].score == 90.0
    assert entries[0].rank == 1
    assert entries[1].score == 70.0
    assert entries[2].score == 50.0


def test_engine_rank_repos_grade_assigned():
    engine = TopicRankEngine(topic="python", _repos_override=[], _score_fn=lambda r, t, to: 0.0)
    repo_scores = [(REPO_A, 85.0)]
    entries = engine.rank_repos(repo_scores)
    assert entries[0].grade == "A"


def test_engine_run_empty_repos():
    engine = TopicRankEngine(topic="python", _repos_override=[])
    result = engine.run()
    assert result.topic == "python"
    assert result.entries == []
    assert result.total_analyzed == 0


def test_engine_run_with_repos():
    scores_iter = iter([80.0, 60.0])

    def fake_score(repo, token, timeout):
        return next(scores_iter)

    engine = TopicRankEngine(
        topic="python",
        limit=2,
        _repos_override=[REPO_A, REPO_B],
        _score_fn=fake_score,
    )
    result = engine.run()
    assert result.total_analyzed == 2
    assert len(result.entries) == 2
    assert result.entries[0].score == 80.0
    assert result.entries[0].rank == 1


def test_engine_run_calls_progress_cb():
    calls = []

    def fake_score(repo, token, timeout):
        return 50.0

    engine = TopicRankEngine(
        topic="python",
        _repos_override=[REPO_A, REPO_B],
        _score_fn=fake_score,
    )
    result = engine.run(progress_cb=lambda i, n, name: calls.append((i, n, name)))
    assert len(calls) == 2


def test_engine_run_generated_at_not_empty():
    engine = TopicRankEngine(
        topic="llm",
        _repos_override=[REPO_A],
        _score_fn=lambda r, t, to: 75.0,
    )
    result = engine.run()
    assert result.generated_at != ""


def test_engine_limit_capped_at_25():
    engine = TopicRankEngine(topic="python", limit=100)
    assert engine.limit == 25
