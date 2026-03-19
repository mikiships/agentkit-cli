"""Tests for D2: pages-org CLI command."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.engines.org_pages import OrgPagesResult

runner = CliRunner()


def _mock_result(published: bool = True, error: str = None) -> OrgPagesResult:
    return OrgPagesResult(
        pages_url="https://myorg.github.io/agentkit-scores/",
        repos_scored=5,
        avg_score=78.4,
        top_repo="myorg/best-repo",
        published=published,
        error=error,
    )


def _patch_engine(result: OrgPagesResult):
    mock_engine = MagicMock()
    mock_engine.return_value.run.return_value = result
    return patch("agentkit_cli.commands.pages_org_cmd.OrgPagesEngine", mock_engine)


# ---------------------------------------------------------------------------
# Help / basic wiring
# ---------------------------------------------------------------------------

def test_pages_org_help():
    result = runner.invoke(app, ["pages-org", "--help"])
    assert result.exit_code == 0
    assert "pages-org" in result.output or "pages_org" in result.output.lower()

def test_pages_org_requires_target():
    result = runner.invoke(app, ["pages-org"])
    assert result.exit_code != 0

def test_pages_org_invalid_target_empty():
    with _patch_engine(_mock_result()):
        result = runner.invoke(app, ["pages-org", "github:"], env={"GITHUB_TOKEN": "tok"})
    assert result.exit_code != 0

def test_pages_org_missing_token_error():
    """Should exit with error when GITHUB_TOKEN is missing and --dry-run is not set."""
    result = runner.invoke(app, ["pages-org", "github:myorg"], env={"GITHUB_TOKEN": ""})
    assert result.exit_code != 0
    assert "GITHUB_TOKEN" in result.output or "token" in result.output.lower()


# ---------------------------------------------------------------------------
# Successful run
# ---------------------------------------------------------------------------

def test_pages_org_success_shows_url():
    with _patch_engine(_mock_result(published=True)):
        result = runner.invoke(app, ["pages-org", "github:myorg"], env={"GITHUB_TOKEN": "tok"})
    assert result.exit_code == 0
    assert "myorg.github.io" in result.output

def test_pages_org_quiet_prints_only_url():
    with _patch_engine(_mock_result(published=True)):
        result = runner.invoke(app, ["pages-org", "github:myorg", "--quiet"], env={"GITHUB_TOKEN": "tok"})
    assert result.exit_code == 0
    lines = [l for l in result.output.strip().splitlines() if l.strip()]
    assert any("github.io" in l for l in lines)

def test_pages_org_json_output():
    with _patch_engine(_mock_result(published=True)):
        result = runner.invoke(app, ["pages-org", "github:myorg", "--json"], env={"GITHUB_TOKEN": "tok"})
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["org"] == "myorg"
    assert "pages_url" in data
    assert "repos_scored" in data


# ---------------------------------------------------------------------------
# --dry-run
# ---------------------------------------------------------------------------

def test_pages_org_dry_run_no_token_ok():
    """dry-run skips git push so no token required (we mock engine anyway)."""
    with _patch_engine(_mock_result(published=False)):
        result = runner.invoke(app, ["pages-org", "github:myorg", "--dry-run"], env={"GITHUB_TOKEN": ""})
    # With dry-run we skip the token check
    assert result.exit_code == 0

def test_pages_org_dry_run_mentions_dry():
    with _patch_engine(_mock_result(published=False)):
        result = runner.invoke(app, ["pages-org", "github:myorg", "--dry-run"], env={"GITHUB_TOKEN": "tok"})
    assert result.exit_code == 0
    assert "dry" in result.output.lower() or "not published" in result.output.lower()


# ---------------------------------------------------------------------------
# Option defaults wired to engine
# ---------------------------------------------------------------------------

def test_pages_org_passes_pages_repo():
    mock_engine_cls = MagicMock()
    mock_engine_cls.return_value.run.return_value = _mock_result()
    with patch("agentkit_cli.commands.pages_org_cmd.OrgPagesEngine", mock_engine_cls):
        runner.invoke(app, ["pages-org", "github:myorg", "--pages-repo", "myorg/custom"], env={"GITHUB_TOKEN": "tok"})
    call_kwargs = mock_engine_cls.call_args[1]
    assert call_kwargs.get("pages_repo") == "myorg/custom"

def test_pages_org_passes_limit():
    mock_engine_cls = MagicMock()
    mock_engine_cls.return_value.run.return_value = _mock_result()
    with patch("agentkit_cli.commands.pages_org_cmd.OrgPagesEngine", mock_engine_cls):
        runner.invoke(app, ["pages-org", "github:myorg", "--limit", "10"], env={"GITHUB_TOKEN": "tok"})
    call_kwargs = mock_engine_cls.call_args[1]
    assert call_kwargs.get("limit") == 10

def test_pages_org_passes_only_below():
    mock_engine_cls = MagicMock()
    mock_engine_cls.return_value.run.return_value = _mock_result()
    with patch("agentkit_cli.commands.pages_org_cmd.OrgPagesEngine", mock_engine_cls):
        runner.invoke(app, ["pages-org", "github:myorg", "--only-below", "75"], env={"GITHUB_TOKEN": "tok"})
    call_kwargs = mock_engine_cls.call_args[1]
    assert call_kwargs.get("only_below") == 75

def test_pages_org_passes_dry_run_flag():
    mock_engine_cls = MagicMock()
    mock_engine_cls.return_value.run.return_value = _mock_result(published=False)
    with patch("agentkit_cli.commands.pages_org_cmd.OrgPagesEngine", mock_engine_cls):
        runner.invoke(app, ["pages-org", "github:myorg", "--dry-run"], env={"GITHUB_TOKEN": "tok"})
    call_kwargs = mock_engine_cls.call_args[1]
    assert call_kwargs.get("dry_run") is True


# ---------------------------------------------------------------------------
# Error reporting
# ---------------------------------------------------------------------------

def test_pages_org_failed_publish_shows_error():
    with _patch_engine(_mock_result(published=False, error="git push failed")):
        result = runner.invoke(app, ["pages-org", "github:myorg"], env={"GITHUB_TOKEN": "tok"})
    assert result.exit_code == 0
    assert "failed" in result.output.lower() or "git push failed" in result.output
