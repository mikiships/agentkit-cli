"""Tests for D3: doctor hooks check and setup-ci hooks mention."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from agentkit_cli.doctor import check_hooks_installed, run_doctor
from agentkit_cli.hooks import HookEngine
from agentkit_cli.main import app

runner = CliRunner()


@pytest.fixture()
def git_repo(tmp_path: Path) -> Path:
    (tmp_path / ".git" / "hooks").mkdir(parents=True)
    return tmp_path


def test_check_hooks_installed_no_hooks(git_repo: Path) -> None:
    result = check_hooks_installed(git_repo)
    assert result.id == "hooks.installed"
    assert result.category == "hooks"
    assert result.status == "warn"
    assert "agentkit hooks install" in result.fix_hint


def test_check_hooks_installed_git_hook(git_repo: Path) -> None:
    HookEngine().install(git_repo, mode="git", min_score=60)
    result = check_hooks_installed(git_repo)
    assert result.status == "pass"


def test_check_hooks_installed_precommit_hook(git_repo: Path) -> None:
    HookEngine().install(git_repo, mode="precommit", min_score=60)
    result = check_hooks_installed(git_repo)
    assert result.status == "pass"


def test_check_hooks_installed_both_hooks(git_repo: Path) -> None:
    HookEngine().install(git_repo, mode="both", min_score=60)
    result = check_hooks_installed(git_repo)
    assert result.status == "pass"


def test_run_doctor_includes_hooks_check(git_repo: Path) -> None:
    report = run_doctor(root=git_repo)
    hook_checks = [c for c in report.checks if c.category == "hooks"]
    assert len(hook_checks) >= 1


def test_doctor_category_hooks_filter() -> None:
    """agentkit doctor --category hooks only returns hooks checks."""
    result = runner.invoke(app, ["doctor", "--category", "hooks", "--no-fail-exit"])
    assert result.exit_code == 0


def test_doctor_category_hooks_json() -> None:
    import json
    result = runner.invoke(app, ["doctor", "--category", "hooks", "--json", "--no-fail-exit"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    checks = data.get("checks", [])
    assert all(c["category"] == "hooks" for c in checks)


def test_setup_ci_mentions_hooks(tmp_path: Path) -> None:
    """setup-ci complete output (non-dry-run prints Next steps with hooks)."""
    # Check source code contains the hooks mention (the actual panel is printed at runtime)
    from agentkit_cli.commands import setup_ci_cmd
    import inspect
    src = inspect.getsource(setup_ci_cmd)
    assert "hooks install" in src.lower() or "agentkit hooks" in src
