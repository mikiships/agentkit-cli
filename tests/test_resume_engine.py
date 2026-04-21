from __future__ import annotations

import json

import pytest

from agentkit_cli.observe import ObserveEngine
from agentkit_cli.reconcile import ReconcileEngine
from agentkit_cli.resume import ResumeEngine, ResumeError
from agentkit_cli.supervise import SuperviseEngine
from tests.test_launch_engine import _make_repo
from tests.test_reconcile_engine import _git, _write_launch, _write_observe_result


def _save_observe_supervise_reconcile(project):
    observe_plan = ObserveEngine().build(project, target="codex")
    ObserveEngine().write_directory(observe_plan, project / "observe")
    supervise_plan = SuperviseEngine().build(project)
    SuperviseEngine().write_directory(supervise_plan, project / "supervise")
    reconcile_plan = ReconcileEngine().build(project)
    ReconcileEngine().write_directory(reconcile_plan, project / "reconcile")
    (project / "reconcile.json").write_text((project / "reconcile" / "reconcile.json").read_text(encoding="utf-8"), encoding="utf-8")


def test_resume_engine_classifies_complete_ready_waiting_and_review(tmp_path):
    project = _make_repo(tmp_path)
    _write_launch(project, target="codex", overlap=True)

    lane1 = project / "stage" / "worktrees" / "demo-repo-phase-01-lane-01"
    (lane1 / "src" / "api" / "handlers.py").write_text("def handler():\n    return 'done'\n", encoding="utf-8")
    _git(lane1, "add", "src/api/handlers.py")
    _git(lane1, "commit", "-m", "finish lane-01")
    _write_observe_result(project, "lane-01", "success", "API lane passed tests.")
    _save_observe_supervise_reconcile(project)

    payload = json.loads((project / "reconcile.json").read_text(encoding="utf-8"))
    payload["lanes"].append(
        {
            **payload["lanes"][0],
            "lane_id": "lane-03",
            "title": "manual review lane",
            "bucket": "needs-human-review",
            "reason": "Worktree drift needs inspection.",
            "next_action": "Inspect manually.",
            "phase_index": 3,
        }
    )
    payload["needs_human_review_lane_ids"] = ["lane-03"]
    payload["source_launch"]["actions"].append(
        {
            **payload["source_launch"]["actions"][0],
            "lane_id": "lane-03",
            "title": "manual review lane",
            "phase_index": 3,
        }
    )
    (project / "reconcile.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    plan = ResumeEngine().build(project)

    assert plan.completed_lane_ids == ["lane-01"]
    assert plan.relaunch_now_lane_ids == ["lane-02"]
    assert plan.review_lane_ids == ["lane-03"]


def test_resume_engine_preserves_serialization_group_safety(tmp_path):
    project = _make_repo(tmp_path)
    _write_launch(project, target="codex", single_lane=True)
    _write_observe_result(project, "lane-01", "failure", "Retry lane 01.")
    _save_observe_supervise_reconcile(project)

    payload = json.loads((project / "reconcile.json").read_text(encoding="utf-8"))
    lane2 = {
        **payload["lanes"][0],
        "lane_id": "lane-02",
        "title": "second retry",
        "bucket": "ready",
        "reason": "Also ready.",
        "next_action": "Launch when ready.",
        "phase_index": 2,
        "serialization_group": "serial-a",
        "dependencies": [],
    }
    payload["lanes"][0]["serialization_group"] = "serial-a"
    payload["relaunch_ready_lane_ids"] = ["lane-01"]
    payload["ready_lane_ids"] = ["lane-02"]
    payload["lanes"].append(lane2)
    payload["source_launch"]["actions"][0]["serialization_group"] = "serial-a"
    payload["source_launch"]["actions"].append({**payload["source_launch"]["actions"][0], "lane_id": "lane-02", "title": "second retry", "phase_index": 2})
    (project / "reconcile.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    plan = ResumeEngine().build(project)

    assert plan.relaunch_now_lane_ids == ["lane-01"]
    assert "lane-02" in plan.waiting_lane_ids


def test_resume_engine_rejects_contradictory_summary_membership(tmp_path):
    project = _make_repo(tmp_path)
    _write_launch(project, target="codex", single_lane=True)
    _write_observe_result(project, "lane-01", "failure", "Retry lane 01.")
    _save_observe_supervise_reconcile(project)

    payload = json.loads((project / "reconcile.json").read_text(encoding="utf-8"))
    payload["relaunch_ready_lane_ids"] = []
    (project / "reconcile.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    with pytest.raises(ResumeError, match="disagrees with summary ids"):
        ResumeEngine().build(project)


def test_resume_engine_requires_saved_supervise_artifact(tmp_path):
    project = _make_repo(tmp_path)
    _write_launch(project, target="codex", single_lane=True)
    _write_observe_result(project, "lane-01", "failure", "Retry lane 01.")
    _save_observe_supervise_reconcile(project)

    payload = json.loads((project / "reconcile.json").read_text(encoding="utf-8"))
    payload["supervise_path"] = None
    (project / "reconcile.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    with pytest.raises(ResumeError, match="supervise_path is required"):
        ResumeEngine().build(project)
