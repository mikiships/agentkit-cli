"""Integration tests: install hook → status → uninstall (D1/D2)."""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from agentkit_cli.hooks import HookEngine


@pytest.fixture()
def git_repo(tmp_path: Path) -> Path:
    (tmp_path / ".git" / "hooks").mkdir(parents=True)
    return tmp_path


def test_full_git_lifecycle(git_repo: Path) -> None:
    engine = HookEngine()

    # Install
    res = engine.install(git_repo, mode="git", min_score=70)
    assert res["git"]["status"] == "installed"

    # Status shows installed
    st = engine.status(git_repo)
    assert st["git_installed"] is True
    assert st["min_score"] == 70

    # Uninstall
    res = engine.uninstall(git_repo, mode="git")
    assert res["git"]["status"] == "removed"

    # Status shows not installed
    st = engine.status(git_repo)
    assert st["git_installed"] is False


def test_full_precommit_lifecycle(tmp_path: Path) -> None:
    engine = HookEngine()

    # Install
    res = engine.install(tmp_path, mode="precommit", min_score=65)
    assert res["precommit"]["status"] == "installed"

    # Status shows installed
    st = engine.status(tmp_path)
    assert st["precommit_installed"] is True

    # Uninstall
    res = engine.uninstall(tmp_path, mode="precommit")
    assert res["precommit"]["status"] == "removed"

    # Status shows not installed
    st = engine.status(tmp_path)
    assert st["precommit_installed"] is False


def test_both_mode_lifecycle(git_repo: Path) -> None:
    engine = HookEngine()

    # Install both
    res = engine.install(git_repo, mode="both", min_score=60)
    assert res["git"]["status"] == "installed"
    assert res["precommit"]["status"] == "installed"

    # Status shows both
    st = engine.status(git_repo)
    assert st["git_installed"] is True
    assert st["precommit_installed"] is True

    # Uninstall both
    res = engine.uninstall(git_repo, mode="both")
    assert res["git"]["status"] == "removed"
    assert res["precommit"]["status"] == "removed"

    st = engine.status(git_repo)
    assert st["git_installed"] is False
    assert st["precommit_installed"] is False


def test_install_preserves_foreign_precommit_repos(git_repo: Path) -> None:
    """Existing pre-commit config entries are not clobbered."""
    existing = {
        "repos": [
            {"repo": "https://github.com/pre-commit/pre-commit-hooks", "rev": "v4.5.0", "hooks": [{"id": "end-of-file-fixer"}]}
        ]
    }
    (git_repo / ".pre-commit-config.yaml").write_text(yaml.dump(existing))

    engine = HookEngine()
    engine.install(git_repo, mode="precommit", min_score=60)

    data = yaml.safe_load((git_repo / ".pre-commit-config.yaml").read_text())
    repo_urls = [r.get("repo") for r in data.get("repos", [])]
    assert "https://github.com/pre-commit/pre-commit-hooks" in repo_urls


def test_uninstall_git_leaves_foreign_hook(git_repo: Path) -> None:
    foreign = git_repo / ".git" / "hooks" / "pre-commit"
    foreign.write_text("#!/bin/sh\necho foreign\n")
    engine = HookEngine()
    res = engine.uninstall(git_repo, mode="git")
    assert res["git"]["status"] == "skipped"
    assert foreign.exists()


def test_status_returns_expected_keys(git_repo: Path) -> None:
    engine = HookEngine()
    st = engine.status(git_repo)
    assert "git_installed" in st
    assert "precommit_installed" in st
    assert "min_score" in st
    assert "last_check" in st
