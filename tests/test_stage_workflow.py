from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agentkit_cli.main import app

runner = CliRunner()


def _write_repo(project: Path) -> None:
    (project / ".agentkit").mkdir(parents=True)
    (project / "src" / "api").mkdir(parents=True)
    (project / "src" / "worker").mkdir(parents=True)
    (project / "tests").mkdir()
    (project / ".agentkit" / "source.md").write_text(
        "# Demo Repo\n\n"
        "## Objective\nShip the stage lane.\n\n"
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


def test_source_to_resolve_to_dispatch_to_stage_workflow(tmp_path):
    project = tmp_path / "demo-repo"
    _write_repo(project)

    contract = runner.invoke(app, ["contract", "Ship the stage lane", "--path", str(project), "--map", str(project)])
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
                    "runner_notes": {"status": "confirmed", "reason": "Codex notes are sufficient for this handoff."}
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

    stage_dir = tmp_path / "stage"
    stage = runner.invoke(app, ["stage", str(project), "--target", "codex", "--output-dir", str(stage_dir), "--json"])
    assert stage.exit_code == 0, stage.output
    payload = json.loads("\n".join(stage.output.splitlines()[1:]))
    assert payload["schema_version"] == "agentkit.stage.v1"
    assert payload["target"] == "codex"
    assert payload["lanes"]
    assert payload["phases"]
    assert payload["lanes"][0]["branch_name"].startswith("stage/")
    assert payload["lanes"][0]["worktree_path"].endswith(payload["lanes"][0]["worktree_name"])


def test_stage_json_output_is_schema_stable(tmp_path):
    project = tmp_path / "stable-repo"
    _write_repo(project)
    (project / "dispatch.json").write_text(
        json.dumps(
            {
                "schema_version": "agentkit.dispatch.v1",
                "project_path": str(project),
                "target": "generic",
                "execution_recommendation": "proceed",
                "recommendation_reason": "Ready.",
                "worktree_guidance": ["Single-lane plan, so no fake parallelism is claimed."],
                "phases": [{"phase_id": "phase-01", "index": 1, "execution_mode": "parallel", "lane_ids": ["lane-01"], "rationale": "single"}],
                "lanes": [{"lane_id": "lane-01", "title": "repo-wide fallback lane", "phase_id": "phase-01", "phase_index": 1, "ownership_mode": "exclusive", "owned_paths": ["."], "subsystem_hints": [], "dependencies": [], "packet": {"objective": "fallback", "runner": "generic coding agent", "execution_notes": [], "stop_conditions": []}}],
                "ownership_conflicts": [],
                "source_resolve": {},
                "source_taskpack": {},
                "source_bundle": {},
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["stage", str(project), "--target", "generic", "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert list(payload.keys()) == [
        "dispatch_path",
        "instructions",
        "lanes",
        "output_root",
        "phases",
        "project_path",
        "schema_version",
        "source_dispatch",
        "target",
    ]
    assert list(payload["lanes"][0].keys()) == [
        "branch_name",
        "dependencies",
        "lane_id",
        "owned_paths",
        "packet_reference",
        "phase_id",
        "phase_index",
        "phase_notes",
        "serialization_group",
        "stage_notes",
        "title",
        "worktree_name",
        "worktree_path",
    ]
    assert list(payload["lanes"][0]["packet_reference"].keys()) == ["json_path", "markdown_path"]
