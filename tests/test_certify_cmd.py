"""Tests for agentkit certify CLI command (D2)."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.certify import CertResult

runner = CliRunner()


def make_fake_result(verdict="PASS", score=85, redteam=75, freshness=80, tests=100):
    """Build a CertResult without running subprocesses."""
    from agentkit_cli.certify import CertEngine, compute_sha256
    from datetime import datetime, timezone
    timestamp = "2026-01-01T00:00:00+00:00"
    payload = {
        "timestamp": timestamp,
        "score": score,
        "redteam_score": redteam,
        "freshness_score": freshness,
        "tests_found": tests,
        "verdict": verdict,
    }
    sha256 = compute_sha256(payload)
    return CertResult(
        timestamp=timestamp,
        score=score,
        redteam_score=redteam,
        freshness_score=freshness,
        tests_found=tests,
        verdict=verdict,
        sha256=sha256,
        cert_id=sha256[:8],
    )


@pytest.fixture
def fake_result_pass():
    return make_fake_result("PASS")


@pytest.fixture
def fake_result_fail():
    return make_fake_result("FAIL", score=30, redteam=20, freshness=10)


@pytest.fixture
def fake_result_warn():
    return make_fake_result("WARN", score=65, redteam=55, freshness=75)


def test_certify_help():
    result = runner.invoke(app, ["certify", "--help"])
    assert result.exit_code == 0
    assert "certification" in result.output.lower()


def test_certify_json_output(fake_result_pass):
    with patch("agentkit_cli.commands.certify_cmd.CertEngine") as MockEngine:
        MockEngine.return_value.certify.return_value = fake_result_pass
        result = runner.invoke(app, ["certify", "--json", "."])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["verdict"] == "PASS"
    assert data["score"] == 85


def test_certify_json_contains_all_fields(fake_result_pass):
    with patch("agentkit_cli.commands.certify_cmd.CertEngine") as MockEngine:
        MockEngine.return_value.certify.return_value = fake_result_pass
        result = runner.invoke(app, ["certify", "--json", "."])
    data = json.loads(result.output)
    for field in ("timestamp", "score", "redteam_score", "freshness_score", "tests_found", "verdict", "sha256", "cert_id"):
        assert field in data


def test_certify_console_shows_verdict(fake_result_pass):
    with patch("agentkit_cli.commands.certify_cmd.CertEngine") as MockEngine:
        MockEngine.return_value.certify.return_value = fake_result_pass
        result = runner.invoke(app, ["certify", "."])
    assert result.exit_code == 0
    assert "PASS" in result.output


def test_certify_console_shows_cert_id(fake_result_pass):
    with patch("agentkit_cli.commands.certify_cmd.CertEngine") as MockEngine:
        MockEngine.return_value.certify.return_value = fake_result_pass
        result = runner.invoke(app, ["certify", "."])
    assert fake_result_pass.cert_id in result.output


def test_certify_min_score_passes(fake_result_pass):
    with patch("agentkit_cli.commands.certify_cmd.CertEngine") as MockEngine:
        MockEngine.return_value.certify.return_value = fake_result_pass
        result = runner.invoke(app, ["certify", "--min-score", "80", "."])
    assert result.exit_code == 0


def test_certify_min_score_fails(fake_result_fail):
    with patch("agentkit_cli.commands.certify_cmd.CertEngine") as MockEngine:
        MockEngine.return_value.certify.return_value = fake_result_fail
        result = runner.invoke(app, ["certify", "--min-score", "80", "."])
    assert result.exit_code == 1


def test_certify_output_writes_html(fake_result_pass, tmp_path):
    out_file = tmp_path / "cert.html"
    with patch("agentkit_cli.commands.certify_cmd.CertEngine") as MockEngine:
        MockEngine.return_value.certify.return_value = fake_result_pass
        result = runner.invoke(app, ["certify", "--output", str(out_file), "."])
    assert result.exit_code == 0
    assert out_file.exists()
    content = out_file.read_text()
    assert "<!DOCTYPE html>" in content


def test_certify_warn_verdict_shown(fake_result_warn):
    with patch("agentkit_cli.commands.certify_cmd.CertEngine") as MockEngine:
        MockEngine.return_value.certify.return_value = fake_result_warn
        result = runner.invoke(app, ["certify", "."])
    assert "WARN" in result.output


def test_certify_fail_verdict_shown(fake_result_fail):
    with patch("agentkit_cli.commands.certify_cmd.CertEngine") as MockEngine:
        MockEngine.return_value.certify.return_value = fake_result_fail
        result = runner.invoke(app, ["certify", "."])
    assert "FAIL" in result.output


def test_certify_share_skipped_without_key(fake_result_pass):
    import os
    env = {k: v for k, v in os.environ.items() if k != "HERENOW_API_KEY"}
    with patch("agentkit_cli.commands.certify_cmd.CertEngine") as MockEngine:
        MockEngine.return_value.certify.return_value = fake_result_pass
        with patch.dict(os.environ, env, clear=True):
            result = runner.invoke(app, ["certify", "--share", "."])
    assert result.exit_code == 0
    assert "skipped" in result.output.lower() or "upload" in result.output.lower()
