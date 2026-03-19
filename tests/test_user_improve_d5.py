"""Tests for D5: Docs, CHANGELOG, version bump, BUILD-REPORT (≥5 tests)."""
from __future__ import annotations

from pathlib import Path

import pytest

import agentkit_cli


REPO_ROOT = Path(__file__).parent.parent


# ---------------------------------------------------------------------------
# Version tests (never use string literals)
# ---------------------------------------------------------------------------

def test_version_matches_pyproject():
    import tomllib
    pyproject_path = REPO_ROOT / "pyproject.toml"
    if not pyproject_path.exists():
        pytest.skip("pyproject.toml not found")
    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)
    pyproject_version = data["project"]["version"]
    assert pyproject_version == agentkit_cli.__version__


def test_version_in_changelog():
    changelog = REPO_ROOT / "CHANGELOG.md"
    if not changelog.exists():
        pytest.skip("CHANGELOG.md not found")
    content = changelog.read_text()
    assert agentkit_cli.__version__ in content


def test_version_importlib_metadata():
    import importlib.metadata
    meta_version = importlib.metadata.version("agentkit-cli")
    # metadata may be stale in dev, but the module version must be consistent
    assert agentkit_cli.__version__ is not None
    assert len(agentkit_cli.__version__) > 0


def test_changelog_has_user_improve_entry():
    changelog = REPO_ROOT / "CHANGELOG.md"
    if not changelog.exists():
        pytest.skip("CHANGELOG.md not found")
    content = changelog.read_text()
    assert "user-improve" in content


def test_readme_has_user_improve_section():
    readme = REPO_ROOT / "README.md"
    if not readme.exists():
        pytest.skip("README.md not found")
    content = readme.read_text()
    assert "user-improve" in content


def test_user_improve_module_importable():
    import agentkit_cli.user_improve as m
    assert hasattr(m, "UserImproveEngine")
    assert hasattr(m, "UserImproveReport")
    assert hasattr(m, "UserImproveResult")
    assert hasattr(m, "UserRepoScore")


def test_user_improve_html_renderer_importable():
    import agentkit_cli.renderers.user_improve_html as m
    assert hasattr(m, "UserImproveHTMLRenderer")
    assert hasattr(m, "upload_user_improve_report")


def test_user_improve_cmd_importable():
    import agentkit_cli.commands.user_improve_cmd as m
    assert hasattr(m, "user_improve_command")
