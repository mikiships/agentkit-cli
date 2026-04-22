from __future__ import annotations

from pathlib import Path

from agentkit_cli.spec_engine import SpecEngine


def _write_repo(project: Path, *, concrete_next_closed: bool = False) -> None:
    (project / ".agentkit").mkdir(parents=True)
    (project / "agentkit_cli" / "commands").mkdir(parents=True)
    (project / "src").mkdir()
    (project / "tests").mkdir()
    (project / ".agentkit" / "source.md").write_text(
        "# Demo Repo\n\n"
        "## Objective\n"
        "Teach the flagship self-spec flow to suppress replay of the already-completed `flagship-concrete-next-step` lane and advance to one fresh adjacent recommendation with an updated flagship contract seed.\n\n"
        "## Scope & Boundaries\nWork only inside this repo.\n\n"
        "## Rules\n- Keep output deterministic.\n\n"
        "## Validation\nRun uv run pytest -q tests/test_spec_engine.py tests/test_spec_cmd.py tests/test_spec_workflow.py\n\n"
        "## Deliverables\nLeave markdown and JSON handoff artifacts.\n",
        encoding="utf-8",
    )
    (project / "agentkit_cli" / "main.py").write_text(
        'from agentkit_cli.commands.spec_cmd import spec_command\n@app.command("spec")\ndef spec():\n    pass\n',
        encoding="utf-8",
    )
    (project / "pyproject.toml").write_text(
        "[project]\nname='demo-repo'\nversion='0.1.0'\n\n[project.scripts]\ndemo='src.main:main'\n",
        encoding="utf-8",
    )
    (project / "src" / "main.py").write_text("def main():\n    return 'ok'\n", encoding="utf-8")
    (project / "tests" / "test_main.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    (project / "README.md").write_text(
        "# Demo Repo\n\n"
        "Supported lane: `source -> audit -> map -> spec -> contract`\n",
        encoding="utf-8",
    )
    (project / "CHANGELOG.md").write_text(
        "# Changelog\n\n"
        "## [0.4.0] - 2026-04-21\n\n"
        "- Refreshed the flagship source objective so `agentkit spec` targets a concrete adjacent build after shipped-truth sync.\n",
        encoding="utf-8",
    )
    (project / "BUILD-REPORT.md").write_text(
        "# BUILD-REPORT.md — demo-repo v0.5.0 spec shipped truth sync\n\n"
        "Status: SHIPPED\n",
        encoding="utf-8",
    )
    (project / "FINAL-SUMMARY.md").write_text(
        "# Final Summary — demo-repo v0.5.0 spec shipped truth sync\n\n"
        "Status: SHIPPED\n",
        encoding="utf-8",
    )
    (project / "progress-log.md").write_text(
        (
            "# Progress Log — demo-repo v0.6.0 flagship post closeout advance\n\n"
            "Status: RELEASE-READY (LOCAL-ONLY)\n"
            "Date: 2026-04-21\n\n"
            "- Introduced a `flagship-concrete-next-step` recommendation after shipped-truth sync.\n"
            "- Verified `agentkit spec . --json` no longer falls back to the generic subsystem recommendation.\n"
        ) if concrete_next_closed else (
            "# Progress Log — demo-repo v0.5.0 spec shipped truth sync\n\n"
            "Status: RELEASE-READY (LOCAL-ONLY)\n"
            "Date: 2026-04-21\n\n"
            "- Introduced a `shipped-truth-sync` recommendation after shipped adjacent grounding.\n"
            "- Verified `agentkit spec . --json` no longer repeats shipped adjacent grounding work.\n"
        ),
        encoding="utf-8",
    )


def test_spec_engine_advances_past_closed_flagship_concrete_next_step_lane(tmp_path):
    project = tmp_path / "demo-repo"
    _write_repo(project, concrete_next_closed=True)

    spec = SpecEngine().build(project)

    assert spec.primary_recommendation is not None
    assert spec.primary_recommendation.kind == "flagship-post-closeout-advance"
    assert spec.primary_recommendation.slug == "flagship-post-closeout-advance"
    assert spec.primary_recommendation.contract_seed.title.endswith("flagship post-closeout advance")
    assert any("`flagship-concrete-next-step` increment as done" in item for item in spec.primary_recommendation.evidence)


def test_spec_engine_advances_past_closed_flagship_concrete_next_lane(tmp_path):
    project = tmp_path / "demo-repo"
    _write_repo(project, concrete_next_closed=True)

    spec = SpecEngine().build(project)

    assert spec.primary_recommendation is not None
    assert spec.primary_recommendation.kind == "flagship-post-closeout-advance"
    assert spec.primary_recommendation.title == "Advance the flagship planner past the closed concrete-next-step lane"
    assert spec.primary_recommendation.contract_seed.title.endswith("flagship post-closeout advance")
    assert any("already record the `flagship-concrete-next-step` increment as done" in item for item in spec.primary_recommendation.evidence)
