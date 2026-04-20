from __future__ import annotations

import json
import subprocess
from pathlib import Path

from typer.testing import CliRunner

from agentkit_cli.main import app

runner = CliRunner()


def _git(project: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(project), *args],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr.strip() or result.stdout.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def _write_repo(project: Path) -> None:
    (project / ".agentkit").mkdir(parents=True)
    (project / "src" / "api").mkdir(parents=True)
    (project / "src" / "worker").mkdir(parents=True)
    (project / "tests").mkdir()
    (project / ".agentkit" / "source.md").write_text(
        "# Demo Repo\n\n"
        "## Objective\nShip the materialize lane.\n\n"
        "## Scope & Boundaries\nWork only inside this repo.\n\n"
        "## Rules\n- Keep output deterministic.\n\n"
        "## Validation\nRun pytest.\n\n"
        "## Deliverables\nLeave markdown and JSON handoff output.\n",
        encoding="utf-8",
    )
    (project / "pyproject.toml").write_text(
        "[project]\nname='demo-repo'\nversion='0.1.0'\n\n[project.scripts]\ndemo='src.main:main'\n",
        encoding="utf-8",
    )
    (project / "src" / "main.py").write_text("def main():\n    return 'ok'\n", encoding="utf-8")
    (project / "src" / "api" / "handlers.py").write_text("def handler():\n    return 'api'\n", encoding="utf-8")
    (project / "src" / "worker" / "jobs.py").write_text("def run_job():\n    return 'worker'\n", encoding="utf-8")
    (project / "tests" / "test_api.py").write_text("def test_api():\n    assert True\n", encoding="utf-8")
    (project / "tests" / "test_worker.py").write_text("def test_worker():\n    assert True\n", encoding="utf-8")
    _git(project, "init")
    _git(project, "config", "user.email", "test@example.com")
    _git(project, "config", "user.name", "Test User")
    _git(project, "add", ".")
    _git(project, "commit", "-m", "init")


def test_source_to_resolve_to_dispatch_to_stage_to_materialize_workflow(tmp_path):
    project = tmp_path / "demo-repo"
    _write_repo(project)

    contract = runner.invoke(app, ["contract", "Ship the materialize lane", "--path", str(project), "--map", str(project)])
    assert contract.exit_code == 0, contract.output

    answers = tmp_path / "answers.json"
    answers.write_text(
        json.dumps(
            {
                "answers": [
                    {"code": "execution_checklist_review", "status": "resolved", "answer": "The mapped checks are enough for codex."}
                ],
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

    materialize = runner.invoke(app, ["materialize", str(project), "--target", "codex", "--json"])
    assert materialize.exit_code == 0, materialize.output
    payload = json.loads(materialize.output)
    assert payload["schema_version"] == "agentkit.materialize.v1"
    assert payload["target"] == "codex"
    assert payload["materialized_lane_ids"]
    assert payload["waiting_lane_ids"] == []
    lane = payload["actions"][0]
    assert lane["state"] == "materialized"
    assert lane["packet_paths"]["source_json_path"].endswith("lanes/lane-01/stage.json")
    worktree_path = Path(lane["worktree_path"])
    assert worktree_path.exists()
    assert (worktree_path / ".agentkit" / "materialize" / "stage.md").exists()
    assert "run Codex from the staged worktree path" in (worktree_path / ".agentkit" / "materialize" / "handoff.md").read_text(encoding="utf-8")


def test_materialize_dry_run_does_not_mutate_git_state_in_workflow(tmp_path):
    project = tmp_path / "demo-repo"
    _write_repo(project)
    (project / "stage").mkdir()
    (project / "stage" / "stage.json").write_text(
        json.dumps(
            {
                "schema_version": "agentkit.stage.v1",
                "project_path": str(project),
                "target": "generic",
                "dispatch_path": str(project / "dispatch.json"),
                "output_root": str(project / "stage"),
                "phases": [{"phase_id": "phase-01", "index": 1, "execution_mode": "parallel", "lane_ids": ["lane-01"], "serialization_groups": ["phase-01-lane-01"], "notes": []}],
                "lanes": [
                    {
                        "lane_id": "lane-01",
                        "title": "repo-wide fallback lane",
                        "phase_id": "phase-01",
                        "phase_index": 1,
                        "serialization_group": "phase-01-lane-01",
                        "branch_name": "stage/phase-01/lane-01",
                        "worktree_name": "demo-repo-phase-01-lane-01",
                        "worktree_path": str(project / "stage" / "worktrees" / "demo-repo-phase-01-lane-01"),
                        "owned_paths": ["."],
                        "dependencies": [],
                        "packet_reference": {"json_path": "lanes/lane-01.json", "markdown_path": "lanes/lane-01.md"},
                        "phase_notes": [],
                        "stage_notes": ["Create the suggested worktree or branch manually before handing this packet to a builder."],
                    }
                ],
                "instructions": ["demo"],
                "source_dispatch": {},
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    lane_dir = project / "stage" / "lanes" / "lane-01"
    lane_dir.mkdir(parents=True)
    (lane_dir / "stage.json").write_text("{}", encoding="utf-8")
    (lane_dir / "stage.md").write_text("# lane-01\n", encoding="utf-8")

    before = _git(project, "worktree", "list", "--porcelain")
    result = runner.invoke(app, ["materialize", str(project), "--dry-run", "--json"])
    after = _git(project, "worktree", "list", "--porcelain")

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["dry_run"] is True
    assert payload["eligible_lane_ids"] == ["lane-01"]
    assert payload["materialized_lane_ids"] == []
    assert before == after
    assert not (project / "stage" / "worktrees" / "demo-repo-phase-01-lane-01").exists()
