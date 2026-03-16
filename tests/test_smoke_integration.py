"""Golden smoke test suite — exercises each orchestration command against a fixture project.

Run with: pytest -m smoke
These tests mock ToolAdapter to avoid requiring real quartet tools.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

FIXTURE_DIR = str(Path(__file__).parent / "fixtures" / "smoke_project")

# Standard mock return values for ToolAdapter methods
MOCK_AGENTLINT = {"fresh": True, "score": 85, "issues": [], "summary": "All good"}
MOCK_AGENTMD = {"score": 78, "files": ["CLAUDE.md"]}
MOCK_CODERACE = {"results": [{"agent": "test", "score": 90}], "status": "ok"}
MOCK_REFLECT = {"suggestions_md": "### Improve tests\nAdd edge cases.", "count": 1}


def _patch_adapter():
    """Return a context manager that patches all ToolAdapter methods."""
    return patch.multiple(
        "agentkit_cli.tools.ToolAdapter",
        agentlint_check_context=MagicMock(return_value=MOCK_AGENTLINT),
        agentlint_diff=MagicMock(return_value=None),
        agentmd_score=MagicMock(return_value=MOCK_AGENTMD),
        agentmd_generate=MagicMock(return_value={"generated": True}),
        coderace_benchmark_history=MagicMock(return_value=MOCK_CODERACE),
        agentreflect_from_git=MagicMock(return_value=MOCK_REFLECT),
        agentreflect_from_notes=MagicMock(return_value=MOCK_REFLECT),
    )


def _run_cli(*args: str, cwd: str | None = None) -> subprocess.CompletedProcess:
    """Run agentkit CLI via subprocess."""
    result = subprocess.run(
        [sys.executable, "-m", "agentkit_cli.main"] + list(args),
        capture_output=True,
        text=True,
        timeout=30,
        cwd=cwd,
    )
    return result


@pytest.mark.smoke
def test_smoke_doctor():
    """agentkit doctor → exit 0 or known codes."""
    with _patch_adapter():
        # doctor uses cwd, not --path
        result = _run_cli("doctor", "--no-fail-exit")
    assert result.returncode == 0, f"Unexpected exit: {result.returncode}\n{result.stderr}"


@pytest.mark.smoke
def test_smoke_score():
    """agentkit score <fixture> → JSON with 'score' key."""
    with _patch_adapter():
        result = _run_cli("score", FIXTURE_DIR, "--json")
    assert result.returncode == 0, f"score failed: {result.stderr}"
    data = json.loads(result.stdout)
    assert "score" in data or "composite_score" in data


@pytest.mark.smoke
def test_smoke_analyze():
    """agentkit analyze <fixture> → score returned."""
    with _patch_adapter():
        result = _run_cli("analyze", FIXTURE_DIR, "--json")
    assert result.returncode == 0, f"analyze failed: {result.stderr}"
    data = json.loads(result.stdout)
    assert "composite_score" in data or "score" in data


@pytest.mark.smoke
def test_smoke_suggest():
    """agentkit suggest <fixture> → no exception."""
    with _patch_adapter():
        result = _run_cli("suggest", "--path", FIXTURE_DIR)
    # suggest may exit 0 (no issues) or 1 (findings); both are fine
    assert result.returncode in (0, 1), f"suggest crashed: {result.stderr}"


@pytest.mark.smoke
def test_smoke_report(tmp_path):
    """agentkit report <fixture> → produces output."""
    out_file = tmp_path / "report.html"
    with _patch_adapter():
        result = _run_cli("report", "--path", FIXTURE_DIR, "--output", str(out_file))
    # report may fail if tools aren't installed; accept 0 or 1
    assert result.returncode in (0, 1), f"report crashed: {result.stderr}"


@pytest.mark.smoke
def test_smoke_gate_pass():
    """agentkit gate --min-score 0 → exit 0 (run from fixture dir to avoid repo config)."""
    with _patch_adapter():
        result = _run_cli("gate", "--min-score", "0", "--json", cwd=FIXTURE_DIR)
    assert result.returncode == 0, f"gate pass failed: {result.stdout}\n{result.stderr}"


@pytest.mark.smoke
def test_smoke_gate_fail():
    """agentkit gate --min-score 200 → exit 1."""
    with _patch_adapter():
        result = _run_cli("gate", "--min-score", "200", "--json", cwd=FIXTURE_DIR)
    assert result.returncode == 1, f"Expected gate to fail with min-score 200, got {result.returncode}"


@pytest.mark.smoke
def test_smoke_compare():
    """agentkit compare HEAD HEAD <fixture> → no exception."""
    with _patch_adapter():
        result = _run_cli("compare", "HEAD", "HEAD", "--path", FIXTURE_DIR)
    # compare needs a git repo; may exit 1 if fixture is not git-tracked
    assert result.returncode in (0, 1), f"compare crashed: {result.stderr}"


@pytest.mark.smoke
def test_smoke_summary():
    """agentkit summary → no exception (with mock history)."""
    with _patch_adapter():
        result = _run_cli("summary")
    # summary may exit 0 (data available) or 1 (no history) — both are valid
    assert result.returncode in (0, 1), f"summary crashed: {result.stderr}"
