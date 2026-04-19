from __future__ import annotations

import json

from typer.testing import CliRunner

from agentkit_cli.main import app

runner = CliRunner()


def test_contract_command_writes_default_output_file(tmp_path):
    (tmp_path / "AGENTS.md").write_text("# Repo Soul\n\n## Commands\nuv run pytest -q\n", encoding="utf-8")

    result = runner.invoke(app, ["contract", "Ship contract generator", "--path", str(tmp_path)])

    assert result.exit_code == 0
    output_path = tmp_path / "all-day-build-contract-ship-contract-generator.md"
    assert output_path.exists()
    assert "## 4. Deliverables" in output_path.read_text(encoding="utf-8")


def test_contract_command_supports_custom_output_title_and_repeatable_flags(tmp_path):
    target = tmp_path / "custom-contract.md"

    result = runner.invoke(
        app,
        [
            "contract",
            "Ship contract generator",
            "--path",
            str(tmp_path),
            "--output",
            str(target),
            "--title",
            "My Contract",
            "--deliverable",
            "Build the engine",
            "--deliverable",
            "Wire the CLI",
            "--test-requirement",
            "Run focused tests",
        ],
    )

    assert result.exit_code == 0
    content = target.read_text(encoding="utf-8")
    assert content.startswith("# My Contract")
    assert "- [ ] Build the engine" in content
    assert "- [ ] Wire the CLI" in content
    assert "- [ ] Run focused tests" in content


def test_contract_command_json_output_is_deterministic(tmp_path):
    result = runner.invoke(app, ["contract", "Ship contract generator", "--path", str(tmp_path), "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["objective"] == "Ship contract generator"
    assert payload["output_path"].endswith("all-day-build-contract-ship-contract-generator.md")
    assert isinstance(payload["deliverables"], list)
    assert isinstance(payload["test_requirements"], list)


def test_contract_command_refuses_to_overwrite_existing_output(tmp_path):
    output_path = tmp_path / "all-day-build-contract-ship-contract-generator.md"
    output_path.write_text("existing\n", encoding="utf-8")

    result = runner.invoke(app, ["contract", "Ship contract generator", "--path", str(tmp_path)])

    assert result.exit_code == 1
    assert "Refusing to overwrite existing contract" in result.output
