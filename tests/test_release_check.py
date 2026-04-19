from __future__ import annotations

import json
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.release_check import (
    CheckResult,
    ReleaseCheckResult,
    _detect_registry,
    _parse_pyproject_manual,
    check_git_push,
    check_git_tag,
    check_registry_npm,
    check_registry_pypi,
    resolve_metadata,
    run_release_check,
    write_step_summary,
)


runner = CliRunner()


def _make_completed(returncode=0, stdout="", stderr=""):
    m = MagicMock()
    m.returncode = returncode
    m.stdout = stdout
    m.stderr = stderr
    return m


class TestCheckGitPush:
    def test_pass_when_branch_clean_and_synced(self, tmp_path):
        def run_mock(cmd, **kwargs):
            key = " ".join(cmd)
            if "git rev-parse HEAD" in key:
                return _make_completed(0, "abc123456789\n")
            if "git rev-parse --abbrev-ref HEAD" in key:
                return _make_completed(0, "main\n")
            if "git status --porcelain" in key:
                return _make_completed(0, "")
            if "@{upstream}" in key:
                return _make_completed(0, "origin/main\n")
            if "git rev-parse origin/main" in key:
                return _make_completed(0, "abc123456789\n")
            if "git rev-list --left-right --count origin/main...HEAD" in key:
                return _make_completed(0, "0\t0\n")
            raise AssertionError(key)

        with patch("agentkit_cli.release_check.subprocess.run", side_effect=run_mock):
            result = check_git_push(tmp_path)

        assert result.status == "pass"
        assert "origin/main" in result.detail

    def test_fail_when_dirty(self, tmp_path):
        def run_mock(cmd, **kwargs):
            key = " ".join(cmd)
            if "git rev-parse HEAD" in key:
                return _make_completed(0, "abc123\n")
            if "git rev-parse --abbrev-ref HEAD" in key:
                return _make_completed(0, "main\n")
            if "git status --porcelain" in key:
                return _make_completed(0, " M README.md\n")
            raise AssertionError(key)

        with patch("agentkit_cli.release_check.subprocess.run", side_effect=run_mock):
            result = check_git_push(tmp_path)

        assert result.status == "fail"
        assert "dirty" in result.detail.lower()
        assert "commit or stash" in result.hint.lower()

    def test_fail_when_detached_head(self, tmp_path):
        def run_mock(cmd, **kwargs):
            key = " ".join(cmd)
            if "git rev-parse HEAD" in key:
                return _make_completed(0, "abc123\n")
            if "git rev-parse --abbrev-ref HEAD" in key:
                return _make_completed(0, "HEAD\n")
            raise AssertionError(key)

        with patch("agentkit_cli.release_check.subprocess.run", side_effect=run_mock):
            result = check_git_push(tmp_path)

        assert result.status == "fail"
        assert "detached" in result.detail.lower()
        assert "check out the release branch" in result.hint.lower()

    def test_fail_when_upstream_missing(self, tmp_path):
        def run_mock(cmd, **kwargs):
            key = " ".join(cmd)
            if "git rev-parse HEAD" in key:
                return _make_completed(0, "abc123\n")
            if "git rev-parse --abbrev-ref HEAD" in key:
                return _make_completed(0, "main\n")
            if "git status --porcelain" in key:
                return _make_completed(0, "")
            if "@{upstream}" in key:
                return _make_completed(1, "", "fatal: no upstream configured")
            raise AssertionError(key)

        with patch("agentkit_cli.release_check.subprocess.run", side_effect=run_mock):
            result = check_git_push(tmp_path)

        assert result.status == "fail"
        assert "no upstream" in result.detail.lower()
        assert "--set-upstream" in result.hint

    def test_fail_when_upstream_ref_not_available_locally(self, tmp_path):
        def run_mock(cmd, **kwargs):
            key = " ".join(cmd)
            if "git rev-parse HEAD" in key:
                return _make_completed(0, "abc123\n")
            if "git rev-parse --abbrev-ref HEAD" in key:
                return _make_completed(0, "main\n")
            if "git status --porcelain" in key:
                return _make_completed(0, "")
            if key == "git rev-parse --abbrev-ref --symbolic-full-name @{upstream}":
                return _make_completed(0, "origin/main\n")
            if key == "git rev-parse origin/main":
                return _make_completed(1, "", "fatal: ambiguous argument 'origin/main'")
            raise AssertionError(key)

        with patch("agentkit_cli.release_check.subprocess.run", side_effect=run_mock):
            result = check_git_push(tmp_path)

        assert result.status == "fail"
        assert "not available locally" in result.detail.lower()
        assert "git fetch --prune" in result.hint


