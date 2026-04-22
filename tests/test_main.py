"""Tests for main app entry point."""
from __future__ import annotations

import json
from unittest.mock import patch

from typer.testing import CliRunner
from agentkit_cli.main import app

runner = CliRunner()


def test_version_flag():
    """--version prints version."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "1.30.0" in result.output


def test_no_args_shows_help():
    """No arguments shows help text."""
    result = runner.invoke(app, [])
    assert result.exit_code == 0
    assert "init" in result.output or "Usage" in result.output


def test_help_flag():
    """--help works."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "init" in result.output


def test_init_subcommand_help():
    result = runner.invoke(app, ["init", "--help"])
    assert result.exit_code == 0


def test_run_subcommand_help():
    result = runner.invoke(app, ["run", "--help"])
    assert result.exit_code == 0


def test_status_subcommand_help():
    result = runner.invoke(app, ["status", "--help"])
    assert result.exit_code == 0


def test_spec_subcommand_help():
    result = runner.invoke(app, ["spec", "--help"])
    assert result.exit_code == 0


def test_run_release_check_flag_is_forwarded(tmp_path):
    with patch("agentkit_cli.main.run_command") as mock_run:
        result = runner.invoke(app, ["run", "--path", str(tmp_path), "--release-check"])
    assert result.exit_code == 0
    assert mock_run.call_args.kwargs["release_check"] is True


def test_spec_cli_entry_emits_bounded_agentkit_next_step(tmp_path):
    project = tmp_path / "demo-repo"
    (project / ".agentkit").mkdir(parents=True)
    (project / "src").mkdir()
    (project / "tests").mkdir()
    (project / ".agentkit" / "source.md").write_text(
        "# Demo Repo\n\n"
        "## Objective\n"
        "Teach the self-spec flow to advance past the generic `subsystem-next-step` fallback for `agentkit_cli`, so the flagship repo-understanding workflow emits one concrete bounded next recommendation inside the `agentkit_cli` subsystem instead of stopping at the generic scoped-surface handoff.\n\n"
        "## Scope & Boundaries\nWork only inside this repo.\n\n"
        "## Rules\n- Keep output deterministic.\n\n"
        "## Validation\nRun uv run pytest -q tests/test_main.py\n\n"
        "## Deliverables\nLeave markdown and JSON handoff artifacts.\n",
        encoding="utf-8",
    )
    (project / "pyproject.toml").write_text(
        "[project]\nname='demo-repo'\nversion='0.1.0'\n\n[project.scripts]\ndemo='src.main:main'\n",
        encoding="utf-8",
    )
    (project / "src" / "main.py").write_text("def main():\n    return 'ok'\n", encoding="utf-8")
    (project / "tests" / "test_main.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    (project / "README.md").write_text(
        "# Demo Repo\n\nSupported lane: `source -> audit -> map -> spec -> contract`\n",
        encoding="utf-8",
    )
    (project / "CHANGELOG.md").write_text(
        "# Changelog\n\n## [0.9.0] - 2026-04-22\n\n"
        "- Taught the flagship `agentkit spec` flow to suppress replay of the closed `flagship-adjacent-closeout-advance` lane and emit one bounded `agentkit_cli` next step.\n",
        encoding="utf-8",
    )
    (project / "BUILD-REPORT.md").write_text(
        "# BUILD-REPORT.md — demo-repo v0.9.0 flagship adjacent closeout advance\n\nStatus: SHIPPED\n- Closed the `flagship-adjacent-closeout-advance` lane and verified the planner should emit one bounded `agentkit_cli` next step.\n",
        encoding="utf-8",
    )
    (project / "FINAL-SUMMARY.md").write_text(
        "# Final Summary — demo-repo v0.9.0 flagship adjacent closeout advance\n\nStatus: SHIPPED\n- The flagship planner already completed the `flagship-adjacent-closeout-advance` lane.\n",
        encoding="utf-8",
    )
    (project / "progress-log.md").write_text(
        "# Progress Log — demo-repo v0.10.0 bounded agentkit next step\n\n"
        "Status: IN PROGRESS\n"
        "Date: 2026-04-22\n\n"
        "- The shipped flagship repo still lets `agentkit spec . --json` fall through to `subsystem-next-step` for `agentkit_cli`.\n"
        "- This lane exists to replace that generic fallback with one bounded `agentkit_cli` recommendation from current repo truth.\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["spec", str(project), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["primary_recommendation"]["kind"] == "agentkit-cli-bounded-next-step"
