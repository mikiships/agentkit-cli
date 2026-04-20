from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agentkit_cli.main import app

runner = CliRunner()


def _make_repo(tmp_path: Path) -> Path:
    project = tmp_path / "demo-repo"
    (project / ".agentkit").mkdir(parents=True)
    (project / "src").mkdir()
    (project / "tests").mkdir()
    (project / ".agentkit" / "source.md").write_text(
        "# Demo Repo\n\n"
        "## Objective\nShip a deterministic clarify workflow.\n\n"
        "## Scope & Boundaries\nWork only inside this repo.\n\n"
        "## Rules\n- Keep output deterministic.\n\n"
        "## Validation\nRun pytest.\n\n"
        "## Deliverables\nLeave a portable clarify artifact.\n",
        encoding="utf-8",
    )
    (project / "pyproject.toml").write_text(
        "[project]\nname='demo-repo'\nversion='0.1.0'\n\n[project.scripts]\ndemo='src.main:main'\n",
        encoding="utf-8",
    )
    (project / "src" / "main.py").write_text("def main():\n    return 'ok'\n", encoding="utf-8")
    (project / "tests" / "test_main.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    return project


def test_clarify_command_supports_json_and_output_dir(tmp_path):
    project = _make_repo(tmp_path)
    output_dir = tmp_path / "clarify-packet"

    result = runner.invoke(app, ["clarify", str(project), "--target", "claude-code", "--json", "--output-dir", str(output_dir)])

    assert result.exit_code == 0, result.output
    payload = json.loads("\n".join(result.output.splitlines()[1:]))
    assert payload["schema_version"] == "agentkit.clarify.v1"
    assert payload["source_taskpack"]["target"] == "claude-code"
    assert (output_dir / "clarify.md").exists()
    assert (output_dir / "clarify.json").exists()


def test_clarify_command_markdown_contains_required_sections(tmp_path):
    project = _make_repo(tmp_path)
    contract_path = project / "all-day-build-contract-demo.md"
    contract_path.write_text("# Demo contract\n\n- Keep output deterministic.\n", encoding="utf-8")

    result = runner.invoke(app, ["clarify", str(project)])

    assert result.exit_code == 0, result.output
    assert "## Upstream status" in result.output
    assert "## Blocking questions" in result.output
    assert "## Follow-up questions" in result.output
    assert "## Assumptions" in result.output
    assert "## Contradictions" in result.output
