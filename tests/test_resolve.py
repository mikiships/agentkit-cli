from __future__ import annotations

import json
from pathlib import Path

from agentkit_cli.resolve import ResolveEngine


def _make_repo(tmp_path: Path) -> Path:
    project = tmp_path / "demo-repo"
    (project / ".agentkit").mkdir(parents=True)
    (project / "src").mkdir()
    (project / "tests").mkdir()
    (project / ".agentkit" / "source.md").write_text(
        "# Demo Repo\n\n"
        "## Objective\nShip a deterministic resolve workflow.\n\n"
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
    (project / "tests" / "test_main.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    (project / "all-day-build-contract-demo.md").write_text("# Demo contract\n\n- Keep output deterministic.\n", encoding="utf-8")
    return project


def test_resolve_engine_is_deterministic_and_ordered(tmp_path):
    project = _make_repo(tmp_path)
    answers = tmp_path / "answers.json"
    answers.write_text(
        json.dumps(
            {
                "answers": [
                    {"code": "missing_contract_artifact", "status": "resolved", "answer": "Use the saved demo contract in the repo root for execution."},
                    {"code": "execution_checklist_review", "status": "resolved", "answer": "The mapped checks are enough."}
                ],
                "assumptions": {
                    "fallback_contract": {"status": "superseded", "reason": "A saved contract artifact is now available.", "replacement": "Use all-day-build-contract-demo.md as the contract source."},
                    "primary_language": {"status": "confirmed", "reason": "Python remains the implementation surface."},
                    "runner_notes": {"status": "confirmed", "reason": "Default runner notes are acceptable."},
                },
            }
        ),
        encoding="utf-8",
    )

    result = ResolveEngine().build(project, answers_path=answers, target="codex")

    assert result.schema_version == "agentkit.resolve.v1"
    assert result.execution_recommendation == "proceed"
    assert result.resolved_questions[0].code == "execution_checklist_review"
    assert [item.code for item in result.confirmed_assumptions] == sorted(item.code for item in result.confirmed_assumptions)
    payload = json.loads(result.to_json())
    assert payload["answers_summary"]["remaining_blockers"] == 0
    assert payload["answers_summary"]["remaining_follow_ups"] >= 0
    assert payload["source_clarify"]["source_taskpack"]["target"] == "codex"


def test_resolve_engine_surfaces_unanswered_and_contradictory_items(tmp_path):
    project = _make_repo(tmp_path)
    answers = tmp_path / "answers.json"
    answers.write_text(
        json.dumps(
            {
                "answers": [
                    {"code": "execution_checklist_review", "status": "contradictory", "answer": "The checklist is incomplete."}
                ],
                "assumptions": {
                    "primary_language": {"status": "confirmed", "reason": "Python remains the implementation surface."}
                },
            }
        ),
        encoding="utf-8",
    )

    result = ResolveEngine().build(project, answers_path=answers)

    assert result.execution_recommendation == "pause"
    assert any(item.status == "contradictory" for item in result.remaining_blockers)
    assert any(item.status == "unanswered" for item in result.remaining_follow_ups)
    assert any(item.status == "unresolved" for item in result.unresolved_assumptions)
