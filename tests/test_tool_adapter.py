"""Tests for ToolAdapter — canonical quartet tool invocations."""
from __future__ import annotations

import subprocess
from unittest.mock import patch, MagicMock

import pytest

from agentkit_cli.tools import ToolAdapter, get_adapter, _parse_json_output


# ---------------------------------------------------------------------------
# _parse_json_output
# ---------------------------------------------------------------------------

def test_parse_json_output_valid():
    assert _parse_json_output('{"score": 82}') == {"score": 82}


def test_parse_json_output_with_prefix():
    assert _parse_json_output('Loading...\n{"score": 82}') == {"score": 82}


def test_parse_json_output_array():
    assert _parse_json_output('[1, 2, 3]') == [1, 2, 3]


def test_parse_json_output_garbage():
    assert _parse_json_output("no json here") is None


def test_parse_json_output_empty():
    assert _parse_json_output("") is None


# ---------------------------------------------------------------------------
# ToolAdapter._run
# ---------------------------------------------------------------------------

class TestToolAdapterRun:
    def setup_method(self):
        self.adapter = ToolAdapter(timeout=10)

    @patch("agentkit_cli.tools.subprocess.run")
    def test_run_success(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess(
            args=["echo"], returncode=0, stdout="ok", stderr=""
        )
        result = self.adapter._run(["echo", "hi"])
        assert result is not None
        assert result.stdout == "ok"

    @patch("agentkit_cli.tools.subprocess.run")
    def test_run_nonzero_returns_none(self, mock_run):
        mock_run.return_value = subprocess.CompletedProcess(
            args=["fail"], returncode=1, stdout="", stderr="error"
        )
        assert self.adapter._run(["fail"]) is None

    @patch("agentkit_cli.tools.subprocess.run", side_effect=FileNotFoundError)
    def test_run_file_not_found(self, mock_run):
        assert self.adapter._run(["nosuch"]) is None

    @patch("agentkit_cli.tools.subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 10))
    def test_run_timeout(self, mock_run):
        assert self.adapter._run(["slow"]) is None

    @patch("agentkit_cli.tools.subprocess.run", side_effect=OSError("boom"))
    def test_run_oserror(self, mock_run):
        assert self.adapter._run(["bad"]) is None


# ---------------------------------------------------------------------------
# agentlint methods
# ---------------------------------------------------------------------------

class TestAgentlintCheckContext:
    def setup_method(self):
        self.adapter = ToolAdapter()

    @patch("agentkit_cli.tools.is_installed", return_value=False)
    def test_not_installed(self, _):
        assert self.adapter.agentlint_check_context("/tmp") is None

    @patch("agentkit_cli.tools.is_installed", return_value=True)
    @patch("agentkit_cli.tools.subprocess.run")
    def test_success(self, mock_run, _):
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0,
            stdout='{"freshness_score": 85, "issues": []}', stderr=""
        )
        result = self.adapter.agentlint_check_context("/project")
        assert result == {"freshness_score": 85, "issues": []}
        cmd = mock_run.call_args[0][0]
        assert cmd == ["agentlint", "check-context", ".", "--format", "json"]

    @patch("agentkit_cli.tools.is_installed", return_value=True)
    @patch("agentkit_cli.tools.subprocess.run")
    def test_bad_json(self, mock_run, _):
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="not json", stderr=""
        )
        assert self.adapter.agentlint_check_context("/project") is None


class TestAgentlintDiff:
    def setup_method(self):
        self.adapter = ToolAdapter()

    @patch("agentkit_cli.tools.is_installed", return_value=False)
    def test_not_installed(self, _):
        assert self.adapter.agentlint_diff("diff content", "/tmp") is None

    @patch("agentkit_cli.tools.is_installed", return_value=True)
    @patch("agentkit_cli.tools.subprocess.run")
    def test_success(self, mock_run, _):
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0,
            stdout='{"findings": []}', stderr=""
        )
        result = self.adapter.agentlint_diff("diff data", "/project")
        assert result == {"findings": []}
        assert mock_run.call_args[1]["input"] == "diff data"


# ---------------------------------------------------------------------------
# agentmd methods
# ---------------------------------------------------------------------------

class TestAgentmdScore:
    def setup_method(self):
        self.adapter = ToolAdapter()

    @patch("agentkit_cli.tools.is_installed", return_value=False)
    def test_not_installed(self, _):
        assert self.adapter.agentmd_score("/tmp") is None

    @patch("agentkit_cli.tools.is_installed", return_value=True)
    @patch("agentkit_cli.tools.subprocess.run")
    def test_score_success(self, mock_run, _):
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0,
            stdout='{"score": 75}', stderr=""
        )
        assert self.adapter.agentmd_score("/p") == {"score": 75}

    @patch("agentkit_cli.tools.is_installed", return_value=True)
    @patch("agentkit_cli.tools.subprocess.run")
    def test_score_fallback_to_generate(self, mock_run, _):
        # First call (score) fails, second (generate) succeeds
        mock_run.side_effect = [
            subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="err"),
            subprocess.CompletedProcess(args=[], returncode=0, stdout='{"score": 60}', stderr=""),
        ]
        assert self.adapter.agentmd_score("/p") == {"score": 60}


