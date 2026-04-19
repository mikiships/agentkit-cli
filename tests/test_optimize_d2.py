from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.models import (
    OptimizationAction,
    OptimizeFinding,
    OptimizeResult,
    OptimizeStats,
    OptimizeSweepResult,
    OptimizeSweepSummary,
)

runner = CliRunner()


def _result(path: Path) -> OptimizeResult:
    return OptimizeResult(
        source_file=str(path),
        original_text="# Project\n\nOld\n",
        optimized_text="# Project\n\nNew\n",
        original_stats=OptimizeStats(lines=3, estimated_tokens=4),
        optimized_stats=OptimizeStats(lines=3, estimated_tokens=3),
        findings=[OptimizeFinding(kind="bloat", severity="medium", message="Repeated lines")],
        actions=[OptimizationAction(kind="compress-section", description="Compressed workflow", lines_affected=5)],
        preserved_sections=["Project"],
        protected_sections=["Project"],
        removed_bloat=["Workflow"],
        warnings=["medium: Repeated lines"],
        no_op=False,
    )


def _sweep(root: Path) -> OptimizeSweepResult:
    item = _result(root / "CLAUDE.md")
    noop = OptimizeResult(
        source_file=str(root / "pkg" / "AGENTS.md"),
        original_text="# Agents\n",
        optimized_text="# Agents\n",
        original_stats=OptimizeStats(lines=1, estimated_tokens=2),
        optimized_stats=OptimizeStats(lines=1, estimated_tokens=2),
        preserved_sections=["Agents"],
        protected_sections=["Agents"],
        no_op=True,
    )
    return OptimizeSweepResult(
        root=str(root),
        results=[item, noop],
        summary=OptimizeSweepSummary(
            total_files=2,
            rewritable_files=1,
            noop_files=1,
            total_line_delta=item.line_delta + noop.line_delta,
            total_token_delta=item.token_delta + noop.token_delta,
            protected_signal_files=2,
            warnings_count=1,
        ),
    )


def test_optimize_help():
    result = runner.invoke(app, ["optimize", "--help"])
    assert result.exit_code == 0
    assert "--apply" in result.output
    assert "--all" in result.output
    assert "--check" in result.output


@patch("agentkit_cli.commands.optimize_cmd.OptimizeEngine")
def test_optimize_dry_run_text_output(mock_engine, tmp_path: Path):
    target = tmp_path / "CLAUDE.md"
    mock_engine.return_value.optimize.return_value = _result(target)
    result = runner.invoke(app, ["optimize", "--path", str(tmp_path)])
    assert result.exit_code == 0
    assert "Lines: 3 -> 3" in result.output
    assert "Diff:" in result.output


@patch("agentkit_cli.commands.optimize_cmd.OptimizeEngine")
def test_optimize_json_output(mock_engine, tmp_path: Path):
    target = tmp_path / "CLAUDE.md"
    mock_engine.return_value.optimize.return_value = _result(target)
    result = runner.invoke(app, ["optimize", "--path", str(tmp_path), "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["source_file"].endswith("CLAUDE.md")
    assert payload["applied"] is False


@patch("agentkit_cli.commands.optimize_cmd.OptimizeEngine")
def test_optimize_apply_overwrites_file(mock_engine, tmp_path: Path):
    target = tmp_path / "CLAUDE.md"
    target.write_text("before", encoding="utf-8")
    mock_engine.return_value.optimize.return_value = _result(target)
    result = runner.invoke(app, ["optimize", "--path", str(tmp_path), "--apply"])
    assert result.exit_code == 0
    assert target.read_text(encoding="utf-8") == "# Project\n\nNew\n"


@patch("agentkit_cli.commands.optimize_cmd.OptimizeEngine")
def test_optimize_apply_skips_noop_rewrite(mock_engine, tmp_path: Path):
    target = tmp_path / "CLAUDE.md"
    original = "# Project\n\nStable\n"
    target.write_text(original, encoding="utf-8")
    noop_result = OptimizeResult(
        source_file=str(target),
        original_text=original,
        optimized_text=original,
        original_stats=OptimizeStats(lines=3, estimated_tokens=3),
        optimized_stats=OptimizeStats(lines=3, estimated_tokens=3),
        preserved_sections=["Project"],
        protected_sections=["Project"],
        no_op=True,
    )
    mock_engine.return_value.optimize.return_value = noop_result

    result = runner.invoke(app, ["optimize", "--path", str(tmp_path), "--apply"])

    assert result.exit_code == 0
    assert "No rewrite needed" in result.output
    assert target.read_text(encoding="utf-8") == original


@patch("agentkit_cli.commands.optimize_cmd.OptimizeEngine")
def test_optimize_explicit_file_forwarded(mock_engine, tmp_path: Path):
    target = tmp_path / "AGENTS.md"
    mock_engine.return_value.optimize.return_value = _result(target)
    runner.invoke(app, ["optimize", "--path", str(tmp_path), "--file", "AGENTS.md"])
    assert mock_engine.return_value.optimize.call_args.kwargs["file"] == Path("AGENTS.md")


@patch("agentkit_cli.commands.optimize_cmd.OptimizeEngine")
def test_optimize_all_uses_sweep_and_check_exit_code(mock_engine, tmp_path: Path):
    mock_engine.return_value.optimize_sweep.return_value = _sweep(tmp_path)

    result = runner.invoke(app, ["optimize", "--path", str(tmp_path), "--all", "--check"])

    assert result.exit_code == 1
    assert "Files: 2 total, 1 rewritable, 1 no-op" in result.output


@patch("agentkit_cli.commands.optimize_cmd.OptimizeEngine")
def test_optimize_all_apply_writes_only_rewritable_files(mock_engine, tmp_path: Path):
    (tmp_path / "pkg").mkdir()
    target = tmp_path / "CLAUDE.md"
    target.write_text("before", encoding="utf-8")
    noop = tmp_path / "pkg" / "AGENTS.md"
    noop.write_text("# Agents\n", encoding="utf-8")
    mock_engine.return_value.optimize_sweep.return_value = _sweep(tmp_path)

    result = runner.invoke(app, ["optimize", "--path", str(tmp_path), "--all", "--apply", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["applied_files"] == 1
    assert target.read_text(encoding="utf-8") == "# Project\n\nNew\n"
    assert noop.read_text(encoding="utf-8") == "# Agents\n"
