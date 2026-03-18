"""Tests for agentkit_cli/search.py (D1 — SearchEngine)."""
from __future__ import annotations

import json
import urllib.error
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

from agentkit_cli.search import SearchEngine, SearchResult


# ---------------------------------------------------------------------------
# SearchResult dataclass
# ---------------------------------------------------------------------------

def test_search_result_full_name():
    r = SearchResult(owner="pallets", repo="flask", url="https://github.com/pallets/flask",
                     stars=100, language="Python", description="x")
    assert r.full_name == "pallets/flask"


def test_search_result_missing_context_true():
    r = SearchResult(owner="a", repo="b", url="u", stars=0, language=None, description=None,
                     has_claude_md=False, has_agents_md=False)
    assert r.missing_context is True


def test_search_result_missing_context_false_when_claude_md():
    r = SearchResult(owner="a", repo="b", url="u", stars=0, language=None, description=None,
                     has_claude_md=True, has_agents_md=False)
    assert r.missing_context is False


def test_search_result_missing_context_false_when_agents_md():
    r = SearchResult(owner="a", repo="b", url="u", stars=0, language=None, description=None,
                     has_claude_md=False, has_agents_md=True)
    assert r.missing_context is False


def test_search_result_to_dict():
    r = SearchResult(owner="pallets", repo="flask", url="https://github.com/pallets/flask",
                     stars=5000, language="Python", description="micro fw",
                     has_claude_md=True, has_agents_md=False, score=0.75)
    d = r.to_dict()
    assert d["repo"] == "pallets/flask"
    assert d["stars"] == 5000
    assert d["has_claude_md"] is True
    assert d["has_agents_md"] is False
    assert d["missing_context"] is False
    assert "score" in d


def test_search_result_to_dict_missing_context_key():
    r = SearchResult(owner="x", repo="y", url="u", stars=0, language=None, description=None)
    d = r.to_dict()
    assert d["missing_context"] is True


# ---------------------------------------------------------------------------
# SearchEngine._build_query
# ---------------------------------------------------------------------------

def test_build_query_empty():
    q = SearchEngine._build_query("", language=None, topic=None, min_stars=None, max_stars=None)
    assert q == "stars:>=10"


def test_build_query_with_text():
    q = SearchEngine._build_query("ai agents", language=None, topic=None, min_stars=None, max_stars=None)
    assert "ai agents" in q


def test_build_query_language():
    q = SearchEngine._build_query("", language="python", topic=None, min_stars=None, max_stars=None)
    assert "language:python" in q


def test_build_query_topic():
    q = SearchEngine._build_query("", language=None, topic="ai-agents", min_stars=None, max_stars=None)
    assert "topic:ai-agents" in q


def test_build_query_min_stars():
    q = SearchEngine._build_query("", language=None, topic=None, min_stars=100, max_stars=None)
    assert "stars:>=100" in q


def test_build_query_max_stars():
    q = SearchEngine._build_query("", language=None, topic=None, min_stars=None, max_stars=500)
    assert "stars:<=500" in q


def test_build_query_star_range():
    q = SearchEngine._build_query("", language=None, topic=None, min_stars=100, max_stars=500)
    assert "stars:100..500" in q


def test_build_query_combined():
    q = SearchEngine._build_query("agent", language="python", topic="llm", min_stars=50, max_stars=None)
    assert "agent" in q
    assert "language:python" in q
    assert "topic:llm" in q
    assert "stars:>=50" in q


# ---------------------------------------------------------------------------
# SearchEngine._parse_item
# ---------------------------------------------------------------------------

def test_parse_item_basic():
    item = {
        "name": "flask",
        "html_url": "https://github.com/pallets/flask",
        "stargazers_count": 1000,
        "language": "Python",
        "description": "micro framework",
        "owner": {"login": "pallets"},
    }
    r = SearchEngine._parse_item(item)
    assert r.owner == "pallets"
    assert r.repo == "flask"
    assert r.stars == 1000
    assert r.language == "Python"


def test_parse_item_missing_fields():
    item = {"name": "foo", "owner": {"login": "bar"}}
    r = SearchEngine._parse_item(item)
    assert r.repo == "foo"
    assert r.stars == 0
    assert r.language is None


# ---------------------------------------------------------------------------
# SearchEngine._compute_score
# ---------------------------------------------------------------------------

def test_compute_score_missing_context_bonus():
    r = SearchResult(owner="a", repo="b", url="u", stars=5000, language=None, description=None,
                     has_claude_md=False, has_agents_md=False)
    score = SearchEngine._compute_score(r)
    assert score > 0.5  # missing context adds 0.5


