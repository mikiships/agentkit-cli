from __future__ import annotations

import json

import pytest

from agentkit_cli.observe import ObserveEngine
from agentkit_cli.reconcile import ReconcileEngine
from agentkit_cli.relaunch import RelaunchEngine, RelaunchError
from agentkit_cli.resume import ResumeEngine
from agentkit_cli.supervise import SuperviseEngine
from tests.test_launch_engine import _make_repo
from tests.test_reconcile_engine import _git, _write_launch, _write_observe_result


def _save_resume_chain(project):
    observe_plan = ObserveEngine().build(project, target="codex")
    ObserveEngine().write_directory(observe_plan, project / "observe")
    supervise_plan = SuperviseEngine().build(project)
    SuperviseEngine().write_directory(supervise_plan, project / "supervise")
    reconcile_plan = ReconcileEngine().build(project)
    ReconcileEngine().write_directory(reconcile_plan, project / "reconcile")
    (project / "reconcile.json").write_text((project / "reconcile" / "reconcile.json").read_text(encoding="utf-8"), encoding="utf-8")
    resume_plan = ResumeEngine().build(project)
    ResumeEngine().write_directory(resume_plan, project / "resume")
    (project / "resume.json").write_text((project / "resume" / "resume.json").read_text(encoding="utf-8"), encoding="utf-8")


def test_relaunch_engine_builds_fresh_packets_for_eligible_lanes(tmp_path):
    project = _make_repo(tmp_path)
    _write_launch(project, target="codex", overlap=True)

    lane1 = project / "stage" / "worktrees" / "demo-repo-phase-01-lane-01"
    (lane1 / "src" / "api" / "handlers.py").write_text("def handler():\n    return 'done'\n", encoding="utf-8")
    _git(lane1, "add", "src/api/handlers.py")
    _git(lane1, "commit", "-m", "finish lane-01")
    _write_observe_result(project, "lane-01", "success", "API lane passed tests.")
    _save_resume_chain(project)

    plan = RelaunchEngine().build(project, packet_dir=project / "relaunch")

    assert plan.relaunch_now_lane_ids == ["lane-02"]
    assert plan.completed_lane_ids == ["lane-01"]
    lane = next(item for item in plan.lanes if item.lane_id == "lane-02")
    assert lane.handoff_markdown_path.endswith("relaunch/lanes/lane-02/handoff.md")
    assert "codex exec --full-auto - <" in lane.display_command
    assert lane.source_reconcile_bucket == "ready"


def test_relaunch_engine_preserves_review_waiting_and_completed_buckets(tmp_path):
    project = _make_repo(tmp_path)
    _write_launch(project, target="codex", single_lane=True)
    _write_observe_result(project, "lane-01", "failure", "Retry lane 01.")
    _save_resume_chain(project)

    payload = json.loads((project / "resume.json").read_text(encoding="utf-8"))
    payload["lanes"][0]["resume_bucket"] = "review-only"
    payload["lanes"][0]["reason"] = "Human inspection required."
    payload["review_lane_ids"] = ["lane-01"]
    payload["relaunch_now_lane_ids"] = []
    (project / "resume.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    reconcile_payload = json.loads((project / "reconcile.json").read_text(encoding="utf-8"))
    reconcile_payload["lanes"][0]["bucket"] = "needs-human-review"
    reconcile_payload["needs_human_review_lane_ids"] = ["lane-01"]
    reconcile_payload["relaunch_ready_lane_ids"] = []
    (project / "reconcile.json").write_text(json.dumps(reconcile_payload, indent=2, sort_keys=True), encoding="utf-8")

    plan = RelaunchEngine().build(project)

    assert plan.review_lane_ids == ["lane-01"]
    lane = plan.lanes[0]
    assert lane.relaunch_bucket == "review-only"
    assert any("should not be relaunched" in note for note in lane.review_notes)


def test_relaunch_engine_rejects_unsatisfied_dependency_marked_relaunch_now(tmp_path):
    project = _make_repo(tmp_path)
    _write_launch(project, target="codex", overlap=True)

    lane1 = project / "stage" / "worktrees" / "demo-repo-phase-01-lane-01"
    (lane1 / "src" / "api" / "handlers.py").write_text("def handler():\n    return 'done'\n", encoding="utf-8")
    _git(lane1, "add", "src/api/handlers.py")
    _git(lane1, "commit", "-m", "finish lane-01")
    _write_observe_result(project, "lane-01", "success", "API lane passed tests.")
    _save_resume_chain(project)

    payload = json.loads((project / "resume.json").read_text(encoding="utf-8"))
    payload["lanes"][1]["dependencies"][0]["satisfied"] = False
    (project / "resume.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    with pytest.raises(RelaunchError, match="cannot relaunch now while dependencies remain unsatisfied"):
        RelaunchEngine().build(project)


def test_relaunch_engine_notes_stale_worktree_paths(tmp_path):
    project = _make_repo(tmp_path)
    _write_launch(project, target="codex", single_lane=True)
    _write_observe_result(project, "lane-01", "failure", "Retry lane 01.")
    _save_resume_chain(project)

    payload = json.loads((project / "launch.json").read_text(encoding="utf-8"))
    payload["actions"][0]["worktree_path"] = str(project / "stage" / "worktrees" / "missing-lane-01")
    launch_packet = project / "launch.json"
    launch_packet.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    plan = RelaunchEngine().build(project, packet_dir=project / "relaunch")

    lane = plan.lanes[0]
    assert lane.relaunch_bucket == "relaunch-now"
    assert any("stale or missing" in note for note in lane.review_notes)
    assert "recreate the lane worktree" in lane.display_command
