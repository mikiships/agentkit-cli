from __future__ import annotations

from pathlib import Path

from agentkit_cli.spec_engine import SpecEngine


def _write_repo(
    project: Path,
    *,
    concrete_next_closed: bool = False,
    post_closeout_closed: bool = False,
    adjacent_next_closed: bool = False,
    adjacent_closeout_closed: bool = False,
) -> None:
    (project / ".agentkit").mkdir(parents=True)
    (project / "agentkit_cli" / "commands").mkdir(parents=True)
    (project / "src").mkdir()
    (project / "tests").mkdir()
    objective = "Teach the flagship self-spec flow to suppress replay of the already-completed `flagship-concrete-next-step` lane and advance to one fresh adjacent recommendation with an updated flagship contract seed."
    if post_closeout_closed:
        objective = "Teach the flagship self-spec flow to recognize when `flagship-post-closeout-advance` is already closed out in current repo truth, stop replaying that lane, and promote the next honest flagship recommendation from current shipped or local-release-ready evidence."
    if adjacent_next_closed:
        objective = "Teach the flagship self-spec flow to recognize when `flagship-adjacent-next-step` is already closed out in current repo truth, stop replaying that lane, and keep the flagship planner advancing with one fresh flagship recommendation from shipped or local-release-ready evidence."
    if adjacent_closeout_closed:
        objective = "Teach the self-spec flow to advance past the generic `subsystem-next-step` fallback for `agentkit_cli`, so the flagship repo-understanding workflow emits one concrete bounded next recommendation inside the `agentkit_cli` subsystem instead of stopping at the generic scoped-surface handoff."
    (project / ".agentkit" / "source.md").write_text(
        "# Demo Repo\n\n"
        "## Objective\n"
        f"{objective}\n\n"
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
    changelog = (
        "# Changelog\n\n"
        "## [0.4.0] - 2026-04-21\n\n"
        "- Refreshed the flagship source objective so `agentkit spec` targets a concrete adjacent build after shipped-truth sync.\n"
    )
    build_report = (
        "# BUILD-REPORT.md — demo-repo v0.5.0 spec shipped truth sync\n\n"
        "Status: SHIPPED\n"
    )
    final_summary = (
        "# Final Summary — demo-repo v0.5.0 spec shipped truth sync\n\n"
        "Status: SHIPPED\n"
    )
    progress_log = (
        "# Progress Log — demo-repo v0.5.0 spec shipped truth sync\n\n"
        "Status: RELEASE-READY (LOCAL-ONLY)\n"
        "Date: 2026-04-21\n\n"
        "- Introduced a `shipped-truth-sync` recommendation after shipped adjacent grounding.\n"
        "- Verified `agentkit spec . --json` no longer repeats shipped adjacent grounding work.\n"
    )
    if concrete_next_closed:
        progress_log = (
            "# Progress Log — demo-repo v0.6.0 flagship post closeout advance\n\n"
            "Status: RELEASE-READY (LOCAL-ONLY)\n"
            "Date: 2026-04-21\n\n"
            "- Introduced a `flagship-concrete-next-step` recommendation after shipped-truth sync.\n"
            "- Verified `agentkit spec . --json` no longer falls back to the generic subsystem recommendation.\n"
        )
    if post_closeout_closed:
        changelog = (
            "# Changelog\n\n"
            "## [0.7.0] - 2026-04-21\n\n"
            "- Taught the flagship `agentkit spec` flow to suppress replay of the closed `flagship-post-closeout-advance` lane.\n"
            "- Kept the supported repo-understanding lane at `source -> audit -> map -> spec -> contract`.\n"
        )
        build_report = (
            "# BUILD-REPORT.md — demo-repo v0.7.0 flagship post-closeout advance\n\n"
            "Status: SHIPPED\n"
            "- Closed the `flagship-post-closeout-advance` lane and verified the planner should advance again.\n"
        )
        final_summary = (
            "# Final Summary — demo-repo v0.7.0 flagship post-closeout advance\n\n"
            "Status: SHIPPED\n"
            "- The flagship planner already completed the `flagship-post-closeout-advance` lane.\n"
        )
        progress_log = (
            "# Progress Log — demo-repo v0.8.0 flagship adjacent next step\n\n"
            "Status: IN PROGRESS\n"
            "Date: 2026-04-21\n\n"
            "- The shipped flagship repo still lets `agentkit spec . --json` replay `flagship-post-closeout-advance`.\n"
            "- This lane exists to promote the next honest flagship recommendation from current repo truth.\n"
        )
    if adjacent_next_closed:
        changelog = (
            "# Changelog\n\n"
            "## [0.8.0] - 2026-04-21\n\n"
            "- Taught the flagship `agentkit spec` flow to suppress replay of the closed `flagship-adjacent-next-step` lane.\n"
            "- Kept the supported repo-understanding lane at `source -> audit -> map -> spec -> contract`.\n"
        )
        build_report = (
            "# BUILD-REPORT.md — demo-repo v0.8.0 flagship adjacent next step\n\n"
            "Status: SHIPPED\n"
            "- Closed the `flagship-adjacent-next-step` lane and verified the planner should advance again.\n"
        )
        final_summary = (
            "# Final Summary — demo-repo v0.8.0 flagship adjacent next step\n\n"
            "Status: SHIPPED\n"
            "- The flagship planner already completed the `flagship-adjacent-next-step` lane.\n"
        )
        progress_log = (
            "# Progress Log — demo-repo v0.9.0 flagship adjacent closeout advance\n\n"
            "Status: IN PROGRESS\n"
            "Date: 2026-04-21\n\n"
            "- The shipped flagship repo still lets `agentkit spec . --json` replay `flagship-adjacent-next-step`.\n"
            "- This lane exists to keep the flagship planner advancing from current repo truth.\n"
        )
    if adjacent_closeout_closed:
        changelog = (
            "# Changelog\n\n"
            "## [0.9.0] - 2026-04-22\n\n"
            "- Taught the flagship `agentkit spec` flow to suppress replay of the closed `flagship-adjacent-closeout-advance` lane and emit one bounded `agentkit_cli` next step.\n"
            "- Kept the supported repo-understanding lane at `source -> audit -> map -> spec -> contract`.\n"
        )
        build_report = (
            "# BUILD-REPORT.md — demo-repo v0.9.0 flagship adjacent closeout advance\n\n"
            "Status: SHIPPED\n"
            "- Closed the `flagship-adjacent-closeout-advance` lane and verified the planner should emit one bounded `agentkit_cli` next step.\n"
        )
        final_summary = (
            "# Final Summary — demo-repo v0.9.0 flagship adjacent closeout advance\n\n"
            "Status: SHIPPED\n"
            "- The flagship planner already completed the `flagship-adjacent-closeout-advance` lane.\n"
        )
        progress_log = (
            "# Progress Log — demo-repo v0.10.0 bounded agentkit next step\n\n"
            "Status: IN PROGRESS\n"
            "Date: 2026-04-22\n\n"
            "- The shipped flagship repo still lets `agentkit spec . --json` fall through to `subsystem-next-step` for `agentkit_cli`.\n"
            "- This lane exists to replace that generic fallback with one bounded `agentkit_cli` recommendation from current repo truth.\n"
        )
    (project / "CHANGELOG.md").write_text(changelog, encoding="utf-8")
    (project / "BUILD-REPORT.md").write_text(build_report, encoding="utf-8")
    (project / "FINAL-SUMMARY.md").write_text(final_summary, encoding="utf-8")
    (project / "progress-log.md").write_text(progress_log, encoding="utf-8")


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


def test_spec_engine_advances_past_closed_flagship_post_closeout_lane(tmp_path):
    project = tmp_path / "demo-repo"
    _write_repo(project, post_closeout_closed=True)

    spec = SpecEngine().build(project)

    assert spec.primary_recommendation is not None
    assert spec.primary_recommendation.kind == "flagship-adjacent-next-step"
    assert spec.primary_recommendation.title == "Emit the next flagship lane after post-closeout advance"
    assert spec.primary_recommendation.contract_seed.title.endswith("flagship adjacent next step")
    assert any("`flagship-post-closeout-advance` increment as done" in item for item in spec.primary_recommendation.evidence)


def test_spec_engine_advances_past_closed_flagship_adjacent_next_lane(tmp_path):
    project = tmp_path / "demo-repo"
    _write_repo(project, adjacent_next_closed=True)

    spec = SpecEngine().build(project)

    assert spec.primary_recommendation is not None
    assert spec.primary_recommendation.kind == "flagship-adjacent-closeout-advance"
    assert spec.primary_recommendation.title == "Advance the flagship planner past the closed adjacent-next-step lane"
    assert spec.primary_recommendation.contract_seed.title.endswith("flagship adjacent closeout advance")
    assert any("`flagship-adjacent-next-step` increment as done" in item for item in spec.primary_recommendation.evidence)


def test_spec_engine_emits_bounded_agentkit_next_step_after_adjacent_closeout(tmp_path):
    project = tmp_path / "demo-repo"
    _write_repo(project, adjacent_closeout_closed=True)

    spec = SpecEngine().build(project)

    assert spec.primary_recommendation is not None
    assert spec.primary_recommendation.kind == "agentkit-cli-bounded-next-step"
    assert spec.primary_recommendation.title == "Emit one bounded `agentkit_cli` next step after adjacent closeout"
    assert spec.primary_recommendation.contract_seed.title.endswith("bounded agentkit next step")
    assert any("`flagship-adjacent-closeout-advance` increment as done" in item for item in spec.primary_recommendation.evidence)