class TestAgentmdGenerate:
    def setup_method(self):
        self.adapter = ToolAdapter()

    @patch("agentkit_cli.tools.is_installed", return_value=False)
    def test_not_installed(self, _):
        assert self.adapter.agentmd_generate("/tmp") is None

    @patch("agentkit_cli.tools.is_installed", return_value=True)
    @patch("agentkit_cli.tools.subprocess.run")
    def test_generate(self, mock_run, _):
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0,
            stdout='{"generated": true}', stderr=""
        )
        assert self.adapter.agentmd_generate("/p") == {"generated": True}

    @patch("agentkit_cli.tools.is_installed", return_value=True)
    @patch("agentkit_cli.tools.subprocess.run")
    def test_generate_minimal(self, mock_run, _):
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0,
            stdout='{"minimal": true}', stderr=""
        )
        self.adapter.agentmd_generate("/p", minimal=True)
        cmd = mock_run.call_args[0][0]
        assert "--minimal" in cmd


# ---------------------------------------------------------------------------
# coderace method
# ---------------------------------------------------------------------------

class TestCoderaceHistory:
    def setup_method(self):
        self.adapter = ToolAdapter()

    @patch("agentkit_cli.tools.is_installed", return_value=False)
    def test_not_installed(self, _):
        assert self.adapter.coderace_benchmark_history("/tmp") is None

    @patch("agentkit_cli.tools.is_installed", return_value=True)
    @patch("agentkit_cli.tools.subprocess.run")
    def test_success(self, mock_run, _):
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0,
            stdout='{"results": []}', stderr=""
        )
        assert self.adapter.coderace_benchmark_history("/p") == {"results": []}

    @patch("agentkit_cli.tools.is_installed", return_value=True)
    @patch("agentkit_cli.tools.subprocess.run")
    def test_fallback_no_results(self, mock_run, _):
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="no data"
        )
        result = self.adapter.coderace_benchmark_history("/p")
        assert result["status"] == "no_results"


# ---------------------------------------------------------------------------
# agentreflect methods
# ---------------------------------------------------------------------------

class TestAgentreflectFromGit:
    def setup_method(self):
        self.adapter = ToolAdapter()

    @patch("agentkit_cli.tools.is_installed", return_value=False)
    def test_not_installed(self, _):
        assert self.adapter.agentreflect_from_git("/tmp") is None

    @patch("agentkit_cli.tools.is_installed", return_value=True)
    @patch("agentkit_cli.tools.subprocess.run")
    def test_success(self, mock_run, _):
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0,
            stdout="### Fix imports\nDo X\n### Add tests\nDo Y", stderr=""
        )
        result = self.adapter.agentreflect_from_git("/p")
        assert result["count"] == 2
        assert "### Fix imports" in result["suggestions_md"]

    @patch("agentkit_cli.tools.is_installed", return_value=True)
    @patch("agentkit_cli.tools.subprocess.run")
    def test_failure(self, mock_run, _):
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="error"
        )
        assert self.adapter.agentreflect_from_git("/p") is None


class TestAgentreflectFromNotes:
    def setup_method(self):
        self.adapter = ToolAdapter()

    @patch("agentkit_cli.tools.is_installed", return_value=False)
    def test_not_installed(self, _):
        assert self.adapter.agentreflect_from_notes("/tmp", "NOTES.md") is None

    @patch("agentkit_cli.tools.is_installed", return_value=True)
    @patch("agentkit_cli.tools.subprocess.run")
    def test_success(self, mock_run, _):
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0,
            stdout="### Note 1\nDetails", stderr=""
        )
        result = self.adapter.agentreflect_from_notes("/p", "NOTES.md")
        assert result["count"] == 1
        cmd = mock_run.call_args[0][0]
        assert "--from-notes" in cmd
        assert "NOTES.md" in cmd


# ---------------------------------------------------------------------------
# get_adapter singleton
# ---------------------------------------------------------------------------

def test_get_adapter_returns_same_instance():
    import agentkit_cli.tools as mod
    mod._default_adapter = None  # reset
    a1 = get_adapter()
    a2 = get_adapter()
    assert a1 is a2
    mod._default_adapter = None  # cleanup


# ---------------------------------------------------------------------------
# report_runner delegation
# ---------------------------------------------------------------------------

class TestReportRunnerDelegation:
    @patch("agentkit_cli.tools.is_installed", return_value=True)
    @patch("agentkit_cli.tools.subprocess.run")
    def test_run_agentlint_check_delegates(self, mock_run, _):
        from agentkit_cli.report_runner import run_agentlint_check
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout='{"ok": true}', stderr=""
        )
        result = run_agentlint_check("/p")
        assert result == {"ok": True}

    @patch("agentkit_cli.tools.is_installed", return_value=True)
    @patch("agentkit_cli.tools.subprocess.run")
    def test_run_agentmd_score_delegates(self, mock_run, _):
        from agentkit_cli.report_runner import run_agentmd_score
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout='{"score": 80}', stderr=""
        )
        result = run_agentmd_score("/p")
        assert result == {"score": 80}

    @patch("agentkit_cli.tools.is_installed", return_value=True)
    @patch("agentkit_cli.tools.subprocess.run")
    def test_run_coderace_bench_delegates(self, mock_run, _):
        from agentkit_cli.report_runner import run_coderace_bench
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout='{"data": []}', stderr=""
        )
        result = run_coderace_bench("/p")
        assert result == {"data": []}

    @patch("agentkit_cli.tools.is_installed", return_value=True)
    @patch("agentkit_cli.tools.subprocess.run")
    def test_run_agentreflect_delegates(self, mock_run, _):
        from agentkit_cli.report_runner import run_agentreflect_analyze
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="### S1\nDetails", stderr=""
        )
        result = run_agentreflect_analyze("/p")
        assert result is not None
        assert result["count"] == 1
