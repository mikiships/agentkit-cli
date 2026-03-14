"""Tests for agentkit sweep command."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from agentkit_cli.analyze import AnalyzeResult
from agentkit_cli.main import app
from agentkit_cli.sweep import resolve_targets, run_sweep

runner = CliRunner()


def _analyze_result(target: str, score: float = 80.0, grade: str = "B") -> AnalyzeResult:
    repo_name = target.split("/")[-1].replace(".", "local")
    return AnalyzeResult(
        target=target,
        repo_name=repo_name,
        composite_score=score,
        grade=grade,
        tools={
            "agentmd": {"tool": "agentmd", "status": "pass", "score": score, "finding": "ok"},
            "agentlint": {"tool": "agentlint", "status": "pass", "score": score, "finding": "ok"},
            "agentreflect": {"tool": "agentreflect", "status": "pass", "score": score, "finding": "ok"},
        },
        generated_context=False,
    )


def test_resolve_targets_dedupes_and_preserves_input_order(tmp_path: Path):
    targets_file = tmp_path / "targets.txt"
    targets_file.write_text("\n".join(["github:psf/requests", "github:pallets/flask", "github:psf/requests"]), encoding="utf-8")

    resolved = resolve_targets(
        ["github:psf/requests", ".", "."],
        targets_file=targets_file,
    )

    assert resolved == ["github:psf/requests", ".", "github:pallets/flask"]


def test_resolve_targets_ignores_blank_lines_and_comments(tmp_path: Path):
    targets_file = tmp_path / "targets.txt"
    targets_file.write_text("# comment\n\n github:psf/requests \n", encoding="utf-8")

    assert resolve_targets([], targets_file=targets_file) == ["github:psf/requests"]


@patch("agentkit_cli.sweep.analyze_target")
def test_run_sweep_isolates_target_failures(mock_analyze):
    mock_analyze.side_effect = [
        _analyze_result("github:psf/requests", score=91.0, grade="A"),
        RuntimeError("clone failed"),
        _analyze_result(".", score=64.0, grade="D"),
    ]

    result = run_sweep(["github:psf/requests", "github:bad/repo", "."])

    assert result.summary_counts() == {
        "total": 3,
        "succeeded": 2,
        "failed": 1,
        "analyzed_with_scores": 2,
    }
    assert [entry.status for entry in result.results] == ["succeeded", "failed", "succeeded"]
    assert result.results[1].error == "clone failed"


@patch("agentkit_cli.commands.sweep_cmd.run_sweep")
def test_sweep_cli_accepts_multiple_targets(mock_run_sweep):
    mock_run_sweep.return_value = run_sweep([])
    result = runner.invoke(app, ["sweep", "github:psf/requests", "github:pallets/flask"])
    assert result.exit_code == 0, result.output
    mock_run_sweep.assert_called_once()
    assert mock_run_sweep.call_args.args[0] == ["github:psf/requests", "github:pallets/flask"]


@patch("agentkit_cli.commands.sweep_cmd.run_sweep")
def test_sweep_cli_supports_targets_file(mock_run_sweep, tmp_path: Path):
    mock_run_sweep.return_value = run_sweep([])
    targets_file = tmp_path / "targets.txt"
    targets_file.write_text("github:psf/requests\n.\n", encoding="utf-8")

    result = runner.invoke(app, ["sweep", "--targets-file", str(targets_file)])

    assert result.exit_code == 0, result.output
    mock_run_sweep.assert_called_once()
    assert mock_run_sweep.call_args.args[0] == ["github:psf/requests", "."]


def test_sweep_cli_requires_targets():
    result = runner.invoke(app, ["sweep"])
    assert result.exit_code == 1
    assert "Provide at least one target" in result.output


def test_sweep_command_help_registered():
    result = runner.invoke(app, ["sweep", "--help"])
    assert result.exit_code == 0
    assert "--targets-file" in result.output
