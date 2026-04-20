from __future__ import annotations

import json
import subprocess
from pathlib import Path

from agentkit_cli.launch import LaunchEngine
from agentkit_cli.materialize import MaterializeEngine
from agentkit_cli.stage import StageEngine
from agentkit_cli.supervise import SuperviseEngine


def _git(project: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(["git", "-C", str(project), *args], capture_output=True, text=True)
    if check and result.returncode != 0:
        raise AssertionError(result.stderr.strip() or result.stdout.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def _make_repo(tmp_path: Path) -> Path:
    project = tmp_path / "demo-repo"
    (project / ".agentkit").mkdir(parents=True)
    (project / "src" / "api").mkdir(parents=True)
    (project / "src" / "worker").mkdir(parents=True)
    (project / "tests").mkdir()
    (project / ".agentkit" / "source.md").write_text("# Demo Repo\n", encoding="utf-8")
    (project / "src" / "api" / "handlers.py").write_text("def handler():\n    return 'api'\n", encoding="utf-8")
    (project / "src" / "worker" / "jobs.py").write_text("def run_job():\n    return 'worker'\n", encoding="utf-8")
    (project / "tests" / "test_api.py").write_text("def test_api():\n    assert True\n", encoding="utf-8")
    (project / "tests" / "test_worker.py").write_text("def test_worker():\n    assert True\n", encoding="utf-8")
    _git(project, "init")
    _git(project, "config", "user.email", "test@example.com")
    _git(project, "config", "user.name", "Test User")
    _git(project, "add", ".")
    _git(project, "commit", "-m", "init")
    return project


def _write_dispatch(project: Path, *, target: str = "codex", overlap: bool = False, single_lane: bool = False) -> None:
    from tests.test_launch_engine import _write_dispatch as base_write_dispatch

    base_write_dispatch(project, target=target, overlap=overlap, single_lane=single_lane)


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
    return output_dir


def test_supervise_engine_classifies_ready_running_completed_waiting(tmp_path):
    project = _make_repo(tmp_path)
    _write_launch(project, target="codex", overlap=True)

    lane1 = project / "stage" / "worktrees" / "demo-repo-phase-01-lane-01"
    (lane1 / "src" / "api" / "handlers.py").write_text("def handler():\n    return 'api v2'\n", encoding="utf-8")
    _git(lane1, "add", "src/api/handlers.py")
    _git(lane1, "commit", "-m", "finish lane-01")

    plan = SuperviseEngine().build(project)

    assert plan.schema_version == "agentkit.supervise.v1"
    assert plan.completed_lane_ids == ["lane-01"]
    assert plan.ready_lane_ids == ["lane-02"]
    assert plan.newly_unblocked_lane_ids == ["lane-02"]
    lane2 = next(item for item in plan.lanes if item.lane_id == "lane-02")
    assert lane2.state == "ready"
    assert lane2.newly_unblocked is True
    assert lane2.dependency_status[0].satisfied is True


def test_supervise_engine_detects_running_dirty_worktree(tmp_path):
    project = _make_repo(tmp_path)
    _write_launch(project, target="generic", single_lane=True)

    lane1 = project / "stage" / "worktrees" / "demo-repo-phase-01-lane-01"
    (lane1 / "src" / "api" / "handlers.py").write_text("def handler():\n    return 'dirty'\n", encoding="utf-8")

    plan = SuperviseEngine().build(project)

    assert plan.running_lane_ids == ["lane-01"]
    lane = plan.lanes[0]
    assert lane.state == "running"
    assert lane.git_summary is not None
    assert lane.git_summary.dirty is True


def test_supervise_engine_blocks_missing_worktree_and_packet(tmp_path):
    project = _make_repo(tmp_path)
    launch_dir = _write_launch(project, target="generic", single_lane=True)

    lane_packet = launch_dir / "lanes" / "lane-01" / "launch.json"
    lane_packet.unlink()
    worktree = project / "stage" / "worktrees" / "demo-repo-phase-01-lane-01"
    subprocess.run(["rm", "-rf", str(worktree)], check=True)

    plan = SuperviseEngine().build(project)

    assert plan.blocked_lane_ids == ["lane-01"]
    assert "launch lane packet is missing" in plan.lanes[0].reason


def test_supervise_engine_marks_detached_head_as_drifted(tmp_path):
    project = _make_repo(tmp_path)
    _write_launch(project, target="codex", single_lane=True)

    lane1 = project / "stage" / "worktrees" / "demo-repo-phase-01-lane-01"
    head = _git(lane1, "rev-parse", "HEAD")
    _git(lane1, "checkout", "--detach", head)

    plan = SuperviseEngine().build(project)

    assert plan.drifted_lane_ids == ["lane-01"]
    assert plan.lanes[0].state == "drifted"


def test_supervise_engine_writes_artifacts(tmp_path):
    project = _make_repo(tmp_path)
    _write_launch(project, target="codex", overlap=True)

    plan = SuperviseEngine().build(project)
    output_dir = tmp_path / "supervise"
    SuperviseEngine().write_directory(plan, output_dir)

    assert (output_dir / "supervise.md").exists()
    assert (output_dir / "supervise.json").exists()
    assert (output_dir / "lanes" / "lane-01" / "supervise.json").exists()
    payload = json.loads((output_dir / "supervise.json").read_text(encoding="utf-8"))
    assert payload["schema_version"] == "agentkit.supervise.v1"
