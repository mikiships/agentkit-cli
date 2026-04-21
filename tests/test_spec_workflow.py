from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agentkit_cli.main import app

runner = CliRunner()


def _write_repo(project: Path, *, stale_self_hosting: bool = False, shipped_adjacent_grounding: bool = False) -> None:
    (project / ".agentkit").mkdir(parents=True)
    (project / "src").mkdir()
    (project / "tests").mkdir()
    if stale_self_hosting:
        (project / "agentkit_cli" / "commands").mkdir(parents=True, exist_ok=True)
        (project / "agentkit_cli" / "main.py").write_text(
            'from agentkit_cli.commands.spec_cmd import spec_command\n@app.command("spec")\ndef spec():\n    pass\n',
            encoding="utf-8",
        )
    objective = "Ship the next repo-understanding increment."
    if stale_self_hosting:
        objective = "Make this repo self-hosted for the repo-understanding lane so `agentkit source-audit`, `agentkit spec`, and the next contract step work cleanly from the repo's own canonical source."
    (project / ".agentkit" / "source.md").write_text(
        "# Demo Repo\n\n"
        f"## Objective\n{objective}\n\n"
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
    changelog = "# Changelog\n\n## [0.3.0] - 2026-04-21\n\n- Added deterministic workflow docs.\n"
    if stale_self_hosting:
        changelog = (
            "# Changelog\n\n"
            "## [0.3.0] - 2026-04-21\n\n"
            "- Added deterministic workflow docs.\n"
            "- Added a real repo-local `.agentkit/source.md` for the flagship repo so source-audit and spec no longer fall back to legacy context.\n"
            "- Supported repo-understanding lane is `source -> audit -> map -> spec -> contract`.\n"
        )
    (project / "CHANGELOG.md").write_text(changelog, encoding="utf-8")
    (project / "BUILD-REPORT.md").write_text(
        "# BUILD-REPORT.md — demo-repo v0.3.0\n\nStatus: SHIPPED\n",
        encoding="utf-8",
    )
    (project / "FINAL-SUMMARY.md").write_text(
        "# Final Summary — demo-repo v0.3.0\n\nStatus: SHIPPED\n",
        encoding="utf-8",
    )
    if shipped_adjacent_grounding:
        (project / "progress-log.md").write_text(
            "# Progress Log — demo-repo v0.4.0 spec grounding\n\n"
            "Status: RELEASE-READY (LOCAL-ONLY)\n"
            "Date: 2026-04-21\n\n"
            "- Introduced an `adjacent-grounding` recommendation for stale self-hosting source objectives.\n"
            "- Verified `agentkit spec . --json` returns `adjacent-grounding` with a contract seed focused on spec grounding.\n",
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


def test_spec_workflow_grounds_next_build_from_current_repo_truth(tmp_path):
    project = tmp_path / "demo-repo"
    _write_repo(project, stale_self_hosting=True)

    audit = runner.invoke(app, ["source-audit", str(project), "--json"])
    assert audit.exit_code == 0, audit.output
    assert json.loads(audit.output)["readiness"]["ready_for_contract"] is True

    spec_dir = tmp_path / "spec-artifacts"
    spec_run = runner.invoke(app, ["spec", str(project), "--output-dir", str(spec_dir), "--json"])
    assert spec_run.exit_code == 0, spec_run.output
    spec_payload = json.loads((spec_dir / "spec.json").read_text(encoding="utf-8"))
    assert spec_payload["primary_recommendation"]["kind"] == "adjacent-grounding"
    assert spec_payload["contract_seed"]["objective"].startswith("Ground `agentkit spec` in current repo truth")

    contract = runner.invoke(app, ["contract", "--spec", str(spec_dir / "spec.json"), "--path", str(project), "--json"])
    assert contract.exit_code == 0, contract.output
    contract_payload = json.loads(contract.output)
    assert contract_payload["objective"] == spec_payload["contract_seed"]["objective"]
    assert contract_payload["output_path"].endswith("all-day-build-contract-ground-agentkit-spec-in-current-repo-truth-so-the-flagship-repo-recommends-the-next-honest-adjacent-build-instead-of-recycling-already-satisfied-source-readiness-work.md")


def test_spec_workflow_moves_to_shipped_truth_sync_after_adjacent_grounding_ships(tmp_path):
    project = tmp_path / "demo-repo"
    _write_repo(project, stale_self_hosting=True, shipped_adjacent_grounding=True)

    audit = runner.invoke(app, ["source-audit", str(project), "--json"])
    assert audit.exit_code == 0, audit.output
    assert json.loads(audit.output)["readiness"]["ready_for_contract"] is True

    spec_dir = tmp_path / "spec-artifacts"
    spec_run = runner.invoke(app, ["spec", str(project), "--output-dir", str(spec_dir), "--json"])
    assert spec_run.exit_code == 0, spec_run.output
    spec_payload = json.loads((spec_dir / "spec.json").read_text(encoding="utf-8"))
    assert spec_payload["primary_recommendation"]["kind"] == "shipped-truth-sync"
    assert spec_payload["contract_seed"]["objective"].startswith("Refresh the flagship source objective")

    contract = runner.invoke(app, ["contract", "--spec", str(spec_dir / "spec.json"), "--path", str(project), "--json"])
    assert contract.exit_code == 0, contract.output
    contract_payload = json.loads(contract.output)
    assert contract_payload["objective"] == spec_payload["contract_seed"]["objective"]
    assert contract_payload["output_path"].endswith("all-day-build-contract-refresh-the-flagship-source-objective-and-closeout-surfaces-so-agentkit-spec-starts-from-current-shipped-repo-truth-instead-of-re-proposing-the-already-shipped-spec-grounding-increment.md")
