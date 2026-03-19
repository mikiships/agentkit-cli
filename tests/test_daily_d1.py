"""Tests for D1: DailyLeaderboardEngine — agentkit_cli/engines/daily_leaderboard.py"""
from __future__ import annotations

import json
from datetime import date, datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from agentkit_cli.engines.daily_leaderboard import (
    DailyLeaderboard,
    RankedRepo,
    _build_query,
    _build_url,
    _build_headers,
    _normalize_item,
    _score_repo,
    fetch_trending_repos,
    GITHUB_API_BASE,
)

# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

SAMPLE_RAW_ITEMS = [
    {
        "full_name": "acme/agent-kit",
        "description": "An AI agent toolkit",
        "stargazers_count": 5000,
        "language": "Python",
        "html_url": "https://github.com/acme/agent-kit",
    },
    {
        "full_name": "beta/llm-core",
        "description": "Core LLM primitives",
        "stargazers_count": 2000,
        "language": "TypeScript",
        "html_url": "https://github.com/beta/llm-core",
    },
    {
        "full_name": "gamma/go-tools",
        "description": "Go CLI utilities",
        "stargazers_count": 500,
        "language": "Go",
        "html_url": "https://github.com/gamma/go-tools",
    },
]

SAMPLE_API_RESPONSE = json.dumps({"items": SAMPLE_RAW_ITEMS, "total_count": 3}).encode()


def _make_mock_urlopen(response_bytes: bytes):
    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=ctx)
    ctx.__exit__ = MagicMock(return_value=False)
    ctx.read.return_value = response_bytes
    return ctx


# ---------------------------------------------------------------------------
# _build_query
# ---------------------------------------------------------------------------

class TestBuildQuery:
    def test_returns_string(self):
        q = _build_query(date(2026, 3, 19))
        assert isinstance(q, str)

    def test_contains_date(self):
        q = _build_query(date(2026, 3, 19))
        assert "2026-03-19" in q

    def test_contains_stars_filter(self):
        q = _build_query(date(2026, 1, 1))
        assert "stars:>" in q

    def test_contains_pushed_filter(self):
        q = _build_query(date(2026, 1, 1))
        assert "pushed:>" in q


# ---------------------------------------------------------------------------
# _build_url
# ---------------------------------------------------------------------------

class TestBuildUrl:
    def test_returns_string(self):
        url = _build_url("stars:>100", 10)
        assert isinstance(url, str)

    def test_starts_with_api_base(self):
        url = _build_url("stars:>100", 10)
        assert url.startswith(GITHUB_API_BASE)

    def test_contains_sort_stars(self):
        url = _build_url("stars:>100", 10)
        assert "sort=stars" in url

    def test_contains_per_page(self):
        url = _build_url("stars:>100", 15)
        assert "per_page=15" in url


# ---------------------------------------------------------------------------
# _build_headers
# ---------------------------------------------------------------------------

class TestBuildHeaders:
    def test_no_token(self):
        with patch.dict("os.environ", {}, clear=True):
            headers = _build_headers(token=None)
        assert "Accept" in headers
        assert "Authorization" not in headers

    def test_with_explicit_token(self):
        headers = _build_headers(token="ghp_test")
        assert headers["Authorization"] == "Bearer ghp_test"

    def test_with_env_token(self):
        with patch.dict("os.environ", {"GITHUB_TOKEN": "env_token"}):
            headers = _build_headers()
        assert headers["Authorization"] == "Bearer env_token"


# ---------------------------------------------------------------------------
# _normalize_item
# ---------------------------------------------------------------------------

class TestNormalizeItem:
    def test_basic_fields(self):
        item = SAMPLE_RAW_ITEMS[0]
        norm = _normalize_item(item)
        assert norm["full_name"] == "acme/agent-kit"
        assert norm["description"] == "An AI agent toolkit"
        assert norm["stars"] == 5000
        assert norm["language"] == "Python"
        assert norm["url"] == "https://github.com/acme/agent-kit"

    def test_missing_description_defaults_empty(self):
        norm = _normalize_item({"full_name": "x/y", "description": None})
        assert norm["description"] == ""

    def test_missing_language_defaults_empty(self):
        norm = _normalize_item({"full_name": "x/y"})
        assert norm["language"] == ""

    def test_url_fallback(self):
        norm = _normalize_item({"full_name": "x/y"})
        assert norm["url"] == "https://github.com/x/y"

    def test_stars_defaults_zero(self):
        norm = _normalize_item({"full_name": "x/y"})
        assert norm["stars"] == 0


# ---------------------------------------------------------------------------
# _score_repo
# ---------------------------------------------------------------------------