class TestCheckGitTag:
    def test_pass_when_lightweight_local_and_remote_tag_match_head(self, tmp_path):
        def run_mock(cmd, **kwargs):
            key = " ".join(cmd)
            if key == "git rev-parse HEAD":
                return _make_completed(0, "abc123456789\n")
            if key == "git rev-parse v1.2.3^{}":
                return _make_completed(0, "abc123456789\n")
            if key == "git ls-remote --tags origin v1.2.3":
                return _make_completed(0, "abc123456789\trefs/tags/v1.2.3\n")
            raise AssertionError(key)

        with patch("agentkit_cli.release_check.subprocess.run", side_effect=run_mock):
            result = check_git_tag(tmp_path, "1.2.3")

        assert result.status == "pass"

    def test_pass_when_annotated_remote_tag_peels_to_head(self, tmp_path):
        def run_mock(cmd, **kwargs):
            key = " ".join(cmd)
            if key == "git rev-parse HEAD":
                return _make_completed(0, "abc123456789\n")
            if key == "git rev-parse v1.2.3^{}":
                return _make_completed(0, "abc123456789\n")
            if key == "git ls-remote --tags origin v1.2.3":
                return _make_completed(
                    0,
                    "deadbeefdeadbeef\trefs/tags/v1.2.3\nabc123456789\trefs/tags/v1.2.3^{}\n",
                )
            raise AssertionError(key)

        with patch("agentkit_cli.release_check.subprocess.run", side_effect=run_mock):
            result = check_git_tag(tmp_path, "1.2.3")

        assert result.status == "pass"

    def test_fail_when_local_tag_missing(self, tmp_path):
        def run_mock(cmd, **kwargs):
            key = " ".join(cmd)
            if key == "git rev-parse HEAD":
                return _make_completed(0, "abc123456789\n")
            if key == "git rev-parse v1.2.3^{}":
                return _make_completed(1, "", "unknown revision")
            raise AssertionError(key)

        with patch("agentkit_cli.release_check.subprocess.run", side_effect=run_mock):
            result = check_git_tag(tmp_path, "1.2.3")

        assert result.status == "fail"
        assert "does not exist" in result.detail

    def test_fail_when_local_tag_points_away_from_head(self, tmp_path):
        def run_mock(cmd, **kwargs):
            key = " ".join(cmd)
            if key == "git rev-parse HEAD":
                return _make_completed(0, "abc123456789\n")
            if key == "git rev-parse v1.2.3^{}":
                return _make_completed(0, "def987654321\n")
            raise AssertionError(key)

        with patch("agentkit_cli.release_check.subprocess.run", side_effect=run_mock):
            result = check_git_tag(tmp_path, "1.2.3")

        assert result.status == "fail"
        assert "but HEAD is" in result.detail

    def test_fail_when_remote_tag_missing(self, tmp_path):
        def run_mock(cmd, **kwargs):
            key = " ".join(cmd)
            if key == "git rev-parse HEAD":
                return _make_completed(0, "abc123456789\n")
            if key == "git rev-parse v1.2.3^{}":
                return _make_completed(0, "abc123456789\n")
            if key == "git ls-remote --tags origin v1.2.3":
                return _make_completed(0, "")
            raise AssertionError(key)

        with patch("agentkit_cli.release_check.subprocess.run", side_effect=run_mock):
            result = check_git_tag(tmp_path, "1.2.3")

        assert result.status == "fail"
        assert "remote origin is missing" in result.detail
        assert "git push origin v1.2.3" in result.hint

    def test_fail_when_remote_tag_has_no_usable_ref(self, tmp_path):
        def run_mock(cmd, **kwargs):
            key = " ".join(cmd)
            if key == "git rev-parse HEAD":
                return _make_completed(0, "abc123456789\n")
            if key == "git rev-parse v1.2.3^{}":
                return _make_completed(0, "abc123456789\n")
            if key == "git ls-remote --tags origin v1.2.3":
                return _make_completed(0, "abc123456789\trefs/tags/other-tag\n")
            raise AssertionError(key)

        with patch("agentkit_cli.release_check.subprocess.run", side_effect=run_mock):
            result = check_git_tag(tmp_path, "1.2.3")

        assert result.status == "fail"
        assert "no usable ref" in result.detail.lower()

    def test_fail_when_remote_tag_points_away_from_head(self, tmp_path):
        def run_mock(cmd, **kwargs):
            key = " ".join(cmd)
            if key == "git rev-parse HEAD":
                return _make_completed(0, "abc123456789\n")
            if key == "git rev-parse v1.2.3^{}":
                return _make_completed(0, "abc123456789\n")
            if key == "git ls-remote --tags origin v1.2.3":
                return _make_completed(0, "def987654321\trefs/tags/v1.2.3\n")
            raise AssertionError(key)

        with patch("agentkit_cli.release_check.subprocess.run", side_effect=run_mock):
            result = check_git_tag(tmp_path, "1.2.3")

        assert result.status == "fail"
        assert "Remote tag v1.2.3 points to def98765" in result.detail


