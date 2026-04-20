from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from agentkit_cli.launch import LaunchEngine
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


def _write_dispatch(project: Path, *, target: str = "codex", overlap: bool = False, single_lane: bool = False) -> None:
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
    phases = [{"phase_id": "phase-01", "index": 1, "execution_mode": "parallel", "lane_ids": ["lane-01"], "rationale": "demo"}]

    if not single_lane:
        lanes.append(
            {
                "lane_id": "lane-02",
                "title": "worker",
                "phase_id": "phase-02" if overlap else "phase-01",
                "phase_index": 2 if overlap else 1,
                "ownership_mode": "serialized-overlap" if overlap else "exclusive",
                "owned_paths": ["src/api/sub" if overlap else "src/worker", "tests/test_worker.py"],
                "subsystem_hints": [],
                "dependencies": [{"lane_id": "lane-01", "reason": "overlapping ownership: src/api"}] if overlap else [],
                "packet": {
                    "objective": "worker",
                    "runner": "codex exec --full-auto" if target == "codex" else "generic coding agent",
                    "execution_notes": [],
                    "stop_conditions": [],
                },
            }
        )
        phases[0] = {
            "phase_id": "phase-01",
            "index": 1,
            "execution_mode": "parallel" if not overlap else "serial",
            "lane_ids": ["lane-01"] if overlap else ["lane-01", "lane-02"],
            "rationale": "demo",
        }
        if overlap:
            phases.append({"phase_id": "phase-02", "index": 2, "execution_mode": "serial", "lane_ids": ["lane-02"], "rationale": "overlap"})

    payload = {
        "schema_version": "agentkit.dispatch.v1",
        "project_path": str(project),
        "target": target,
        "execution_recommendation": "proceed",
        "recommendation_reason": "Ready.",
        "worktree_guidance": ["Use separate worktrees or isolated branches per lane when phases contain more than one lane."],
        "phases": phases,
        "lanes": lanes,
        "ownership_conflicts": [{"left_lane_id": "lane-01", "right_lane_id": "lane-02", "overlap": "src/api"}] if overlap else [],
        "source_resolve": {},
        "source_taskpack": {},
        "source_bundle": {},
    }
    (project / "dispatch.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_materialize(
    project: Path,
    *,
    target: str = "codex",
    overlap: bool = False,
    single_lane: bool = False,
    dry_run: bool = False,
) -> Path:
    _write_dispatch(project, target=target, overlap=overlap, single_lane=single_lane)
    stage_dir = project / "stage"
    stage_manifest = StageEngine().build(project, target=target, output_dir=stage_dir)
    StageEngine().write_directory(stage_manifest, stage_dir)
    engine = MaterializeEngine()
    if dry_run:
        plan = engine.build(project, target=target, dry_run=True)
    else:
        plan = engine.materialize(project, target=target, dry_run=False)
    output_dir = project / "materialize"
    engine.write_directory(plan, output_dir)
    return output_dir


@pytest.mark.parametrize(
    ("target", "expected_command", "expected_mode", "expected_tool", "expected_runner"),
    [
        ("generic", ["cat"], "manual", None, "manual handoff packet"),
        ("codex", ["codex", "exec", "--full-auto", "-"], "local-subprocess", "codex", "codex exec --full-auto"),
        (
            "claude-code",
            ["claude", "--print", "--permission-mode", "bypassPermissions"],
            "local-subprocess",
            "claude",
            "claude --print --permission-mode bypassPermissions",
        ),
    ],
)
def test_launch_engine_builds_target_aware_launch_commands(tmp_path, target, expected_command, expected_mode, expected_tool, expected_runner):
    project = _make_repo(tmp_path / target)
    _write_materialize(project, target=target, single_lane=True)

    plan = LaunchEngine().build(project, target=target)

    assert plan.schema_version == "agentkit.launch.v1"
    assert plan.target == target
    assert plan.launchable_lane_ids == ["lane-01"]
    assert plan.waiting_lane_ids == []
    assert plan.blocked_lane_ids == []
    action = plan.actions[0]
    assert action.state == "ready"
    assert action.execution_mode == expected_mode
    assert action.required_tool == expected_tool
    assert action.runner == expected_runner
    assert action.command[: len(expected_command)] == expected_command
    assert action.packet_paths is not None
    assert action.packet_paths.handoff_markdown_path.endswith(".agentkit/materialize/handoff.md")
    payload = json.loads(plan.to_json())
    assert payload["target"] == target


def test_launch_engine_preserves_waiting_lanes_from_materialize(tmp_path):
    project = _make_repo(tmp_path)
    _write_materialize(project, target="codex", overlap=True)

    plan = LaunchEngine().build(project, target="codex")

    assert plan.launchable_lane_ids == ["lane-01"]
    assert plan.waiting_lane_ids == ["lane-02"]
    assert plan.blocked_lane_ids == []
    waiting = next(item for item in plan.actions if item.lane_id == "lane-02")
    assert waiting.state == "waiting"
    assert "wait" in waiting.state_reason.lower()
    assert any("waiting" in note.lower() for note in waiting.launch_notes)


def test_launch_engine_blocks_dry_run_materialize_plans(tmp_path):
    project = _make_repo(tmp_path)
    _write_materialize(project, target="generic", single_lane=True, dry_run=True)

    plan = LaunchEngine().build(project, target="generic")

    assert plan.launchable_lane_ids == []
    assert plan.blocked_lane_ids == ["lane-01"]
    action = plan.actions[0]
    assert action.state == "blocked"
    assert "without --dry-run" in action.state_reason


def test_launch_engine_blocks_missing_lane_handoff_artifacts(tmp_path):
    project = _make_repo(tmp_path)
    _write_materialize(project, target="codex", single_lane=True)

    handoff_path = project / "stage" / "worktrees" / "demo-repo-phase-01-lane-01" / ".agentkit" / "materialize" / "handoff.md"
    handoff_path.unlink()

    plan = LaunchEngine().build(project, target="codex")

    assert plan.launchable_lane_ids == []
    assert plan.blocked_lane_ids == ["lane-01"]
    action = plan.actions[0]
    assert action.state == "blocked"
    assert "handoff markdown is missing" in action.state_reason
