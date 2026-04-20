from __future__ import annotations

import json

from typer.testing import CliRunner

from agentkit_cli.main import app

runner = CliRunner()


def test_source_audit_to_contract_workflow(tmp_path):
    project = tmp_path / "demo-repo"
    project.mkdir()
    (project / ".agentkit").mkdir()
    (project / ".agentkit" / "source.md").write_text(
        "# Demo Repo\n\n"
        "## Objective\nShip a deterministic source audit workflow.\n\n"
        "## Scope & Boundaries\nWork only inside this repo.\n\n"
        "## Rules\n- Commit after each deliverable.\n- Keep output deterministic.\n\n"
        "## Validation\nRun uv run pytest -q tests/test_source_audit.py tests/test_source_audit_workflow.py\n\n"
        "## Deliverables\nLeave markdown and JSON handoff output.\n",
        encoding="utf-8",
    )

    audit = runner.invoke(app, ["source-audit", str(project), "--json"])
    assert audit.exit_code == 0, audit.output
    audit_payload = json.loads(audit.output)
    assert audit_payload["readiness"]["ready_for_contract"] is True

    repo_map = runner.invoke(app, ["map", str(project), "--json"])
    assert repo_map.exit_code == 0, repo_map.output
    map_payload = json.loads(repo_map.output)
    assert map_payload["summary"]["name"] == "demo-repo"

    contract = runner.invoke(
        app,
        [
            "contract",
            "Ship the source audit lane",
            "--path",
            str(project),
            "--map",
            str(project),
            "--json",
        ],
    )
    assert contract.exit_code == 0, contract.output
    contract_payload = json.loads(contract.output)
    assert contract_payload["source_context_format"] == "agentkit-source"
    assert contract_payload["map_context"]["summary"]["name"] == "demo-repo"
    assert contract_payload["output_path"].endswith("all-day-build-contract-ship-the-source-audit-lane.md")