class TestRegistryChecks:
    def _mock_response(self, status, body=b'{"info": {"version": "1.0.0"}, "version": "1.0.0"}'):
        m = MagicMock()
        m.status = status
        m.read.return_value = body
        m.__enter__ = lambda s: s
        m.__exit__ = MagicMock(return_value=False)
        return m

    def test_pypi_version_mismatch(self):
        with patch("urllib.request.urlopen") as mock_open:
            mock_open.return_value = self._mock_response(200, b'{"info": {"version": "9.9.9"}}')
            result = check_registry_pypi("mypkg", "1.0.0")
        assert result.status == "fail"
        assert "expected 1.0.0" in result.detail

    def test_npm_404(self):
        with patch("urllib.request.urlopen") as mock_open:
            mock_open.side_effect = urllib.error.HTTPError(None, 404, "Not Found", {}, None)
            result = check_registry_npm("mypkg", "1.0.0")
        assert result.status == "fail"


class TestMetadataAndReport:
    def test_detect_registry(self, tmp_path):
        (tmp_path / "package.json").write_text('{"name": "pkg", "version": "1.0.0"}')
        assert _detect_registry(tmp_path) == "npm"

    def test_parse_pyproject_manual(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "pkg"\nversion = "1.2.3"\n')
        assert _parse_pyproject_manual(tmp_path) == ("pkg", "1.2.3")

    def test_resolve_metadata(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "pkg"\nversion = "1.2.3"\n')
        assert resolve_metadata(tmp_path, None, None, "auto") == ("pkg", "1.2.3", "pypi")

    def test_release_result_as_dict_contains_markdown(self):
        result = ReleaseCheckResult(
            verdict="RELEASE-READY",
            package="agentkit-cli",
            version="0.96.0",
            registry="pypi",
            path="/tmp/repo",
            checks=[CheckResult("git_push", "pass", "ok")],
        )
        data = result.as_dict()
        assert data["markdown"].startswith("# agentkit release-check")

    def test_release_result_markdown_is_deterministic_and_escaped(self):
        result = ReleaseCheckResult(
            verdict="SHIPPED",
            package="agentkit-cli",
            version="0.96.0",
            registry="pypi",
            path="/tmp/repo",
            checks=[
                CheckResult("smoke_tests", "pass", "2 passed", ""),
                CheckResult("registry", "fail", "expected a|b\nnext", "publish | verify"),
            ],
        )

        assert result.to_markdown() == "\n".join([
            "# agentkit release-check",
            "",
            "- Verdict: **SHIPPED**",
            "- Path: `/tmp/repo`",
            "- Package: `agentkit-cli`",
            "- Version: `0.96.0`",
            "- Registry: `pypi`",
            "",
            "| Surface | Status | Detail | Hint |",
            "|---|---|---|---|",
            "| smoke_tests | pass | 2 passed |  |",
            "| registry | fail | expected a\\|b<br>next | publish \\| verify |",
        ])

    def test_write_step_summary(self, tmp_path):
        result = ReleaseCheckResult(path=str(tmp_path), checks=[CheckResult("git_push", "pass", "ok")])
        out = tmp_path / "summary.md"
        write_step_summary(result, out)
        assert out.exists()
        assert out.read_text().endswith("\n")
        assert "agentkit release-check" in out.read_text()


class TestRunReleaseCheck:
    def test_release_ready_when_registry_missing(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "agentkit-cli"\nversion = "0.96.0"\n')
        with patch("agentkit_cli.release_check.check_smoke_tests", return_value=CheckResult("smoke_tests", "pass", "ok")), \
             patch("agentkit_cli.release_check.check_tests", return_value=CheckResult("tests", "pass", "ok")), \
             patch("agentkit_cli.release_check.check_git_push", return_value=CheckResult("git_push", "pass", "ok")), \
             patch("agentkit_cli.release_check.check_git_tag", return_value=CheckResult("git_tag", "pass", "ok")), \
             patch("agentkit_cli.release_check.check_registry_pypi", return_value=CheckResult("registry", "fail", "missing")):
            result = run_release_check(path=tmp_path)
        assert result.verdict == "RELEASE-READY"

    def test_unknown_when_tests_fail(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "agentkit-cli"\nversion = "0.96.0"\n')
        with patch("agentkit_cli.release_check.check_smoke_tests", return_value=CheckResult("smoke_tests", "pass", "ok")), \
             patch("agentkit_cli.release_check.check_tests", return_value=CheckResult("tests", "fail", "boom")), \
             patch("agentkit_cli.release_check.check_git_push", return_value=CheckResult("git_push", "pass", "ok")), \
             patch("agentkit_cli.release_check.check_git_tag", return_value=CheckResult("git_tag", "pass", "ok")), \
             patch("agentkit_cli.release_check.check_registry_pypi", return_value=CheckResult("registry", "pass", "ok")):
            result = run_release_check(path=tmp_path)
        assert result.verdict == "UNKNOWN"


class TestCLI:
    def test_release_check_json_output_contains_markdown(self, tmp_path):
        with patch("agentkit_cli.commands.release_check_cmd.run_release_check") as mock_run:
            mock_run.return_value = ReleaseCheckResult(
                verdict="RELEASE-READY",
                package="agentkit-cli",
                version="0.96.0",
                registry="pypi",
                path=str(tmp_path),
                checks=[CheckResult("git_push", "pass", "ok")],
            )
            result = runner.invoke(app, ["release-check", str(tmp_path), "--json"])

        assert result.exit_code == 1
        data = json.loads(result.output)
        assert data["markdown"].startswith("# agentkit release-check")

    def test_release_check_help_mentions_release(self):
        result = runner.invoke(app, ["release-check", "--help"])
        assert result.exit_code == 0
        assert "release" in result.output.lower()
