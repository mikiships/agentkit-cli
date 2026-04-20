from __future__ import annotations

import json
from pathlib import Path

from agentkit_cli.clarify import ClarifyEngine


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


def test_clarify_engine_is_deterministic_and_ordered(tmp_path):
    project = _make_repo(tmp_path)
    result = ClarifyEngine().build(project, target="codex")

    assert result.schema_version == "agentkit.clarify.v1"
    assert result.execution_recommendation == "pause"
    assert result.blocking_questions[0].code == "missing_contract_artifact"
    assert [item.priority for item in result.blocking_questions] == sorted(item.priority for item in result.blocking_questions)
    payload = json.loads(result.to_json())
    assert payload["execution_recommendation"] == "pause"
    assert payload["source_taskpack"]["target"] == "codex"
