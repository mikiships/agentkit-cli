from __future__ import annotations

import json

import pytest

from agentkit_cli.merge import MergeEngine, MergeError
from tests.test_land_engine import _save_land_chain
from tests.test_launch_engine import _make_repo
from tests.test_reconcile_engine import _git, _write_launch, _write_observe_result


def test_merge_engine_classifies_merge_now_blocked_waiting_and_already_landed(tmp_path):
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

    plan = MergeEngine().build(project, output_dir=project / "merge")

    assert plan.merge_now_lane_ids == ["lane-01"]
    assert plan.already_landed_lane_ids == ["lane-02"]
    lane = next(item for item in plan.lanes if item.lane_id == "lane-01")
    assert lane.merge_bucket == "merge-now"
    assert lane.merge_packet_path.endswith("merge/lanes/lane-01/packet.md")


def test_merge_engine_blocks_dirty_target_worktree(tmp_path):
    project = _make_repo(tmp_path)
    _write_launch(project, target="codex", single_lane=True)
    lane1 = project / "stage" / "worktrees" / "demo-repo-phase-01-lane-01"
    (lane1 / "src" / "api" / "handlers.py").write_text("def handler():\n    return 'done'\n", encoding="utf-8")
    _git(lane1, "add", "src/api/handlers.py")
    _git(lane1, "commit", "-m", "finish lane-01")
    _write_observe_result(project, "lane-01", "success", "API lane passed tests.")
    _save_land_chain(project)
    (project / "ROOT_DIRTY.txt").write_text("dirty\n", encoding="utf-8")

    plan = MergeEngine().build(project)

    assert plan.blocked_lane_ids == ["lane-01"]
    assert plan.lanes[0].merge_bucket == "blocked"


def test_merge_engine_marks_already_merged_branch_as_already_landed(tmp_path):
    project = _make_repo(tmp_path)
    _write_launch(project, target="codex", single_lane=True)
    lane1 = project / "stage" / "worktrees" / "demo-repo-phase-01-lane-01"
    (lane1 / "src" / "api" / "handlers.py").write_text("def handler():\n    return 'done'\n", encoding="utf-8")
    _git(lane1, "add", "src/api/handlers.py")
    _git(lane1, "commit", "-m", "finish lane-01")
    _write_observe_result(project, "lane-01", "success", "API lane passed tests.")
    _save_land_chain(project)

    branch = json.loads((project / "launch.json").read_text(encoding="utf-8"))["actions"][0]["branch_name"]
    _git(project, "merge", "--no-ff", "--no-edit", branch)

    plan = MergeEngine().build(project)

    assert plan.already_landed_lane_ids == ["lane-01"]


def test_merge_engine_rejects_apply_when_not_on_target_branch(tmp_path):
    project = _make_repo(tmp_path)
    _write_launch(project, target="codex", single_lane=True)
    lane1 = project / "stage" / "worktrees" / "demo-repo-phase-01-lane-01"
    (lane1 / "src" / "api" / "handlers.py").write_text("def handler():\n    return 'done'\n", encoding="utf-8")
    _git(lane1, "add", "src/api/handlers.py")
    _git(lane1, "commit", "-m", "finish lane-01")
    _write_observe_result(project, "lane-01", "success", "API lane passed tests.")
    _save_land_chain(project)
    _git(project, "checkout", "-b", "scratch")

    with pytest.raises(MergeError, match="requires the project root to be on target branch"):
        MergeEngine().build(project, apply=True)
