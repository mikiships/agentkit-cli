from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agentkit_cli.main import app

runner = CliRunner()


def _write_repo(project: Path, source_text: str) -> None:
    (project / ".agentkit").mkdir(parents=True)
    (project / "src").mkdir()
    (project / "tests").mkdir()
    (project / ".agentkit" / "source.md").write_text(source_text, encoding="utf-8")
    (project / "pyproject.toml").write_text(
        "[project]\nname='demo-repo'\nversion='0.1.0'\n\n[project.scripts]\ndemo='src.main:main'\n",
        encoding="utf-8",
    )
    (project / "src" / "main.py").write_text("def main():\n    return 'ok'\n", encoding="utf-8")
    (project / "tests" / "test_main.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")


def test_source_to_clarify_to_resolve_workflow(tmp_path):
    project = tmp_path / "demo-repo"
    _write_repo(
        project,
        "# Demo Repo\n\n"
        "## Objective\nShip the resolve loop.\n\n"
        "## Scope & Boundaries\nWork only inside this repo.\n\n"
        "## Rules\n- Keep output deterministic.\n\n"
        "## Validation\nRun pytest.\n\n"
        "## Deliverables\nLeave markdown and JSON handoff output.\n",
    )

    audit = runner.invoke(app, ["source-audit", str(project), "--json"])
    assert audit.exit_code == 0, audit.output
    assert json.loads(audit.output)["readiness"]["ready_for_contract"] is True

    contract = runner.invoke(app, ["contract", "Ship the resolve loop", "--path", str(project), "--map", str(project)])
    assert contract.exit_code == 0, contract.output

    clarify = runner.invoke(app, ["clarify", str(project), "--json", "--target", "codex"])
    assert clarify.exit_code == 0, clarify.output
    clarify_payload = json.loads(clarify.output)
    assert clarify_payload["execution_recommendation"] in {"proceed", "proceed-with-assumptions"}

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

    resolve = runner.invoke(app, ["resolve", str(project), "--answers", str(answers), "--json", "--target", "codex"])
    assert resolve.exit_code == 0, resolve.output
    payload = json.loads(resolve.output)
    assert payload["execution_recommendation"] == "proceed"
    assert payload["source_clarify"]["schema_version"] == "agentkit.clarify.v1"
    assert payload["answers_summary"]["remaining_blockers"] == 0


def test_resolve_stays_paused_when_answers_are_incomplete(tmp_path):
    project = tmp_path / "demo-repo"
    _write_repo(
        project,
        "# Demo Repo\n\n"
        "## Objective\nShip the resolve loop.\n\n"
        "## Scope & Boundaries\nWork only inside this repo.\n\n"
        "## Rules\n- Always update docs.\n- Do not update docs.\n\n"
        "## Validation\nRun pytest.\n\n"
        "## Deliverables\nLeave markdown and JSON handoff output.\n",
    )
    (project / "all-day-build-contract-demo.md").write_text("# Demo contract\n\n- Keep output deterministic.\n", encoding="utf-8")
    answers = tmp_path / "answers.json"
    answers.write_text(
        json.dumps(
            {
                "answers": [
                    {"code": "execution_checklist_review", "status": "resolved", "answer": "The checklist is enough."}
                ],
                "assumptions": {
                    "primary_language": {"status": "confirmed", "reason": "Python remains the implementation surface."}
                },
            }
        ),
        encoding="utf-8",
    )

    resolve = runner.invoke(app, ["resolve", str(project), "--answers", str(answers), "--json"])
    assert resolve.exit_code == 0, resolve.output
    payload = json.loads(resolve.output)
    assert payload["execution_recommendation"] == "pause"
    assert payload["remaining_blockers"]
    assert any(item["status"] in {"unanswered", "contradictory"} for item in payload["remaining_blockers"])
