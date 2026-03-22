"""Tests for D5: version bump, CHANGELOG, README, pyproject docs."""
from __future__ import annotations

from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).parent.parent


def test_version_bumped() -> None:
    from agentkit_cli import __version__
    assert __version__ == "0.86.0"


def test_pyproject_version() -> None:
    pyproject = REPO_ROOT / "pyproject.toml"
    assert pyproject.exists()
    content = pyproject.read_text()
    assert 'version = "0.86.0"' in content


def test_changelog_has_v0860_entry() -> None:
    changelog = REPO_ROOT / "CHANGELOG.md"
    assert changelog.exists()
    content = changelog.read_text()
    assert "0.86.0" in content


def test_changelog_mentions_hooks() -> None:
    changelog = REPO_ROOT / "CHANGELOG.md"
    content = changelog.read_text()
    assert "hooks" in content.lower()


def test_readme_has_hooks_command() -> None:
    readme = REPO_ROOT / "README.md"
    assert readme.exists()
    content = readme.read_text()
    assert "hooks" in content.lower()


def test_hooks_module_importable() -> None:
    from agentkit_cli.hooks import HookEngine
    assert HookEngine is not None


def test_hooks_cmd_importable() -> None:
    from agentkit_cli.commands.hooks_cmd import hooks_app
    assert hooks_app is not None


def test_hooks_registered_in_app() -> None:
    from agentkit_cli.main import app
    command_names = [c.name for c in app.registered_groups]
    assert "hooks" in command_names


def test_doctor_valid_categories_include_hooks() -> None:
    from agentkit_cli.commands.doctor_cmd import _VALID_CATEGORIES
    assert "hooks" in _VALID_CATEGORIES
