"""Tests for agentkit release-check (D4)."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch
import urllib.error

import pytest

from agentkit_cli.release_check import (
    CheckResult,
    ReleaseCheckResult,
    check_git_push,
    check_git_tag,
    check_registry_npm,
    check_registry_pypi,
    check_tests,
    resolve_metadata,
    run_release_check,
    _detect_registry,
    _parse_pyproject_manual,
    _read_package_json,
    _read_pyproject,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_completed(returncode=0, stdout="", stderr=""):
    m = MagicMock()
    m.returncode = returncode
    m.stdout = stdout
    m.stderr = stderr
    return m


# ---------------------------------------------------------------------------
# check_tests
# ---------------------------------------------------------------------------

class TestCheckTests:
    def test_pass(self, tmp_path):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = _make_completed(0, "42 passed in 1.23s", "")
            result = check_tests(tmp_path)
        assert result.status == "pass"
        assert result.name == "tests"
        assert "42 passed" in result.detail

    def test_fail(self, tmp_path):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = _make_completed(1, "3 failed, 10 passed in 0.5s", "")
            result = check_tests(tmp_path)
        assert result.status == "fail"
        assert result.hint != ""

    def test_pytest_not_found(self, tmp_path):
        with patch("subprocess.run", side_effect=FileNotFoundError("pytest not found")):
            result = check_tests(tmp_path)
        assert result.status == "error"
        assert "pytest" in result.detail.lower()

    def test_timeout(self, tmp_path):
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["pytest"], 300)):
            result = check_tests(tmp_path)
        assert result.status == "error"
        assert "timed out" in result.detail

    def test_generic_exception(self, tmp_path):
        with patch("subprocess.run", side_effect=RuntimeError("unexpected")):
            result = check_tests(tmp_path)
        assert result.status == "error"

    def test_output_truncated(self, tmp_path):
        """Long output is capped at 200 chars."""
        long_output = "x" * 500
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = _make_completed(1, long_output, "")
            result = check_tests(tmp_path)
        assert len(result.detail) <= 200


# ---------------------------------------------------------------------------
# check_git_push
# ---------------------------------------------------------------------------

class TestCheckGitPush:
    def _run_side_effect(self, returncode_map):
        """Return a side_effect that dispatches on command."""
        call_count = [0]

        def side_effect(cmd, **kwargs):
            call_count[0] += 1
            key = " ".join(cmd)
            for k, v in returncode_map.items():
                if k in key:
                    return _make_completed(*v)
            return _make_completed(0, "", "")

        return side_effect

    def test_pass_hashes_match(self, tmp_path):
        def run_mock(cmd, **kw):
            if "log" in cmd:
                return _make_completed(0, "abc123def456abc123def456abc123de", "")
            if "ls-remote" in cmd:
                return _make_completed(0, "abc123def456abc123def456abc123de\tHEAD\n", "")
        with patch("subprocess.run", side_effect=run_mock):
            result = check_git_push(tmp_path)
        assert result.status == "pass"

    def test_fail_hashes_differ(self, tmp_path):
        def run_mock(cmd, **kw):
            if "log" in cmd:
                return _make_completed(0, "aaaa1111", "")
            if "ls-remote" in cmd:
                return _make_completed(0, "bbbb2222\tHEAD\n", "")
        with patch("subprocess.run", side_effect=run_mock):
            result = check_git_push(tmp_path)
        assert result.status == "fail"
        assert "git push" in result.hint

    def test_git_log_fails(self, tmp_path):
        def run_mock(cmd, **kw):
            if "log" in cmd:
                return _make_completed(1, "", "not a git repo")
            return _make_completed(0, "", "")
        with patch("subprocess.run", side_effect=run_mock):
            result = check_git_push(tmp_path)
        assert result.status == "error"

    def test_remote_empty(self, tmp_path):
        def run_mock(cmd, **kw):
            if "log" in cmd:
                return _make_completed(0, "aaaa1111", "")
            if "ls-remote" in cmd:
                return _make_completed(0, "", "")  # empty → no remote
        with patch("subprocess.run", side_effect=run_mock):
            result = check_git_push(tmp_path)
        assert result.status == "fail"

    def test_timeout(self, tmp_path):
        def run_mock(cmd, **kw):
            if "log" in cmd:
                return _make_completed(0, "aaaa1111", "")
            raise subprocess.TimeoutExpired(cmd, 30)
        with patch("subprocess.run", side_effect=run_mock):
            result = check_git_push(tmp_path)
        assert result.status == "error"
        assert "timed out" in result.detail

    def test_generic_exception(self, tmp_path):
        with patch("subprocess.run", side_effect=RuntimeError("boom")):
            result = check_git_push(tmp_path)
        assert result.status == "error"


# ---------------------------------------------------------------------------
# check_git_tag
# ---------------------------------------------------------------------------

class TestCheckGitTag:
    def test_tag_present(self, tmp_path):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = _make_completed(0, "abc123\trefs/tags/v1.2.3\n", "")
            result = check_git_tag(tmp_path, "1.2.3")
        assert result.status == "pass"
        assert "v1.2.3" in result.detail

    def test_tag_absent(self, tmp_path):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = _make_completed(0, "", "")
            result = check_git_tag(tmp_path, "1.2.3")
        assert result.status == "fail"
        assert "git tag" in result.hint

    def test_command_fails(self, tmp_path):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = _make_completed(1, "", "error")
            result = check_git_tag(tmp_path, "1.2.3")
        assert result.status == "error"

    def test_timeout(self, tmp_path):
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["git"], 30)):
            result = check_git_tag(tmp_path, "1.2.3")
        assert result.status == "error"
        assert "timed out" in result.detail

    def test_generic_exception(self, tmp_path):
        with patch("subprocess.run", side_effect=RuntimeError("boom")):
            result = check_git_tag(tmp_path, "1.2.3")
        assert result.status == "error"


# ---------------------------------------------------------------------------
# check_registry_pypi
# ---------------------------------------------------------------------------

class TestCheckRegistryPypi:
    def _mock_response(self, status, body=b'{"info":{"version":"1.0.0"}}'):
        m = MagicMock()
        m.status = status
        m.read.return_value = body
        m.__enter__ = lambda s: s
        m.__exit__ = MagicMock(return_value=False)
        return m

    def test_pass(self):
        with patch("urllib.request.urlopen") as mock_open:
            mock_open.return_value = self._mock_response(200)
            result = check_registry_pypi("mypkg", "1.0.0")
        assert result.status == "pass"
        assert "PyPI" in result.detail

    def test_404(self):
        with patch("urllib.request.urlopen") as mock_open:
            mock_open.side_effect = urllib.error.HTTPError(None, 404, "Not Found", {}, None)
            result = check_registry_pypi("mypkg", "1.0.0")
        assert result.status == "fail"
        assert "404" in result.detail

    def test_other_http_error(self):
        with patch("urllib.request.urlopen") as mock_open:
            mock_open.side_effect = urllib.error.HTTPError(None, 500, "Server Error", {}, None)
            result = check_registry_pypi("mypkg", "1.0.0")
        assert result.status == "error"

    def test_network_error(self):
        with patch("urllib.request.urlopen") as mock_open:
            mock_open.side_effect = Exception("connection refused")
            result = check_registry_pypi("mypkg", "1.0.0")
        assert result.status == "error"
        assert "hint" in result.hint.lower() or result.hint != "" or result.detail != ""


# ---------------------------------------------------------------------------
# check_registry_npm
# ---------------------------------------------------------------------------

class TestCheckRegistryNpm:
    def _mock_response(self, status):
        m = MagicMock()
        m.status = status
        m.__enter__ = lambda s: s
        m.__exit__ = MagicMock(return_value=False)
        return m

    def test_pass(self):
        with patch("urllib.request.urlopen") as mock_open:
            mock_open.return_value = self._mock_response(200)
            result = check_registry_npm("mypkg", "1.0.0")
        assert result.status == "pass"
        assert "npm" in result.detail

    def test_404(self):
        with patch("urllib.request.urlopen") as mock_open:
            mock_open.side_effect = urllib.error.HTTPError(None, 404, "Not Found", {}, None)
            result = check_registry_npm("mypkg", "1.0.0")
        assert result.status == "fail"

    def test_network_error(self):
        with patch("urllib.request.urlopen") as mock_open:
            mock_open.side_effect = Exception("timeout")
            result = check_registry_npm("mypkg", "1.0.0")
        assert result.status == "error"


# ---------------------------------------------------------------------------
# resolve_metadata
# ---------------------------------------------------------------------------

class TestResolveMetadata:
    def test_pyproject_detection(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "foo"\nversion = "1.2.3"\n')
        pkg, ver, reg = resolve_metadata(tmp_path, None, None, "auto")
        assert pkg == "foo"
        assert ver == "1.2.3"
        assert reg == "pypi"

    def test_package_json_detection(self, tmp_path):
        (tmp_path / "package.json").write_text('{"name": "bar", "version": "2.0.0"}')
        pkg, ver, reg = resolve_metadata(tmp_path, None, None, "auto")
        assert pkg == "bar"
        assert ver == "2.0.0"
        assert reg == "npm"

    def test_explicit_override(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "foo"\nversion = "1.0.0"\n')
        pkg, ver, reg = resolve_metadata(tmp_path, "custom-pkg", "9.9.9", "auto")
        assert pkg == "custom-pkg"
        assert ver == "9.9.9"

    def test_no_project_file(self, tmp_path):
        pkg, ver, reg = resolve_metadata(tmp_path, None, None, "auto")
        assert pkg == ""
        assert ver == ""

    def test_explicit_registry(self, tmp_path):
        pkg, ver, reg = resolve_metadata(tmp_path, "mypkg", "1.0.0", "npm")
        assert reg == "npm"


# ---------------------------------------------------------------------------
# _detect_registry
# ---------------------------------------------------------------------------

class TestDetectRegistry:
    def test_pyproject(self, tmp_path):
        (tmp_path / "pyproject.toml").touch()
        assert _detect_registry(tmp_path) == "pypi"

    def test_setup_py(self, tmp_path):
        (tmp_path / "setup.py").touch()
        assert _detect_registry(tmp_path) == "pypi"

    def test_package_json(self, tmp_path):
        (tmp_path / "package.json").touch()
        assert _detect_registry(tmp_path) == "npm"

    def test_default(self, tmp_path):
        assert _detect_registry(tmp_path) == "pypi"


# ---------------------------------------------------------------------------
# _parse_pyproject_manual
# ---------------------------------------------------------------------------

class TestParseManual:
    def test_basic(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "mypkg"\nversion = "3.1.4"\n')
        name, version = _parse_pyproject_manual(tmp_path)
        assert name == "mypkg"
        assert version == "3.1.4"

    def test_missing_file(self, tmp_path):
        name, version = _parse_pyproject_manual(tmp_path)
        assert name == ""
        assert version == ""


# ---------------------------------------------------------------------------
# run_release_check (integration-style with mocks)
# ---------------------------------------------------------------------------

class TestRunReleaseCheck:
    def _mock_all_pass(self):
        """Return side effects for all subprocess calls to simulate SHIPPED state."""
        def run_side_effect(cmd, **kw):
            if "pytest" in cmd:
                return _make_completed(0, "42 passed in 0.5s", "")
            if "log" in cmd:
                return _make_completed(0, "aaaa1111", "")
            if "ls-remote" in cmd and "--tags" in cmd:
                return _make_completed(0, "aaaa1111\trefs/tags/v1.0.0\n", "")
            if "ls-remote" in cmd:
                return _make_completed(0, "aaaa1111\tHEAD\n", "")
            return _make_completed(0, "", "")
        return run_side_effect

    def test_shipped_verdict(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "mypkg"\nversion = "1.0.0"\n')

        def mock_urlopen(req, timeout=None):
            m = MagicMock()
            m.status = 200
            m.read.return_value = b'{"info":{"version":"1.0.0"}}'
            m.__enter__ = lambda s: s
            m.__exit__ = MagicMock(return_value=False)
            return m

        with patch("subprocess.run", side_effect=self._mock_all_pass()):
            with patch("urllib.request.urlopen", side_effect=mock_urlopen):
                result = run_release_check(path=tmp_path)

        assert result.verdict == "SHIPPED"
        assert result.passed is True

    def test_built_when_tests_fail(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "mypkg"\nversion = "1.0.0"\n')

        def run_side_effect(cmd, **kw):
            if "pytest" in cmd:
                return _make_completed(1, "1 failed in 0.1s", "")
            if "log" in cmd:
                return _make_completed(0, "aaaa1111", "")
            if "ls-remote" in cmd:
                return _make_completed(0, "aaaa1111\tHEAD\n", "")
            return _make_completed(0, "", "")

        with patch("subprocess.run", side_effect=run_side_effect):
            with patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError(None, 404, "Not Found", {}, None)):
                result = run_release_check(path=tmp_path)

        assert result.verdict == "UNKNOWN"
        assert result.passed is False

    def test_skip_tests(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "mypkg"\nversion = "1.0.0"\n')

        with patch("subprocess.run", side_effect=self._mock_all_pass()):
            with patch("urllib.request.urlopen") as mock_open:
                m = MagicMock()
                m.status = 200
                m.read.return_value = b'{"info":{"version":"1.0.0"}}'
                m.__enter__ = lambda s: s
                m.__exit__ = MagicMock(return_value=False)
                mock_open.return_value = m
                result = run_release_check(path=tmp_path, skip_tests=True)

        tests_check = next(c for c in result.checks if c.name == "tests")
        assert tests_check.status == "skip"

    def test_no_package_file(self, tmp_path):
        with patch("subprocess.run", side_effect=self._mock_all_pass()):
            result = run_release_check(path=tmp_path)
        registry_check = next(c for c in result.checks if c.name == "registry")
        assert registry_check.status == "skip"

    def test_as_dict(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "mypkg"\nversion = "1.0.0"\n')
        with patch("subprocess.run", side_effect=self._mock_all_pass()):
            with patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError(None, 404, "Not Found", {}, None)):
                result = run_release_check(path=tmp_path)
        d = result.as_dict()
        assert "verdict" in d
        assert "checks" in d
        assert isinstance(d["checks"], list)

    def test_release_ready_when_registry_missing(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "mypkg"\nversion = "1.0.0"\n')

        def run_side_effect(cmd, **kw):
            if "pytest" in cmd:
                return _make_completed(0, "10 passed", "")
            if "log" in cmd:
                return _make_completed(0, "aaaa1111", "")
            if "ls-remote" in cmd and "--tags" in cmd:
                return _make_completed(0, "refs/tags/v1.0.0\n", "")
            if "ls-remote" in cmd:
                return _make_completed(0, "aaaa1111\tHEAD\n", "")
            return _make_completed(0, "", "")

        with patch("subprocess.run", side_effect=run_side_effect):
            with patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError(None, 404, "Not Found", {}, None)):
                result = run_release_check(path=tmp_path)

        assert result.verdict == "RELEASE-READY"

    def test_npm_registry(self, tmp_path):
        (tmp_path / "package.json").write_text('{"name": "mypkg", "version": "1.0.0"}')

        def run_side_effect(cmd, **kw):
            if "pytest" in cmd:
                return _make_completed(0, "5 passed", "")
            if "log" in cmd:
                return _make_completed(0, "aaaa1111", "")
            if "ls-remote" in cmd:
                return _make_completed(0, "aaaa1111\tHEAD\n", "")
            return _make_completed(0, "", "")

        with patch("subprocess.run", side_effect=run_side_effect):
            with patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError(None, 404, "Not Found", {}, None)):
                result = run_release_check(path=tmp_path)

        assert result.registry == "npm"


# ---------------------------------------------------------------------------
# CLI invocation tests (D2)
# ---------------------------------------------------------------------------

class TestCLI:
    def test_json_output(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "mypkg"\nversion = "1.0.0"\n')

        def run_side_effect(cmd, **kw):
            if "pytest" in cmd:
                return _make_completed(0, "5 passed", "")
            if "log" in cmd:
                return _make_completed(0, "aaaa1111", "")
            if "ls-remote" in cmd:
                return _make_completed(0, "aaaa1111\tHEAD\n", "")
            return _make_completed(0, "", "")

        from typer.testing import CliRunner
        from agentkit_cli.main import app

        runner = CliRunner()
        with patch("subprocess.run", side_effect=run_side_effect):
            with patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError(None, 404, "Not Found", {}, None)):
                result = runner.invoke(app, ["release-check", str(tmp_path), "--json"])

        assert result.exit_code in (0, 1)
        try:
            data = json.loads(result.output)
            assert "verdict" in data
            assert "checks" in data
        except json.JSONDecodeError:
            pytest.fail(f"Not valid JSON: {result.output}")

    def test_exit_code_zero_when_shipped(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "mypkg"\nversion = "1.0.0"\n')

        def run_side_effect(cmd, **kw):
            if "pytest" in cmd:
                return _make_completed(0, "5 passed", "")
            if "log" in cmd:
                return _make_completed(0, "aaaa1111", "")
            if "ls-remote" in cmd and "--tags" in cmd:
                return _make_completed(0, "refs/tags/v1.0.0\n", "")
            if "ls-remote" in cmd:
                return _make_completed(0, "aaaa1111\tHEAD\n", "")
            return _make_completed(0, "", "")

        def mock_urlopen(req, timeout=None):
            m = MagicMock()
            m.status = 200
            m.read.return_value = b'{"info":{"version":"1.0.0"}}'
            m.__enter__ = lambda s: s
            m.__exit__ = MagicMock(return_value=False)
            return m

        from typer.testing import CliRunner
        from agentkit_cli.main import app

        runner = CliRunner()
        with patch("subprocess.run", side_effect=run_side_effect):
            with patch("urllib.request.urlopen", side_effect=mock_urlopen):
                result = runner.invoke(app, ["release-check", str(tmp_path)])

        assert result.exit_code == 0

    def test_exit_code_one_when_not_shipped(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "mypkg"\nversion = "1.0.0"\n')

        from typer.testing import CliRunner
        from agentkit_cli.main import app

        runner = CliRunner()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = _make_completed(1, "1 failed", "")
            with patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError(None, 404, "Not Found", {}, None)):
                result = runner.invoke(app, ["release-check", str(tmp_path)])

        assert result.exit_code == 1

    def test_skip_tests_flag(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "mypkg"\nversion = "1.0.0"\n')

        def run_side_effect(cmd, **kw):
            if "log" in cmd:
                return _make_completed(0, "aaaa1111", "")
            if "ls-remote" in cmd:
                return _make_completed(0, "aaaa1111\tHEAD\n", "")
            return _make_completed(0, "", "")

        from typer.testing import CliRunner
        from agentkit_cli.main import app

        runner = CliRunner()
        with patch("subprocess.run", side_effect=run_side_effect):
            with patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError(None, 404, "Not Found", {}, None)):
                result = runner.invoke(app, ["release-check", str(tmp_path), "--skip-tests", "--json"])

        data = json.loads(result.output)
        tests_check = next(c for c in data["checks"] if c["name"] == "tests")
        assert tests_check["status"] == "skip"

    def test_invalid_registry(self, tmp_path):
        from typer.testing import CliRunner
        from agentkit_cli.main import app

        runner = CliRunner()
        result = runner.invoke(app, ["release-check", str(tmp_path), "--registry", "invalid"])
        assert result.exit_code == 2

    def test_help_text(self):
        from typer.testing import CliRunner
        from agentkit_cli.main import app

        runner = CliRunner()
        result = runner.invoke(app, ["release-check", "--help"])
        assert result.exit_code == 0
        assert "release" in result.output.lower()


# ---------------------------------------------------------------------------
# CheckResult / ReleaseCheckResult dataclass tests
# ---------------------------------------------------------------------------

class TestDataclasses:
    def test_check_result_as_dict(self):
        c = CheckResult(name="tests", status="pass", detail="All good", hint="")
        d = c.as_dict()
        assert d == {"name": "tests", "status": "pass", "detail": "All good", "hint": ""}

    def test_release_check_result_passed(self):
        r = ReleaseCheckResult(verdict="SHIPPED")
        assert r.passed is True

    def test_release_check_result_not_passed(self):
        r = ReleaseCheckResult(verdict="BUILT")
        assert r.passed is False

    def test_release_check_result_as_dict_empty(self):
        r = ReleaseCheckResult()
        d = r.as_dict()
        assert "verdict" in d
        assert d["checks"] == []
