"""Tests for agentkit setup-ci command."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_git_repo(tmp_path: Path, with_github_remote: bool = True) -> Path:
    """Create a minimal fake git repo."""
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    config_content = (
        '[remote "origin"]\n\turl = https://github.com/owner/repo.git\n'
        if with_github_remote
        else '[core]\n\tbare = false\n'
    )
    (git_dir / "config").write_text(config_content)
    return tmp_path


# ---------------------------------------------------------------------------
# D1: Core workflow writer
# ---------------------------------------------------------------------------

def test_workflow_written_to_default_path(tmp_path: Path) -> None:
    repo = _make_git_repo(tmp_path)
    with patch("agentkit_cli.commands.setup_ci_cmd._run_baseline", return_value=False), \
         patch("agentkit_cli.commands.setup_ci_cmd._inject_badge", return_value=False):
        result = runner.invoke(app, ["setup-ci", "--path", str(repo), "--skip-baseline", "--no-badge"])
    assert result.exit_code == 0, result.output
    wf = repo / ".github" / "workflows" / "agentkit-quality.yml"
    assert wf.exists(), "Workflow file should be written"
    content = wf.read_text()
    assert "agentkit gate" in content


def test_dry_run_prints_to_stdout_without_writing(tmp_path: Path) -> None:
    repo = _make_git_repo(tmp_path)
    result = runner.invoke(app, ["setup-ci", "--path", str(repo), "--dry-run"])
    assert result.exit_code == 0, result.output
    assert "agentkit gate" in result.output
    wf = repo / ".github" / "workflows" / "agentkit-quality.yml"
    assert not wf.exists(), "Dry run must not write any file"


def test_force_overwrites_existing_workflow(tmp_path: Path) -> None:
    repo = _make_git_repo(tmp_path)
    wf = repo / ".github" / "workflows" / "agentkit-quality.yml"
    wf.parent.mkdir(parents=True)
    wf.write_text("old content")
    with patch("agentkit_cli.commands.setup_ci_cmd._run_baseline", return_value=False), \
         patch("agentkit_cli.commands.setup_ci_cmd._inject_badge", return_value=False):
        result = runner.invoke(app, ["setup-ci", "--path", str(repo), "--force", "--skip-baseline", "--no-badge"])
    assert result.exit_code == 0, result.output
    assert "old content" not in wf.read_text(), "File should be overwritten"
    assert "agentkit gate" in wf.read_text()


def test_without_force_skips_existing_workflow(tmp_path: Path) -> None:
    repo = _make_git_repo(tmp_path)
    wf = repo / ".github" / "workflows" / "agentkit-quality.yml"
    wf.parent.mkdir(parents=True)
    wf.write_text("old content")
    with patch("agentkit_cli.commands.setup_ci_cmd._run_baseline", return_value=False), \
         patch("agentkit_cli.commands.setup_ci_cmd._inject_badge", return_value=False):
        result = runner.invoke(app, ["setup-ci", "--path", str(repo), "--skip-baseline", "--no-badge"])
    assert result.exit_code == 0, result.output
    assert wf.read_text() == "old content", "File should NOT be overwritten without --force"
    assert "Skipped" in result.output or "already exists" in result.output


def test_workflow_contains_min_score(tmp_path: Path) -> None:
    repo = _make_git_repo(tmp_path)
    with patch("agentkit_cli.commands.setup_ci_cmd._run_baseline", return_value=False), \
         patch("agentkit_cli.commands.setup_ci_cmd._inject_badge", return_value=False):
        runner.invoke(app, ["setup-ci", "--path", str(repo), "--min-score", "85", "--skip-baseline", "--no-badge"])
    wf = repo / ".github" / "workflows" / "agentkit-quality.yml"
    assert "85" in wf.read_text()


def test_workflow_contains_baseline_report_reference(tmp_path: Path) -> None:
    repo = _make_git_repo(tmp_path)
    with patch("agentkit_cli.commands.setup_ci_cmd._run_baseline", return_value=False), \
         patch("agentkit_cli.commands.setup_ci_cmd._inject_badge", return_value=False):
        runner.invoke(app, ["setup-ci", "--path", str(repo), "--skip-baseline", "--no-badge"])
    wf = repo / ".github" / "workflows" / "agentkit-quality.yml"
    content = wf.read_text()
    assert ".agentkit-baseline.json" in content
    assert "--baseline-report" in content


def test_custom_workflow_path(tmp_path: Path) -> None:
    repo = _make_git_repo(tmp_path)
    custom = tmp_path / "custom-workflow.yml"
    with patch("agentkit_cli.commands.setup_ci_cmd._run_baseline", return_value=False), \
         patch("agentkit_cli.commands.setup_ci_cmd._inject_badge", return_value=False):
        result = runner.invoke(
            app,
            ["setup-ci", "--path", str(repo), "--workflow-path", str(custom), "--skip-baseline", "--no-badge"],
        )
    assert result.exit_code == 0, result.output
    assert custom.exists()


# ---------------------------------------------------------------------------
# D2: Baseline generation
# ---------------------------------------------------------------------------

def test_skip_baseline_bypasses_report_generation(tmp_path: Path) -> None:
    repo = _make_git_repo(tmp_path)
    with patch("agentkit_cli.commands.setup_ci_cmd._run_baseline") as mock_baseline, \
         patch("agentkit_cli.commands.setup_ci_cmd._inject_badge", return_value=False):
        runner.invoke(app, ["setup-ci", "--path", str(repo), "--skip-baseline", "--no-badge"])
    mock_baseline.assert_not_called()


def test_baseline_file_written_on_success(tmp_path: Path) -> None:
    repo = _make_git_repo(tmp_path)
    baseline = repo / ".agentkit-baseline.json"

    def _fake_baseline(root: Path) -> bool:
        baseline.write_text('{"coverage": 100}')
        return True

    with patch("agentkit_cli.commands.setup_ci_cmd._run_baseline", side_effect=_fake_baseline), \
         patch("agentkit_cli.commands.setup_ci_cmd._inject_badge", return_value=False):
        result = runner.invoke(app, ["setup-ci", "--path", str(repo), "--no-badge"])
    assert result.exit_code == 0, result.output
    assert baseline.exists()
    assert "Baseline saved" in result.output


def test_baseline_failure_warns_but_does_not_abort(tmp_path: Path) -> None:
    repo = _make_git_repo(tmp_path)
    with patch("agentkit_cli.commands.setup_ci_cmd._run_baseline", return_value=False), \
         patch("agentkit_cli.commands.setup_ci_cmd._inject_badge", return_value=False):
        result = runner.invoke(app, ["setup-ci", "--path", str(repo), "--no-badge"])
    assert result.exit_code == 0, result.output
    assert "Warning" in result.output or "failed" in result.output


# ---------------------------------------------------------------------------
# D3: Badge injection
# ---------------------------------------------------------------------------

def test_no_badge_skips_injection(tmp_path: Path) -> None:
    repo = _make_git_repo(tmp_path)
    with patch("agentkit_cli.commands.setup_ci_cmd._run_baseline", return_value=False), \
         patch("agentkit_cli.commands.setup_ci_cmd._inject_badge") as mock_badge:
        runner.invoke(app, ["setup-ci", "--path", str(repo), "--skip-baseline", "--no-badge"])
    mock_badge.assert_not_called()


def test_badge_injected_when_readme_exists(tmp_path: Path) -> None:
    repo = _make_git_repo(tmp_path)
    (repo / "README.md").write_text("# My project\n")
    with patch("agentkit_cli.commands.setup_ci_cmd._run_baseline", return_value=False), \
         patch("agentkit_cli.commands.setup_ci_cmd._inject_badge", return_value=True) as mock_badge:
        result = runner.invoke(app, ["setup-ci", "--path", str(repo), "--skip-baseline"])
    mock_badge.assert_called_once()
    assert "Badge injected" in result.output


def test_badge_skipped_when_no_readme(tmp_path: Path) -> None:
    repo = _make_git_repo(tmp_path)
    with patch("agentkit_cli.commands.setup_ci_cmd._run_baseline", return_value=False), \
         patch("agentkit_cli.commands.setup_ci_cmd._inject_badge", return_value=False):
        result = runner.invoke(app, ["setup-ci", "--path", str(repo), "--skip-baseline"])
    assert result.exit_code == 0, result.output
    assert "Badge injection skipped" in result.output or "Skipped" in result.output or "skipped" in result.output


# ---------------------------------------------------------------------------
# Helpers unit tests
# ---------------------------------------------------------------------------

def test_is_github_repo_true(tmp_path: Path) -> None:
    from agentkit_cli.commands.setup_ci_cmd import _is_github_repo
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "config").write_text('[remote "origin"]\n\turl = https://github.com/owner/repo.git\n')
    assert _is_github_repo(tmp_path) is True


def test_is_github_repo_false(tmp_path: Path) -> None:
    from agentkit_cli.commands.setup_ci_cmd import _is_github_repo
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "config").write_text('[core]\n\tbare = false\n')
    assert _is_github_repo(tmp_path) is False


def test_is_github_repo_no_git_dir(tmp_path: Path) -> None:
    from agentkit_cli.commands.setup_ci_cmd import _is_github_repo
    assert _is_github_repo(tmp_path) is False
