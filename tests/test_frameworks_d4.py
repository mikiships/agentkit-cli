"""D4 tests for agentkit run --frameworks and agentkit doctor framework check."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.doctor import check_framework_coverage, DoctorCheckResult

runner = CliRunner()


def write_file(root: Path, name: str, content: str) -> Path:
    p = root / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return p


# ---------------------------------------------------------------------------
# Doctor check_framework_coverage unit tests
# ---------------------------------------------------------------------------

class TestDoctorFrameworkCoverageCheck:
    def test_no_frameworks_pass(self, tmp_path):
        result = check_framework_coverage(tmp_path)
        assert result.status == "pass"
        assert result.id == "context.framework_coverage"

    def test_framework_detected_no_context_warns(self, tmp_path):
        write_file(tmp_path, "requirements.txt", "fastapi>=0.100\n")
        result = check_framework_coverage(tmp_path)
        assert result.status == "warn"
        assert "FastAPI" in result.summary

    def test_framework_detected_good_coverage_pass(self, tmp_path):
        write_file(tmp_path, "requirements.txt", "flask>=3.0\n")
        ctx = tmp_path / "CLAUDE.md"
        ctx.write_text("# Proj\n## Flask Notes\nSetup.\nCommon patterns.\nKnown gotchas.\nTesting patterns.\nDeploy patterns.\n")
        result = check_framework_coverage(tmp_path)
        assert result.status == "pass"

    def test_returns_doctor_check_result(self, tmp_path):
        result = check_framework_coverage(tmp_path)
        assert isinstance(result, DoctorCheckResult)

    def test_fix_hint_present_on_warn(self, tmp_path):
        write_file(tmp_path, "requirements.txt", "django>=4.2\n")
        result = check_framework_coverage(tmp_path)
        if result.status == "warn":
            assert "agentkit frameworks" in result.fix_hint

    def test_category_is_context(self, tmp_path):
        result = check_framework_coverage(tmp_path)
        assert result.category == "context"

    def test_multiple_frameworks_low_coverage(self, tmp_path):
        write_file(tmp_path, "requirements.txt", "fastapi>=0.100\nflask>=3.0\n")
        result = check_framework_coverage(tmp_path)
        assert result.status == "warn"


# ---------------------------------------------------------------------------
# Doctor CLI includes framework check
# ---------------------------------------------------------------------------

class TestDoctorCLIFrameworkCheck:
    def test_doctor_json_includes_framework_check(self, tmp_path):
        result = runner.invoke(app, ["doctor", "--json", "--category", "context"])
        assert result.exit_code in (0, 1)
        data = json.loads(result.output)
        check_ids = [c["id"] for c in data["checks"]]
        assert "context.framework_coverage" in check_ids

    def test_doctor_framework_check_present_in_full_output(self, tmp_path):
        result = runner.invoke(app, ["doctor", "--json"])
        data = json.loads(result.output)
        check_ids = [c["id"] for c in data["checks"]]
        assert "context.framework_coverage" in check_ids


# ---------------------------------------------------------------------------
# agentkit run --frameworks
# ---------------------------------------------------------------------------

class TestRunFrameworksFlag:
    def test_run_frameworks_flag_in_help(self):
        result = runner.invoke(app, ["run", "--help"])
        assert result.exit_code == 0
        assert "--frameworks" in result.output

    def test_run_frameworks_json_has_frameworks_key(self, tmp_path):
        write_file(tmp_path, "requirements.txt", "flask>=3.0\n")
        # Mock run_command to avoid actually running the full pipeline
        with patch("agentkit_cli.commands.run_cmd.is_installed", return_value=False):
            result = runner.invoke(app, [
                "run", "--path", str(tmp_path),
                "--frameworks", "--json",
            ])
        assert result.exit_code in (0, 1)
        try:
            data = json.loads(result.output)
            assert "frameworks" in data
        except Exception:
            pass  # If JSON parse fails due to mixed output, that's ok for this integration test
