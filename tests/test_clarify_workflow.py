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


def test_source_to_taskpack_to_clarify_workflow(tmp_path):
    project = tmp_path / "demo-repo"
    _write_repo(
        project,
        "# Demo Repo\n\n"
        "## Objective\nShip the clarify loop.\n\n"
        "## Scope & Boundaries\nWork only inside this repo.\n\n"
        "## Rules\n- Keep output deterministic.\n\n"
        "## Validation\nRun pytest.\n\n"
        "## Deliverables\nLeave markdown and JSON handoff output.\n",
    )

    audit = runner.invoke(app, ["source-audit", str(project), "--json"])
    assert audit.exit_code == 0, audit.output
    assert json.loads(audit.output)["readiness"]["ready_for_contract"] is True

    contract = runner.invoke(app, ["contract", "Ship the clarify loop", "--path", str(project), "--map", str(project)])
    assert contract.exit_code == 0, contract.output

    bundle = runner.invoke(app, ["bundle", str(project), "--json"])
    assert bundle.exit_code == 0, bundle.output

    taskpack = runner.invoke(app, ["taskpack", str(project), "--json"])
    assert taskpack.exit_code == 0, taskpack.output

    clarify = runner.invoke(app, ["clarify", str(project), "--json"])
    assert clarify.exit_code == 0, clarify.output
    payload = json.loads(clarify.output)
    assert payload["execution_recommendation"] in {"proceed", "proceed-with-assumptions"}
    assert payload["source_bundle"]["contract"]["missing"] is False
    assert payload["source_taskpack"]["schema_version"] == "agentkit.taskpack.v1"


def test_clarify_fails_clearly_when_upstream_source_is_missing(tmp_path):
    project = tmp_path / "demo-repo"
    project.mkdir()

    result = runner.invoke(app, ["clarify", str(project), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["execution_recommendation"] == "pause"
    assert any(item["code"] == "missing_source" for item in payload["blocking_questions"])


def test_clarify_surfaces_contradictory_source_guidance(tmp_path):
    project = tmp_path / "demo-repo"
    _write_repo(
        project,
        "# Demo Repo\n\n"
        "## Objective\nShip the clarify loop.\n\n"
        "## Scope & Boundaries\nWork only inside this repo.\n\n"
        "## Rules\n- Always update docs.\n- Do not update docs.\n\n"
        "## Validation\nRun pytest.\n\n"
        "## Deliverables\nLeave markdown and JSON handoff output.\n",
    )
    (project / "all-day-build-contract-demo.md").write_text("# Demo contract\n\n- Keep output deterministic.\n", encoding="utf-8")

    result = runner.invoke(app, ["clarify", str(project), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["execution_recommendation"] == "pause"
    assert payload["contradictions"]
    assert payload["contradictions"][0]["code"] in {"contradiction", "contract_preview_contradiction"}
