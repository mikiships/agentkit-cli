"""Tests for agentkit_cli/commands/search_cmd.py (D2)."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.search import SearchResult

runner = CliRunner()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_results(n: int = 2, missing: bool = True) -> list[SearchResult]:
    results = []
    for i in range(n):
        r = SearchResult(
            owner="user",
            repo=f"repo{i}",
            url=f"https://github.com/user/repo{i}",
            stars=1000 * (i + 1),
            language="Python",
            description=f"repo {i}",
            has_claude_md=not missing,
            has_agents_md=False,
            score=0.5 if missing else 0.25,
        )
        results.append(r)
    return results


# ---------------------------------------------------------------------------
# CLI — basic invocation
# ---------------------------------------------------------------------------

def test_search_command_exists():
    result = runner.invoke(app, ["search", "--help"])
    assert result.exit_code == 0
    assert "search" in result.output.lower() or "GitHub" in result.output


def test_search_returns_table():
    mock_results = _make_results(2, missing=True)
    with patch("agentkit_cli.commands.search_cmd.SearchEngine") as MockEngine:
        MockEngine.return_value.search.return_value = mock_results
        result = runner.invoke(app, ["search", "ai agents"])
    assert result.exit_code == 0
    assert "repo0" in result.output or "user" in result.output


def test_search_json_output():
    mock_results = _make_results(2)
    with patch("agentkit_cli.commands.search_cmd.SearchEngine") as MockEngine:
        MockEngine.return_value.search.return_value = mock_results
        result = runner.invoke(app, ["search", "ai agents", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) == 2
    assert "repo" in data[0]
    assert "stars" in data[0]


def test_search_json_has_context_fields():
    mock_results = _make_results(1)
    with patch("agentkit_cli.commands.search_cmd.SearchEngine") as MockEngine:
        MockEngine.return_value.search.return_value = mock_results
        result = runner.invoke(app, ["search", "test", "--json"])
    data = json.loads(result.output)
    assert "has_claude_md" in data[0]
    assert "has_agents_md" in data[0]
    assert "missing_context" in data[0]


def test_search_missing_only_flag():
    mock_results = _make_results(1, missing=True)
    with patch("agentkit_cli.commands.search_cmd.SearchEngine") as MockEngine:
        instance = MockEngine.return_value
        instance.search.return_value = mock_results
        runner.invoke(app, ["search", "--missing-only"])
    call_kwargs = instance.search.call_args[1]
    assert call_kwargs.get("missing_only") is True


def test_search_language_flag():
    mock_results = _make_results(1)
    with patch("agentkit_cli.commands.search_cmd.SearchEngine") as MockEngine:
        instance = MockEngine.return_value
        instance.search.return_value = mock_results
        runner.invoke(app, ["search", "--language", "python"])
    call_kwargs = instance.search.call_args[1]
    assert call_kwargs.get("language") == "python"


def test_search_topic_flag():
    mock_results = _make_results(1)
    with patch("agentkit_cli.commands.search_cmd.SearchEngine") as MockEngine:
        instance = MockEngine.return_value
        instance.search.return_value = mock_results
        runner.invoke(app, ["search", "--topic", "ai-agents"])
    call_kwargs = instance.search.call_args[1]
    assert call_kwargs.get("topic") == "ai-agents"


def test_search_min_stars_flag():
    mock_results = _make_results(1)
    with patch("agentkit_cli.commands.search_cmd.SearchEngine") as MockEngine:
        instance = MockEngine.return_value
        instance.search.return_value = mock_results
        runner.invoke(app, ["search", "--min-stars", "500"])
    call_kwargs = instance.search.call_args[1]
    assert call_kwargs.get("min_stars") == 500


def test_search_limit_flag():
    mock_results = _make_results(1)
    with patch("agentkit_cli.commands.search_cmd.SearchEngine") as MockEngine:
        instance = MockEngine.return_value
        instance.search.return_value = mock_results
        runner.invoke(app, ["search", "--limit", "10"])
    call_kwargs = instance.search.call_args[1]
    assert call_kwargs.get("limit") == 10


def test_search_no_check_flag():
    mock_results = _make_results(1)
    with patch("agentkit_cli.commands.search_cmd.SearchEngine") as MockEngine:
        instance = MockEngine.return_value
        instance.search.return_value = mock_results
        runner.invoke(app, ["search", "--no-check"])
    call_kwargs = instance.search.call_args[1]
    assert call_kwargs.get("no_check") is True or call_kwargs.get("check_contents") is False


def test_search_empty_results():
    with patch("agentkit_cli.commands.search_cmd.SearchEngine") as MockEngine:
        MockEngine.return_value.search.return_value = []
        result = runner.invoke(app, ["search", "xyz"])
    assert result.exit_code == 0
    assert "No repos" in result.output


def test_search_api_error_exits_1():
    with patch("agentkit_cli.commands.search_cmd.SearchEngine") as MockEngine:
        MockEngine.return_value.search.side_effect = Exception("API error")
        result = runner.invoke(app, ["search", "test"])
    assert result.exit_code == 1


def test_search_output_flag_writes_html(tmp_path):
    mock_results = _make_results(1)
    out = tmp_path / "report.html"
    with patch("agentkit_cli.commands.search_cmd.SearchEngine") as MockEngine:
        MockEngine.return_value.search.return_value = mock_results
        result = runner.invoke(app, ["search", "test", "--output", str(out)])
    assert result.exit_code == 0
    assert out.exists()
    content = out.read_text()
    assert "html" in content.lower()


def test_search_share_no_key(monkeypatch):
    monkeypatch.delenv("HERENOW_API_KEY", raising=False)
    mock_results = _make_results(1)
    with patch("agentkit_cli.commands.search_cmd.SearchEngine") as MockEngine:
        MockEngine.return_value.search.return_value = mock_results
        result = runner.invoke(app, ["search", "test", "--share"])
    assert result.exit_code == 0
    assert "HERENOW_API_KEY" in result.output or "set" in result.output.lower()


def test_search_summary_line():
    mock_results = _make_results(3, missing=True)
    with patch("agentkit_cli.commands.search_cmd.SearchEngine") as MockEngine:
        MockEngine.return_value.search.return_value = mock_results
        result = runner.invoke(app, ["search", "test"])
    assert "3" in result.output or "repos" in result.output
