"""Tests for D4: GitHub Actions cron workflow file."""
from __future__ import annotations

from pathlib import Path

import pytest

WORKFLOW_PATH = Path(__file__).parent.parent / ".github" / "workflows" / "examples" / "agentkit-daily-leaderboard.yml"


def _load_yaml():
    import yaml
    return yaml.safe_load(WORKFLOW_PATH.read_text())


def _get_on(doc: dict) -> dict:
    """Return the 'on' section — pyyaml parses 'on' as True."""
    return doc.get("on") or doc.get(True) or {}


# ---------------------------------------------------------------------------
# File existence + basic parsing
# ---------------------------------------------------------------------------

class TestWorkflowFileExists:
    def test_file_exists(self):
        assert WORKFLOW_PATH.exists(), f"Workflow file not found: {WORKFLOW_PATH}"

    def test_is_yaml(self):
        content = WORKFLOW_PATH.read_text()
        assert content.strip()

    def test_parses_without_error(self):
        doc = _load_yaml()
        assert doc is not None

    def test_has_name_key(self):
        doc = _load_yaml()
        assert "name" in doc

    def test_has_on_key(self):
        doc = _load_yaml()
        assert "on" in doc or True in doc

    def test_has_jobs_key(self):
        doc = _load_yaml()
        assert "jobs" in doc


# ---------------------------------------------------------------------------
# Schedule
# ---------------------------------------------------------------------------

class TestWorkflowSchedule:
    def test_has_schedule_trigger(self):
        doc = _load_yaml()
        on = _get_on(doc)
        assert "schedule" in on

    def test_schedule_is_9am(self):
        doc = _load_yaml()
        on = _get_on(doc)
        schedules = on["schedule"]
        crons = [s["cron"] for s in schedules]
        assert any("0 9" in c for c in crons)

    def test_has_workflow_dispatch(self):
        doc = _load_yaml()
        on = _get_on(doc)
        assert "workflow_dispatch" in on


# ---------------------------------------------------------------------------
# Job steps
# ---------------------------------------------------------------------------

class TestWorkflowSteps:
    def test_has_at_least_one_job(self):
        doc = _load_yaml()
        assert len(doc["jobs"]) >= 1

    def test_job_runs_on_ubuntu(self):
        doc = _load_yaml()
        for job in doc["jobs"].values():
            assert "ubuntu" in job["runs-on"]

    def test_job_has_steps(self):
        doc = _load_yaml()
        for job in doc["jobs"].values():
            assert "steps" in job
            assert len(job["steps"]) > 0

    def test_has_agentkit_daily_command(self):
        doc = _load_yaml()
        all_steps = []
        for job in doc["jobs"].values():
            all_steps.extend(job.get("steps", []))
        run_scripts = " ".join(s.get("run", "") for s in all_steps)
        assert "agentkit daily" in run_scripts

    def test_has_share_flag(self):
        doc = _load_yaml()
        all_steps = []
        for job in doc["jobs"].values():
            all_steps.extend(job.get("steps", []))
        run_scripts = " ".join(s.get("run", "") for s in all_steps)
        assert "--share" in run_scripts

    def test_has_quiet_flag(self):
        doc = _load_yaml()
        all_steps = []
        for job in doc["jobs"].values():
            all_steps.extend(job.get("steps", []))
        run_scripts = " ".join(s.get("run", "") for s in all_steps)
        assert "--quiet" in run_scripts

    def test_url_captured_to_output(self):
        doc = _load_yaml()
        all_steps = []
        for job in doc["jobs"].values():
            all_steps.extend(job.get("steps", []))
        run_scripts = " ".join(s.get("run", "") for s in all_steps)
        assert "GITHUB_OUTPUT" in run_scripts or "url" in run_scripts

    def test_step_summary_written(self):
        doc = _load_yaml()
        all_steps = []
        for job in doc["jobs"].values():
            all_steps.extend(job.get("steps", []))
        run_scripts = " ".join(s.get("run", "") for s in all_steps)
        assert "GITHUB_STEP_SUMMARY" in run_scripts

    def test_python_setup_step_present(self):
        doc = _load_yaml()
        all_steps = []
        for job in doc["jobs"].values():
            all_steps.extend(job.get("steps", []))
        uses_vals = [s.get("uses", "") for s in all_steps]
        assert any("setup-python" in u for u in uses_vals)

    def test_checkout_step_present(self):
        doc = _load_yaml()
        all_steps = []
        for job in doc["jobs"].values():
            all_steps.extend(job.get("steps", []))
        uses_vals = [s.get("uses", "") for s in all_steps]
        assert any("checkout" in u for u in uses_vals)
