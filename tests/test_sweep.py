"""Tests for agentkit sweep command."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from agentkit_cli.analyze import AnalyzeResult
from agentkit_cli.main import app
from agentkit_cli.sweep import (
    SweepTargetResult,
    resolve_targets,
    run_sweep,
    sort_results,
)

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


def _make_result(
    target: str,
    score: float | None = 80.0,
    grade: str | None = "B",
    status: str = "succeeded",
    error: str | None = None,
) -> SweepTargetResult:
    return SweepTargetResult(
        target=target,
        status=status,
        repo_name=target.split("/")[-1],
        composite_score=score,
        grade=grade,
        successful_tools=3 if status == "succeeded" else 0,
        total_tools=3,
        error=error,
    )


# ── D1 tests ────────────────────────────────────────────────────────

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


# ── D2 tests: sort + limit + Rich table ─────────────────────────────

def test_sort_results_by_score_descending():
    results = [
        _make_result("repo-low", score=50.0, grade="D"),
        _make_result("repo-high", score=95.0, grade="A"),
        _make_result("repo-mid", score=75.0, grade="C"),
    ]
    sorted_r = sort_results(results, sort_by="score")
    assert [r.target for r in sorted_r] == ["repo-high", "repo-mid", "repo-low"]


def test_sort_results_by_name():
    results = [
        _make_result("charlie", score=50.0),
        _make_result("alpha", score=90.0),
        _make_result("bravo", score=70.0),
    ]
    sorted_r = sort_results(results, sort_by="name")
    assert [r.target for r in sorted_r] == ["alpha", "bravo", "charlie"]


def test_sort_results_by_grade():
    results = [
        _make_result("d-grade", score=55.0, grade="D"),
        _make_result("a-grade", score=95.0, grade="A"),
        _make_result("b-grade", score=80.0, grade="B"),
    ]
    sorted_r = sort_results(results, sort_by="grade")
    assert [r.target for r in sorted_r] == ["a-grade", "b-grade", "d-grade"]


def test_sort_results_failed_targets_sort_last_by_score():
    results = [
        _make_result("failed-repo", score=None, grade=None, status="failed", error="boom"),
        _make_result("good-repo", score=80.0, grade="B"),
    ]
    sorted_r = sort_results(results, sort_by="score")
    assert sorted_r[0].target == "good-repo"
    assert sorted_r[1].target == "failed-repo"


def test_sort_results_failed_targets_sort_last_by_grade():
    results = [
        _make_result("failed-repo", score=None, grade=None, status="failed", error="boom"),
        _make_result("c-repo", score=65.0, grade="C"),
    ]
    sorted_r = sort_results(results, sort_by="grade")
    assert sorted_r[0].target == "c-repo"
    assert sorted_r[1].target == "failed-repo"


@patch("agentkit_cli.commands.sweep_cmd.run_sweep")
def test_sweep_cli_sort_by_flag(mock_run_sweep):
    from agentkit_cli.sweep import SweepRunResult
    mock_run_sweep.return_value = SweepRunResult(
        targets=["a", "b"],
        results=[
            _make_result("a", score=50.0, grade="D"),
            _make_result("b", score=90.0, grade="A"),
        ],
    )
    result = runner.invoke(app, ["sweep", "a", "b", "--sort-by", "name"])
    assert result.exit_code == 0, result.output
    # Table should contain both targets
    assert "a" in result.output
    assert "b" in result.output


@patch("agentkit_cli.commands.sweep_cmd.run_sweep")
def test_sweep_cli_limit_flag(mock_run_sweep):
    from agentkit_cli.sweep import SweepRunResult
    mock_run_sweep.return_value = SweepRunResult(
        targets=["a", "b", "c"],
        results=[
            _make_result("a", score=90.0, grade="A"),
            _make_result("b", score=80.0, grade="B"),
            _make_result("c", score=70.0, grade="C"),
        ],
    )
    result = runner.invoke(app, ["sweep", "a", "b", "c", "--limit", "2"])
    assert result.exit_code == 0, result.output
    assert "Showing top 2 of 3" in result.output


@patch("agentkit_cli.commands.sweep_cmd.run_sweep")
def test_sweep_cli_rich_table_columns(mock_run_sweep):
    from agentkit_cli.sweep import SweepRunResult
    mock_run_sweep.return_value = SweepRunResult(
        targets=["github:psf/requests"],
        results=[_make_result("github:psf/requests", score=85.0, grade="B")],
    )
    result = runner.invoke(app, ["sweep", "github:psf/requests"])
    assert result.exit_code == 0, result.output
    assert "target" in result.output
    assert "score" in result.output
    assert "grade" in result.output
    assert "status" in result.output


# ── D3 tests: JSON output ───────────────────────────────────────────

@patch("agentkit_cli.commands.sweep_cmd.run_sweep")
def test_sweep_json_output_schema(mock_run_sweep):
    from agentkit_cli.sweep import SweepRunResult
    mock_run_sweep.return_value = SweepRunResult(
        targets=["github:psf/requests", "github:bad/repo"],
        results=[
            _make_result("github:psf/requests", score=85.0, grade="B"),
            _make_result("github:bad/repo", score=None, grade=None, status="failed", error="clone failed"),
        ],
    )
    result = runner.invoke(app, ["sweep", "github:psf/requests", "github:bad/repo", "--json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert "targets" in data
    assert "results" in data
    assert "summary_counts" in data
    assert data["targets"] == ["github:psf/requests", "github:bad/repo"]
    assert len(data["results"]) == 2


@patch("agentkit_cli.commands.sweep_cmd.run_sweep")
def test_sweep_json_results_have_rank(mock_run_sweep):
    from agentkit_cli.sweep import SweepRunResult
    mock_run_sweep.return_value = SweepRunResult(
        targets=["a", "b"],
        results=[
            _make_result("a", score=70.0, grade="C"),
            _make_result("b", score=90.0, grade="A"),
        ],
    )
    result = runner.invoke(app, ["sweep", "a", "b", "--json"])
    data = json.loads(result.output)
    # Default sort is by score descending, so b should be rank 1
    assert data["results"][0]["rank"] == 1
    assert data["results"][0]["target"] == "b"
    assert data["results"][1]["rank"] == 2
    assert data["results"][1]["target"] == "a"


@patch("agentkit_cli.commands.sweep_cmd.run_sweep")
def test_sweep_json_summary_counts(mock_run_sweep):
    from agentkit_cli.sweep import SweepRunResult
    mock_run_sweep.return_value = SweepRunResult(
        targets=["a", "b", "c"],
        results=[
            _make_result("a", score=85.0, grade="B"),
            _make_result("b", score=None, grade=None, status="failed", error="err"),
            _make_result("c", score=70.0, grade="C"),
        ],
    )
    result = runner.invoke(app, ["sweep", "a", "b", "c", "--json"])
    data = json.loads(result.output)
    assert data["summary_counts"] == {
        "total": 3,
        "succeeded": 2,
        "failed": 1,
        "analyzed_with_scores": 2,
    }


@patch("agentkit_cli.commands.sweep_cmd.run_sweep")
def test_sweep_json_error_field_present_only_on_failure(mock_run_sweep):
    from agentkit_cli.sweep import SweepRunResult
    mock_run_sweep.return_value = SweepRunResult(
        targets=["ok", "bad"],
        results=[
            _make_result("ok", score=80.0, grade="B"),
            _make_result("bad", score=None, grade=None, status="failed", error="oops"),
        ],
    )
    result = runner.invoke(app, ["sweep", "ok", "bad", "--json"])
    data = json.loads(result.output)
    ok_entry = next(r for r in data["results"] if r["target"] == "ok")
    bad_entry = next(r for r in data["results"] if r["target"] == "bad")
    assert "error" not in ok_entry
    assert bad_entry["error"] == "oops"


@patch("agentkit_cli.commands.sweep_cmd.run_sweep")
def test_sweep_json_deterministic(mock_run_sweep):
    """JSON output should be deterministic across runs."""
    from agentkit_cli.sweep import SweepRunResult
    results_data = SweepRunResult(
        targets=["x", "y"],
        results=[
            _make_result("x", score=60.0, grade="D"),
            _make_result("y", score=90.0, grade="A"),
        ],
    )
    mock_run_sweep.return_value = results_data
    r1 = runner.invoke(app, ["sweep", "x", "y", "--json"])
    mock_run_sweep.return_value = results_data
    r2 = runner.invoke(app, ["sweep", "x", "y", "--json"])
    assert r1.output == r2.output
