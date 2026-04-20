from __future__ import annotations

import json

from typer.testing import CliRunner

from agentkit_cli.main import app

runner = CliRunner()


def test_source_audit_prefers_canonical_source(tmp_path):
    (tmp_path / ".agentkit").mkdir()
    (tmp_path / ".agentkit" / "source.md").write_text(
        "# Repo\n\n## Objective\nShip it.\n\n## Scope\nOnly this repo.\n\n## Rules\nDo not touch deploy.\n\n## Validation\nRun pytest.\n\n## Deliverables\nLeave a handoff.\n",
        encoding="utf-8",
    )
    (tmp_path / "AGENTS.md").write_text("# Legacy\n\n## Objective\nOld\n", encoding="utf-8")

    result = runner.invoke(app, ["source-audit", str(tmp_path), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["source_format"] == "agentkit-source"
    assert payload["used_fallback"] is False
    assert payload["readiness"]["ready_for_contract"] is True


def test_source_audit_reports_missing_sections_and_ambiguity(tmp_path):
    (tmp_path / "AGENTS.md").write_text(
        "# Repo\n\n## Objective\nMaybe improve things.\n\n## Rules\nTODO: add real rules.\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["source-audit", str(tmp_path), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    codes = {item["code"] for item in payload["findings"]}
    assert "legacy_fallback" in codes
    assert "missing_scope" in codes
    assert "missing_validation" in codes
    assert "missing_deliverables" in codes
    assert "soft_language" in codes
    assert "tbd" in codes
    assert payload["readiness"]["ready_for_contract"] is False


def test_source_audit_detects_contradictory_guidance(tmp_path):
    (tmp_path / ".agentkit").mkdir()
    (tmp_path / ".agentkit" / "source.md").write_text(
        "# Repo\n\n## Objective\nShip it.\n\n## Scope\nOnly this repo.\n\n## Rules\n- Do run tests before commit\n- Do not run tests before commit\n\n## Validation\nRun pytest.\n\n## Deliverables\nLeave a handoff.\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["source-audit", str(tmp_path), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    contradiction = [item for item in payload["findings"] if item["code"] == "contradiction"]
    assert contradiction


def test_source_audit_can_write_markdown_output(tmp_path):
    (tmp_path / ".agentkit").mkdir()
    (tmp_path / ".agentkit" / "source.md").write_text(
        "# Repo\n\n## Objective\nShip it.\n\n## Scope\nOnly this repo.\n\n## Rules\nDo not touch deploy.\n\n## Validation\nRun pytest.\n\n## Deliverables\nLeave a handoff.\n",
        encoding="utf-8",
    )
    output = tmp_path / "audit.md"

    result = runner.invoke(app, ["source-audit", str(tmp_path), "--format", "markdown", "--output", str(output)])

    assert result.exit_code == 0, result.output
    text = output.read_text(encoding="utf-8")
    assert "# Source audit" in text
    assert "## Contract readiness" in text


def test_source_audit_help_lists_command():
    result = runner.invoke(app, ["source-audit", "--help"])
    assert result.exit_code == 0
    assert "Audit canonical source structure" in result.output
