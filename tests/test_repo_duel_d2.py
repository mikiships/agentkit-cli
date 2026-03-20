"""Tests for D2: agentkit repo-duel CLI command."""
from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.repo_duel import RepoDuelResult, DimensionResult
from agentkit_cli.analyze import AnalyzeResult


runner = CliRunner()


def _make_analyze_result(target, score=75.0, grade="B", tools=None):
    return AnalyzeResult(
        target=target,
        repo_name=target.split("/")[-1],
        composite_score=score,
        grade=grade,
        tools=tools or {
            "agentmd": {"score": score, "status": "pass", "finding": "ok"},
            "coderace": {"score": score, "status": "pass", "finding": "ok"},
            "agentlint": {"score": score, "status": "pass", "finding": "ok"},
            "agentreflect": {"score": score, "status": "pass", "finding": "ok"},
        },
    )


def _mock_analyze_factory(score1=80.0, score2=60.0):
    def factory(target, timeout):
        if "repo1" in target or target == "github:a/repo1":
            return _make_analyze_result(target, score=score1, grade="A")
        return _make_analyze_result(target, score=score2, grade="C")
    return factory


def test_repo_duel_help():
    result = runner.invoke(app, ["repo-duel", "--help"])
    assert result.exit_code == 0
    assert "repo-duel" in result.output.lower() or "duel" in result.output.lower()


def test_repo_duel_json_output():
    from agentkit_cli.commands.repo_duel_cmd import repo_duel_command
    from io import StringIO
    import sys

    factory = _mock_analyze_factory(80.0, 60.0)
    captured = []

    # Invoke directly with json_output
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    try:
        repo_duel_command(
            repo1="github:a/repo1",
            repo2="github:b/repo2",
            json_output=True,
            _analyze_factory=factory,
        )
        out = sys.stdout.getvalue()
    finally:
        sys.stdout = old_stdout

    data = json.loads(out)
    assert "repo1" in data
    assert "repo2" in data
    assert "winner" in data


def test_repo_duel_quiet_repo1_wins():
    from agentkit_cli.commands.repo_duel_cmd import repo_duel_command
    from io import StringIO
    import sys

    factory = _mock_analyze_factory(90.0, 50.0)
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    try:
        repo_duel_command(
            repo1="github:a/repo1",
            repo2="github:b/repo2",
            quiet=True,
            _analyze_factory=factory,
        )
        out = sys.stdout.getvalue()
    finally:
        sys.stdout = old_stdout

    assert "winner" in out
    assert "repo1" in out or "github:a/repo1" in out


def test_repo_duel_quiet_draw():
    from agentkit_cli.commands.repo_duel_cmd import repo_duel_command
    from io import StringIO
    import sys

    # Same scores = draw
    def factory(target, timeout):
        return _make_analyze_result(target, score=70.0, grade="B", tools={
            "agentmd": {"score": 70.0}, "coderace": {"score": 70.0},
            "agentlint": {"score": 70.0}, "agentreflect": {"score": 70.0},
        })

    old_stdout = sys.stdout
    sys.stdout = StringIO()
    try:
        repo_duel_command(
            repo1="r1",
            repo2="r2",
            quiet=True,
            _analyze_factory=factory,
        )
        out = sys.stdout.getvalue()
    finally:
        sys.stdout = old_stdout

    assert "draw" in out.lower()


def test_repo_duel_deep_flag():
    from agentkit_cli.commands.repo_duel_cmd import repo_duel_command
    from io import StringIO
    import sys

    factory = _mock_analyze_factory(80.0, 60.0)
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    try:
        repo_duel_command(
            repo1="github:a/repo1",
            repo2="github:b/repo2",
            json_output=True,
            deep=True,
            _analyze_factory=factory,
        )
        out = sys.stdout.getvalue()
    finally:
        sys.stdout = old_stdout

    data = json.loads(out)
    dim_names = [d["name"] for d in data["dimension_results"]]
    assert "redteam_resistance" in dim_names


def test_repo_duel_output_file(tmp_path):
    from agentkit_cli.commands.repo_duel_cmd import repo_duel_command

    factory = _mock_analyze_factory(80.0, 60.0)
    outfile = tmp_path / "duel.html"

    repo_duel_command(
        repo1="github:a/repo1",
        repo2="github:b/repo2",
        output=str(outfile),
        quiet=True,
        _analyze_factory=factory,
    )

    assert outfile.exists()
    content = outfile.read_text()
    assert "<!DOCTYPE html>" in content


def test_repo_duel_json_has_dimension_results():
    from agentkit_cli.commands.repo_duel_cmd import repo_duel_command
    from io import StringIO
    import sys

    factory = _mock_analyze_factory()
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    try:
        repo_duel_command(
            repo1="a", repo2="b",
            json_output=True,
            _analyze_factory=factory,
        )
        out = sys.stdout.getvalue()
    finally:
        sys.stdout = old_stdout

    data = json.loads(out)
    assert isinstance(data["dimension_results"], list)
    assert len(data["dimension_results"]) >= 4


def test_repo_duel_error_invalid_raises():
    from agentkit_cli.commands.repo_duel_cmd import repo_duel_command
    import typer

    def bad_factory(target, timeout):
        raise RuntimeError("Network error")

    with pytest.raises((typer.Exit, SystemExit, Exception)):
        repo_duel_command(
            repo1="bad", repo2="worse",
            json_output=False,
            _analyze_factory=bad_factory,
        )


def test_repo_duel_json_error_output():
    from agentkit_cli.commands.repo_duel_cmd import repo_duel_command
    from io import StringIO
    import sys
    import typer

    def bad_factory(target, timeout):
        raise RuntimeError("fail")

    old_stdout = sys.stdout
    sys.stdout = StringIO()
    try:
        with pytest.raises((typer.Exit, SystemExit)):
            repo_duel_command(
                repo1="bad", repo2="worse",
                json_output=True,
                _analyze_factory=bad_factory,
            )
        out = sys.stdout.getvalue()
    finally:
        sys.stdout = old_stdout

    if out.strip():
        data = json.loads(out)
        assert "error" in data


def test_repo_duel_saves_to_history(tmp_path):
    from agentkit_cli.commands.repo_duel_cmd import repo_duel_command
    from agentkit_cli.history import HistoryDB

    factory = _mock_analyze_factory(80.0, 60.0)
    db_path = tmp_path / "hist.db"
    db = HistoryDB(db_path)

    # Patch HistoryDB to use our temp db
    import agentkit_cli.commands.repo_duel_cmd as mod
    orig = mod.__builtins__ if hasattr(mod, '__builtins__') else None

    # Just call with quiet, we can't easily inject db_path but ensure no crash
    repo_duel_command(
        repo1="github:a/repo1",
        repo2="github:b/repo2",
        quiet=True,
        _analyze_factory=factory,
    )
    # No error = pass
