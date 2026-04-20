from __future__ import annotations

import json
import subprocess
from pathlib import Path

from agentkit_cli.launch import LaunchEngine
from agentkit_cli.materialize import MaterializeEngine
from agentkit_cli.observe import ObserveEngine
from agentkit_cli.reconcile import ReconcileEngine
from agentkit_cli.stage import StageEngine
from agentkit_cli.supervise import SuperviseEngine
from tests.test_launch_engine import _make_repo, _write_dispatch


def _git(project: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(["git", "-C", str(project), *args], capture_output=True, text=True)
    if check and result.returncode != 0:
        raise AssertionError(result.stderr.strip() or result.stdout.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def _write_launch(project: Path, *, target: str = "codex", overlap: bool = False, single_lane: bool = False) -> Path:
    _write_dispatch(project, target=target, overlap=overlap, single_lane=single_lane)
    stage_dir = project / "stage"
    stage_manifest = StageEngine().build(project, target=target, output_dir=stage_dir)
    StageEngine().write_directory(stage_manifest, stage_dir)
    plan = MaterializeEngine().materialize(project, target=target, dry_run=False)
    MaterializeEngine().write_directory(plan, project / "materialize")
    launch_plan = LaunchEngine().build(project, target=target)
    output_dir = project / "launch"
    LaunchEngine().write_directory(launch_plan, output_dir)
    (project / "launch.json").write_text((output_dir / "launch.json").read_text(encoding="utf-8"), encoding="utf-8")
    return output_dir


def _write_observe_result(project: Path, lane_id: str, status: str, summary: str) -> None:
    matches = sorted((project / "stage" / "worktrees").glob(f"{project.name}-phase-*-{lane_id}"))
    if not matches:
        raise AssertionError(f"worktree for {lane_id} not found")
    worktree = matches[0]
    result_dir = worktree / ".agentkit" / "observe"
    result_dir.mkdir(parents=True, exist_ok=True)
    (result_dir / "result.json").write_text(
        json.dumps(
            {
                "schema_version": "agentkit.observe.lane-result.v1",
                "lane_id": lane_id,
                "target": "codex",
                "status": status,
                "summary": summary,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def _save_observe_and_supervise(project: Path) -> None:
    observe_plan = ObserveEngine().build(project, target="codex")
    ObserveEngine().write_directory(observe_plan, project / "observe")
    supervise_plan = SuperviseEngine().build(project)
    SuperviseEngine().write_directory(supervise_plan, project / "supervise")


def test_reconcile_engine_classifies_complete_and_newly_unblocked_next_order(tmp_path):
    project = _make_repo(tmp_path)
    _write_launch(project, target="codex", overlap=True)

    lane1 = project / "stage" / "worktrees" / "demo-repo-phase-01-lane-01"
    (lane1 / "src" / "api" / "handlers.py").write_text("def handler():\n    return 'done'\n", encoding="utf-8")
    _git(lane1, "add", "src/api/handlers.py")
    _git(lane1, "commit", "-m", "finish lane-01")
    _write_observe_result(project, "lane-01", "success", "API lane passed tests.")
    _save_observe_and_supervise(project)

    plan = ReconcileEngine().build(project)

    assert plan.complete_lane_ids == ["lane-01"]
    assert plan.ready_lane_ids == ["lane-02"]
    assert plan.newly_unblocked_lane_ids == ["lane-02"]
    assert plan.next_execution_order == ["lane-02"]


def test_reconcile_engine_marks_failed_lane_relaunch_ready(tmp_path):
    project = _make_repo(tmp_path)
    _write_launch(project, target="codex", single_lane=True)
    _write_observe_result(project, "lane-01", "failure", "Lane failed tests.")
    _save_observe_and_supervise(project)

    plan = ReconcileEngine().build(project)

    assert plan.relaunch_ready_lane_ids == ["lane-01"]
    assert plan.next_execution_order == ["lane-01"]


def test_reconcile_engine_marks_dirty_lane_for_human_review_not_auto_advance(tmp_path):
    project = _make_repo(tmp_path)
    _write_launch(project, target="codex", single_lane=True)
    _write_observe_result(project, "lane-01", "failure", "Lane failed tests.")

    lane1 = project / "stage" / "worktrees" / "demo-repo-phase-01-lane-01"
    (lane1 / "src" / "api" / "handlers.py").write_text("def handler():\n    return 'dirty'\n", encoding="utf-8")
    _save_observe_and_supervise(project)

    plan = ReconcileEngine().build(project)

    assert plan.needs_human_review_lane_ids == ["lane-01"]
    assert plan.next_execution_order == []


def test_reconcile_engine_degrades_cleanly_when_saved_observe_missing(tmp_path):
    project = _make_repo(tmp_path)
    _write_launch(project, target="codex", overlap=True)

    lane1 = project / "stage" / "worktrees" / "demo-repo-phase-01-lane-01"
    (lane1 / "src" / "api" / "handlers.py").write_text("def handler():\n    return 'done'\n", encoding="utf-8")
    _git(lane1, "add", "src/api/handlers.py")
    _git(lane1, "commit", "-m", "finish lane-01")
    supervise_plan = SuperviseEngine().build(project)
    SuperviseEngine().write_directory(supervise_plan, project / "supervise")

    plan = ReconcileEngine().build(project)

    assert plan.complete_lane_ids == ["lane-01"]
    assert plan.ready_lane_ids == ["lane-02"]
    assert plan.observe_path is None


def test_reconcile_engine_marks_drifted_lane(tmp_path):
    project = _make_repo(tmp_path)
    _write_launch(project, target="codex", single_lane=True)

    lane1 = project / "stage" / "worktrees" / "demo-repo-phase-01-lane-01"
    head = _git(lane1, "rev-parse", "HEAD")
    _git(lane1, "checkout", "--detach", head)
    _save_observe_and_supervise(project)

    plan = ReconcileEngine().build(project)

    assert plan.drifted_lane_ids == ["lane-01"]
    assert plan.next_execution_order == []


def test_reconcile_engine_marks_launched_without_completion_evidence_for_review(tmp_path):
    project = _make_repo(tmp_path)
    _write_launch(project, target="codex", single_lane=True)

    launch_path = project / "launch.json"
    payload = json.loads(launch_path.read_text(encoding="utf-8"))
    payload["actions"][0]["state"] = "launched"
    payload["actions"][0]["state_reason"] = "Local launch command exited successfully."
    launch_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    plan = ReconcileEngine().build(project)

    assert plan.needs_human_review_lane_ids == ["lane-01"]
    assert plan.next_execution_order == []
