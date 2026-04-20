from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.taskpack import TaskpackEngine

runner = CliRunner()


def _make_repo(tmp_path: Path) -> Path:
    project = tmp_path / "demo-repo"
    (project / ".agentkit").mkdir(parents=True)
    (project / "src").mkdir()
    (project / "tests").mkdir()
    (project / ".agentkit" / "source.md").write_text(
        "# Demo Repo\n\n"
        "## Objective\nShip a deterministic taskpack.\n\n"
        "## Scope & Boundaries\nWork only inside this repo.\n\n"
        "## Rules\n- Keep output deterministic.\n\n"
        "## Validation\nRun pytest.\n\n"
        "## Deliverables\nLeave a portable taskpack artifact.\n",
        encoding="utf-8",
    )
    (project / "pyproject.toml").write_text(
        "[project]\nname='demo-repo'\nversion='0.1.0'\n\n[project.scripts]\ndemo='src.main:main'\n",
        encoding="utf-8",
    )
    (project / "src" / "main.py").write_text("def main():\n    return 'ok'\n", encoding="utf-8")
    (project / "tests" / "test_main.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    return project


def test_taskpack_engine_assembles_deterministic_sections(tmp_path):
    project = _make_repo(tmp_path)
    pack = TaskpackEngine().build(project, target="codex")

    assert pack.schema_version == "agentkit.taskpack.v1"
    assert pack.target == "codex"
    assert [section.title for section in pack.durable_context] == [
        "Source context",
        "Architecture map",
        "Execution contract",
    ]
    assert pack.execution.runner == "codex exec --full-auto"
    assert pack.source_bundle["schema_version"] == "agentkit.bundle.v1"


def test_taskpack_engine_surfaces_missing_contract_gap(tmp_path):
    project = _make_repo(tmp_path)
    pack = TaskpackEngine().build(project)

    assert any(gap.code == "missing_contract_artifact" for gap in pack.gaps)
    assert pack.execution.target == "generic"


def test_taskpack_command_json_is_deterministic(tmp_path):
    project = _make_repo(tmp_path)

    result = runner.invoke(app, ["taskpack", str(project), "--target", "claude-code", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["schema_version"] == "agentkit.taskpack.v1"
    assert payload["target"] == "claude-code"
    assert payload["execution"]["runner"] == "claude --print --permission-mode bypassPermissions"


def test_taskpack_command_writes_packet_directory(tmp_path):
    project = _make_repo(tmp_path)
    output_dir = tmp_path / "packet"

    result = runner.invoke(app, ["taskpack", str(project), "--output-dir", str(output_dir)])

    assert result.exit_code == 0, result.output
    assert (output_dir / "taskpack.md").exists()
    assert (output_dir / "taskpack.json").exists()
    assert "Wrote taskpack directory" in result.output


def test_source_to_taskpack_workflow(tmp_path):
    project = _make_repo(tmp_path)
    contract = runner.invoke(
        app,
        [
            "contract",
            "Ship the next increment",
            "--path",
            str(project),
            "--map",
            str(project),
        ],
    )
    assert contract.exit_code == 0, contract.output

    bundle = runner.invoke(app, ["bundle", str(project)])
    assert bundle.exit_code == 0, bundle.output

    taskpack = runner.invoke(app, ["taskpack", str(project), "--json"])
    assert taskpack.exit_code == 0, taskpack.output
    payload = json.loads(taskpack.output)
    assert payload["source_bundle"]["contract"]["missing"] is False
    assert payload["gaps"] == []


def test_taskpack_help():
    result = runner.invoke(app, ["taskpack", "--help"])
    assert result.exit_code == 0
    assert "--target" in result.output
    assert "--output-dir" in result.output
