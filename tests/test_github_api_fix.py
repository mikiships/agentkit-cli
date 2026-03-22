"""Regression tests for github_api._fetch_page search dict handling.

Bug: _fetch_page previously returned [] for any non-list response, silently
dropping GitHub search API results which return {"items": [...], "total_count": N}.
This caused populate, topic, topic-rank, etc. to return 0 repos.
Fixed in v0.88.0 by extracting items from dict["items"] when present.
"""
from __future__ import annotations

import json
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

from agentkit_cli.github_api import _fetch_page


class _FakeResponse:
    """Mock urllib response."""

    def __init__(self, body: dict | list, headers: dict | None = None):
        self._data = json.dumps(body).encode()
        self.headers = headers or {}

    def read(self) -> bytes:
        return self._data

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


def _mock_urlopen(body: dict | list, headers: dict | None = None):
    resp = _FakeResponse(body, headers)
    return patch("agentkit_cli.github_api.urllib_request.urlopen", return_value=resp)


class TestFetchPageSearchResponse:
    """_fetch_page correctly handles GitHub search API dict responses."""

    def test_search_dict_returns_items(self):
        """Dict response with 'items' key returns the items list."""
        search_result = {
            "total_count": 2,
            "incomplete_results": False,
            "items": [
                {"full_name": "owner/repo1", "stargazers_count": 100},
                {"full_name": "owner/repo2", "stargazers_count": 50},
            ],
        }
        with _mock_urlopen(search_result):
            items, headers, next_url = _fetch_page("https://api.github.com/search/repositories?q=test")

        assert len(items) == 2
        assert items[0]["full_name"] == "owner/repo1"
        assert items[1]["full_name"] == "owner/repo2"

    def test_search_empty_items(self):
        """Dict response with empty items list returns empty list."""
        search_result = {"total_count": 0, "incomplete_results": False, "items": []}
        with _mock_urlopen(search_result):
            items, headers, next_url = _fetch_page("https://api.github.com/search/repositories?q=noresults")

        assert items == []

    def test_list_response_still_works(self):
        """List response (e.g. /repos/:owner/:repo/forks) still returns the list."""
        list_result = [
            {"full_name": "owner/fork1"},
            {"full_name": "owner/fork2"},
        ]
        with _mock_urlopen(list_result):
            items, headers, next_url = _fetch_page("https://api.github.com/repos/owner/repo/forks")

        assert len(items) == 2
        assert items[0]["full_name"] == "owner/fork1"

    def test_dict_without_items_key_returns_empty(self):
        """Dict without 'items' key (unexpected format) returns empty list without crashing."""
        weird_result = {"something": "unexpected"}
        with _mock_urlopen(weird_result):
            items, headers, next_url = _fetch_page("https://api.github.com/some/endpoint")

        assert items == []

    def test_search_result_with_pagination(self):
        """Search results with Link header sets next_url correctly."""
        search_result = {
            "total_count": 30,
            "items": [{"full_name": f"owner/repo{i}"} for i in range(10)],
        }
        link_header = '<https://api.github.com/search/repositories?q=test&page=2>; rel="next"'
        with _mock_urlopen(search_result, headers={"Link": link_header}):
            items, headers, next_url = _fetch_page("https://api.github.com/search/repositories?q=test")

        assert len(items) == 10
        assert next_url == "https://api.github.com/search/repositories?q=test&page=2"
