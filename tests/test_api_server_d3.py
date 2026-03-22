"""Tests for D3: doctor api check + run --api-cache flag."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from typer.testing import CliRunner

from agentkit_cli.doctor import check_api_reachable, DoctorCheckResult
from agentkit_cli.main import app

runner = CliRunner()


# ---------------------------------------------------------------------------
# check_api_reachable
# ---------------------------------------------------------------------------

def test_check_api_reachable_pass():
    """Returns pass when server responds."""
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = check_api_reachable()
    assert result.status == "pass"
    assert result.category == "api"
    assert result.id == "api.reachable"


def test_check_api_reachable_warn():
    """Returns warn when server is not reachable."""
    with patch("urllib.request.urlopen", side_effect=ConnectionRefusedError("refused")):
        result = check_api_reachable()
    assert result.status == "warn"
    assert result.category == "api"
    assert "agentkit api" in result.fix_hint.lower() or "api" in result.fix_hint.lower()


def test_check_api_reachable_timeout():
    """Returns warn on timeout."""
    import socket
    with patch("urllib.request.urlopen", side_effect=socket.timeout("timed out")):
        result = check_api_reachable()
    assert result.status == "warn"


def test_check_api_reachable_returns_dataclass():
    """Result is a DoctorCheckResult."""
    with patch("urllib.request.urlopen", side_effect=Exception("any error")):
        result = check_api_reachable()
    assert isinstance(result, DoctorCheckResult)


def test_doctor_includes_api_check():
    """run_doctor includes api.reachable check."""
    from agentkit_cli.doctor import run_doctor
    with patch("urllib.request.urlopen", side_effect=ConnectionRefusedError("refused")):
        report = run_doctor(Path("."))
    ids = [c.id for c in report.checks]
    assert "api.reachable" in ids


def test_api_check_non_fatal():
    """api warn doesn't cause doctor exit code 1."""
    from agentkit_cli.doctor import run_doctor
    with patch("urllib.request.urlopen", side_effect=Exception("error")):
        report = run_doctor(Path("."))
    api_check = next(c for c in report.checks if c.id == "api.reachable")
    assert api_check.status == "warn"  # not fail


def test_doctor_api_check_custom_host():
    """check_api_reachable accepts custom host/port."""
    with patch("urllib.request.urlopen", side_effect=Exception("error")):
        result = check_api_reachable(host="0.0.0.0", port=9000)
    assert result.status == "warn"


# ---------------------------------------------------------------------------
# run --api-cache flag
# ---------------------------------------------------------------------------

def test_run_api_cache_option_exists():
    """--api-cache option is available in run command."""
    result = runner.invoke(app, ["run", "--help"])
    assert "--api-cache" in result.output