def test_compute_score_has_context_no_bonus():
    r = SearchResult(owner="a", repo="b", url="u", stars=5000, language=None, description=None,
                     has_claude_md=True, has_agents_md=False)
    score = SearchEngine._compute_score(r)
    assert score <= 0.5


def test_compute_score_zero_stars_missing():
    r = SearchResult(owner="a", repo="b", url="u", stars=0, language=None, description=None)
    score = SearchEngine._compute_score(r)
    assert score == 0.5  # 0 star score + 0.5 context bonus


# ---------------------------------------------------------------------------
# SearchEngine._file_exists — mocked
# ---------------------------------------------------------------------------

def _make_response(data: dict):
    mock = MagicMock()
    mock.read.return_value = json.dumps(data).encode()
    mock.__enter__ = lambda s: s
    mock.__exit__ = MagicMock(return_value=False)
    return mock


def test_file_exists_returns_true():
    engine = SearchEngine()
    with patch("urllib.request.urlopen", return_value=_make_response({"name": "CLAUDE.md"})):
        assert engine._file_exists("pallets", "flask", "CLAUDE.md") is True


def test_file_exists_returns_false_on_404():
    engine = SearchEngine()
    err = urllib.error.HTTPError("url", 404, "Not Found", {}, None)
    with patch("urllib.request.urlopen", side_effect=err):
        assert engine._file_exists("pallets", "flask", "CLAUDE.md") is False


def test_file_exists_returns_false_on_exception():
    engine = SearchEngine()
    with patch("urllib.request.urlopen", side_effect=Exception("network error")):
        assert engine._file_exists("pallets", "flask", "CLAUDE.md") is False


# ---------------------------------------------------------------------------
# SearchEngine.search — mocked
# ---------------------------------------------------------------------------

_MOCK_ITEMS = [
    {
        "name": "repo1",
        "html_url": "https://github.com/user/repo1",
        "stargazers_count": 500,
        "language": "Python",
        "description": "test repo",
        "owner": {"login": "user"},
    },
    {
        "name": "repo2",
        "html_url": "https://github.com/user/repo2",
        "stargazers_count": 200,
        "language": "TypeScript",
        "description": "another repo",
        "owner": {"login": "user"},
    },
]


def test_search_returns_results():
    engine = SearchEngine()
    search_resp = {"items": _MOCK_ITEMS}

    def fake_request(url):
        if "search/repositories" in url:
            return {"items": _MOCK_ITEMS}
        raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)

    with patch.object(engine, "_github_request", side_effect=fake_request):
        with patch("time.sleep"):
            results = engine.search("test", check_contents=True)
    assert len(results) == 2


def test_search_missing_only_filter():
    engine = SearchEngine()

    def fake_request(url):
        if "search/repositories" in url:
            return {"items": _MOCK_ITEMS}
        raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)

    with patch.object(engine, "_github_request", side_effect=fake_request):
        with patch("time.sleep"):
            results = engine.search("test", missing_only=True, check_contents=True)
    # Both repos should be missing (404 for contents)
    assert all(r.missing_context for r in results)


def test_search_no_check():
    engine = SearchEngine()

    def fake_request(url):
        return {"items": _MOCK_ITEMS}

    with patch.object(engine, "_github_request", side_effect=fake_request):
        results = engine.search("test", check_contents=False)
    assert len(results) == 2
    # No contents checked — both fields default False
    for r in results:
        assert r.has_claude_md is False
        assert r.has_agents_md is False


def test_search_respects_limit():
    engine = SearchEngine()

    def fake_request(url):
        return {"items": _MOCK_ITEMS}

    with patch.object(engine, "_github_request", side_effect=fake_request):
        results = engine.search("test", limit=1, check_contents=False)
    assert len(results) <= 1


def test_search_uses_token():
    engine = SearchEngine(token="mytoken")
    assert engine.token == "mytoken"


def test_search_uses_env_token(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "envtoken")
    engine = SearchEngine()
    assert engine.token == "envtoken"


def test_check_repo_returns_result():
    engine = SearchEngine()
    item = _MOCK_ITEMS[0].copy()

    def fake_request(url):
        if "contents" in url:
            raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)
        return item

    with patch.object(engine, "_github_request", side_effect=fake_request):
        result = engine.check_repo("user", "repo1")
    assert result.owner == "user"
    assert result.repo == "repo1"
    assert result.missing_context is True
