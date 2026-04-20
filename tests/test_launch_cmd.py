from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.materialize import MaterializeEngine
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


def _write_materialize(project: Path, *, target: str = "codex", overlap: bool = False, single_lane: bool = False) -> Path:
    _write_dispatch(project, target=target, overlap=overlap, single_lane=single_lane)
    stage_dir = project / "stage"
    stage_manifest = StageEngine().build(project, target=target, output_dir=stage_dir)
    StageEngine().write_directory(stage_manifest, stage_dir)
    plan = MaterializeEngine().materialize(project, target=target, dry_run=False)
    output_dir = project / "materialize"
    MaterializeEngine().write_directory(plan, output_dir)
    return output_dir


def test_launch_command_writes_packet_directory(tmp_path):
    project = _make_repo(tmp_path)
    _write_materialize(project, target="codex", overlap=True)
    output_dir = tmp_path / "launch-report"

    result = runner.invoke(app, ["launch", str(project), "--target", "codex", "--output-dir", str(output_dir), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads("\n".join(result.output.splitlines()[1:]))
    assert payload["schema_version"] == "agentkit.launch.v1"
    assert payload["launchable_lane_ids"] == ["lane-01"]
    assert payload["waiting_lane_ids"] == ["lane-02"]
    assert (output_dir / "launch.md").exists()
    assert (output_dir / "launch.json").exists()
    assert (output_dir / "lanes" / "lane-01" / "launch.json").exists()
    assert (output_dir / "lanes" / "lane-01" / "launch.md").exists()
    assert (output_dir / "lanes" / "lane-01" / "launch.sh").exists()


def test_launch_command_executes_ready_lane_only_when_requested(tmp_path):
    project = _make_repo(tmp_path)
    _write_materialize(project, target="codex", single_lane=True)

    with patch("agentkit_cli.launch.shutil.which", return_value="/usr/bin/codex"), patch("agentkit_cli.launch.subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(args=["codex"], returncode=0, stdout="", stderr="")
        result = runner.invoke(app, ["launch", str(project), "--target", "codex", "--execute", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["launched_lane_ids"] == ["lane-01"]
    assert payload["actions"][0]["state"] == "launched"
    mock_run.assert_called_once()


def test_launch_command_fails_when_required_tool_is_missing(tmp_path):
    project = _make_repo(tmp_path)
    _write_materialize(project, target="claude-code", single_lane=True)

    with patch("agentkit_cli.launch.shutil.which", return_value=None):
        result = runner.invoke(app, ["launch", str(project), "--target", "claude-code", "--execute"])

    assert result.exit_code == 2
    assert "Required tool not found on PATH: claude" in result.output


def test_launch_command_rejects_execute_for_generic_target(tmp_path):
    project = _make_repo(tmp_path)
    _write_materialize(project, target="generic", single_lane=True)

    result = runner.invoke(app, ["launch", str(project), "--target", "generic", "--execute"])

    assert result.exit_code == 2
    assert "does not support explicit local execution" in result.output


def test_launch_help():
    result = runner.invoke(app, ["launch", "--help"])
    assert result.exit_code == 0
    assert "--execute" in result.output
    assert "--output-dir" in result.output
