from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agentkit_cli.launch import LaunchEngine
from agentkit_cli.materialize import MaterializeEngine
from agentkit_cli.main import app
from agentkit_cli.stage import StageEngine
from tests.test_materialize_workflow import _write_repo

runner = CliRunner()


def _save_observe_result(worktree: Path, lane_id: str, target: str, status: str, summary: str) -> None:
    result_dir = worktree / ".agentkit" / "observe"
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


def test_source_to_resolve_to_dispatch_to_stage_to_materialize_to_launch_to_observe_workflow(tmp_path):
    project = tmp_path / "demo-repo"
    _write_repo(project)

    contract = runner.invoke(app, ["contract", "Ship the observe lane", "--path", str(project), "--map", str(project)])
    assert contract.exit_code == 0, contract.output

    answers = tmp_path / "answers.json"
    answers.write_text(
        json.dumps(
            {
                "answers": [{"code": "execution_checklist_review", "status": "resolved", "answer": "The mapped checks are enough for codex."}],
                "assumptions": {
                    "primary_language": {"status": "confirmed", "reason": "Python remains the implementation surface."},
                    "runner_notes": {"status": "confirmed", "reason": "Codex notes are sufficient for this handoff."},
                },
            }
        ),
        encoding="utf-8",
    )

    resolve_dir = tmp_path / "resolve"
    resolve = runner.invoke(app, ["resolve", str(project), "--answers", str(answers), "--target", "codex", "--output-dir", str(resolve_dir)])
    assert resolve.exit_code == 0, resolve.output
    (project / "resolve.json").write_text((resolve_dir / "resolve.json").read_text(encoding="utf-8"), encoding="utf-8")

    dispatch_dir = tmp_path / "dispatch"
    dispatch = runner.invoke(app, ["dispatch", str(project), "--target", "codex", "--output-dir", str(dispatch_dir)])
    assert dispatch.exit_code == 0, dispatch.output
    (project / "dispatch.json").write_text((dispatch_dir / "dispatch.json").read_text(encoding="utf-8"), encoding="utf-8")

    stage_dir = project / "stage"
    stage_plan = StageEngine().build(project, target="codex", output_dir=stage_dir)
    StageEngine().write_directory(stage_plan, stage_dir)

    materialize_dir = project / "materialize"
    materialize_plan = MaterializeEngine().materialize(project, target="codex", dry_run=False)
    MaterializeEngine().write_directory(materialize_plan, materialize_dir)

    launch_dir = project / "launch"
    launch_plan = LaunchEngine().build(project, target="codex")
    LaunchEngine().write_directory(launch_plan, launch_dir)
    (project / "launch.json").write_text((launch_dir / "launch.json").read_text(encoding="utf-8"), encoding="utf-8")

    _save_observe_result(project / "stage" / "worktrees" / "demo-repo-phase-01-lane-01", "lane-01", "codex", "success", "API lane passed tests.")
    _save_observe_result(project / "stage" / "worktrees" / "demo-repo-phase-01-lane-02", "lane-02", "codex", "failure", "Worker lane hit a failing test.")

    observe_dir = tmp_path / "observe"
    observe = runner.invoke(app, ["observe", str(project), "--target", "codex", "--output-dir", str(observe_dir), "--json"])
    assert observe.exit_code == 0, observe.output
    payload = json.loads("\n".join(observe.output.splitlines()[1:]))
    assert payload["schema_version"] == "agentkit.observe.v1"
    assert payload["success_lane_ids"] == ["lane-01"]
    assert payload["failure_lane_ids"] == ["lane-02"]
    assert payload["running_lane_ids"] == []
    assert (observe_dir / "observe.md").exists()
    assert (observe_dir / "lanes" / "lane-01" / "observe.md").exists()


def test_observe_workflow_keeps_manual_target_unknown_without_result_packet(tmp_path):
    project = tmp_path / "demo-repo"
    _write_repo(project)
    worktree = project / "stage" / "worktrees" / "demo-repo-phase-01-lane-01"
    handoff_dir = worktree / ".agentkit" / "materialize"
    handoff_dir.mkdir(parents=True, exist_ok=True)
    (handoff_dir / "handoff.md").write_text("# prompt\n", encoding="utf-8")
    (handoff_dir / "materialize.json").write_text(json.dumps({"schema_version": "agentkit.materialize.lane.v1", "target": "generic", "lane": {"lane_id": "lane-01", "worktree_path": str(worktree)}}), encoding="utf-8")
    (handoff_dir / "stage.json").write_text("{}", encoding="utf-8")
    (handoff_dir / "stage.md").write_text("# stage\n", encoding="utf-8")
    (project / "launch.json").write_text(
        json.dumps(
            {
                "schema_version": "agentkit.launch.v1",
                "project_path": str(project),
                "target": "generic",
                "actions": [
                    {
                        "lane_id": "lane-01",
                        "title": "manual",
                        "phase_id": "phase-01",
                        "phase_index": 1,
                        "serialization_group": "phase-01",
                        "branch_name": "stage/phase-01/lane-01",
                        "worktree_name": "demo-repo-phase-01-lane-01",
                        "worktree_path": str(worktree),
                        "owned_paths": ["."],
                        "dependencies": [],
                        "packet_paths": {
                            "handoff_markdown_path": str(handoff_dir / "handoff.md"),
                            "materialize_metadata_path": str(handoff_dir / "materialize.json"),
                            "stage_json_path": str(handoff_dir / "stage.json"),
                            "stage_markdown_path": str(handoff_dir / "stage.md"),
                        },
                        "state": "ready",
                        "state_reason": "manual launch",
                        "execution_mode": "manual",
                        "runner": "manual handoff packet",
                        "display_command": "cat .agentkit/materialize/handoff.md",
                    }
                ],
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["observe", str(project), "--target", "generic", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["unknown_lane_ids"] == ["lane-01"]
