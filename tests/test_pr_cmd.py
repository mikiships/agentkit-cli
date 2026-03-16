"""Tests for agentkit pr command."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock, patch, call

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.commands.pr_cmd import (
    _render_pr_body,
    _default_pr_body_template,
    _compute_score,
    _BRANCH_NAME,
    _DEFAULT_PR_TITLE,
)

runner = CliRunner()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fake_git_clone_side_effect(clone_dir: str, ctx_file: str = "CLAUDE.md"):
    """Return a subprocess.run side effect that creates a fake cloned repo."""
    def side_effect(cmd, cwd=None, check=True, capture_output=False, text=False):
        cp = MagicMock(spec=subprocess.CompletedProcess)
        cp.returncode = 0
        cp.stdout = ""
        cp.stderr = ""
        if "clone" in cmd:
            Path(clone_dir).mkdir(parents=True, exist_ok=True)
        elif "generate" in cmd or (len(cmd) > 1 and cmd[1] == "generate"):
            # Simulate agentmd writing CLAUDE.md
            Path(cwd or ".") / ctx_file
            (Path(cwd) / "CLAUDE.md").write_text("# Context\n\nAuto-generated.")
        return cp
    return side_effect


# ---------------------------------------------------------------------------
# D1: Core pr command
# ---------------------------------------------------------------------------

def test_pr_help():
    """agentkit pr --help renders cleanly."""
    result = runner.invoke(app, ["pr", "--help"])
    assert result.exit_code == 0
    assert "github:owner/repo" in result.output or "Target repo" in result.output


def test_pr_invalid_target_format():
    """Non-github: target format returns error."""
    result = runner.invoke(app, ["pr", "owner/repo"])
    assert result.exit_code != 0
    assert "github:" in result.output


def test_pr_invalid_target_missing_repo():
    """github:owner without /repo returns error."""
    result = runner.invoke(app, ["pr", "github:owner"])
    assert result.exit_code != 0


def test_pr_invalid_target_extra_slashes():
    """github:owner/repo/extra returns error."""
    result = runner.invoke(app, ["pr", "github:owner/repo/extra"])
    assert result.exit_code != 0


def test_pr_dry_run_no_git_ops():
    """--dry-run shows steps without any git or API operations."""
    result = runner.invoke(app, ["pr", "github:testowner/testrepo", "--dry-run"])
    assert result.exit_code == 0
    assert "DRY RUN" in result.output
    assert "Clone" in result.output
    assert "generate" in result.output.lower()
    assert "fork" in result.output.lower()
    assert "PR" in result.output or "pr" in result.output.lower()


def test_pr_dry_run_json():
    """--dry-run --json returns valid JSON with dry_run=True."""
    result = runner.invoke(app, ["pr", "github:testowner/testrepo", "--dry-run", "--json"])
    assert result.exit_code == 0
    # Extract JSON line from output
    for line in result.output.splitlines():
        line = line.strip()
        if line.startswith("{"):
            data = json.loads(line)
            assert data["dry_run"] is True
            assert data["repo"] == "testowner/testrepo"
            assert data["file"] == "CLAUDE.md"
            break
    else:
        pytest.fail("No JSON output found")


def test_pr_dry_run_with_agents_file():
    """--dry-run with --file AGENTS.md mentions AGENTS.md."""
    result = runner.invoke(app, ["pr", "github:testowner/testrepo", "--dry-run", "--file", "AGENTS.md"])
    assert result.exit_code == 0
    assert "AGENTS.md" in result.output


def test_pr_missing_github_token(monkeypatch):
    """Missing GITHUB_TOKEN gives helpful error."""
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    result = runner.invoke(app, ["pr", "github:testowner/testrepo"])
    assert result.exit_code != 0
    assert "GITHUB_TOKEN" in result.output


def test_pr_missing_github_token_empty_string(monkeypatch):
    """Empty GITHUB_TOKEN gives helpful error."""
    monkeypatch.setenv("GITHUB_TOKEN", "")
    result = runner.invoke(app, ["pr", "github:testowner/testrepo"])
    assert result.exit_code != 0
    assert "GITHUB_TOKEN" in result.output


# ---------------------------------------------------------------------------
# D1: skip if file exists
# ---------------------------------------------------------------------------

def test_pr_skips_if_file_exists(tmp_path, monkeypatch):
    """If CLAUDE.md already exists in the cloned repo, command skips without --force."""
    monkeypatch.setenv("GITHUB_TOKEN", "fake-token")

    def fake_run(cmd, cwd=None, check=True, capture_output=False, text=False):
        cp = MagicMock(spec=subprocess.CompletedProcess)
        cp.returncode = 0
        cp.stdout = ""
        cp.stderr = ""
        if "clone" in cmd:
            target = cmd[-1]  # last arg is destination
            Path(target).mkdir(parents=True, exist_ok=True)
            (Path(target) / "CLAUDE.md").write_text("existing content")
        return cp

    with patch("agentkit_cli.commands.pr_cmd._run", side_effect=fake_run):
        with patch("agentkit_cli.commands.pr_cmd.tempfile.mkdtemp", return_value=str(tmp_path)):
            result = runner.invoke(app, ["pr", "github:owner/repo"])
    assert result.exit_code == 0
    assert "Skipping" in result.output or "already exists" in result.output


def test_pr_force_overwrites_existing_file(tmp_path, monkeypatch):
    """--force proceeds even if CLAUDE.md already exists."""
    monkeypatch.setenv("GITHUB_TOKEN", "fake-token")

    clone_dir = tmp_path / "repo"

    def fake_run(cmd, cwd=None, check=True, capture_output=False, text=False):
        cp = MagicMock(spec=subprocess.CompletedProcess)
        cp.returncode = 0
        cp.stdout = ""
        cp.stderr = ""
        if "clone" in cmd:
            clone_dir.mkdir(parents=True, exist_ok=True)
            (clone_dir / "CLAUDE.md").write_text("existing content")
        elif cmd[0] == "agentmd":
            (Path(cwd) / "CLAUDE.md").write_text("new generated content")
        return cp

    with patch("agentkit_cli.commands.pr_cmd._run", side_effect=fake_run):
        with patch("agentkit_cli.commands.pr_cmd.tempfile.mkdtemp", return_value=str(tmp_path)):
            with patch("agentkit_cli.commands.pr_cmd._get_authenticated_user", return_value="testuser"):
                with patch("agentkit_cli.commands.pr_cmd._get_fork", return_value={"html_url": "https://github.com/testuser/repo", "clone_url": "https://github.com/testuser/repo.git"}):
                    with patch("agentkit_cli.commands.pr_cmd._create_pull_request", return_value={"html_url": "https://github.com/owner/repo/pull/1"}):
                        result = runner.invoke(app, ["pr", "github:owner/repo", "--force"])
    # Should not skip
    assert "Skipping" not in result.output


# ---------------------------------------------------------------------------
# D2: GitHub API flow (mocked)
# ---------------------------------------------------------------------------

def test_pr_creates_fork_if_not_exists(tmp_path, monkeypatch):
    """If no fork exists, _create_fork is called."""
    monkeypatch.setenv("GITHUB_TOKEN", "fake-token")
    clone_dir = tmp_path / "repo"

    def fake_run(cmd, cwd=None, check=True, capture_output=False, text=False):
        cp = MagicMock(spec=subprocess.CompletedProcess)
        cp.returncode = 0
        cp.stdout = ""
        cp.stderr = ""
        if "clone" in cmd:
            clone_dir.mkdir(parents=True, exist_ok=True)
        elif cmd[0] == "agentmd":
            (Path(cwd) / "CLAUDE.md").write_text("generated")
        return cp

    create_fork_mock = MagicMock(return_value={"html_url": "https://github.com/u/repo", "clone_url": "https://github.com/u/repo.git"})

    with patch("agentkit_cli.commands.pr_cmd._run", side_effect=fake_run):
        with patch("agentkit_cli.commands.pr_cmd.tempfile.mkdtemp", return_value=str(tmp_path)):
            with patch("agentkit_cli.commands.pr_cmd._get_authenticated_user", return_value="u"):
                with patch("agentkit_cli.commands.pr_cmd._get_fork", return_value=None):
                    with patch("agentkit_cli.commands.pr_cmd._create_fork", create_fork_mock):
                        with patch("agentkit_cli.commands.pr_cmd._create_pull_request", return_value={"html_url": "https://github.com/owner/repo/pull/1"}):
                            runner.invoke(app, ["pr", "github:owner/repo"])

    create_fork_mock.assert_called_once()


def test_pr_uses_existing_fork(tmp_path, monkeypatch):
    """If fork already exists, _create_fork is NOT called."""
    monkeypatch.setenv("GITHUB_TOKEN", "fake-token")
    clone_dir = tmp_path / "repo"

    def fake_run(cmd, cwd=None, check=True, capture_output=False, text=False):
        cp = MagicMock(spec=subprocess.CompletedProcess)
        cp.returncode = 0
        cp.stdout = ""
        cp.stderr = ""
        if "clone" in cmd:
            clone_dir.mkdir(parents=True, exist_ok=True)
        elif cmd[0] == "agentmd":
            (Path(cwd) / "CLAUDE.md").write_text("generated")
        return cp

    create_fork_mock = MagicMock()

    with patch("agentkit_cli.commands.pr_cmd._run", side_effect=fake_run):
        with patch("agentkit_cli.commands.pr_cmd.tempfile.mkdtemp", return_value=str(tmp_path)):
            with patch("agentkit_cli.commands.pr_cmd._get_authenticated_user", return_value="u"):
                with patch("agentkit_cli.commands.pr_cmd._get_fork", return_value={"html_url": "https://github.com/u/repo", "clone_url": "https://github.com/u/repo.git"}):
                    with patch("agentkit_cli.commands.pr_cmd._create_fork", create_fork_mock):
                        with patch("agentkit_cli.commands.pr_cmd._create_pull_request", return_value={"html_url": "https://github.com/owner/repo/pull/1"}):
                            runner.invoke(app, ["pr", "github:owner/repo"])

    create_fork_mock.assert_not_called()


def test_pr_opens_pr_with_correct_title(tmp_path, monkeypatch):
    """PR is opened with the default title."""
    monkeypatch.setenv("GITHUB_TOKEN", "fake-token")
    clone_dir = tmp_path / "repo"

    def fake_run(cmd, cwd=None, check=True, capture_output=False, text=False):
        cp = MagicMock(spec=subprocess.CompletedProcess)
        cp.returncode = 0
        cp.stdout = ""
        cp.stderr = ""
        if "clone" in cmd:
            clone_dir.mkdir(parents=True, exist_ok=True)
        elif cmd[0] == "agentmd":
            (Path(cwd) / "CLAUDE.md").write_text("generated")
        return cp

    create_pr_mock = MagicMock(return_value={"html_url": "https://github.com/owner/repo/pull/1"})

    with patch("agentkit_cli.commands.pr_cmd._run", side_effect=fake_run):
        with patch("agentkit_cli.commands.pr_cmd.tempfile.mkdtemp", return_value=str(tmp_path)):
            with patch("agentkit_cli.commands.pr_cmd._get_authenticated_user", return_value="u"):
                with patch("agentkit_cli.commands.pr_cmd._get_fork", return_value={"html_url": "https://github.com/u/repo", "clone_url": "https://github.com/u/repo.git"}):
                    with patch("agentkit_cli.commands.pr_cmd._create_pull_request", create_pr_mock):
                        runner.invoke(app, ["pr", "github:owner/repo"])

    call_kwargs = create_pr_mock.call_args
    assert call_kwargs.kwargs["title"] == _DEFAULT_PR_TITLE


def test_pr_custom_title(tmp_path, monkeypatch):
    """--pr-title overrides default PR title."""
    monkeypatch.setenv("GITHUB_TOKEN", "fake-token")
    clone_dir = tmp_path / "repo"

    def fake_run(cmd, cwd=None, check=True, capture_output=False, text=False):
        cp = MagicMock(spec=subprocess.CompletedProcess)
        cp.returncode = 0
        cp.stdout = ""
        cp.stderr = ""
        if "clone" in cmd:
            clone_dir.mkdir(parents=True, exist_ok=True)
        elif cmd[0] == "agentmd":
            (Path(cwd) / "CLAUDE.md").write_text("generated")
        return cp

    create_pr_mock = MagicMock(return_value={"html_url": "https://github.com/owner/repo/pull/1"})

    with patch("agentkit_cli.commands.pr_cmd._run", side_effect=fake_run):
        with patch("agentkit_cli.commands.pr_cmd.tempfile.mkdtemp", return_value=str(tmp_path)):
            with patch("agentkit_cli.commands.pr_cmd._get_authenticated_user", return_value="u"):
                with patch("agentkit_cli.commands.pr_cmd._get_fork", return_value={"html_url": "https://github.com/u/repo", "clone_url": "https://github.com/u/repo.git"}):
                    with patch("agentkit_cli.commands.pr_cmd._create_pull_request", create_pr_mock):
                        runner.invoke(app, ["pr", "github:owner/repo", "--pr-title", "Custom Title"])

    assert create_pr_mock.call_args.kwargs["title"] == "Custom Title"


# ---------------------------------------------------------------------------
# D3: Output + UX
# ---------------------------------------------------------------------------

def test_pr_success_prints_pr_url(tmp_path, monkeypatch):
    """On success, PR URL is printed to output."""
    monkeypatch.setenv("GITHUB_TOKEN", "fake-token")
    clone_dir = tmp_path / "repo"

    def fake_run(cmd, cwd=None, check=True, capture_output=False, text=False):
        cp = MagicMock(spec=subprocess.CompletedProcess)
        cp.returncode = 0
        cp.stdout = ""
        cp.stderr = ""
        if "clone" in cmd:
            clone_dir.mkdir(parents=True, exist_ok=True)
        elif cmd[0] == "agentmd":
            (Path(cwd) / "CLAUDE.md").write_text("generated")
        return cp

    with patch("agentkit_cli.commands.pr_cmd._run", side_effect=fake_run):
        with patch("agentkit_cli.commands.pr_cmd.tempfile.mkdtemp", return_value=str(tmp_path)):
            with patch("agentkit_cli.commands.pr_cmd._get_authenticated_user", return_value="u"):
                with patch("agentkit_cli.commands.pr_cmd._get_fork", return_value={"html_url": "https://github.com/u/repo", "clone_url": "https://github.com/u/repo.git"}):
                    with patch("agentkit_cli.commands.pr_cmd._create_pull_request", return_value={"html_url": "https://github.com/owner/repo/pull/42"}):
                        result = runner.invoke(app, ["pr", "github:owner/repo"])

    assert result.exit_code == 0
    assert "https://github.com/owner/repo/pull/42" in result.output


def test_pr_json_output_structure(tmp_path, monkeypatch):
    """--json output is valid JSON with expected keys."""
    monkeypatch.setenv("GITHUB_TOKEN", "fake-token")
    clone_dir = tmp_path / "repo"

    def fake_run(cmd, cwd=None, check=True, capture_output=False, text=False):
        cp = MagicMock(spec=subprocess.CompletedProcess)
        cp.returncode = 0
        cp.stdout = ""
        cp.stderr = ""
        if "clone" in cmd:
            clone_dir.mkdir(parents=True, exist_ok=True)
        elif cmd[0] == "agentmd":
            (Path(cwd) / "CLAUDE.md").write_text("generated")
        return cp

    with patch("agentkit_cli.commands.pr_cmd._run", side_effect=fake_run):
        with patch("agentkit_cli.commands.pr_cmd.tempfile.mkdtemp", return_value=str(tmp_path)):
            with patch("agentkit_cli.commands.pr_cmd._get_authenticated_user", return_value="u"):
                with patch("agentkit_cli.commands.pr_cmd._get_fork", return_value={"html_url": "https://github.com/u/repo", "clone_url": "https://github.com/u/repo.git"}):
                    with patch("agentkit_cli.commands.pr_cmd._create_pull_request", return_value={"html_url": "https://github.com/owner/repo/pull/1"}):
                        result = runner.invoke(app, ["pr", "github:owner/repo", "--json"])

    assert result.exit_code == 0
    # find JSON line
    json_data = None
    for line in result.output.splitlines():
        line = line.strip()
        if line.startswith("{"):
            json_data = json.loads(line)
            break
    assert json_data is not None
    assert "pr_url" in json_data
    assert "repo" in json_data
    assert "file" in json_data
    assert "score_before" in json_data
    assert "score_after" in json_data


def test_pr_json_output_is_valid_json(tmp_path, monkeypatch):
    """--json output can be parsed as JSON."""
    monkeypatch.setenv("GITHUB_TOKEN", "fake-token")
    clone_dir = tmp_path / "repo"

    def fake_run(cmd, cwd=None, check=True, capture_output=False, text=False):
        cp = MagicMock(spec=subprocess.CompletedProcess)
        cp.returncode = 0
        cp.stdout = ""
        cp.stderr = ""
        if "clone" in cmd:
            clone_dir.mkdir(parents=True, exist_ok=True)
        elif cmd[0] == "agentmd":
            (Path(cwd) / "CLAUDE.md").write_text("generated")
        return cp

    with patch("agentkit_cli.commands.pr_cmd._run", side_effect=fake_run):
        with patch("agentkit_cli.commands.pr_cmd.tempfile.mkdtemp", return_value=str(tmp_path)):
            with patch("agentkit_cli.commands.pr_cmd._get_authenticated_user", return_value="u"):
                with patch("agentkit_cli.commands.pr_cmd._get_fork", return_value={"html_url": "https://github.com/u/repo", "clone_url": "https://github.com/u/repo.git"}):
                    with patch("agentkit_cli.commands.pr_cmd._create_pull_request", return_value={"html_url": "https://github.com/owner/repo/pull/1"}):
                        result = runner.invoke(app, ["pr", "github:owner/repo", "--json"])

    for line in result.output.splitlines():
        line = line.strip()
        if line.startswith("{"):
            json.loads(line)  # Must not raise
            return
    pytest.fail("No JSON found in output")


def test_pr_json_repo_field(tmp_path, monkeypatch):
    """JSON output repo field matches owner/repo."""
    monkeypatch.setenv("GITHUB_TOKEN", "fake-token")
    clone_dir = tmp_path / "repo"

    def fake_run(cmd, cwd=None, check=True, capture_output=False, text=False):
        cp = MagicMock(spec=subprocess.CompletedProcess)
        cp.returncode = 0
        cp.stdout = ""
        cp.stderr = ""
        if "clone" in cmd:
            clone_dir.mkdir(parents=True, exist_ok=True)
        elif cmd[0] == "agentmd":
            (Path(cwd) / "CLAUDE.md").write_text("generated")
        return cp

    with patch("agentkit_cli.commands.pr_cmd._run", side_effect=fake_run):
        with patch("agentkit_cli.commands.pr_cmd.tempfile.mkdtemp", return_value=str(tmp_path)):
            with patch("agentkit_cli.commands.pr_cmd._get_authenticated_user", return_value="u"):
                with patch("agentkit_cli.commands.pr_cmd._get_fork", return_value={"html_url": "https://github.com/u/repo", "clone_url": "https://github.com/u/repo.git"}):
                    with patch("agentkit_cli.commands.pr_cmd._create_pull_request", return_value={"html_url": "https://github.com/owner/repo/pull/1"}):
                        result = runner.invoke(app, ["pr", "github:owner/repo", "--json"])

    for line in result.output.splitlines():
        line = line.strip()
        if line.startswith("{"):
            data = json.loads(line)
            assert data["repo"] == "owner/repo"
            return


# ---------------------------------------------------------------------------
# PR body template tests
# ---------------------------------------------------------------------------

def test_pr_body_template_exists():
    """pr_body.md template file exists."""
    from agentkit_cli.commands.pr_cmd import _templates_dir
    tpl = _templates_dir() / "pr_body.md"
    assert tpl.exists()


def test_pr_body_template_has_required_sections():
    """PR body template contains expected sections."""
    template = _default_pr_body_template()
    assert "CLAUDE.md" in template
    assert "agentkit-cli" in template
    assert "AI coding agent" in template or "AI coding agents" in template


def test_pr_body_renders_owner_repo():
    """_render_pr_body substitutes {owner} and {repo} placeholders."""
    template = "github:{owner}/{repo}"
    result = _render_pr_body(template, "myowner", "myrepo")
    assert result == "github:myowner/myrepo"


def test_pr_body_renders_both_placeholders():
    """Template placeholders are both replaced."""
    template = "See {owner}/{repo} for details. Visit github.com/{owner}/{repo}."
    result = _render_pr_body(template, "alice", "wonderland")
    assert "{owner}" not in result
    assert "{repo}" not in result
    assert "alice" in result
    assert "wonderland" in result


def test_pr_body_default_contains_pip_install():
    """Default PR body template mentions pip install."""
    body = _default_pr_body_template()
    assert "pip install agentkit-cli" in body


def test_pr_body_custom_file_override(tmp_path, monkeypatch):
    """--pr-body-file reads from a custom file."""
    monkeypatch.setenv("GITHUB_TOKEN", "fake-token")
    clone_dir = tmp_path / "repo"

    custom_body_file = tmp_path / "custom_body.md"
    custom_body_file.write_text("Custom body text for {owner}/{repo}")

    def fake_run(cmd, cwd=None, check=True, capture_output=False, text=False):
        cp = MagicMock(spec=subprocess.CompletedProcess)
        cp.returncode = 0
        cp.stdout = ""
        cp.stderr = ""
        if "clone" in cmd:
            clone_dir.mkdir(parents=True, exist_ok=True)
        elif cmd[0] == "agentmd":
            (Path(cwd) / "CLAUDE.md").write_text("generated")
        return cp

    create_pr_mock = MagicMock(return_value={"html_url": "https://github.com/owner/repo/pull/1"})

    with patch("agentkit_cli.commands.pr_cmd._run", side_effect=fake_run):
        with patch("agentkit_cli.commands.pr_cmd.tempfile.mkdtemp", return_value=str(tmp_path)):
            with patch("agentkit_cli.commands.pr_cmd._get_authenticated_user", return_value="u"):
                with patch("agentkit_cli.commands.pr_cmd._get_fork", return_value={"html_url": "https://github.com/u/repo", "clone_url": "https://github.com/u/repo.git"}):
                    with patch("agentkit_cli.commands.pr_cmd._create_pull_request", create_pr_mock):
                        runner.invoke(app, ["pr", "github:owner/repo", "--pr-body-file", str(custom_body_file)])

    body_used = create_pr_mock.call_args.kwargs["body"]
    assert "Custom body text" in body_used
    assert "owner" in body_used


# ---------------------------------------------------------------------------
# Constants + misc unit tests
# ---------------------------------------------------------------------------

def test_branch_name_constant():
    """Branch name constant is correct."""
    assert _BRANCH_NAME == "agentkit/add-claude-md"


def test_default_pr_title_constant():
    """Default PR title is correct."""
    assert _DEFAULT_PR_TITLE == "feat: add CLAUDE.md for AI coding agents"


def test_compute_score_returns_none_when_tool_unavailable():
    """_compute_score returns None gracefully when agentlint is not installed."""
    score = _compute_score("/nonexistent/path")
    assert score is None


def test_dry_run_returns_zero_exit():
    """Dry run always exits 0."""
    result = runner.invoke(app, ["pr", "github:owner/repo", "--dry-run"])
    assert result.exit_code == 0


def test_pr_branches_correctly_named(tmp_path, monkeypatch):
    """git checkout creates the correct branch name."""
    monkeypatch.setenv("GITHUB_TOKEN", "fake-token")
    clone_dir = tmp_path / "repo"
    git_calls = []

    def fake_run(cmd, cwd=None, check=True, capture_output=False, text=False):
        git_calls.append(cmd)
        cp = MagicMock(spec=subprocess.CompletedProcess)
        cp.returncode = 0
        cp.stdout = ""
        cp.stderr = ""
        if "clone" in cmd:
            clone_dir.mkdir(parents=True, exist_ok=True)
        elif cmd[0] == "agentmd":
            (Path(cwd) / "CLAUDE.md").write_text("generated")
        return cp

    with patch("agentkit_cli.commands.pr_cmd._run", side_effect=fake_run):
        with patch("agentkit_cli.commands.pr_cmd.tempfile.mkdtemp", return_value=str(tmp_path)):
            with patch("agentkit_cli.commands.pr_cmd._get_authenticated_user", return_value="u"):
                with patch("agentkit_cli.commands.pr_cmd._get_fork", return_value={"html_url": "https://github.com/u/repo", "clone_url": "https://github.com/u/repo.git"}):
                    with patch("agentkit_cli.commands.pr_cmd._create_pull_request", return_value={"html_url": "https://github.com/owner/repo/pull/1"}):
                        runner.invoke(app, ["pr", "github:owner/repo"])

    # Verify branch creation command was called
    branch_cmds = [c for c in git_calls if "checkout" in c and "-b" in c]
    assert any(_BRANCH_NAME in c for c in branch_cmds)
