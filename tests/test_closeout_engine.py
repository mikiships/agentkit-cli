from __future__ import annotations

import json

import pytest

from agentkit_cli.closeout import CloseoutEngine, CloseoutError
from tests.test_launch_engine import _make_repo
from tests.test_reconcile_engine import _git, _write_launch, _write_observe_result
from tests.test_relaunch_engine import _save_resume_chain
from agentkit_cli.relaunch import RelaunchEngine


def _save_closeout_chain(project):
    _save_resume_chain(project)
    relaunch_plan = RelaunchEngine().build(project)
    RelaunchEngine().write_directory(relaunch_plan, project / "relaunch")
    (project / "relaunch.json").write_text((project / "relaunch" / "relaunch.json").read_text(encoding="utf-8"), encoding="utf-8")


def test_closeout_engine_classifies_merge_ready_review_and_waiting(tmp_path):
    project = _make_repo(tmp_path)
    _write_launch(project, target="codex", overlap=True)

    lane1 = project / "stage" / "worktrees" / "demo-repo-phase-01-lane-01"
    (lane1 / "src" / "api" / "handlers.py").write_text("def handler():\n    return 'done'\n", encoding="utf-8")
    _git(lane1, "add", "src/api/handlers.py")
    _git(lane1, "commit", "-m", "finish lane-01")
    _write_observe_result(project, "lane-01", "success", "API lane passed tests.")
    _save_closeout_chain(project)

    plan = CloseoutEngine().build(project, packet_dir=project / "closeout")

    assert plan.merge_ready_lane_ids == ["lane-01"]
    assert plan.review_required_lane_ids == ["lane-02"]
    assert plan.waiting_lane_ids == []
    lane = next(item for item in plan.lanes if item.lane_id == "lane-01")
    assert lane.closeout_bucket == "merge-ready"
    assert lane.closeout_packet_path.endswith("closeout/lanes/lane-01/packet.md")


def test_closeout_engine_marks_completed_dirty_worktree_for_review(tmp_path):
    project = _make_repo(tmp_path)
    _write_launch(project, target="codex", single_lane=True)

    lane1 = project / "stage" / "worktrees" / "demo-repo-phase-01-lane-01"
    (lane1 / "src" / "api" / "handlers.py").write_text("def handler():\n    return 'done'\n", encoding="utf-8")
    _git(lane1, "add", "src/api/handlers.py")
    _git(lane1, "commit", "-m", "finish lane-01")
    _write_observe_result(project, "lane-01", "success", "API lane passed tests.")
    _save_closeout_chain(project)

    (lane1 / "notes.txt").write_text("dirty\n", encoding="utf-8")
    plan = CloseoutEngine().build(project)

    assert plan.review_required_lane_ids == ["lane-01"]
    assert plan.merge_ready_lane_ids == []
    lane = plan.lanes[0]
    assert lane.worktree_dirty is True


def test_closeout_engine_surfaces_follow_on_notes_for_unblocked_waiting_lane(tmp_path):
    project = _make_repo(tmp_path)
    _write_launch(project, target="codex", overlap=True)

    lane1 = project / "stage" / "worktrees" / "demo-repo-phase-01-lane-01"
    (lane1 / "src" / "api" / "handlers.py").write_text("def handler():\n    return 'done'\n", encoding="utf-8")
    _git(lane1, "add", "src/api/handlers.py")
    _git(lane1, "commit", "-m", "finish lane-01")
    _write_observe_result(project, "lane-01", "success", "API lane passed tests.")
    _save_closeout_chain(project)

    relaunch_payload = json.loads((project / "relaunch.json").read_text(encoding="utf-8"))
    relaunch_payload["lanes"][1]["relaunch_bucket"] = "waiting"
    relaunch_payload["waiting_lane_ids"] = ["lane-02"]
    relaunch_payload["review_lane_ids"] = []
    relaunch_payload["relaunch_now_lane_ids"] = []
    (project / "relaunch.json").write_text(json.dumps(relaunch_payload, indent=2, sort_keys=True), encoding="utf-8")

    plan = CloseoutEngine().build(project)

    assert plan.waiting_lane_ids == ["lane-02"]
    lane = next(item for item in plan.lanes if item.lane_id == "lane-02")
    assert lane.follow_on_notes


def test_closeout_engine_rejects_missing_resume_artifact(tmp_path):
    project = _make_repo(tmp_path)
    _write_launch(project, target="codex", single_lane=True)
    _write_observe_result(project, "lane-01", "failure", "Retry lane 01.")
    _save_closeout_chain(project)

    payload = json.loads((project / "relaunch.json").read_text(encoding="utf-8"))
    payload["resume_path"] = str(project / "missing-resume.json")
    (project / "relaunch.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    with pytest.raises(CloseoutError, match="missing resume packet"):
        CloseoutEngine().build(project)
