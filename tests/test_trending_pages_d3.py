"""Tests for D3: GitHub Actions workflow for agentkit pages-trending."""
from __future__ import annotations

from pathlib import Path

import pytest

WORKFLOW_PATH = Path(__file__).parent.parent / ".github" / "workflows" / "examples" / "agentkit-trending-pages.yml"


def _load_yaml_text() -> str:
    return WORKFLOW_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Workflow file existence
# ---------------------------------------------------------------------------

def test_workflow_file_exists():
    assert WORKFLOW_PATH.exists(), f"Workflow file not found: {WORKFLOW_PATH}"

def test_workflow_is_non_empty():
    content = _load_yaml_text()
    assert len(content) > 100


# ---------------------------------------------------------------------------
# Workflow structure
# ---------------------------------------------------------------------------

def test_workflow_has_schedule_cron():
    content = _load_yaml_text()
    assert "schedule" in content
    assert "cron" in content

def test_workflow_cron_is_daily_8am():
    content = _load_yaml_text()
    assert "0 8 * * *" in content

def test_workflow_uses_github_token():
    content = _load_yaml_text()
    assert "GITHUB_TOKEN" in content

def test_workflow_has_pages_trending_command():
    content = _load_yaml_text()
    assert "pages-trending" in content

def test_workflow_has_workflow_dispatch():
    content = _load_yaml_text()
    assert "workflow_dispatch" in content

def test_workflow_inputs_limit():
    content = _load_yaml_text()
    assert "limit" in content

def test_workflow_inputs_language():
    content = _load_yaml_text()
    assert "language" in content

def test_workflow_inputs_period():
    content = _load_yaml_text()
    assert "period" in content

def test_workflow_permissions():
    content = _load_yaml_text()
    assert "contents: write" in content

def test_workflow_python_setup():
    content = _load_yaml_text()
    assert "setup-python" in content

def test_workflow_installs_agentkit():
    content = _load_yaml_text()
    assert "pip install agentkit-cli" in content or "pip install" in content

def test_workflow_updates_index_html():
    content = _load_yaml_text()
    assert "index.html" in content or "trending.html" in content

def test_workflow_git_configure():
    content = _load_yaml_text()
    assert "git config" in content
