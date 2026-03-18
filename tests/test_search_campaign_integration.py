"""Tests for D4 — --from-search integration on agentkit campaign."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.search import SearchResult

runner = CliRunner()


def _make_search_results(n: int = 2) -> list[SearchResult]:
    results = []
    for i in range(n):
        results.append(SearchResult(
            owner="user",
            repo=f"repo{i}",
            url=f"https://github.com/user/repo{i}",
            stars=500 * (i + 1),
            language="Python",
            description=f"desc {i}",
            has_claude_md=False,
            has_agents_md=False,
            score=0.75,
        ))
    return results


def test_campaign_from_search_flag_exists():
    result = runner.invoke(app, ["campaign", "--help"])
    assert result.exit_code == 0
    assert "--from-search" in result.output


def test_campaign_from_search_no_results():
    with patch("agentkit_cli.search.SearchEngine") as MockEngine:
        MockEngine.return_value.search.return_value = []
        result = runner.invoke(app, ["campaign", "--from-search", "nothing"])
    assert result.exit_code == 0
    assert "No repos" in result.output


def test_campaign_from_search_runs_search():
    mock_results = _make_search_results(2)
    with patch("agentkit_cli.search.SearchEngine") as MockEngine:
        MockEngine.return_value.search.return_value = mock_results
        with patch("agentkit_cli.campaign.CampaignEngine") as MockCampaign:
            MockCampaign.return_value.find_repos.return_value = []
            MockCampaign.return_value.run_campaign.return_value = MagicMock(
                campaign_id="abc", submitted=[], skipped=[], failed=[], target_spec="", file="CLAUDE.md",
                to_dict=lambda: {"campaign_id": "abc", "submitted": [], "skipped": [], "failed": [], "totals": {"prs": 0, "skipped": 0, "failed": 0}, "target_spec": "", "file": "CLAUDE.md"}
            )
            result = runner.invoke(app, ["campaign", "--from-search", "ai agents", "--dry-run"])
    # Should call search
    assert MockEngine.return_value.search.called


def test_campaign_from_search_passes_language():
    mock_results = _make_search_results(1)
    with patch("agentkit_cli.search.SearchEngine") as MockEngine:
        MockEngine.return_value.search.return_value = mock_results
        with patch("agentkit_cli.campaign.CampaignEngine") as MockCampaign:
            MockCampaign.return_value.find_repos.return_value = []
            MockCampaign.return_value.run_campaign.return_value = MagicMock(
                campaign_id="abc", submitted=[], skipped=[], failed=[], target_spec="", file="CLAUDE.md",
                to_dict=lambda: {}
            )
            runner.invoke(app, ["campaign", "--from-search", "ai", "--language", "python", "--dry-run"])
    call_kwargs = MockEngine.return_value.search.call_args[1]
    assert call_kwargs.get("language") == "python"


def test_search_json_compatible_with_campaign(tmp_path):
    """JSON output from search should have keys usable as campaign targets."""
    from agentkit_cli.search import SearchResult
    results = _make_search_results(2)
    data = [r.to_dict() for r in results]
    # Verify keys match what campaign expects for repos-file targets
    for item in data:
        assert "repo" in item
        assert "/" in item["repo"]  # owner/repo format
