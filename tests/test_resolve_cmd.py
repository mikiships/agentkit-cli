from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agentkit_cli.main import app

runner = CliRunner()


def _make_repo(tmp_path: Path) -> tuple[Path, Path]:
    project = tmp_path / "demo-repo"
    (project / ".agentkit").mkdir(parents=True)
    (project / "src").mkdir()
    (project / "tests").mkdir()
    (project / ".agentkit" / "source.md").write_text(
        "# Demo Repo\n\n"
        "## Objective\nShip a deterministic resolve workflow.\n\n"
        "## Scope & Boundaries\nWork only inside this repo.\n\n"
        "## Rules\n- Keep output deterministic.\n\n"
        "## Validation\nRun pytest.\n\n"
        "## Deliverables\nLeave markdown and JSON handoff output.\n",
        encoding="utf-8",
    )
    (project / "pyproject.toml").write_text(
        "[project]\nname='demo-repo'\nversion='0.1.0'\n\n[project.scripts]\ndemo='src.main:main'\n",
        encoding="utf-8",
    )
    (project / "src" / "main.py").write_text("def main():\n    return 'ok'\n", encoding="utf-8")
    (project / "tests" / "test_main.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    (project / "all-day-build-contract-demo.md").write_text("# Demo contract\n\n- Keep output deterministic.\n", encoding="utf-8")
    answers = tmp_path / "answers.json"
    answers.write_text(
        json.dumps(
            {
                "answers": [
                    {"code": "execution_checklist_review", "status": "resolved", "answer": "The mapped checks are enough."}
                ],
                "assumptions": {
                    "primary_language": {"status": "confirmed", "reason": "Python remains the implementation surface."},
                    "runner_notes": {"status": "confirmed", "reason": "Default runner notes are acceptable."},
                },
            }
        ),
        encoding="utf-8",
    )
    return project, answers


def test_resolve_command_supports_json_and_output_dir(tmp_path):
    project, answers = _make_repo(tmp_path)
    output_dir = tmp_path / "resolve-packet"

    result = runner.invoke(app, ["resolve", str(project), "--answers", str(answers), "--target", "codex", "--json", "--output-dir", str(output_dir)])

    assert result.exit_code == 0, result.output
    payload = json.loads("\n".join(result.output.splitlines()[1:]))
    assert payload["schema_version"] == "agentkit.resolve.v1"
    assert payload["source_clarify"]["source_taskpack"]["target"] == "codex"
    assert (output_dir / "resolve.md").exists()
    assert (output_dir / "resolve.json").exists()


def test_resolve_command_markdown_contains_required_sections(tmp_path):
    project, answers = _make_repo(tmp_path)

    result = runner.invoke(app, ["resolve", str(project), "--answers", str(answers)])

    assert result.exit_code == 0, result.output
    assert "## Summary" in result.output
    assert "## Resolved questions" in result.output
    assert "## Remaining blockers" in result.output
    assert "## Remaining follow-ups" in result.output
    assert "## Confirmed assumptions" in result.output


def test_resolve_command_requires_answers_file(tmp_path):
    project, _answers = _make_repo(tmp_path)

    result = runner.invoke(app, ["resolve", str(project), "--answers", str(tmp_path / 'missing.json')])

    assert result.exit_code != 0
    assert "Answers file not found" in result.output
