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
        "## Objective\nShip the dispatch lane.\n\n"
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


def test_source_to_resolve_to_dispatch_workflow(tmp_path):
    project = tmp_path / "demo-repo"
    _write_repo(project)

    contract = runner.invoke(app, ["contract", "Ship the dispatch lane", "--path", str(project), "--map", str(project)])
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

    resolve_dir = tmp_path / "resolve-packet"
    resolve = runner.invoke(app, ["resolve", str(project), "--answers", str(answers), "--target", "codex", "--output-dir", str(resolve_dir)])
    assert resolve.exit_code == 0, resolve.output

    (project / "resolve.json").write_text((resolve_dir / "resolve.json").read_text(encoding="utf-8"), encoding="utf-8")
    dispatch = runner.invoke(app, ["dispatch", str(project), "--target", "codex", "--json"])
    assert dispatch.exit_code == 0, dispatch.output
    payload = json.loads(dispatch.output)
    assert payload["execution_recommendation"] == "proceed"
    assert payload["phases"]
    assert payload["lanes"]
    assert all(lane["packet"]["runner"] == "codex exec --full-auto" for lane in payload["lanes"])


def test_dispatch_falls_back_to_single_lane_without_saved_upstream_artifacts(tmp_path):
    project = tmp_path / "tiny-repo"
    (project / ".agentkit").mkdir(parents=True)
    (project / ".agentkit" / "source.md").write_text("# Tiny Repo\n\n## Rules\n- Keep output deterministic.\n", encoding="utf-8")
    (project / "resolve.json").write_text(
        json.dumps(
            {
                "schema_version": "agentkit.resolve.v1",
                "project_path": str(project),
                "answers_path": str(project / "answers.json"),
                "execution_recommendation": "proceed-with-assumptions",
                "recommendation_reason": "Fallback planning is acceptable.",
                "resolved_questions": [],
                "remaining_blockers": [],
                "remaining_follow_ups": [],
                "confirmed_assumptions": [],
                "superseded_assumptions": [],
                "unresolved_assumptions": [],
                "answers_summary": {"remaining_blockers": 0},
                "source_clarify": {},
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["dispatch", str(project), "--target", "claude-code", "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["execution_recommendation"] == "proceed-with-assumptions"
    assert len(payload["lanes"]) == 1
    assert payload["worktree_guidance"] == ["Single-lane plan, so no fake parallelism is claimed."]
    assert payload["lanes"][0]["packet"]["runner"] == "claude --print --permission-mode bypassPermissions"


def test_dispatch_json_output_is_schema_stable(tmp_path):
    project = tmp_path / "stable-repo"
    _write_repo(project)
    (project / "resolve.json").write_text(
        json.dumps(
            {
                "schema_version": "agentkit.resolve.v1",
                "project_path": str(project),
                "answers_path": str(project / "answers.json"),
                "execution_recommendation": "proceed",
                "recommendation_reason": "Ready.",
                "resolved_questions": [],
                "remaining_blockers": [],
                "remaining_follow_ups": [],
                "confirmed_assumptions": [],
                "superseded_assumptions": [],
                "unresolved_assumptions": [],
                "answers_summary": {"remaining_blockers": 0},
                "source_clarify": {},
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["dispatch", str(project), "--target", "generic", "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert list(payload.keys()) == [
        "execution_recommendation",
        "lanes",
        "ownership_conflicts",
        "phases",
        "project_path",
        "recommendation_reason",
        "schema_version",
        "source_bundle",
        "source_resolve",
        "source_taskpack",
        "target",
        "worktree_guidance",
    ]
    assert list(payload["lanes"][0].keys()) == [
        "dependencies",
        "lane_id",
        "owned_paths",
        "ownership_mode",
        "packet",
        "phase_id",
        "phase_index",
        "subsystem_hints",
        "title",
    ]
    assert list(payload["lanes"][0]["packet"].keys()) == [
        "execution_notes",
        "objective",
        "runner",
        "stop_conditions",
    ]


def test_dispatch_forces_pause_when_saved_resolve_has_blockers(tmp_path):
    project = tmp_path / "paused-repo"
    _write_repo(project)
    (project / "resolve.json").write_text(
        json.dumps(
            {
                "schema_version": "agentkit.resolve.v1",
                "project_path": str(project),
                "answers_path": str(project / "answers.json"),
                "execution_recommendation": "proceed",
                "recommendation_reason": "Resolve asked to proceed, but blockers remain.",
                "resolved_questions": [],
                "remaining_blockers": [
                    {
                        "code": "missing_policy",
                        "title": "Missing policy answer",
                        "status": "unanswered",
                        "answer": "",
                        "source_section": "blocking_questions",
                        "kind": "question",
                        "rationale": "Need a final answer.",
                    }
                ],
                "remaining_follow_ups": [],
                "confirmed_assumptions": [],
                "superseded_assumptions": [],
                "unresolved_assumptions": [],
                "answers_summary": {"remaining_blockers": 1},
                "source_clarify": {},
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["dispatch", str(project), "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["execution_recommendation"] == "pause"
    assert len(payload["lanes"]) == 1
    assert payload["recommendation_reason"] == "Resolve still contains remaining blockers, so dispatch must pause."


def test_dispatch_serializes_overlapping_paths_in_json_output(tmp_path):
    project = tmp_path / "overlap-repo"
    _write_repo(project)
    (project / "resolve.json").write_text(
        json.dumps(
            {
                "schema_version": "agentkit.resolve.v1",
                "project_path": str(project),
                "answers_path": str(project / "answers.json"),
                "execution_recommendation": "proceed",
                "recommendation_reason": "Ready.",
                "resolved_questions": [],
                "remaining_blockers": [],
                "remaining_follow_ups": [],
                "confirmed_assumptions": [],
                "superseded_assumptions": [],
                "unresolved_assumptions": [],
                "answers_summary": {"remaining_blockers": 0},
                "source_clarify": {
                    "source_bundle": {
                        "architecture_map": {
                            "subsystems": [
                                {"name": "src", "path": "src", "why": "app"},
                                {"name": "api", "path": "src/api", "why": "api"},
                            ],
                            "tests": [],
                            "hints": [],
                        }
                    }
                },
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["dispatch", str(project), "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert len(payload["phases"]) == 2
    assert payload["phases"][1]["execution_mode"] == "serial"
    assert payload["ownership_conflicts"] == [{"left_lane_id": "lane-01", "right_lane_id": "lane-02", "overlap": "src"}]
    assert payload["lanes"][1]["ownership_mode"] == "serialized-overlap"
    assert payload["lanes"][1]["dependencies"] == [{"lane_id": "lane-01", "reason": "overlapping ownership: src"}]
