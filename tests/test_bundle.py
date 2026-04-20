from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agentkit_cli.bundle import BundleEngine
from agentkit_cli.main import app

runner = CliRunner()


def _make_repo(tmp_path: Path) -> Path:
    project = tmp_path / "demo-repo"
    (project / ".agentkit").mkdir(parents=True)
    (project / "src").mkdir()
    (project / "tests").mkdir()
    (project / ".agentkit" / "source.md").write_text(
        "# Demo Repo\n\n"
        "## Objective\nShip a deterministic bundle.\n\n"
        "## Scope & Boundaries\nWork only inside this repo.\n\n"
        "## Rules\n- Keep output deterministic.\n\n"
        "## Validation\nRun pytest.\n\n"
        "## Deliverables\nLeave a portable handoff artifact.\n",
        encoding="utf-8",
    )
    (project / "pyproject.toml").write_text(
        "[project]\nname='demo-repo'\nversion='0.1.0'\n\n[project.scripts]\ndemo='src.main:main'\n",
        encoding="utf-8",
    )
    (project / "src" / "main.py").write_text("def main():\n    return 'ok'\n", encoding="utf-8")
    (project / "tests" / "test_main.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    return project


def test_bundle_engine_assembles_all_surfaces(tmp_path):
    project = _make_repo(tmp_path)
    contract_path = project / "all-day-build-contract-demo.md"
    contract_path.write_text("# Demo contract\n\nShip it carefully.\n", encoding="utf-8")

    bundle = BundleEngine().build(project)

    assert bundle.schema_version == "agentkit.bundle.v1"
    assert bundle.source.missing is False
    assert bundle.source_audit["readiness"]["ready_for_contract"] is True
    assert bundle.architecture_map["summary"]["name"] == "demo-repo"
    assert bundle.contract.artifact_path == str(contract_path)
    assert bundle.gaps == []


def test_bundle_engine_reports_missing_contract_gap(tmp_path):
    project = _make_repo(tmp_path)

    bundle = BundleEngine().build(project)

    assert bundle.contract.missing is True
    assert bundle.contract.mode == "map-handoff-fallback"
    assert any(gap.code == "missing_contract_artifact" for gap in bundle.gaps)


def test_bundle_command_json_is_deterministic(tmp_path):
    project = _make_repo(tmp_path)

    result = runner.invoke(app, ["bundle", str(project), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["schema_version"] == "agentkit.bundle.v1"
    assert payload["source_audit"]["readiness"]["ready_for_contract"] is True
    assert payload["architecture_map"]["summary"]["name"] == "demo-repo"
    assert payload["contract"]["mode"] == "map-handoff-fallback"


def test_bundle_command_markdown_contains_required_sections(tmp_path):
    project = _make_repo(tmp_path)

    result = runner.invoke(app, ["bundle", str(project)])

    assert result.exit_code == 0, result.output
    assert "## Source" in result.output
    assert "## Source audit" in result.output
    assert "## Architecture map" in result.output
    assert "## Execution contract" in result.output
    assert "## Open gaps" in result.output


def test_bundle_help():
    result = runner.invoke(app, ["bundle", "--help"])
    assert result.exit_code == 0
    assert "--json" in result.output
