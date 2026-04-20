from __future__ import annotations

import json
import os
from pathlib import Path

from typer.testing import CliRunner

from agentkit_cli.main import app
from tests.test_materialize_workflow import _write_repo

runner = CliRunner()


def test_source_to_resolve_to_dispatch_to_stage_to_materialize_to_launch_workflow(tmp_path):
    project = tmp_path / "demo-repo"
    _write_repo(project)

    contract = runner.invoke(app, ["contract", "Ship the launch lane", "--path", str(project), "--map", str(project)])
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
    stage = runner.invoke(app, ["stage", str(project), "--target", "codex", "--output-dir", str(stage_dir)])
    assert stage.exit_code == 0, stage.output

    materialize = runner.invoke(app, ["materialize", str(project), "--target", "codex", "--output-dir", str(project / "materialize")])
    assert materialize.exit_code == 0, materialize.output

    launch_dir = tmp_path / "launch"
    launch = runner.invoke(app, ["launch", str(project), "--target", "codex", "--output-dir", str(launch_dir), "--json"])
    assert launch.exit_code == 0, launch.output
    payload_text = launch.output.split("\n", 1)[1] if launch.output.startswith("Wrote launch directory:") else launch.output
    payload = json.loads(payload_text)
    assert payload["schema_version"] == "agentkit.launch.v1"
    assert payload["target"] == "codex"
    assert payload["launchable_lane_ids"] == ["lane-01", "lane-02"]
    lane = payload["actions"][0]
    assert lane["state"] == "ready"
    assert lane["packet_paths"]["handoff_markdown_path"].endswith(".agentkit/materialize/handoff.md")
    assert (launch_dir / "lanes" / "lane-01" / "launch.sh").exists()


def test_launch_execute_requires_installed_tool(tmp_path, monkeypatch):
    project = tmp_path / "demo-repo"
    _write_repo(project)
    worktree = project / "stage" / "worktrees" / "demo-repo-phase-01-lane-01"
    handoff_dir = worktree / ".agentkit" / "materialize"
    handoff_dir.mkdir(parents=True)
    (handoff_dir / "handoff.md").write_text("# prompt\n", encoding="utf-8")
    lane_payload = {
        "schema_version": "agentkit.materialize.lane.v1",
        "target": "codex",
        "lane": {"lane_id": "lane-01", "worktree_path": str(worktree)},
    }
    (handoff_dir / "materialize.json").write_text(json.dumps(lane_payload), encoding="utf-8")
    (handoff_dir / "stage.json").write_text("{}", encoding="utf-8")
    (handoff_dir / "stage.md").write_text("# stage\n", encoding="utf-8")
    (project / "materialize.json").write_text(
        json.dumps(
            {
                "schema_version": "agentkit.materialize.v1",
                "project_path": str(project),
                "target": "codex",
                "actions": [
                    {
                        "lane_id": "lane-01",
                        "title": "api",
                        "phase_id": "phase-01",
                        "phase_index": 1,
                        "serialization_group": "phase-01",
                        "branch_name": "stage/phase-01/lane-01",
                        "worktree_name": "demo-repo-phase-01-lane-01",
                        "worktree_path": str(worktree),
                        "owned_paths": ["."],
                        "dependencies": [],
                        "phase_notes": [],
                        "stage_notes": [],
                        "materialize_notes": [],
                        "state": "materialized",
                        "state_reason": "ok",
                        "packet_paths": {
                            "handoff_dir": str(handoff_dir),
                            "handoff_markdown_path": str(handoff_dir / "handoff.md"),
                            "metadata_json_path": str(handoff_dir / "materialize.json"),
                            "copied_stage_json_path": str(handoff_dir / "stage.json"),
                            "copied_stage_markdown_path": str(handoff_dir / "stage.md"),
                        },
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv("PATH", os.defpath)
    result = runner.invoke(app, ["launch", str(project), "--target", "codex", "--execute"])

    assert result.exit_code == 2
    assert "Required tool not found on PATH: codex" in result.output
