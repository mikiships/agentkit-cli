from __future__ import annotations

import json
import subprocess
from pathlib import Path

from agentkit_cli.materialize import MaterializeEngine
from agentkit_cli.stage import StageEngine


def _git(project: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", "-C", str(project), *args],
        capture_output=True,
        text=True,
    )
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


def _write_dispatch(project: Path, *, target: str = "codex", single_lane: bool = False) -> None:
    lanes = [
        {
            "lane_id": "lane-01",
            "title": "api",
            "phase_id": "phase-01",
            "phase_index": 1,
            "ownership_mode": "exclusive",
            "owned_paths": ["src/api", "tests/test_api.py"],
            "subsystem_hints": [],
            "dependencies": [],
            "packet": {
                "objective": "api",
                "runner": "codex exec --full-auto" if target == "codex" else "generic coding agent",
                "execution_notes": [],
                "stop_conditions": [],
            },
        }
    ]
    phase = {"phase_id": "phase-01", "index": 1, "execution_mode": "parallel", "lane_ids": ["lane-01"], "rationale": "demo"}
    if not single_lane:
        lanes.append(
            {
                "lane_id": "lane-02",
                "title": "worker",
                "phase_id": "phase-01",
                "phase_index": 1,
                "ownership_mode": "exclusive",
                "owned_paths": ["src/worker", "tests/test_worker.py"],
                "subsystem_hints": [],
                "dependencies": [],
                "packet": {
                    "objective": "worker",
                    "runner": "codex exec --full-auto" if target == "codex" else "generic coding agent",
                    "execution_notes": [],
                    "stop_conditions": [],
                },
            }
        )
        phase["lane_ids"] = ["lane-01", "lane-02"]
    payload = {
        "schema_version": "agentkit.dispatch.v1",
        "project_path": str(project),
        "target": target,
        "execution_recommendation": "proceed",
        "recommendation_reason": "Ready.",
        "worktree_guidance": ["Use separate worktrees or isolated branches per lane when phases contain more than one lane."],
        "phases": [phase],
        "lanes": lanes,
        "ownership_conflicts": [],
        "source_resolve": {},
        "source_taskpack": {},
        "source_bundle": {},
    }
    (project / "dispatch.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_stage(project: Path, *, target: str = "codex", single_lane: bool = False) -> Path:
    _write_dispatch(project, target=target, single_lane=single_lane)
    stage_dir = project / "stage"
    manifest = StageEngine().build(project, target=target, output_dir=stage_dir)
    StageEngine().write_directory(manifest, stage_dir)
    return stage_dir


def test_materialize_engine_builds_stable_dry_run_plan(tmp_path):
    project = _make_repo(tmp_path)
    _write_stage(project, target="codex")
    engine = MaterializeEngine()

    before_worktrees = _git(project, "worktree", "list", "--porcelain")
    plan_one = engine.build(project, target="codex", dry_run=True)
    plan_two = engine.build(project, target="codex", dry_run=True)
    after_worktrees = _git(project, "worktree", "list", "--porcelain")

    assert plan_one.to_json() == plan_two.to_json()
    assert before_worktrees == after_worktrees
    assert plan_one.schema_version == "agentkit.materialize.v1"
    assert plan_one.eligible_lane_ids == ["lane-01", "lane-02"]
    assert plan_one.actions[0].packet_paths is not None
    assert plan_one.actions[0].packet_paths.source_json_path.endswith("lanes/lane-01/stage.json")
    assert not Path(plan_one.actions[0].worktree_path).exists()


def test_materialize_honors_worktree_root_override_for_single_lane_plan(tmp_path):
    project = _make_repo(tmp_path)
    _write_stage(project, target="generic", single_lane=True)
    worktree_root = tmp_path / "custom-worktrees"

    plan = MaterializeEngine().build(project, target="generic", worktree_root=worktree_root, dry_run=True)

    assert plan.eligible_lane_ids == ["lane-01"]
    assert plan.actions[0].worktree_path == str(worktree_root / "demo-repo-phase-01-lane-01")
    assert plan.actions[0].packet_paths is not None
    assert plan.actions[0].packet_paths.handoff_dir == str(worktree_root / "demo-repo-phase-01-lane-01" / ".agentkit" / "materialize")
