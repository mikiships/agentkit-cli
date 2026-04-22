from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agentkit_cli.main import app

runner = CliRunner()


def _write_repo(
    project: Path,
    *,
    stale_self_hosting: bool = False,
    shipped_adjacent_grounding: bool = False,
    post_shipped_truth_objective: bool = False,
    shipped_truth_sync: bool = False,
    shipped_flagship_concrete_next_step: bool = False,
    concrete_next_closed: bool = False,
    post_closeout_closed: bool = False,
) -> None:
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
    if post_shipped_truth_objective:
        objective = "Teach the flagship self-spec flow to detect that the shipped `flagship-concrete-next-step` lane is already complete, suppress replay of the just-shipped v1.27.0 work, and advance to one fresh adjacent recommendation with an updated flagship contract seed."
    if post_closeout_closed:
        objective = "Teach the flagship self-spec flow to recognize when `flagship-post-closeout-advance` is already closed out in current repo truth, stop replaying that lane, and promote the next honest flagship recommendation from current shipped or local-release-ready evidence."
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
    readme = (
        "# Demo Repo\n\n"
        "Supported lane: `source -> source-audit -> map -> contract`\n\n"
        "Recommended flow:\n\n"
        "```bash\n"
        "agentkit source-audit .\n"
        "agentkit map . --json > repo-map.json\n"
        "agentkit contract \"Ship the next increment\" --path . --map repo-map.json\n"
        "```\n"
    )
    if stale_self_hosting or post_shipped_truth_objective or post_closeout_closed:
        readme = (
            "# Demo Repo\n\n"
            "Supported lane: `source -> audit -> map -> spec -> contract`\n\n"
            "Recommended flow:\n\n"
            "```bash\n"
            "agentkit source-audit .\n"
            "agentkit map . --json > repo-map.json\n"
            "agentkit spec . --json > repo-spec.json\n"
            "agentkit contract --spec repo-spec.json --path .\n"
            "```\n"
        )
    (project / "README.md").write_text(readme, encoding="utf-8")
    changelog = "# Changelog\n\n## [0.3.0] - 2026-04-21\n\n- Added deterministic workflow docs.\n"
    if stale_self_hosting:
        changelog = (
            "# Changelog\n\n"
            "## [0.3.0] - 2026-04-21\n\n"
            "- Added deterministic workflow docs.\n"
            "- Added a real repo-local `.agentkit/source.md` for the flagship repo so source-audit and spec no longer fall back to legacy context.\n"
            "- Supported repo-understanding lane is `source -> audit -> map -> spec -> contract`.\n"
        )
    if post_shipped_truth_objective:
        changelog = (
            "# Changelog\n\n"
            "## [0.4.0] - 2026-04-21\n\n"
            "- Refreshed the flagship source objective so `agentkit spec` targets a concrete adjacent build after shipped-truth sync.\n"
            "- Kept the supported repo-understanding lane at `source -> audit -> map -> spec -> contract`.\n"
        )
    if post_closeout_closed:
        changelog = (
            "# Changelog\n\n"
            "## [0.7.0] - 2026-04-21\n\n"
            "- Taught the flagship `agentkit spec` flow to suppress replay of the closed `flagship-post-closeout-advance` lane.\n"
            "- Kept the supported repo-understanding lane at `source -> audit -> map -> spec -> contract`.\n"
        )
    if concrete_next_closed or shipped_flagship_concrete_next_step:
        changelog = (
            "# Changelog\n\n"
            "## [0.5.0] - 2026-04-21\n\n"
            "- Taught the flagship `agentkit spec` flow to emit a `flagship-concrete-next-step` recommendation after shipped-truth sync.\n"
            "- Kept the supported repo-understanding lane at `source -> audit -> map -> spec -> contract`.\n"
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
    if shipped_truth_sync:
        (project / "progress-log.md").write_text(
            "# Progress Log — demo-repo v0.5.0 spec shipped truth sync\n\n"
            "Status: RELEASE-READY (LOCAL-ONLY)\n"
            "Date: 2026-04-21\n\n"
            "- Introduced a `shipped-truth-sync` recommendation after shipped adjacent grounding.\n"
            "- Verified `agentkit spec . --json` no longer repeats shipped adjacent grounding work.\n",
            encoding="utf-8",
        )
    if shipped_flagship_concrete_next_step:
        (project / "BUILD-REPORT.md").write_text(
            "# BUILD-REPORT.md — demo-repo v0.6.0 spec concrete next step\n\nStatus: SHIPPED\n- Closed the `flagship-concrete-next-step` lane and verified the planner should not replay it.\n",
            encoding="utf-8",
        )
        (project / "FINAL-SUMMARY.md").write_text(
            "# Final Summary — demo-repo v0.6.0 spec concrete next step\n\nStatus: SHIPPED\n- The flagship planner already completed the `flagship-concrete-next-step` lane.\n",
            encoding="utf-8",
        )
        (project / "progress-log.md").write_text(
            "# Progress Log — demo-repo v0.6.0 spec concrete next step\n\n"
            "Status: RELEASE-READY (LOCAL-ONLY)\n"
            "Date: 2026-04-21\n\n"
            "- Closed the `flagship-concrete-next-step` lane and proved the flagship planner now needs a fresh adjacent recommendation.\n"
            "- Verified `agentkit spec . --json` should suppress replay of the just-finished v1.27.0 work.\n",
            encoding="utf-8",
        )
    if concrete_next_closed:
        (project / "progress-log.md").write_text(
            "# Progress Log — demo-repo v0.6.0 flagship concrete next step\n\n"
            "Status: RELEASE-READY (LOCAL-ONLY)\n"
            "Date: 2026-04-21\n\n"
            "- Introduced a `flagship-concrete-next-step` recommendation after shipped-truth sync.\n"
            "- Verified `agentkit spec . --json` no longer falls back to the generic subsystem recommendation.\n",
            encoding="utf-8",
        )
    if post_closeout_closed:
        (project / "BUILD-REPORT.md").write_text(
            "# BUILD-REPORT.md — demo-repo v0.7.0 flagship post-closeout advance\n\nStatus: SHIPPED\n- Closed the `flagship-post-closeout-advance` lane and verified the planner should advance again.\n",
            encoding="utf-8",
        )
        (project / "FINAL-SUMMARY.md").write_text(
            "# Final Summary — demo-repo v0.7.0 flagship post-closeout advance\n\nStatus: SHIPPED\n- The flagship planner already completed the `flagship-post-closeout-advance` lane.\n",
            encoding="utf-8",
        )
        (project / "progress-log.md").write_text(
            "# Progress Log — demo-repo v0.8.0 flagship adjacent next step\n\n"
            "Status: IN PROGRESS\n"
            "Date: 2026-04-21\n\n"
            "- The shipped flagship repo still lets `agentkit spec . --json` replay `flagship-post-closeout-advance`.\n"
            "- This lane exists to promote the next honest flagship recommendation from current repo truth.\n",
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


def test_spec_workflow_advances_past_closed_flagship_concrete_next_lane(tmp_path):
    project = tmp_path / "demo-repo"
    _write_repo(project, post_shipped_truth_objective=True, concrete_next_closed=True)

    audit = runner.invoke(app, ["source-audit", str(project), "--json"])
    assert audit.exit_code == 0, audit.output
    assert json.loads(audit.output)["readiness"]["ready_for_contract"] is True

    spec_dir = tmp_path / "spec-artifacts"
    spec_run = runner.invoke(app, ["spec", str(project), "--output-dir", str(spec_dir), "--json"])
    assert spec_run.exit_code == 0, spec_run.output
    spec_payload = json.loads((spec_dir / "spec.json").read_text(encoding="utf-8"))
    assert spec_payload["primary_recommendation"]["kind"] == "flagship-post-closeout-advance"
    assert spec_payload["contract_seed"]["title"].endswith("flagship post-closeout advance")

    contract = runner.invoke(app, ["contract", "--spec", str(spec_dir / "spec.json"), "--path", str(project), "--json"])
    assert contract.exit_code == 0, contract.output
    contract_payload = json.loads(contract.output)
    assert contract_payload["objective"] == spec_payload["contract_seed"]["objective"]
    assert contract_payload["output_path"].endswith("all-day-build-contract-teach-the-flagship-self-spec-flow-to-suppress-replay-of-the-closed-flagship-concrete-next-step-lane-from-the-just-shipped-v1-27-0-work-and-advance-to-one-fresh-adjacent-recommendation-with-an-updated-flagship-contract-seed.md")


def test_spec_workflow_advances_past_closed_flagship_concrete_next_step_lane(tmp_path):
    project = tmp_path / "demo-repo"
    _write_repo(project, post_shipped_truth_objective=True, concrete_next_closed=True)

    audit = runner.invoke(app, ["source-audit", str(project), "--json"])
    assert audit.exit_code == 0, audit.output
    assert json.loads(audit.output)["readiness"]["ready_for_contract"] is True

    spec_dir = tmp_path / "spec-artifacts"
    spec_run = runner.invoke(app, ["spec", str(project), "--output-dir", str(spec_dir), "--json"])
    assert spec_run.exit_code == 0, spec_run.output
    spec_payload = json.loads((spec_dir / "spec.json").read_text(encoding="utf-8"))
    assert spec_payload["primary_recommendation"]["kind"] == "flagship-post-closeout-advance"
    assert spec_payload["contract_seed"]["title"].endswith("flagship post-closeout advance")

    contract = runner.invoke(app, ["contract", "--spec", str(spec_dir / "spec.json"), "--path", str(project), "--json"])
    assert contract.exit_code == 0, contract.output
    contract_payload = json.loads(contract.output)
    assert contract_payload["objective"] == spec_payload["contract_seed"]["objective"]
    assert contract_payload["output_path"].endswith("all-day-build-contract-teach-the-flagship-self-spec-flow-to-suppress-replay-of-the-closed-flagship-concrete-next-step-lane-from-the-just-shipped-v1-27-0-work-and-advance-to-one-fresh-adjacent-recommendation-with-an-updated-flagship-contract-seed.md")


def test_spec_workflow_advances_past_closed_flagship_post_closeout_lane(tmp_path):
    project = tmp_path / "demo-repo"
    _write_repo(project, post_closeout_closed=True)

    audit = runner.invoke(app, ["source-audit", str(project), "--json"])
    assert audit.exit_code == 0, audit.output
    assert json.loads(audit.output)["readiness"]["ready_for_contract"] is True

    spec_dir = tmp_path / "spec-artifacts"
    spec_run = runner.invoke(app, ["spec", str(project), "--output-dir", str(spec_dir), "--json"])
    assert spec_run.exit_code == 0, spec_run.output
    spec_payload = json.loads((spec_dir / "spec.json").read_text(encoding="utf-8"))
    assert spec_payload["primary_recommendation"]["kind"] == "flagship-adjacent-next-step"
    assert spec_payload["contract_seed"]["title"].endswith("flagship adjacent next step")

    contract = runner.invoke(app, ["contract", "--spec", str(spec_dir / "spec.json"), "--path", str(project), "--json"])
    assert contract.exit_code == 0, contract.output
    contract_payload = json.loads(contract.output)
    assert contract_payload["objective"] == spec_payload["contract_seed"]["objective"]
    assert contract_payload["output_path"].endswith("all-day-build-contract-teach-the-flagship-self-spec-flow-to-advance-past-the-closed-flagship-post-closeout-advance-lane-and-emit-one-concrete-adjacent-flagship-recommendation-instead-of-the-generic-subsystem-fallback.md")
