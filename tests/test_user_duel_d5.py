"""Tests for D5: docs, CHANGELOG, and BUILD-REPORT validation."""
from __future__ import annotations

from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).parent.parent


def test_changelog_has_0_61_0_entry():
    changelog = (REPO_ROOT / "CHANGELOG.md").read_text()
    assert "0.61.0" in changelog


def test_changelog_0_61_0_before_0_60_0():
    changelog = (REPO_ROOT / "CHANGELOG.md").read_text()
    pos_61 = changelog.find("0.61.0")
    pos_60 = changelog.find("0.60.0")
    assert pos_61 < pos_60, "0.61.0 entry must appear before 0.60.0"


def test_changelog_mentions_user_duel():
    changelog = (REPO_ROOT / "CHANGELOG.md").read_text()
    assert "user-duel" in changelog.lower()


def test_readme_mentions_user_duel():
    readme = (REPO_ROOT / "README.md").read_text()
    assert "user-duel" in readme


def test_readme_user_duel_usage_section():
    readme = (REPO_ROOT / "README.md").read_text()
    assert "User Duel" in readme


def test_user_duel_module_exists():
    assert (REPO_ROOT / "agentkit_cli" / "user_duel.py").exists()


def test_user_duel_cmd_exists():
    assert (REPO_ROOT / "agentkit_cli" / "commands" / "user_duel_cmd.py").exists()


def test_user_duel_wired_in_main():
    main_text = (REPO_ROOT / "agentkit_cli" / "main.py").read_text()
    assert "user_duel_command" in main_text
    assert "user-duel" in main_text


def test_build_report_exists():
    assert (REPO_ROOT / "BUILD-REPORT-v0.61.0.md").exists()
