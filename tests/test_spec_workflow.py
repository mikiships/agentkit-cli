from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agentkit_cli.main import app

runner = CliRunner()


def _write_repo(project: Path) -> None:
    (project / ".agentkit").mkdir(parents=True)
    (project / "src").mkdir()
    (project / "tests").mkdir()
    (project / ".agentkit" / "source.md").write_text(
        "# Demo Repo\n\n"
        "## Objective\nShip the next repo-understanding increment.\n\n"
        "## Scope & Boundaries\nWork only inside this repo.\n\n"
        "## Rules\n- Keep output deterministic.\n\n"
        "## Validation\nRun uv run pytest -q tests/test_spec_cmd.py tests/test_spec_workflow.py tests/test_contract_d2.py\n\n"
        "## Deliverables\nLeave markdown and JSON handoff artifacts.\n",
        encoding="utf-8",
    )
    (project / "pyproject.toml").write_text(
        "[project]\nname='demo-repo'\nversion='0.1.0'\n\n[project.scripts]\ndemo='src.main:main'\n",
        encoding="utf-8",
    )
    (project / "src" / "main.py").write_text("def main():\n    return 'ok'\n", encoding="utf-8")
    (project / "tests" / "test_main.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    (project / "README.md").write_text(
        "# Demo Repo\n\n"
        "Supported lane: `source -> source-audit -> map -> contract`\n\n"
        "Recommended flow:\n\n"
        "```bash\n"
        "agentkit source-audit .\n"
        "agentkit map . --json > repo-map.json\n"
        "agentkit contract \"Ship the next increment\" --path . --map repo-map.json\n"
        "```\n",
        encoding="utf-8",
    )
    (project / "CHANGELOG.md").write_text(
        "# Changelog\n\n## [0.3.0] - 2026-04-21\n\n- Added deterministic workflow docs.\n",
        encoding="utf-8",
    )
    (project / "BUILD-REPORT.md").write_text(
        "# BUILD-REPORT.md — demo-repo v0.3.0\n\nStatus: RELEASE-READY (LOCAL-ONLY)\n",
        encoding="utf-8",
    )
    (project / "FINAL-SUMMARY.md").write_text(
        "# Final Summary — demo-repo v0.3.0\n\nStatus: RELEASE-READY (LOCAL-ONLY)\n",
        encoding="utf-8",
    )


def test_source_audit_to_map_to_spec_to_contract_workflow(tmp_path):
    project = tmp_path / "demo-repo"
    _write_repo(project)

    audit = runner.invoke(app, ["source-audit", str(project), "--json"])
    assert audit.exit_code == 0, audit.output
    assert json.loads(audit.output)["readiness"]["ready_for_contract"] is True

    repo_map = runner.invoke(app, ["map", str(project), "--json"])
    assert repo_map.exit_code == 0, repo_map.output
    assert json.loads(repo_map.output)["summary"]["name"] == "demo-repo"

    spec_dir = tmp_path / "spec-artifacts"
    spec_run = runner.invoke(app, ["spec", str(project), "--output-dir", str(spec_dir), "--json"])
    assert spec_run.exit_code == 0, spec_run.output
    spec_payload = json.loads((spec_dir / "spec.json").read_text(encoding="utf-8"))
    assert spec_payload["primary_recommendation"]["kind"] == "workflow-gap"

    contract = runner.invoke(app, ["contract", "--spec", str(spec_dir / "spec.json"), "--path", str(project), "--json"])
    assert contract.exit_code == 0, contract.output
    contract_payload = json.loads(contract.output)
    assert contract_payload["objective"] == spec_payload["contract_seed"]["objective"]
    assert contract_payload["map_context"]["summary"]["name"] == "demo-repo"
    assert contract_payload["output_path"].endswith("all-day-build-contract-add-a-deterministic-agentkit-spec-step-between-map-and-contract-so-repo-understanding-artifacts-produce-a-contract-ready-next-build-plan.md")
