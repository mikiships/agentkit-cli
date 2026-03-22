"""Tests for agentkit hooks CLI commands (D2)."""
from __future__ import annotations

import json
import stat
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app

runner = CliRunner()


@pytest.fixture()
def git_repo(tmp_path: Path) -> Path:
    (tmp_path / ".git" / "hooks").mkdir(parents=True)
    return tmp_path


def test_hooks_install_dry_run(git_repo: Path) -> None:
    result = runner.invoke(app, ["hooks", "install", "--path", str(git_repo), "--dry-run"])
    assert result.exit_code == 0
    assert "Would install" in result.output or "dry run" in result.output.lower()


def test_hooks_install_git_mode(git_repo: Path) -> None:
    result = runner.invoke(app, ["hooks", "install", "--path", str(git_repo), "--mode", "git"])
    assert result.exit_code == 0
    assert (git_repo / ".git" / "hooks" / "pre-commit").exists()


def test_hooks_install_precommit_mode(git_repo: Path) -> None:
    result = runner.invoke(app, ["hooks", "install", "--path", str(git_repo), "--mode", "precommit"])
    assert result.exit_code == 0
    assert (git_repo / ".pre-commit-config.yaml").exists()


def test_hooks_install_both_mode(git_repo: Path) -> None:
    result = runner.invoke(app, ["hooks", "install", "--path", str(git_repo), "--mode", "both"])
    assert result.exit_code == 0
    assert (git_repo / ".git" / "hooks" / "pre-commit").exists()
    assert (git_repo / ".pre-commit-config.yaml").exists()


def test_hooks_install_invalid_mode(git_repo: Path) -> None:
    result = runner.invoke(app, ["hooks", "install", "--path", str(git_repo), "--mode", "invalid"])
    assert result.exit_code != 0


def test_hooks_install_min_score(git_repo: Path) -> None:
    result = runner.invoke(app, ["hooks", "install", "--path", str(git_repo), "--mode", "git", "--min-score", "85"])
    assert result.exit_code == 0
    content = (git_repo / ".git" / "hooks" / "pre-commit").read_text()
    assert "85" in content


def test_hooks_status_no_hooks(git_repo: Path) -> None:
    result = runner.invoke(app, ["hooks", "status", "--path", str(git_repo)])
    assert result.exit_code == 0
    assert "✗" in result.output or "not installed" in result.output.lower() or "agentkit hooks install" in result.output


def test_hooks_status_json_no_hooks(git_repo: Path) -> None:
    result = runner.invoke(app, ["hooks", "status", "--path", str(git_repo), "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["git_installed"] is False
    assert data["precommit_installed"] is False


def test_hooks_status_after_install(git_repo: Path) -> None:
    runner.invoke(app, ["hooks", "install", "--path", str(git_repo), "--mode", "git"])
    result = runner.invoke(app, ["hooks", "status", "--path", str(git_repo), "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["git_installed"] is True


def test_hooks_uninstall_git(git_repo: Path) -> None:
    runner.invoke(app, ["hooks", "install", "--path", str(git_repo), "--mode", "git"])
    result = runner.invoke(app, ["hooks", "uninstall", "--path", str(git_repo), "--mode", "git"])
    assert result.exit_code == 0
    assert not (git_repo / ".git" / "hooks" / "pre-commit").exists()


def test_hooks_uninstall_not_installed(git_repo: Path) -> None:
    result = runner.invoke(app, ["hooks", "uninstall", "--path", str(git_repo)])
    assert result.exit_code == 0
    assert "not installed" in result.output.lower() or "not_found" in result.output


def test_hooks_run_passes(git_repo: Path) -> None:
    """Mock the engine.check to return a pass."""
    with patch("agentkit_cli.commands.hooks_cmd._engine") as mock_engine:
        mock_engine.status.return_value = {"git_installed": True, "precommit_installed": False, "min_score": 60}
        mock_engine.check.return_value = {"passed": True, "returncode": 0, "stdout": "score: 75", "stderr": "", "min_score": 60, "timestamp": "2026-03-22T00:00:00"}
        result = runner.invoke(app, ["hooks", "run", "--path", str(git_repo)])
    assert result.exit_code == 0
    assert "PASSED" in result.output


def test_hooks_run_fails(git_repo: Path) -> None:
    """Mock the engine.check to return a fail."""
    with patch("agentkit_cli.commands.hooks_cmd._engine") as mock_engine:
        mock_engine.status.return_value = {"git_installed": True, "precommit_installed": False, "min_score": 60}
        mock_engine.check.return_value = {"passed": False, "returncode": 1, "stdout": "", "stderr": "score: 40", "min_score": 60, "timestamp": "2026-03-22T00:00:00"}
        result = runner.invoke(app, ["hooks", "run", "--path", str(git_repo)])
    assert result.exit_code == 1
    assert "FAILED" in result.output


def test_hooks_run_json(git_repo: Path) -> None:
    with patch("agentkit_cli.commands.hooks_cmd._engine") as mock_engine:
        mock_engine.status.return_value = {"git_installed": False, "precommit_installed": False, "min_score": None}
        mock_engine.check.return_value = {"passed": True, "returncode": 0, "stdout": "", "stderr": "", "min_score": 60, "timestamp": "2026-03-22T00:00:00"}
        result = runner.invoke(app, ["hooks", "run", "--path", str(git_repo), "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "passed" in data


def test_hooks_install_prints_installed_message(git_repo: Path) -> None:
    result = runner.invoke(app, ["hooks", "install", "--path", str(git_repo), "--mode", "git"])
    assert "Installed" in result.output or "✓" in result.output


def test_hooks_uninstall_precommit(git_repo: Path) -> None:
    runner.invoke(app, ["hooks", "install", "--path", str(git_repo), "--mode", "precommit"])
    result = runner.invoke(app, ["hooks", "uninstall", "--path", str(git_repo), "--mode", "precommit"])
    assert result.exit_code == 0
    assert "Removed" in result.output or "removed" in result.output.lower()
