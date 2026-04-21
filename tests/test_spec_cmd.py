from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agentkit_cli.main import app

runner = CliRunner()


def _write_repo(
    project: Path,
    *,
    canonical: bool = True,
    workflow_lane: bool = True,
    contradictory: bool = False,
    stale_self_hosting: bool = False,
    shipped_adjacent_grounding: bool = False,
    post_shipped_truth_objective: bool = False,
    shipped_truth_sync: bool = False,
) -> None:
    if canonical:
        (project / ".agentkit").mkdir(parents=True)
        source_path = project / ".agentkit" / "source.md"
    else:
        source_path = project / "AGENTS.md"
    project.mkdir(parents=True, exist_ok=True)
    (project / "src").mkdir(exist_ok=True)
    (project / "tests").mkdir(exist_ok=True)
    if stale_self_hosting:
        (project / "agentkit_cli" / "commands").mkdir(parents=True, exist_ok=True)
        (project / "agentkit_cli" / "main.py").write_text(
            'from agentkit_cli.commands.spec_cmd import spec_command\n@app.command("spec")\ndef spec():\n    pass\n',
            encoding="utf-8",
        )
    rules = "- Keep output deterministic.\n"
    if contradictory:
        rules = "- Always update docs.\n- Do not update docs.\n"
    objective = "Ship the next repo-understanding increment."
    if stale_self_hosting:
        objective = "Make this repo self-hosted for the repo-understanding lane so `agentkit source-audit`, `agentkit spec`, and the next contract step work cleanly from the repo's own canonical source."
    if post_shipped_truth_objective:
        objective = "Teach the flagship self-spec flow to emit a concrete adjacent build recommendation and contract seed after shipped-truth sync instead of falling back to the generic subsystem-next-step recommendation."
    source_path.write_text(
        "# Demo Repo\n\n"
        f"## Objective\n{objective}\n\n"
        "## Scope & Boundaries\nWork only inside this repo.\n\n"
        f"## Rules\n{rules}\n"
        "## Validation\nRun uv run pytest -q tests/test_spec_cmd.py tests/test_spec_workflow.py\n\n"
        "## Deliverables\nLeave markdown and JSON handoff artifacts.\n",
        encoding="utf-8",
    )
    (project / "pyproject.toml").write_text(
        "[project]\nname='demo-repo'\nversion='0.1.0'\n\n[project.scripts]\ndemo='src.main:main'\n",
        encoding="utf-8",
    )
    (project / "src" / "main.py").write_text("def main():\n    return 'ok'\n", encoding="utf-8")
    (project / "tests" / "test_main.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    if workflow_lane:
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
        if stale_self_hosting or post_shipped_truth_objective:
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


def test_spec_command_json_output_is_deterministic(tmp_path):
    project = tmp_path / "demo-repo"
    _write_repo(project)

    first = runner.invoke(app, ["spec", str(project), "--json"])
    second = runner.invoke(app, ["spec", str(project), "--json"])

    assert first.exit_code == 0, first.output
    assert second.exit_code == 0, second.output
    assert first.output == second.output
    payload = json.loads(first.output)
    assert payload["schema_version"] == "agentkit.spec.v1"
    assert payload["primary_recommendation"]["kind"] == "workflow-gap"
    assert payload["contract_seed"]["objective"].startswith("Add a deterministic `agentkit spec` step")


def test_spec_command_output_dir_writes_markdown_and_json(tmp_path):
    project = tmp_path / "demo-repo"
    out = tmp_path / "out"
    _write_repo(project)

    result = runner.invoke(app, ["spec", str(project), "--output-dir", str(out)])

    assert result.exit_code == 0, result.output
    assert (out / "spec.md").exists()
    assert (out / "spec.json").exists()
    assert "Wrote spec directory:" in result.output
    assert "Primary recommendation" in (out / "spec.md").read_text(encoding="utf-8")


def test_spec_command_json_stdout_stays_clean_when_output_dir_is_used(tmp_path):
    project = tmp_path / "demo-repo"
    out = tmp_path / "out"
    _write_repo(project)

    result = runner.invoke(app, ["spec", str(project), "--output-dir", str(out), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["schema_version"] == "agentkit.spec.v1"
    assert "Wrote spec directory:" not in result.stdout
    assert "Wrote spec directory:" in result.stderr
    assert (out / "spec.md").exists()
    assert (out / "spec.json").exists()


def test_spec_command_fails_when_required_upstream_source_is_missing(tmp_path):
    project = tmp_path / "demo-repo"
    project.mkdir()

    result = runner.invoke(app, ["spec", str(project), "--json"])

    assert result.exit_code != 0
    assert "canonical or legacy source" in result.output.lower()


def test_spec_command_fails_on_contradictory_source_guidance(tmp_path):
    project = tmp_path / "demo-repo"
    _write_repo(project, contradictory=True)

    result = runner.invoke(app, ["spec", str(project), "--json"])

    assert result.exit_code != 0
    assert "contradictory upstream source guidance" in result.output.lower()


def test_spec_command_truthfully_handles_fallback_without_workflow_artifacts(tmp_path):
    project = tmp_path / "demo-repo"
    _write_repo(project, canonical=False, workflow_lane=False)

    result = runner.invoke(app, ["spec", str(project), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["recent_workflow_artifacts"] == []
    assert payload["primary_recommendation"]["kind"] == "fallback-hardening"


def test_spec_suppresses_stale_self_hosting_objective_when_repo_truth_already_satisfies_it(tmp_path):
    project = tmp_path / "demo-repo"
    _write_repo(project, stale_self_hosting=True)

    result = runner.invoke(app, ["spec", str(project), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    recommendation = payload["primary_recommendation"]
    assert recommendation["kind"] == "adjacent-grounding"
    assert "self-hosted" not in recommendation["objective"]
    assert recommendation["contract_seed"]["objective"].startswith("Ground `agentkit spec` in current repo truth")
    assert any("already ships the canonical source" in item for item in recommendation["why_now"])
    assert any("source -> audit -> map -> spec -> contract" in item for item in recommendation["evidence"])


def test_spec_moves_past_adjacent_grounding_once_that_increment_is_already_shipped(tmp_path):
    project = tmp_path / "demo-repo"
    _write_repo(project, stale_self_hosting=True, shipped_adjacent_grounding=True)

    result = runner.invoke(app, ["spec", str(project), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    recommendation = payload["primary_recommendation"]
    assert recommendation["kind"] == "shipped-truth-sync"
    assert "already-shipped spec-grounding increment" in recommendation["objective"]
    assert recommendation["contract_seed"]["title"].endswith("shipped truth sync")
    assert any("adjacent spec-grounding increment" in item for item in recommendation["why_now"])
    assert any("Recent shipped/local-ready artifacts already record" in item for item in recommendation["evidence"])


def test_spec_emits_concrete_flagship_next_step_after_shipped_truth_sync(tmp_path):
    project = tmp_path / "demo-repo"
    _write_repo(project, post_shipped_truth_objective=True, shipped_truth_sync=True)

    result = runner.invoke(app, ["spec", str(project), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    recommendation = payload["primary_recommendation"]
    assert recommendation["kind"] == "flagship-concrete-next-step"
    assert recommendation["title"] == "Emit a concrete next flagship lane after shipped-truth sync"
    assert recommendation["contract_seed"]["title"].endswith("spec concrete next step")
    assert "generic subsystem-next-step" in recommendation["objective"]
    assert any("shipped-truth-sync increment as done" in item for item in recommendation["evidence"])


def test_spec_help():
    result = runner.invoke(app, ["spec", "--help"])
    assert result.exit_code == 0
    assert "--output-dir" in result.output
