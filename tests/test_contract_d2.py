from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agentkit_cli.main import app

runner = CliRunner()
FIXTURES = Path(__file__).parent / "fixtures" / "map"


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


def test_contract_command_can_use_live_map_target(tmp_path):
    result = runner.invoke(
        app,
        [
            "contract",
            "Extend repo-understanding handoff",
            "--path",
            str(tmp_path),
            "--map",
            str(FIXTURES / "basic_repo"),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["map_context"]["summary"]["name"] == "basic_repo"
    assert any(item["name"] == "python-tooling" for item in payload["map_context"]["subsystems"])


def test_contract_command_can_use_saved_map_json(tmp_path):
    map_json = tmp_path / "repo-map.json"
    map_payload = {
        "target": "fixtures/basic_repo",
        "summary": {
            "name": "basic_repo",
            "root": "fixtures/basic_repo",
            "total_files": 7,
            "total_dirs": 3,
            "primary_language": "Python",
        },
        "subsystems": [
            {"name": "python-tooling", "path": "src", "why": "Primary Python source tree"},
        ],
        "hints": [
            {"kind": "next_task", "severity": "info", "title": "Explore src", "detail": "Start in src/main.py and src/service.py."},
        ],
        "contract_handoff": {
            "suggested_artifact": "map.json",
            "summary_lines": ["Focus the contract on src."],
            "contract_prompt": "Use the repo map as the explorer artifact.",
        },
    }
    map_json.write_text(json.dumps(map_payload), encoding="utf-8")

    output = tmp_path / "contract.md"
    result = runner.invoke(
        app,
        [
            "contract",
            "Extend repo-understanding handoff",
            "--path",
            str(tmp_path),
            "--map",
            str(map_json),
            "--output",
            str(output),
        ],
    )

    assert result.exit_code == 0, result.output
    text = output.read_text(encoding="utf-8")
    assert "## 3. Explorer Artifact" in text
    assert "`src` (python-tooling): Primary Python source tree" in text
    assert "Use the repo map as the explorer artifact." in text
