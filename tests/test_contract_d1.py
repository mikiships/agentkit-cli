from __future__ import annotations

from agentkit_cli.contracts import ContractEngine, slugify


def test_contract_engine_uses_dedicated_source_when_present(tmp_path):
    dedicated = tmp_path / ".agentkit" / "source.md"
    dedicated.parent.mkdir()
    dedicated.write_text(
        "# Repo Soul\n\n## Commands\nuv run pytest -q\n",
        encoding="utf-8",
    )
    engine = ContractEngine()

    spec = engine.build_spec(tmp_path, "Ship contract generator")
    rendered = engine.render_markdown(spec)

    assert spec.source_context.format == "agentkit-source"
    assert spec.source_context.path == str(dedicated)
    assert "Canonical source path" in rendered
    assert "`uv run pytest -q`" in rendered


def test_contract_engine_falls_back_to_legacy_source_file(tmp_path):
    agents = tmp_path / "AGENTS.md"
    agents.write_text("# Repo Soul\n\n## Commands\npython3 -m pytest tests/ -x\n", encoding="utf-8")
    engine = ContractEngine()

    spec = engine.build_spec(tmp_path, "Harden release flow")

    assert spec.source_context.format == "agents-md"
    assert spec.source_context.path == str(agents)
    assert any("python3 -m pytest tests/ -x" in hint for hint in spec.repo_hints.command_hints)


def test_contract_engine_supports_explicit_sections_and_deterministic_render(tmp_path):
    engine = ContractEngine()
    spec = engine.build_spec(
        tmp_path,
        "Add source-aware contract generation",
        deliverables=["Build the engine", "Add tests"],
        test_requirements=["Run unit tests", "Run integration tests"],
    )

    rendered_one = engine.render_markdown(spec)
    rendered_two = engine.render_markdown(spec)

    assert rendered_one == rendered_two
    assert "- [ ] Build the engine" in rendered_one
    assert "- [ ] Run integration tests" in rendered_one
    assert "## 7. Stop Conditions" in rendered_one


def test_slugify_is_stable_for_default_output_names():
    assert slugify("Build `agentkit contract` feature!") == "build-agentkit-contract-feature"
