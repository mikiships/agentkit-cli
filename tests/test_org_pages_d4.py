"""Tests for D4: example GitHub Actions workflow validation."""
from __future__ import annotations

from pathlib import Path

import pytest

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

WORKFLOW_PATH = Path(__file__).parent.parent / ".github" / "workflows" / "examples" / "agentkit-org-pages.yml"


# ---------------------------------------------------------------------------
# File existence
# ---------------------------------------------------------------------------

def test_workflow_file_exists():
    assert WORKFLOW_PATH.exists(), f"Workflow file not found: {WORKFLOW_PATH}"

def test_workflow_file_not_empty():
    assert WORKFLOW_PATH.stat().st_size > 0


# ---------------------------------------------------------------------------
# YAML structure (skip if pyyaml not available)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not HAS_YAML, reason="pyyaml not installed")
def test_workflow_is_valid_yaml():
    content = WORKFLOW_PATH.read_text(encoding="utf-8")
    data = yaml.safe_load(content)
    assert isinstance(data, dict)

@pytest.mark.skipif(not HAS_YAML, reason="pyyaml not installed")
def test_workflow_has_name():
    data = yaml.safe_load(WORKFLOW_PATH.read_text())
    assert "name" in data
    assert "Agentkit" in data["name"] or "agentkit" in data["name"].lower()

@pytest.mark.skipif(not HAS_YAML, reason="pyyaml not installed")
def test_workflow_has_on_trigger():
    data = yaml.safe_load(WORKFLOW_PATH.read_text())
    # PyYAML parses 'on' as True (boolean keyword in YAML 1.1)
    assert True in data or "on" in data

@pytest.mark.skipif(not HAS_YAML, reason="pyyaml not installed")
def test_workflow_has_schedule():
    data = yaml.safe_load(WORKFLOW_PATH.read_text())
    # 'on' key is parsed as True by PyYAML
    on = data.get(True) or data.get("on", {})
    assert "schedule" in on

@pytest.mark.skipif(not HAS_YAML, reason="pyyaml not installed")
def test_workflow_has_workflow_dispatch():
    data = yaml.safe_load(WORKFLOW_PATH.read_text())
    on = data.get(True) or data.get("on", {})
    assert "workflow_dispatch" in on

@pytest.mark.skipif(not HAS_YAML, reason="pyyaml not installed")
def test_workflow_has_jobs():
    data = yaml.safe_load(WORKFLOW_PATH.read_text())
    assert "jobs" in data
    assert len(data["jobs"]) > 0

@pytest.mark.skipif(not HAS_YAML, reason="pyyaml not installed")
def test_workflow_uses_ubuntu():
    data = yaml.safe_load(WORKFLOW_PATH.read_text())
    jobs = data["jobs"]
    for job in jobs.values():
        assert "ubuntu" in job.get("runs-on", "")

@pytest.mark.skipif(not HAS_YAML, reason="pyyaml not installed")
def test_workflow_has_steps():
    data = yaml.safe_load(WORKFLOW_PATH.read_text())
    for job in data["jobs"].values():
        assert "steps" in job
        assert len(job["steps"]) > 0


# ---------------------------------------------------------------------------
# Content checks (raw text — no yaml dependency)
# ---------------------------------------------------------------------------

def test_workflow_contains_pip_install_agentkit():
    content = WORKFLOW_PATH.read_text(encoding="utf-8")
    assert "agentkit-cli" in content

def test_workflow_contains_pages_org_command():
    content = WORKFLOW_PATH.read_text(encoding="utf-8")
    assert "pages-org" in content

def test_workflow_contains_github_token():
    content = WORKFLOW_PATH.read_text(encoding="utf-8")
    assert "GITHUB_TOKEN" in content

def test_workflow_contains_monday_cron():
    content = WORKFLOW_PATH.read_text(encoding="utf-8")
    # '0 8 * * 1' = Monday 8 AM UTC
    assert "0 8 * * 1" in content

def test_workflow_contains_setup_guide_comment():
    content = WORKFLOW_PATH.read_text(encoding="utf-8")
    assert "Setup Guide" in content or "setup" in content.lower()

def test_workflow_contains_pages_url_format():
    content = WORKFLOW_PATH.read_text(encoding="utf-8")
    assert "github.io" in content
