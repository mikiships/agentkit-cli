from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from agentkit_cli.improve_engine import ImproveEngine
from agentkit_cli.main import app
import json

from agentkit_cli.models import OptimizeResult, OptimizeStats

runner = CliRunner()


def _opt_result(path: Path, *, no_op: bool = False) -> OptimizeResult:
    text = "# Project\n\nold\n" if no_op else "# Project\n\nnew\n"
    return OptimizeResult(
        source_file=str(path),
        original_text="# Project\n\nold\n",
        optimized_text=text,
        original_stats=OptimizeStats(lines=3, estimated_tokens=4),
        optimized_stats=OptimizeStats(lines=3, estimated_tokens=4 if no_op else 3),
        no_op=no_op,
    )


@patch("agentkit_cli.improve_engine.OptimizeEngine")
@patch("agentkit_cli.improve_engine._run_harden", return_value=0)
@patch("agentkit_cli.improve_engine._run_agentmd_generate", return_value=False)
@patch("agentkit_cli.improve_engine._get_redteam_score", return_value=90.0)
@patch("agentkit_cli.improve_engine._get_score", side_effect=[82.0, 82.0])
def test_improve_engine_can_apply_optimize(
    mock_score, mock_redteam, mock_generate, mock_harden, mock_optimize, tmp_path: Path
):
    path = tmp_path / "CLAUDE.md"
    path.write_text("# Project\n\nold\n", encoding="utf-8")
    mock_optimize.return_value.optimize.return_value = _opt_result(path)

    plan = ImproveEngine().run(str(tmp_path), optimize_context=True)

    assert "new" in path.read_text(encoding="utf-8")
    assert any("Optimized CLAUDE.md" in action for action in plan.actions_taken)


@patch("agentkit_cli.improve_engine.ImproveEngine")
def test_improve_cli_forwards_optimize_context(mock_engine, tmp_path: Path):
    mock_engine.return_value.run.return_value.baseline_score = 80.0
    mock_engine.return_value.run.return_value.final_score = 80.0
    mock_engine.return_value.run.return_value.delta = 0.0
    mock_engine.return_value.run.return_value.actions_taken = []
    mock_engine.return_value.run.return_value.actions_skipped = []

    result = runner.invoke(app, ["improve", str(tmp_path), "--optimize-context"])

    assert result.exit_code == 0
    assert mock_engine.return_value.run.call_args.kwargs["optimize_context"] is True


@patch("agentkit_cli.improve_engine.OptimizeEngine")
@patch("agentkit_cli.improve_engine._run_harden", return_value=0)
@patch("agentkit_cli.improve_engine._run_agentmd_generate", return_value=False)
@patch("agentkit_cli.improve_engine._get_redteam_score", return_value=90.0)
@patch("agentkit_cli.improve_engine._get_score", side_effect=[82.0, 82.0])
def test_improve_engine_surfaces_optimize_failures_without_aborting(
    mock_score, mock_redteam, mock_generate, mock_harden, mock_optimize, tmp_path: Path
):
    (tmp_path / "CLAUDE.md").write_text("# Project\n\nold\n", encoding="utf-8")
    mock_optimize.return_value.optimize.side_effect = RuntimeError("optimizer exploded")

    plan = ImproveEngine().run(str(tmp_path), optimize_context=True)

    assert any("context optimization failed (optimizer exploded)" == item for item in plan.actions_skipped)
    assert plan.final_score == 82.0


@patch("agentkit_cli.commands.run_cmd.is_installed", return_value=False)
@patch("agentkit_cli.improve_engine.ImproveEngine")
def test_run_cli_forwards_improve_optimize_context(mock_engine, mock_installed, tmp_path: Path):
    mock_engine.return_value.run.return_value.baseline_score = 60.0
    mock_engine.return_value.run.return_value.final_score = 70.0
    mock_engine.return_value.run.return_value.delta = 10.0
    mock_engine.return_value.run.return_value.actions_taken = ["Optimized CLAUDE.md (-2 lines, -5 tokens)"]
    mock_engine.return_value.run.return_value.actions_skipped = []

    result = runner.invoke(app, ["run", "--path", str(tmp_path), "--improve", "--improve-optimize-context", "--json"])

    assert result.exit_code == 0
    assert mock_engine.return_value.run.call_args.kwargs["optimize_context"] is True
    payload = json.loads(result.output[result.output.find("{") : result.output.rfind("}") + 1])
    assert payload["improvement"]["delta"] == 10.0
