from __future__ import annotations

import json

import pytest

from agentkit_cli.closeout import CloseoutEngine
from agentkit_cli.land import LandEngine, LandError
from tests.test_closeout_engine import _save_closeout_chain
from tests.test_launch_engine import _make_repo
from tests.test_reconcile_engine import _git, _write_launch, _write_observe_result


def _save_land_chain(project):
    _save_closeout_chain(project)
    closeout_plan = CloseoutEngine().build(project)
    CloseoutEngine().write_directory(closeout_plan, project / "closeout")
    (project / "closeout.json").write_text((project / "closeout" / "closeout.json").read_text(encoding="utf-8"), encoding="utf-8")


def test_land_engine_classifies_land_now_review_waiting_and_already_closed(tmp_path):
    project = _make_repo(tmp_path)
    _write_launch(project, target="codex", overlap=True)

    lane1 = project / "stage" / "worktrees" / "demo-repo-phase-01-lane-01"
    (lane1 / "src" / "api" / "handlers.py").write_text("def handler():\n    return 'done'\n", encoding="utf-8")
    _git(lane1, "add", "src/api/handlers.py")
    _git(lane1, "commit", "-m", "finish lane-01")
    _write_observe_result(project, "lane-01", "success", "API lane passed tests.")
    _save_land_chain(project)

    payload = json.loads((project / "closeout.json").read_text(encoding="utf-8"))
    payload["lanes"][1]["closeout_bucket"] = "already-closed"
    payload["already_closed_lane_ids"] = ["lane-02"]
    payload["review_required_lane_ids"] = []
    (project / "closeout.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    plan = LandEngine().build(project, packet_dir=project / "land")

    assert plan.land_now_lane_ids == ["lane-01"]
    assert plan.already_closed_lane_ids == ["lane-02"]
    assert plan.review_required_lane_ids == []
    lane = next(item for item in plan.lanes if item.lane_id == "lane-01")
    assert lane.land_bucket == "land-now"
    assert lane.landing_packet_path.endswith("land/lanes/lane-01/packet.md")
    assert lane.landing_sequence == 1


def test_land_engine_marks_dirty_merge_ready_lane_for_review(tmp_path):
    project = _make_repo(tmp_path)
    _write_launch(project, target="codex", single_lane=True)

    lane1 = project / "stage" / "worktrees" / "demo-repo-phase-01-lane-01"
    (lane1 / "src" / "api" / "handlers.py").write_text("def handler():\n    return 'done'\n", encoding="utf-8")
    _git(lane1, "add", "src/api/handlers.py")
    _git(lane1, "commit", "-m", "finish lane-01")
    _write_observe_result(project, "lane-01", "success", "API lane passed tests.")
    _save_land_chain(project)

    (lane1 / "notes.txt").write_text("dirty\n", encoding="utf-8")
    plan = LandEngine().build(project)

    assert plan.review_required_lane_ids == ["lane-01"]
    assert plan.land_now_lane_ids == []
    assert plan.lanes[0].worktree_dirty is True


def test_land_engine_keeps_serialized_lane_waiting_until_review_clears(tmp_path):
    project = _make_repo(tmp_path)
    _write_launch(project, target="codex", overlap=True)

    lane1 = project / "stage" / "worktrees" / "demo-repo-phase-01-lane-01"
    lane2 = project / "stage" / "worktrees" / "demo-repo-phase-01-lane-02"
    (lane1 / "src" / "api" / "handlers.py").write_text("def handler():\n    return 'done'\n", encoding="utf-8")
    (lane2 / "src" / "api").mkdir(parents=True, exist_ok=True)
    (lane2 / "src" / "api" / "routes.py").write_text("def route():\n    return 'done'\n", encoding="utf-8")
    _git(lane1, "add", "src/api/handlers.py")
    _git(lane1, "commit", "-m", "finish lane-01")
    _git(lane2, "add", "src/api/routes.py")
    _git(lane2, "commit", "-m", "finish lane-02")
    _write_observe_result(project, "lane-01", "success", "API lane passed tests.")
    _write_observe_result(project, "lane-02", "success", "Routes lane passed tests.")
    _save_land_chain(project)

    payload = json.loads((project / "closeout.json").read_text(encoding="utf-8"))
    payload["lanes"][0]["closeout_bucket"] = "review-required"
    payload["lanes"][0]["serialization_group"] = "phase-01"
    payload["lanes"][1]["closeout_bucket"] = "merge-ready"
    payload["lanes"][1]["serialization_group"] = "phase-01"
    payload["merge_ready_lane_ids"] = ["lane-02"]
    payload["review_required_lane_ids"] = ["lane-01"]
    payload["waiting_lane_ids"] = []
    (project / "closeout.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    plan = LandEngine().build(project)

    assert plan.review_required_lane_ids == ["lane-01"]
    assert plan.waiting_lane_ids == ["lane-02"]
    assert plan.land_now_lane_ids == []
    lane = next(item for item in plan.lanes if item.lane_id == "lane-02")
    assert lane.follow_on_notes


def test_land_engine_rejects_contradictory_closeout_summary_membership(tmp_path):
    project = _make_repo(tmp_path)
    _write_launch(project, target="codex", single_lane=True)

    lane1 = project / "stage" / "worktrees" / "demo-repo-phase-01-lane-01"
    (lane1 / "src" / "api" / "handlers.py").write_text("def handler():\n    return 'done'\n", encoding="utf-8")
    _git(lane1, "add", "src/api/handlers.py")
    _git(lane1, "commit", "-m", "finish lane-01")
    _write_observe_result(project, "lane-01", "success", "API lane passed tests.")
    _save_land_chain(project)

    payload = json.loads((project / "closeout.json").read_text(encoding="utf-8"))
    payload["merge_ready_lane_ids"] = []
    (project / "closeout.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    with pytest.raises(LandError, match="disagrees with summary ids"):
        LandEngine().build(project)


def test_land_engine_rejects_missing_relaunch_artifact(tmp_path):
    project = _make_repo(tmp_path)
    _write_launch(project, target="codex", single_lane=True)
    _write_observe_result(project, "lane-01", "failure", "Retry lane 01.")
    _save_land_chain(project)

    payload = json.loads((project / "closeout.json").read_text(encoding="utf-8"))
    payload["relaunch_path"] = str(project / "missing-relaunch.json")
    (project / "closeout.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    with pytest.raises(LandError, match="missing relaunch packet"):
        LandEngine().build(project)
