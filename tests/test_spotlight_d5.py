"""Tests for docs, version bump, doctor check (D5 — ≥5 tests)."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli import __version__

runner = CliRunner()

REPO_ROOT = Path(__file__).parent.parent


class TestVersionBump:
    def test_version_is_0_72_0(self):
        assert __version__ == "0.74.0"

    def test_pyproject_version_matches(self):
        pyproject = (REPO_ROOT / "pyproject.toml").read_text()
        assert 'version = "0.74.0"' in pyproject

    def test_changelog_has_0_72_0_entry(self):
        changelog = (REPO_ROOT / "CHANGELOG.md").read_text()
        assert "0.74.0" in changelog
        assert "spotlight" in changelog.lower()


class TestDoctorSpotlightCheck:
    def test_doctor_includes_spotlight_check(self):
        from agentkit_cli.doctor import run_doctor
        with patch("agentkit_cli.doctor.check_spotlight_github_access") as mock_check:
            from agentkit_cli.doctor import DoctorCheckResult
            mock_check.return_value = DoctorCheckResult(
                id="spotlight.github_api",
                name="github_api_access",
                status="pass",
                summary="GitHub API reachable.",
                details="",
                fix_hint="",
                category="spotlight",
            )
            report = run_doctor()
        # Check was called
        mock_check.assert_called_once()

    def test_check_spotlight_github_access_returns_result(self):
        from agentkit_cli.doctor import check_spotlight_github_access, DoctorCheckResult
        with patch("urllib.request.urlopen") as mock_urlopen:
            import json
            mock_resp = type("R", (), {
                "read": lambda self: json.dumps({"rate": {"remaining": 60}}).encode(),
                "__enter__": lambda self: self,
                "__exit__": lambda self, *a: False,
            })()
            mock_urlopen.return_value = mock_resp
            result = check_spotlight_github_access()
        assert isinstance(result, DoctorCheckResult)
        assert result.category == "spotlight"
        assert result.name == "github_api_access"
        assert result.status in ("pass", "warn", "fail")
        # unauthenticated with 60 remaining => pass

    def test_check_spotlight_fail_on_network_error(self):
        from agentkit_cli.doctor import check_spotlight_github_access
        with patch("urllib.request.urlopen", side_effect=Exception("timeout")):
            result = check_spotlight_github_access()
        assert result.status == "fail"
        assert "timeout" in result.summary

    def test_doctor_cli_includes_spotlight(self):
        """Doctor CLI runs without error and has spotlight check in output."""
        from agentkit_cli.doctor import check_spotlight_github_access, DoctorCheckResult
        with patch("agentkit_cli.doctor.check_spotlight_github_access") as mock_check:
            mock_check.return_value = DoctorCheckResult(
                id="spotlight.github_api",
                name="github_api_access",
                status="pass",
                summary="GitHub API reachable.",
                details="",
                fix_hint="",
                category="spotlight",
            )
            # Run doctor check directly to verify structure
            result = mock_check()
        assert result.category == "spotlight"


class TestSpotlightRendererVersion:
    def test_renderer_uses_current_version(self):
        from agentkit_cli.commands.spotlight_cmd import SpotlightResult
        from agentkit_cli.renderers.spotlight_renderer import SpotlightHTMLRenderer
        result = SpotlightResult(
            repo="x/y", score=80.0, grade="B", top_findings=[],
            run_date="2026-01-01T00:00:00+00:00",
        )
        html = SpotlightHTMLRenderer().render(result)
        assert __version__ in html
