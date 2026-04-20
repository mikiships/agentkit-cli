from __future__ import annotations

import json
import subprocess
from pathlib import Path

from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.launch import LaunchEngine
from agentkit_cli.materialize import MaterializeEngine
from agentkit_cli.stage import StageEngine
from tests.test_materialize_workflow import _write_repo

runner = CliRunner()


def test_source_to_resolve_to_dispatch_to_stage_to_materialize_to_launch_to_supervise_workflow(tmp_path):
    project = tmp_path / "demo-repo"
    _write_repo(project)

    contract = runner.invoke(app, ["contract", "Ship the supervise lane", "--path", str(project), "--map", str(project)])
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

    launch_dir = tmp_path / "launch"
    launch_plan = LaunchEngine().build(project, target="codex")
    LaunchEngine().write_directory(launch_plan, launch_dir)
    (project / "launch.json").write_text((launch_dir / "launch.json").read_text(encoding="utf-8"), encoding="utf-8")

    lane1 = project / "stage" / "worktrees" / f"{project.name}-phase-01-lane-01"
    (lane1 / "src" / "api" / "handlers.py").write_text("def handler():\n    return 'done'\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(lane1), "add", "src/api/handlers.py"], check=True)
    subprocess.run(["git", "-C", str(lane1), "commit", "-m", "finish lane-01"], check=True)

    supervise_dir = tmp_path / "supervise"
    result = runner.invoke(app, ["supervise", str(project), "--output-dir", str(supervise_dir), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads("\n".join(result.output.splitlines()[1:]))
    assert payload["schema_version"] == "agentkit.supervise.v1"
    assert payload["completed_lane_ids"] == ["lane-01"]
    assert payload["lanes"][0]["state"] == "completed"
    assert (supervise_dir / "supervise.md").exists()
    assert (supervise_dir / "lanes" / "lane-01" / "supervise.json").exists()