class TestScoreRepo:
    def test_returns_tuple(self):
        score, finding = _score_repo({"full_name": "x/y", "stars": 100})
        assert isinstance(score, float)
        assert isinstance(finding, str)

    def test_high_stars_boosts_score(self):
        score_high, _ = _score_repo({"full_name": "x/y", "stars": 15000})
        score_low, _ = _score_repo({"full_name": "x/y", "stars": 50})
        assert score_high > score_low

    def test_python_language_boosts_score(self):
        score_py, _ = _score_repo({"full_name": "x/y", "stars": 100, "language": "Python"})
        score_go, _ = _score_repo({"full_name": "x/y", "stars": 100, "language": "Go"})
        assert score_py >= score_go

    def test_agent_keyword_boosts_score(self):
        score_agent, _ = _score_repo({"full_name": "x/y", "stars": 100, "description": "An AI agent SDK"})
        score_plain, _ = _score_repo({"full_name": "x/y", "stars": 100, "description": "A random tool"})
        assert score_agent > score_plain

    def test_score_capped_at_100(self):
        score, _ = _score_repo({
            "full_name": "x/y",
            "stars": 50000,
            "language": "Python",
            "description": "AI agent framework for llm",
        })
        assert score <= 100.0

    def test_score_at_least_50(self):
        score, _ = _score_repo({"full_name": "x/y", "stars": 0})
        assert score >= 50.0


# ---------------------------------------------------------------------------
# fetch_trending_repos
# ---------------------------------------------------------------------------

class TestFetchTrendingRepos:
    def test_returns_daily_leaderboard(self):
        with patch("agentkit_cli.engines.daily_leaderboard.urllib_request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = _make_mock_urlopen(SAMPLE_API_RESPONSE)
            result = fetch_trending_repos(for_date=date(2026, 3, 19), limit=5)
        assert isinstance(result, DailyLeaderboard)

    def test_repos_are_ranked(self):
        with patch("agentkit_cli.engines.daily_leaderboard.urllib_request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = _make_mock_urlopen(SAMPLE_API_RESPONSE)
            result = fetch_trending_repos(for_date=date(2026, 3, 19))
        for i, repo in enumerate(result.repos, start=1):
            assert repo.rank == i

    def test_repos_sorted_by_score_desc(self):
        with patch("agentkit_cli.engines.daily_leaderboard.urllib_request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = _make_mock_urlopen(SAMPLE_API_RESPONSE)
            result = fetch_trending_repos(for_date=date(2026, 3, 19))
        scores = [r.composite_score for r in result.repos]
        assert scores == sorted(scores, reverse=True)

    def test_date_stored(self):
        with patch("agentkit_cli.engines.daily_leaderboard.urllib_request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = _make_mock_urlopen(SAMPLE_API_RESPONSE)
            result = fetch_trending_repos(for_date=date(2026, 3, 19))
        assert result.date == date(2026, 3, 19)

    def test_default_date_is_today(self):
        with patch("agentkit_cli.engines.daily_leaderboard.urllib_request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = _make_mock_urlopen(SAMPLE_API_RESPONSE)
            result = fetch_trending_repos()
        assert result.date == date.today()

    def test_limit_respected(self):
        with patch("agentkit_cli.engines.daily_leaderboard.urllib_request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = _make_mock_urlopen(SAMPLE_API_RESPONSE)
            result = fetch_trending_repos(limit=2)
        assert len(result.repos) <= 2

    def test_fallback_when_api_fails(self):
        with patch("agentkit_cli.engines.daily_leaderboard.urllib_request.urlopen", side_effect=Exception("network")):
            result = fetch_trending_repos(for_date=date(2026, 3, 19))
        assert len(result.repos) > 0

    def test_custom_fallback(self):
        fallback = [
            {
                "full_name": "test/repo",
                "description": "Test",
                "stars": 100,
                "language": "Python",
                "url": "https://github.com/test/repo",
                "composite_score": 75.0,
                "top_finding": "Test finding",
            }
        ]
        with patch("agentkit_cli.engines.daily_leaderboard.urllib_request.urlopen", side_effect=Exception("net")):
            result = fetch_trending_repos(_fallback=fallback)
        assert result.repos[0].full_name == "test/repo"

    def test_ranked_repo_fields(self):
        with patch("agentkit_cli.engines.daily_leaderboard.urllib_request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = _make_mock_urlopen(SAMPLE_API_RESPONSE)
            result = fetch_trending_repos()
        repo = result.repos[0]
        assert hasattr(repo, "rank")
        assert hasattr(repo, "full_name")
        assert hasattr(repo, "composite_score")
        assert hasattr(repo, "top_finding")

    def test_generated_at_is_datetime(self):
        with patch("agentkit_cli.engines.daily_leaderboard.urllib_request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = _make_mock_urlopen(SAMPLE_API_RESPONSE)
            result = fetch_trending_repos()
        assert isinstance(result.generated_at, datetime)

    def test_api_error_falls_back(self):
        from urllib.error import HTTPError
        with patch("agentkit_cli.engines.daily_leaderboard.urllib_request.urlopen",
                   side_effect=HTTPError(None, 403, "Forbidden", {}, None)):
            result = fetch_trending_repos()
        assert isinstance(result, DailyLeaderboard)

    def test_total_fetched_set_on_success(self):
        with patch("agentkit_cli.engines.daily_leaderboard.urllib_request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = _make_mock_urlopen(SAMPLE_API_RESPONSE)
            result = fetch_trending_repos()
        assert result.total_fetched == len(SAMPLE_RAW_ITEMS)
