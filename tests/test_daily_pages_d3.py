"""Tests for D3: GitHub Actions daily leaderboard workflow YAML."""
from __future__ import annotations

from pathlib import Path

import pytest

WORKFLOW_PATH = (
    Path(__file__).parent.parent
    / ".github"
    / "workflows"
    / "examples"
    / "agentkit-daily-leaderboard-pages.yml"
)


def _content() -> str:
    return WORKFLOW_PATH.read_text(encoding="utf-8")


def test_workflow_file_exists():
    assert WORKFLOW_PATH.exists(), f"Workflow file not found at {WORKFLOW_PATH}"


def test_workflow_has_schedule_trigger():
    content = _content()
    assert "schedule" in content
    assert "cron" in content


def test_workflow_cron_is_daily_8am():
    content = _content()
    assert "0 8 * * *" in content


def test_workflow_has_workflow_dispatch():
    content = _content()
    assert "workflow_dispatch" in content


def test_workflow_has_contents_write_permission():
    content = _content()
    assert "contents: write" in content


def test_workflow_has_pages_write_permission():
    content = _content()
    assert "pages: write" in content


def test_workflow_has_checkout_step():
    content = _content()
    assert "actions/checkout" in content


def test_workflow_has_install_agentkit_step():
    content = _content()
    assert "agentkit-cli" in content
    assert "pip install" in content


def test_workflow_has_pages_flag():
    content = _content()
    assert "--pages" in content


def test_workflow_uses_github_token():
    content = _content()
    assert "GITHUB_TOKEN" in content
