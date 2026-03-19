"""Tests for D5: docs, CHANGELOG, version, quickstart."""
from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent


def test_changelog_has_060():
    changelog = (REPO_ROOT / "CHANGELOG.md").read_text()
    assert "[0.60.0]" in changelog


def test_changelog_user_scorecard_entry():
    changelog = (REPO_ROOT / "CHANGELOG.md").read_text()
    assert "user-scorecard" in changelog


def test_pyproject_version_060():
    pyproject = (REPO_ROOT / "pyproject.toml").read_text()
    assert 'version = "0.62.0"' in pyproject


def test_docs_has_user_scorecard_card():
    html = (REPO_ROOT / "docs" / "index.html").read_text()
    assert "user-scorecard" in html.lower() or "Developer Profile Card" in html


def test_docs_feature_card_present():
    html = (REPO_ROOT / "docs" / "index.html").read_text()
    assert "Developer Profile Card" in html
