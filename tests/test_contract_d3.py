from __future__ import annotations

from pathlib import Path

from agentkit_cli.contracts import ContractEngine


def test_contract_engine_generates_useful_default_deliverables(tmp_path):
    engine = ContractEngine()

    spec = engine.build_spec(tmp_path, "Add contract workflow")

    assert len(spec.deliverables) >= 4
    assert any("Implement the objective" in item for item in spec.deliverables)
    assert any("docs" in item.lower() for item in spec.deliverables)


def test_contract_engine_marks_missing_source_and_uses_repo_boundaries(tmp_path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "docs").mkdir()
    engine = ContractEngine()

    spec = engine.build_spec(tmp_path, "Add contract workflow")
    rendered = engine.render_markdown(spec)

    assert spec.source_context.missing is True
    assert "Canonical source: not found" in rendered
    assert "- tests" in rendered
    assert "- docs" in rendered


def test_contract_engine_infers_commands_from_pyproject_without_guessing(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname='repo-soul'\nversion='0.1.0'\n[tool.pytest.ini_options]\naddopts='-q'\n",
        encoding="utf-8",
    )
    engine = ContractEngine()

    spec = engine.build_spec(tmp_path, "Add contract workflow")

    assert "uv run pytest -q" in spec.repo_hints.command_hints
    assert "Python project metadata present in pyproject.toml" in spec.repo_hints.context_notes


def test_contract_write_contract_creates_requested_output_path(tmp_path):
    engine = ContractEngine()
    spec = engine.build_spec(tmp_path, "Add contract workflow", output_path=tmp_path / "nested" / "contract.md")

    Path(spec.output_path).parent.mkdir(parents=True, exist_ok=True)
    written = engine.write_contract(spec)

    assert written == tmp_path / "nested" / "contract.md"
    assert written.exists()
