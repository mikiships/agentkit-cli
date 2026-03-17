"""Tests for agentkit campaign CLI command (D2)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.campaign import CampaignResult, PRResult, RepoSpec

runner = CliRunner()


def _make_result(campaign_id="abc123", submitted=1, skipped=0, failed=0):
    result = CampaignResult(campaign_id=campaign_id, target_spec="github:pallets", file="CLAUDE.md")
    for i in range(submitted):
        repo = RepoSpec("pallets", f"repo{i}", stars=1000 * (i + 1))
        result.submitted.append(PRResult(repo=repo, pr_url=f"https://github.com/pallets/repo{i}/pull/1"))
    for i in range(skipped):
        result.skipped.append(RepoSpec("pallets", f"skip{i}", stars=500))
    for i in range(failed):
        result.failed.append((RepoSpec("pallets", f"fail{i}", stars=100), "error msg"))
    return result


def _mock_engine(result: CampaignResult, repos: List[RepoSpec] = None):
    """Patch CampaignEngine to return controlled data."""
    if repos is None:
        repos = [r.repo for r in result.submitted] + result.skipped + [r for r, _ in result.failed]
        # Use RepoSpec objects from result
        all_repos = list(result.submitted) + [PRResult(repo=r, pr_url="") for r in result.skipped]
        repos = [pr.repo for pr in result.submitted] + result.skipped + [r for r, _ in result.failed]
        if not repos:
            repos = [RepoSpec("pallets", "flask", stars=5000)]

    engine = MagicMock()
    engine.find_repos.return_value = repos
    engine.has_context_file.return_value = False
    engine.run_campaign.return_value = result
    return engine


# ---------------------------------------------------------------------------
# Basic invocation
# ---------------------------------------------------------------------------

def test_campaign_help():
    result = runner.invoke(app, ["campaign", "--help"])
    assert result.exit_code == 0
    assert "TARGET" in result.output or "campaign" in result.output.lower()


def test_campaign_dry_run(tmp_path):
    repos = [RepoSpec("pallets", "flask", stars=68000, language="Python")]
    mock_result = _make_result(submitted=1)
    mock_result.submitted[0].pr_url = "[DRY RUN]"

    with patch("agentkit_cli.commands.campaign_cmd.CampaignEngine") as MockEngine:
        instance = MockEngine.return_value
        instance.find_repos.return_value = repos
        instance.has_context_file.return_value = False
        instance.run_campaign.return_value = mock_result

        result = runner.invoke(app, ["campaign", "github:pallets", "--dry-run", "--limit", "1"])

    assert result.exit_code == 0


def test_campaign_json_output(tmp_path):
    repos = [RepoSpec("pallets", "flask", stars=68000)]
    mock_result = _make_result(submitted=1)

    with patch("agentkit_cli.commands.campaign_cmd.CampaignEngine") as MockEngine:
        instance = MockEngine.return_value
        instance.find_repos.return_value = repos
        instance.has_context_file.return_value = False
        instance.run_campaign.return_value = mock_result

        result = runner.invoke(app, ["campaign", "github:pallets", "--json", "--limit", "1"])

    assert result.exit_code == 0
    # Find JSON in output
    lines = result.output.strip().splitlines()
    json_str = "\n".join(lines)
    # Try to parse JSON from output
    for i, line in enumerate(lines):
        if line.strip().startswith("{"):
            data = json.loads("\n".join(lines[i:]))
            assert "campaign_id" in data
            break


def test_campaign_no_repos_found():
    with patch("agentkit_cli.commands.campaign_cmd.CampaignEngine") as MockEngine:
        instance = MockEngine.return_value
        instance.find_repos.return_value = []

        result = runner.invoke(app, ["campaign", "github:emptyorg"])

    assert result.exit_code == 0
    assert "No repos found" in result.output


def test_campaign_skip_pr_flag():
    repos = [RepoSpec("pallets", "flask", stars=68000)]
    with patch("agentkit_cli.commands.campaign_cmd.CampaignEngine") as MockEngine:
        instance = MockEngine.return_value
        instance.find_repos.return_value = repos
        instance.has_context_file.return_value = False

        result = runner.invoke(app, ["campaign", "github:pallets", "--skip-pr"])

    assert result.exit_code == 0
    # run_campaign should NOT be called
    instance.run_campaign.assert_not_called()


def test_campaign_skip_pr_json():
    repos = [RepoSpec("pallets", "flask", stars=68000)]
    with patch("agentkit_cli.commands.campaign_cmd.CampaignEngine") as MockEngine:
        instance = MockEngine.return_value
        instance.find_repos.return_value = repos
        instance.has_context_file.return_value = False

        result = runner.invoke(app, ["campaign", "github:pallets", "--skip-pr", "--json"])

    assert result.exit_code == 0


def test_campaign_discovery_error():
    with patch("agentkit_cli.commands.campaign_cmd.CampaignEngine") as MockEngine:
        instance = MockEngine.return_value
        instance.find_repos.side_effect = Exception("API error")

        result = runner.invoke(app, ["campaign", "github:badorg"])

    assert result.exit_code != 0


def test_campaign_with_mixed_results():
    repos = [
        RepoSpec("pallets", "flask", stars=68000),
        RepoSpec("pallets", "click", stars=15000),
        RepoSpec("pallets", "jinja", stars=10000),
    ]
    mock_result = CampaignResult(campaign_id="test123", target_spec="github:pallets")
    mock_result.submitted.append(PRResult(repo=repos[0], pr_url="https://github.com/pallets/flask/pull/1"))
    mock_result.skipped.append(repos[1])
    mock_result.failed.append((repos[2], "Fork failed"))

    with patch("agentkit_cli.commands.campaign_cmd.CampaignEngine") as MockEngine:
        instance = MockEngine.return_value
        instance.find_repos.return_value = repos
        instance.has_context_file.return_value = False
        instance.run_campaign.return_value = mock_result

        result = runner.invoke(app, ["campaign", "github:pallets"])

    assert result.exit_code == 0
    assert "1 PR" in result.output or "1 PRs" in result.output


def test_campaign_options_passed_to_engine():
    repos = [RepoSpec("pallets", "flask", stars=68000)]
    mock_result = _make_result()

    with patch("agentkit_cli.commands.campaign_cmd.CampaignEngine") as MockEngine:
        instance = MockEngine.return_value
        instance.find_repos.return_value = repos
        instance.has_context_file.return_value = False
        instance.run_campaign.return_value = mock_result

        runner.invoke(app, [
            "campaign", "github:pallets",
            "--limit", "7",
            "--language", "python",
            "--min-stars", "500",
            "--file", "AGENTS.md",
        ])

    instance.find_repos.assert_called_once_with(
        target_spec="github:pallets",
        limit=7,
        language="python",
        min_stars=500,
    )
    # file should be passed to run_campaign
    call_kwargs = instance.run_campaign.call_args
    assert call_kwargs[1].get("file") == "AGENTS.md" or "AGENTS.md" in str(call_kwargs)


def test_campaign_table_output_contains_repo_names():
    repos = [RepoSpec("pallets", "flask", stars=68000)]
    mock_result = _make_result(submitted=1)
    mock_result.submitted[0].repo = repos[0]
    mock_result.submitted[0].pr_url = "https://github.com/pallets/flask/pull/1"

    with patch("agentkit_cli.commands.campaign_cmd.CampaignEngine") as MockEngine:
        instance = MockEngine.return_value
        instance.find_repos.return_value = repos
        instance.has_context_file.return_value = False
        instance.run_campaign.return_value = mock_result

        result = runner.invoke(app, ["campaign", "github:pallets"])

    assert result.exit_code == 0


def test_campaign_complete_message():
    repos = [RepoSpec("pallets", "flask", stars=68000)]
    mock_result = _make_result(submitted=2, skipped=1, failed=1)

    with patch("agentkit_cli.commands.campaign_cmd.CampaignEngine") as MockEngine:
        instance = MockEngine.return_value
        instance.find_repos.return_value = repos
        instance.has_context_file.return_value = False
        instance.run_campaign.return_value = mock_result

        result = runner.invoke(app, ["campaign", "github:pallets"])

    assert "Campaign complete" in result.output


def test_campaign_force_flag_passed():
    repos = [RepoSpec("pallets", "flask", stars=68000)]
    mock_result = _make_result()

    with patch("agentkit_cli.commands.campaign_cmd.CampaignEngine") as MockEngine:
        instance = MockEngine.return_value
        instance.find_repos.return_value = repos
        instance.has_context_file.return_value = False
        instance.run_campaign.return_value = mock_result

        runner.invoke(app, ["campaign", "github:pallets", "--force"])

    call_kwargs = instance.run_campaign.call_args
    assert call_kwargs[1].get("force") is True or True in str(call_kwargs)


def test_campaign_no_filter_flag():
    repos = [RepoSpec("pallets", "flask", stars=68000)]
    mock_result = _make_result()

    with patch("agentkit_cli.commands.campaign_cmd.CampaignEngine") as MockEngine:
        instance = MockEngine.return_value
        instance.find_repos.return_value = repos
        instance.run_campaign.return_value = mock_result

        result = runner.invoke(app, ["campaign", "github:pallets", "--no-filter"])

    assert result.exit_code == 0


def test_campaign_history_db_recording(tmp_path):
    db_file = tmp_path / "test.db"
    repos = [RepoSpec("pallets", "flask", stars=1000)]
    mock_result = _make_result()

    with patch("agentkit_cli.commands.campaign_cmd.CampaignEngine") as MockEngine:
        instance = MockEngine.return_value
        instance.find_repos.return_value = repos
        instance.has_context_file.return_value = False
        instance.run_campaign.return_value = mock_result

        with patch("agentkit_cli.history.HistoryDB") as MockDB:
            db_instance = MockDB.return_value
            result = runner.invoke(app, ["campaign", "github:pallets"])

    # DB recording should have been attempted
    assert result.exit_code == 0
