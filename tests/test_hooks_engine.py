"""Tests for HookEngine (D1)."""
from __future__ import annotations

import stat
from pathlib import Path

import pytest
import yaml

from agentkit_cli.hooks import HookEngine, _GIT_HOOK_HEADER, _PRECOMMIT_REPO_URL, _PRECOMMIT_HOOK_ID


@pytest.fixture()
def git_repo(tmp_path: Path) -> Path:
    """Create a minimal fake git repo."""
    (tmp_path / ".git" / "hooks").mkdir(parents=True)
    return tmp_path


@pytest.fixture()
def non_git_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_install_git_hook_creates_file(git_repo: Path) -> None:
    engine = HookEngine()
    result = engine.install(git_repo, mode="git", min_score=70)
    hook_path = git_repo / ".git" / "hooks" / "pre-commit"
    assert hook_path.exists()
    assert result["git"]["status"] == "installed"


def test_install_git_hook_content(git_repo: Path) -> None:
    engine = HookEngine()
    engine.install(git_repo, mode="git", min_score=75)
    hook_path = git_repo / ".git" / "hooks" / "pre-commit"
    content = hook_path.read_text()
    assert _GIT_HOOK_HEADER in content
    assert "75" in content
    assert "agentkit score" in content


def test_install_git_hook_executable(git_repo: Path) -> None:
    engine = HookEngine()
    engine.install(git_repo, mode="git", min_score=60)
    hook_path = git_repo / ".git" / "hooks" / "pre-commit"
    mode = hook_path.stat().st_mode
    assert mode & stat.S_IXUSR


def test_install_git_hook_idempotent(git_repo: Path) -> None:
    """Re-installing should overwrite our own hook."""
    engine = HookEngine()
    engine.install(git_repo, mode="git", min_score=60)
    result = engine.install(git_repo, mode="git", min_score=80)
    assert result["git"]["status"] == "installed"
    content = (git_repo / ".git" / "hooks" / "pre-commit").read_text()
    assert "80" in content


def test_install_git_hook_does_not_clobber_foreign(git_repo: Path) -> None:
    """Should not overwrite a pre-commit hook not installed by agentkit."""
    foreign_hook = git_repo / ".git" / "hooks" / "pre-commit"
    foreign_hook.write_text("#!/bin/sh\necho foreign\n")
    engine = HookEngine()
    result = engine.install(git_repo, mode="git", min_score=60)
    assert result["git"]["status"] == "skipped"
    assert "foreign" in foreign_hook.read_text()


def test_install_skips_without_git_dir(non_git_dir: Path) -> None:
    engine = HookEngine()
    result = engine.install(non_git_dir, mode="git", min_score=60)
    assert result["git"]["status"] == "skipped"


def test_install_precommit_creates_file(tmp_path: Path) -> None:
    engine = HookEngine()
    result = engine.install(tmp_path, mode="precommit", min_score=65)
    cfg = tmp_path / ".pre-commit-config.yaml"
    assert cfg.exists()
    assert result["precommit"]["status"] == "installed"


def test_install_precommit_content(tmp_path: Path) -> None:
    engine = HookEngine()
    engine.install(tmp_path, mode="precommit", min_score=65)
    data = yaml.safe_load((tmp_path / ".pre-commit-config.yaml").read_text())
    repos = data.get("repos", [])
    assert any(r.get("repo") == _PRECOMMIT_REPO_URL for r in repos)
    hook_ids = [h["id"] for r in repos for h in r.get("hooks", [])]
    assert _PRECOMMIT_HOOK_ID in hook_ids


def test_install_precommit_idempotent(tmp_path: Path) -> None:
    engine = HookEngine()
    engine.install(tmp_path, mode="precommit", min_score=60)
    engine.install(tmp_path, mode="precommit", min_score=70)
    data = yaml.safe_load((tmp_path / ".pre-commit-config.yaml").read_text())
    # Should not duplicate entries
    repos = [r for r in data.get("repos", []) if r.get("repo") == _PRECOMMIT_REPO_URL]
    assert len(repos) == 1


def test_install_precommit_does_not_clobber_existing(tmp_path: Path) -> None:
    """Existing repos in .pre-commit-config.yaml are preserved."""
    existing = {"repos": [{"repo": "https://github.com/pre-commit/pre-commit-hooks", "rev": "v4.4.0", "hooks": [{"id": "trailing-whitespace"}]}]}
    (tmp_path / ".pre-commit-config.yaml").write_text(yaml.dump(existing))
    engine = HookEngine()
    engine.install(tmp_path, mode="precommit", min_score=60)
    data = yaml.safe_load((tmp_path / ".pre-commit-config.yaml").read_text())
    repos = data.get("repos", [])
    assert len(repos) == 2  # original + agentkit


def test_uninstall_git_hook(git_repo: Path) -> None:
    engine = HookEngine()
    engine.install(git_repo, mode="git", min_score=60)
    result = engine.uninstall(git_repo, mode="git")
    assert result["git"]["status"] == "removed"
    assert not (git_repo / ".git" / "hooks" / "pre-commit").exists()


def test_uninstall_git_hook_not_found(git_repo: Path) -> None:
    engine = HookEngine()
    result = engine.uninstall(git_repo, mode="git")
    assert result["git"]["status"] == "not_found"


def test_uninstall_precommit_hook(tmp_path: Path) -> None:
    engine = HookEngine()
    engine.install(tmp_path, mode="precommit", min_score=60)
    result = engine.uninstall(tmp_path, mode="precommit")
    assert result["precommit"]["status"] == "removed"
    data = yaml.safe_load((tmp_path / ".pre-commit-config.yaml").read_text())
    repos = [r for r in (data.get("repos") or []) if r.get("repo") == _PRECOMMIT_REPO_URL]
    assert len(repos) == 0


def test_status_no_hooks(git_repo: Path) -> None:
    engine = HookEngine()
    st = engine.status(git_repo)
    assert st["git_installed"] is False
    assert st["precommit_installed"] is False


def test_status_git_installed(git_repo: Path) -> None:
    engine = HookEngine()
    engine.install(git_repo, mode="git", min_score=55)
    st = engine.status(git_repo)
    assert st["git_installed"] is True
    assert st["min_score"] == 55


def test_status_precommit_installed(tmp_path: Path) -> None:
    engine = HookEngine()
    engine.install(tmp_path, mode="precommit", min_score=60)
    st = engine.status(tmp_path)
    assert st["precommit_installed"] is True


def test_install_both_mode(git_repo: Path) -> None:
    engine = HookEngine()
    results = engine.install(git_repo, mode="both", min_score=60)
    assert results["git"]["status"] == "installed"
    assert results["precommit"]["status"] == "installed"


def test_uninstall_both_mode(git_repo: Path) -> None:
    engine = HookEngine()
    engine.install(git_repo, mode="both", min_score=60)
    results = engine.uninstall(git_repo, mode="both")
    assert results["git"]["status"] == "removed"
    assert results["precommit"]["status"] == "removed"
