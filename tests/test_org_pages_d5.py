"""Tests for D5: version bump, CHANGELOG, README, docs."""
from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
PYPROJECT = REPO_ROOT / "pyproject.toml"
CHANGELOG = REPO_ROOT / "CHANGELOG.md"
README = REPO_ROOT / "README.md"
DOCS_INDEX = REPO_ROOT / "docs" / "index.html"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Version
# ---------------------------------------------------------------------------

def test_version_in_pyproject():
    assert 'version = "0.58.0"' in _read(PYPROJECT)

def test_version_in_init():
    from agentkit_cli import __version__
    assert __version__ == "0.58.0"

def test_version_not_stale():
    content = _read(PYPROJECT)
    assert '0.57.0' not in content


# ---------------------------------------------------------------------------
# CHANGELOG
# ---------------------------------------------------------------------------

def test_changelog_has_058_entry():
    content = _read(CHANGELOG)
    assert "0.58.0" in content

def test_changelog_mentions_pages_org():
    content = _read(CHANGELOG)
    assert "pages-org" in content

def test_changelog_058_is_first_entry():
    content = _read(CHANGELOG)
    for line in content.splitlines():
        if line.startswith("## ["):
            assert "0.58.0" in line, f"First version entry in CHANGELOG is not 0.58.0: {line}"
            break


# ---------------------------------------------------------------------------
# README
# ---------------------------------------------------------------------------

def test_readme_has_publishing_section():
    content = _read(README)
    assert "Publishing & Sharing" in content

def test_readme_has_org_leaderboard_section():
    content = _read(README)
    assert "Org Leaderboard" in content

def test_readme_has_pages_org_command():
    content = _read(README)
    assert "pages-org" in content


# ---------------------------------------------------------------------------
# docs/index.html
# ---------------------------------------------------------------------------

def test_docs_index_has_org_leaderboard_nav():
    if not DOCS_INDEX.exists():
        pytest.skip("docs/index.html not found")
    content = _read(DOCS_INDEX)
    assert "Org Leaderboard" in content or "org-leaderboard" in content
