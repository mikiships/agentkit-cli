from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentkit_cli.launch import LaunchEngine
from agentkit_cli.observe import ObserveEngine, ObserveError
from tests.test_launch_engine import _make_repo, _write_materialize


def _write_launch(project: Path, *, target: str = "codex", overlap: bool = False, single_lane: bool = False) -> None:
    _write_materialize(project, target=target, overlap=overlap, single_lane=single_lane)
    launch_dir = project / "launch"
    plan = LaunchEngine().build(project, target=target)
    LaunchEngine().write_directory(plan, launch_dir)
    (project / "launch.json").write_text((launch_dir / "launch.json").read_text(encoding="utf-8"), encoding="utf-8")


def _write_observe_result(project: Path, lane_id: str, status: str, summary: str, *, target: str = "codex") -> None:
    worktree = project / "stage" / "worktrees"
    lane_dirs = list(worktree.glob(f"*{lane_id}"))
    assert lane_dirs, f"missing worktree for {lane_id}"
    result_dir = lane_dirs[0] / ".agentkit" / "observe"
    result_dir.mkdir(parents=True, exist_ok=True)
    (result_dir / "result.json").write_text(
        json.dumps(
            {
                "schema_version": "agentkit.observe.lane-result.v1",
                "lane_id": lane_id,
                "target": target,
                "status": status,
                "summary": summary,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def test_observe_engine_classifies_success_failure_running_waiting_unknown(tmp_path):
    project = _make_repo(tmp_path)
    _write_launch(project, target="codex", overlap=True)
    _write_observe_result(project, "lane-01", "success", "Builder finished cleanly.")
    waiting_worktree = project / "stage" / "worktrees" / "demo-repo-phase-02-lane-02"
    waiting_worktree.mkdir(parents=True, exist_ok=True)

    launch = json.loads((project / "launch.json").read_text(encoding="utf-8"))
    launch["actions"].append(
        {
            **launch["actions"][0],
            "lane_id": "lane-03",
            "title": "worker-2",
            "worktree_name": "demo-repo-phase-01-lane-03",
            "worktree_path": str(project / "stage" / "worktrees" / "demo-repo-phase-01-lane-03"),
            "state": "launched",
            "state_reason": "Local launch command exited successfully.",
            "dependencies": [],
        }
    )
    launch["actions"].append(
        {
            **launch["actions"][0],
            "lane_id": "lane-04",
            "title": "worker-3",
            "worktree_name": "demo-repo-phase-01-lane-04",
            "worktree_path": str(project / "stage" / "worktrees" / "demo-repo-phase-01-lane-04"),
            "state": "ready",
            "state_reason": "Eligible for deterministic launch planning from the saved materialize artifacts.",
            "dependencies": [],
        }
    )
    (project / "stage" / "worktrees" / "demo-repo-phase-01-lane-03").mkdir(parents=True, exist_ok=True)
    (project / "stage" / "worktrees" / "demo-repo-phase-01-lane-04").mkdir(parents=True, exist_ok=True)
    (project / "launch.json").write_text(json.dumps(launch, indent=2, sort_keys=True), encoding="utf-8")

    plan = ObserveEngine().build(project, target="codex")

    assert plan.success_lane_ids == ["lane-01"]
    assert plan.waiting_lane_ids == ["lane-02"]
    assert plan.running_lane_ids == ["lane-03"]
    assert plan.unknown_lane_ids == ["lane-04"]
    assert plan.summary_counts["success"] == 1
    lane = next(item for item in plan.actions if item.lane_id == "lane-01")
    assert lane.status == "success"
    assert lane.packet_paths is not None
    assert lane.packet_paths.observe_result_path.endswith(".agentkit/observe/result.json")


def test_observe_engine_reports_failure_from_saved_result(tmp_path):
    project = _make_repo(tmp_path)
    _write_launch(project, target="codex", single_lane=True)
    _write_observe_result(project, "lane-01", "failure", "Pytest failed in the isolated worktree.")

    plan = ObserveEngine().build(project, target="codex")

    assert plan.failure_lane_ids == ["lane-01"]
    assert "Investigate failed lanes first" in plan.recommended_next_actions[0]


def test_observe_engine_rejects_malformed_result_json(tmp_path):
    project = _make_repo(tmp_path)
    _write_launch(project, target="codex", single_lane=True)
    worktree = project / "stage" / "worktrees" / "demo-repo-phase-01-lane-01" / ".agentkit" / "observe"
    worktree.mkdir(parents=True, exist_ok=True)
    (worktree / "result.json").write_text("{not-json", encoding="utf-8")

    with pytest.raises(ObserveError, match="malformed JSON"):
        ObserveEngine().build(project, target="codex")


def test_observe_engine_writes_packet_directory(tmp_path):
    project = _make_repo(tmp_path)
    _write_launch(project, target="generic", single_lane=True)

    plan = ObserveEngine().build(project, target="generic")
    output_dir = tmp_path / "observe"
    ObserveEngine().write_directory(plan, output_dir)

    assert (output_dir / "observe.md").exists()
    assert (output_dir / "observe.json").exists()
    assert (output_dir / "lanes" / "lane-01" / "observe.md").exists()
    payload = json.loads((output_dir / "lanes" / "lane-01" / "observe.json").read_text(encoding="utf-8"))
    assert payload["recommended_next_action"]
