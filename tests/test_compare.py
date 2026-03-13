"""Tests for agentkit compare command."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.commands.compare_cmd import (
    _extract_score,
    _compute_verdict,
    compare_command,
    IMPROVED_THRESHOLD,
    DEGRADED_THRESHOLD,
)

runner = CliRunner()


# ---------------------------------------------------------------------------
# Unit tests: _extract_score
# ---------------------------------------------------------------------------

class TestExtractScore:
    def test_json_score_key(self):
        assert _extract_score('{"score": 85}') == 85.0

    def test_json_score_key_float(self):
        assert _extract_score('{"score": 72.5, "other": 1}') == 72.5

    def test_score_colon_pattern(self):
        assert _extract_score("Score: 90") == 90.0

    def test_score_lowercase(self):
        assert _extract_score("score: 42") == 42.0

    def test_bare_number_line(self):
        assert _extract_score("Running tool...\n78\n") == 78.0

    def test_bare_float_line(self):
        assert _extract_score("Results:\n65.5\n") == 65.5

    def test_no_score_returns_none(self):
        assert _extract_score("no numbers here (except like text-form)") is None

    def test_out_of_range_number_ignored(self):
        # 200 is not a valid 0-100 score
        result = _extract_score("value: 200")
        assert result is None or result != 200.0

    def test_json_inline(self):
        output = 'some preamble\n{"score": 55, "grade": "B"}\nfooter'
        assert _extract_score(output) == 55.0

    def test_empty_string(self):
        assert _extract_score("") is None


# ---------------------------------------------------------------------------
# Unit tests: _compute_verdict
# ---------------------------------------------------------------------------

class TestComputeVerdict:
    def test_none_is_neutral(self):
        assert _compute_verdict(None) == "NEUTRAL"

    def test_above_threshold_is_improved(self):
        assert _compute_verdict(IMPROVED_THRESHOLD + 1) == "IMPROVED"

    def test_exactly_threshold_is_neutral(self):
        assert _compute_verdict(IMPROVED_THRESHOLD) == "NEUTRAL"

    def test_below_degraded_threshold(self):
        assert _compute_verdict(DEGRADED_THRESHOLD - 1) == "DEGRADED"

    def test_exactly_degraded_threshold_is_neutral(self):
        assert _compute_verdict(DEGRADED_THRESHOLD) == "NEUTRAL"

    def test_zero_is_neutral(self):
        assert _compute_verdict(0.0) == "NEUTRAL"

    def test_small_positive_is_neutral(self):
        assert _compute_verdict(3.0) == "NEUTRAL"

    def test_small_negative_is_neutral(self):
        assert _compute_verdict(-3.0) == "NEUTRAL"


# ---------------------------------------------------------------------------
# Integration tests: CLI via CliRunner with mocks
# ---------------------------------------------------------------------------

def _mock_score_ref(scores: dict[str, Optional[float]]):
    """Return a replacement for _score_ref that injects fixed scores."""
    def _inner(ref: str, tools: list, repo_root: Path) -> dict:
        return {
            tool: {"tool": tool, "status": "ok", "score": scores.get(tool)}
            for tool in tools
        }
    return _inner


@pytest.fixture()
def mock_git_root(tmp_path):
    """Patch git_root to return tmp_path."""
    with patch("agentkit_cli.commands.compare_cmd.git_root", return_value=tmp_path):
        yield tmp_path


@pytest.fixture()
def mock_score_stable(mock_git_root):
    """Both refs return the same scores (neutral)."""
    scores = {"agentlint": 80.0, "agentreflect": 75.0, "coderace": 70.0, "agentmd": 85.0}
    with patch("agentkit_cli.commands.compare_cmd._score_ref", side_effect=_mock_score_ref(scores)):
        yield scores


@pytest.fixture()
def mock_score_improved(mock_git_root):
    """ref2 is 10 points better on every tool."""
    scores_base = {"agentlint": 70.0, "agentreflect": 65.0, "coderace": 60.0, "agentmd": 75.0}
    scores_head = {k: v + 10 for k, v in scores_base.items()}

    call_count = [0]

    def _side_effect(ref: str, tools: list, repo_root: Path) -> dict:
        call_count[0] += 1
        scores = scores_base if call_count[0] == 1 else scores_head
        return {t: {"tool": t, "status": "ok", "score": scores[t]} for t in tools}

    with patch("agentkit_cli.commands.compare_cmd._score_ref", side_effect=_side_effect):
        yield scores_base, scores_head


@pytest.fixture()
def mock_score_degraded(mock_git_root):
    """ref2 is 10 points worse on every tool."""
    scores_base = {"agentlint": 80.0, "agentreflect": 75.0, "coderace": 70.0, "agentmd": 85.0}
    scores_head = {k: v - 10 for k, v in scores_base.items()}

    call_count = [0]

    def _side_effect(ref: str, tools: list, repo_root: Path) -> dict:
        call_count[0] += 1
        scores = scores_base if call_count[0] == 1 else scores_head
        return {t: {"tool": t, "status": "ok", "score": scores[t]} for t in tools}

    with patch("agentkit_cli.commands.compare_cmd._score_ref", side_effect=_side_effect):
        yield scores_base, scores_head


class TestCompareHelp:
    def test_help_renders(self):
        result = runner.invoke(app, ["compare", "--help"])
        assert result.exit_code == 0
        assert "compare" in result.output.lower()
        assert "ref1" in result.output.lower() or "HEAD" in result.output


class TestCompareQuiet:
    def test_quiet_neutral(self, mock_score_stable):
        result = runner.invoke(app, ["compare", "HEAD~1", "HEAD", "--quiet"])
        assert result.exit_code == 0
        assert result.output.strip() == "NEUTRAL"

    def test_quiet_improved(self, mock_score_improved):
        result = runner.invoke(app, ["compare", "HEAD~1", "HEAD", "--quiet"])
        assert result.exit_code == 0
        assert result.output.strip() == "IMPROVED"

    def test_quiet_degraded(self, mock_score_degraded):
        result = runner.invoke(app, ["compare", "HEAD~1", "HEAD", "--quiet"])
        assert result.exit_code == 0
        assert result.output.strip() == "DEGRADED"


class TestCompareJson:
    def test_json_output_structure(self, mock_score_stable):
        result = runner.invoke(app, ["compare", "HEAD~1", "HEAD", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "verdict" in data
        assert "net_delta" in data
        assert "tools" in data
        assert isinstance(data["tools"], list)
        assert data["ref1"] == "HEAD~1"
        assert data["ref2"] == "HEAD"

    def test_json_verdict_neutral(self, mock_score_stable):
        result = runner.invoke(app, ["compare", "HEAD~1", "HEAD", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["verdict"] == "NEUTRAL"

    def test_json_verdict_improved(self, mock_score_improved):
        result = runner.invoke(app, ["compare", "HEAD~1", "HEAD", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["verdict"] == "IMPROVED"
        assert data["net_delta"] > 0

    def test_json_verdict_degraded(self, mock_score_degraded):
        result = runner.invoke(app, ["compare", "HEAD~1", "HEAD", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["verdict"] == "DEGRADED"
        assert data["net_delta"] < 0

    def test_json_tools_have_delta(self, mock_score_improved):
        result = runner.invoke(app, ["compare", "HEAD~1", "HEAD", "--json"])
        data = json.loads(result.output)
        for entry in data["tools"]:
            assert "tool" in entry
            assert "score_ref1" in entry
            assert "score_ref2" in entry
            assert "delta" in entry


class TestCompareCIMode:
    def test_ci_exit_0_on_neutral(self, mock_score_stable):
        result = runner.invoke(app, ["compare", "HEAD~1", "HEAD", "--ci", "--quiet"])
        assert result.exit_code == 0

    def test_ci_exit_0_on_improved(self, mock_score_improved):
        result = runner.invoke(app, ["compare", "HEAD~1", "HEAD", "--ci", "--quiet"])
        assert result.exit_code == 0

    def test_ci_exit_1_on_degraded(self, mock_score_degraded):
        result = runner.invoke(app, ["compare", "HEAD~1", "HEAD", "--ci", "--quiet"])
        assert result.exit_code == 1

    def test_min_delta_fail(self, mock_score_stable):
        # net_delta is 0 (stable), require +10 -> should fail
        result = runner.invoke(app, ["compare", "HEAD~1", "HEAD", "--min-delta", "10", "--quiet"])
        assert result.exit_code == 1

    def test_min_delta_pass(self, mock_score_improved):
        # net_delta is +10, require +5 -> should pass
        result = runner.invoke(app, ["compare", "HEAD~1", "HEAD", "--min-delta", "5", "--quiet"])
        assert result.exit_code == 0


class TestCompareToolFilter:
    def test_single_tool(self, mock_git_root):
        """--tools limits which tools are scored."""
        called_tools = []

        def _side_effect(ref: str, tools: list, repo_root: Path) -> dict:
            called_tools.extend(tools)
            return {t: {"tool": t, "status": "ok", "score": 80.0} for t in tools}

        with patch("agentkit_cli.commands.compare_cmd._score_ref", side_effect=_side_effect):
            result = runner.invoke(app, ["compare", "HEAD~1", "HEAD", "--tools", "agentlint", "--quiet"])
        assert result.exit_code == 0
        # Each side-effect call gets only agentlint
        assert all(t == "agentlint" for t in called_tools)

    def test_unknown_tool_ignored(self, mock_git_root):
        def _side_effect(ref: str, tools: list, repo_root: Path) -> dict:
            return {t: {"tool": t, "status": "ok", "score": 80.0} for t in tools}

        with patch("agentkit_cli.commands.compare_cmd._score_ref", side_effect=_side_effect):
            result = runner.invoke(app, ["compare", "HEAD~1", "HEAD", "--tools", "nonexistent", "--quiet"])
        # Falls back to all tools or gracefully handles
        assert result.exit_code == 0


class TestCompareNaHandling:
    def test_na_tool_does_not_crash(self, mock_git_root):
        """If a tool returns score=None, the command should still complete."""
        def _side_effect(ref: str, tools: list, repo_root: Path) -> dict:
            return {t: {"tool": t, "status": "error", "score": None, "reason": "tool failed"} for t in tools}

        with patch("agentkit_cli.commands.compare_cmd._score_ref", side_effect=_side_effect):
            result = runner.invoke(app, ["compare", "HEAD~1", "HEAD", "--quiet"])
        assert result.exit_code == 0
        assert result.output.strip() == "NEUTRAL"


class TestCompareFiles:
    def test_files_flag_included_in_json(self, mock_score_stable):
        with patch("agentkit_cli.commands.compare_cmd.changed_files", return_value=["README.md", "src/foo.py"]):
            result = runner.invoke(app, ["compare", "HEAD~1", "HEAD", "--files", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "changed_files" in data
        assert "README.md" in data["changed_files"]

    def test_files_fallback_on_error(self, mock_score_stable):
        """--files should not crash even if changed_files raises."""
        with patch("agentkit_cli.commands.compare_cmd.changed_files", side_effect=Exception("git error")):
            result = runner.invoke(app, ["compare", "HEAD~1", "HEAD", "--files", "--json"])
        assert result.exit_code == 0


# ---------------------------------------------------------------------------
# git_utils unit tests
# ---------------------------------------------------------------------------

class TestGitUtils:
    def test_resolve_ref_valid(self, tmp_path):
        """resolve_ref returns a SHA for HEAD in a real repo."""
        from agentkit_cli.utils.git_utils import resolve_ref
        # Use this repo as test target
        repo = Path(__file__).parent.parent
        sha = resolve_ref("HEAD", cwd=str(repo))
        assert len(sha) == 40
        assert all(c in "0123456789abcdef" for c in sha)

    def test_resolve_ref_invalid(self, tmp_path):
        from agentkit_cli.utils.git_utils import resolve_ref, GitError
        # Initialize an empty git repo
        subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
        with pytest.raises(GitError):
            resolve_ref("nonexistent-branch-xyz", cwd=str(tmp_path))

    def test_git_root(self):
        from agentkit_cli.utils.git_utils import git_root
        repo = Path(__file__).parent.parent
        root = git_root(cwd=str(repo))
        assert root.is_dir()

    def test_changed_files_same_ref(self):
        from agentkit_cli.utils.git_utils import changed_files
        repo = Path(__file__).parent.parent
        # diff HEAD HEAD -> no changes
        result = changed_files("HEAD", "HEAD", cwd=str(repo))
        assert result == []

    def test_changed_files_returns_list(self):
        from agentkit_cli.utils.git_utils import changed_files
        repo = Path(__file__).parent.parent
        # May or may not have changes; result is always a list
        result = changed_files("HEAD~1", "HEAD", cwd=str(repo))
        assert isinstance(result, list)
