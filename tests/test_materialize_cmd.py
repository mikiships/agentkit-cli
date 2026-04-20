from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.stage import StageEngine

runner = CliRunner()


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


def _write_stage(project: Path, *, target: str = "codex", overlap: bool = False, single_lane: bool = False) -> Path:
    _write_dispatch(project, target=target, overlap=overlap, single_lane=single_lane)
    stage_dir = project / "stage"
    manifest = StageEngine().build(project, target=target, output_dir=stage_dir)
    StageEngine().write_directory(manifest, stage_dir)
    return stage_dir


def _lane_packet(project: Path) -> dict[str, Any]:
    return json.loads((project / "stage" / "materialize.json").read_text(encoding="utf-8"))["actions"][0]


def test_materialize_command_creates_ready_worktrees_and_seeds_handoff(tmp_path):
    project = _make_repo(tmp_path)
    _write_stage(project, target="codex")
    output_dir = tmp_path / "materialize-report"

    result = runner.invoke(app, ["materialize", str(project), "--target", "codex", "--output-dir", str(output_dir)])

    assert result.exit_code == 0, result.output
    assert (output_dir / "materialize.md").exists()
    assert (output_dir / "materialize.json").exists()
    lane_path = project / "stage" / "worktrees" / "demo-repo-phase-01-lane-01"
    handoff_dir = lane_path / ".agentkit" / "materialize"
    assert lane_path.exists()
    assert (handoff_dir / "stage.json").exists()
    assert (handoff_dir / "stage.md").exists()
    assert (handoff_dir / "materialize.json").exists()
    assert "run Codex from the staged worktree path" in (handoff_dir / "handoff.md").read_text(encoding="utf-8")
    assert "Wrote materialize directory" in result.output
    assert "demo-repo-phase-01-lane-01" in _git(project, "worktree", "list", "--porcelain")


def test_materialize_handoff_preserves_target_specific_stage_notes(tmp_path):
    expected_handoff_notes = {
        "generic": "Create the suggested worktree or branch manually before handing this packet to a builder.",
        "claude-code": "run Claude Code from the staged worktree path",
    }

    for target, expected_note in expected_handoff_notes.items():
        project = _make_repo(tmp_path / target)
        _write_stage(project, target=target, single_lane=True)

        result = runner.invoke(app, ["materialize", str(project), "--target", target, "--output-dir", str(project / "stage")])

        assert result.exit_code == 0, result.output
        lane = _lane_packet(project)
        handoff_dir = Path(lane["packet_paths"]["handoff_dir"])
        handoff_text = (handoff_dir / "handoff.md").read_text(encoding="utf-8")
        assert expected_note in handoff_text


def test_materialize_keeps_serialized_lanes_waiting_until_dependencies_finish(tmp_path):
    project = _make_repo(tmp_path)
    _write_stage(project, target="codex", overlap=True)

    result = runner.invoke(app, ["materialize", str(project), "--target", "codex", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["materialized_lane_ids"] == ["lane-01"]
    assert payload["waiting_lane_ids"] == ["lane-02"]
    assert (project / "stage" / "worktrees" / "demo-repo-phase-01-lane-01").exists()
    assert not (project / "stage" / "worktrees" / "demo-repo-phase-02-lane-02").exists()
    assert any(action["state"] == "waiting" and action["lane_id"] == "lane-02" for action in payload["actions"])


def test_materialize_command_fails_cleanly_on_branch_collision(tmp_path):
    project = _make_repo(tmp_path)
    _write_stage(project, target="codex", single_lane=True)
    _git(project, "branch", "stage/phase-01/lane-01")
    before_worktrees = _git(project, "worktree", "list", "--porcelain")

    result = runner.invoke(app, ["materialize", str(project), "--target", "codex"])

    assert result.exit_code == 2
    assert "Branch already exists: stage/phase-01/lane-01" in result.output
    assert before_worktrees == _git(project, "worktree", "list", "--porcelain")


def test_materialize_help():
    result = runner.invoke(app, ["materialize", "--help"])
    assert result.exit_code == 0
    assert "--worktree-root" in result.output
    assert "--dry-run" in result.output
