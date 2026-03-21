"""Tests for agentkit leaderboard-page D2 — GitHub Pages workflow."""
from __future__ import annotations

import yaml
from pathlib import Path


WORKFLOW_PATH = Path(__file__).parent.parent / ".github" / "workflows" / "update-leaderboard.yml"


def _load_workflow() -> dict:
    return yaml.safe_load(WORKFLOW_PATH.read_text())


def test_workflow_file_exists():
    assert WORKFLOW_PATH.exists()


def test_workflow_is_valid_yaml():
    data = _load_workflow()
    assert isinstance(data, dict)


def test_workflow_has_schedule_trigger():
    data = _load_workflow()
    assert "schedule" in data.get("on", {}) or "schedule" in data.get(True, {})


def test_workflow_schedule_is_weekly():
    data = _load_workflow()
    on = data.get("on") or data.get(True)
    schedule = on.get("schedule", [])
    assert len(schedule) > 0
    cron = schedule[0].get("cron", "")
    # Should be weekly (not daily)
    parts = cron.strip().split()
    assert len(parts) == 5


def test_workflow_has_jobs():
    data = _load_workflow()
    assert "jobs" in data


def test_workflow_job_runs_on_ubuntu():
    data = _load_workflow()
    jobs = data.get("jobs", {})
    first_job = next(iter(jobs.values()))
    assert "ubuntu" in first_job.get("runs-on", "")


def test_workflow_has_checkout_step():
    data = _load_workflow()
    jobs = data.get("jobs", {})
    first_job = next(iter(jobs.values()))
    steps = first_job.get("steps", [])
    uses_list = [s.get("uses", "") for s in steps]
    assert any("checkout" in u for u in uses_list)


def test_workflow_has_python_setup_step():
    data = _load_workflow()
    jobs = data.get("jobs", {})
    first_job = next(iter(jobs.values()))
    steps = first_job.get("steps", [])
    uses_list = [s.get("uses", "") for s in steps]
    assert any("setup-python" in u for u in uses_list)


def test_workflow_runs_leaderboard_command():
    content = WORKFLOW_PATH.read_text()
    assert "leaderboard-page" in content or "leaderboard_page" in content


def test_workflow_commits_to_docs():
    content = WORKFLOW_PATH.read_text()
    assert "docs" in content


def test_workflow_no_push_trigger():
    data = _load_workflow()
    on = data.get("on") or data.get(True)
    assert "push" not in on
    assert "pull_request" not in on


def test_workflow_has_git_commit_step():
    content = WORKFLOW_PATH.read_text()
    assert "git commit" in content


def test_workflow_has_git_push_step():
    content = WORKFLOW_PATH.read_text()
    assert "git push" in content
