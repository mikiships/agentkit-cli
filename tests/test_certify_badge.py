"""Tests for --badge flag and README inject (D4)."""
from __future__ import annotations

import re
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.commands.certify_cmd import (
    _build_badge_md,
    _inject_badge,
    _verdict_badge_url,
    BADGE_LINE_PATTERN,
)
from agentkit_cli.certify import CertResult, compute_sha256

runner = CliRunner()


def _make_result(verdict="PASS", score=85, redteam=75, freshness=80, tests=100):
    ts = "2026-01-01T00:00:00+00:00"
    payload = dict(timestamp=ts, score=score, redteam_score=redteam,
                   freshness_score=freshness, tests_found=tests, verdict=verdict)
    sha = compute_sha256(payload)
    return CertResult(timestamp=ts, score=score, redteam_score=redteam,
                      freshness_score=freshness, tests_found=tests, verdict=verdict,
                      sha256=sha, cert_id=sha[:8])


# ---------------------------------------------------------------------------
# Badge URL / Markdown helpers
# ---------------------------------------------------------------------------

def test_badge_url_pass():
    url = _verdict_badge_url("PASS")
    assert "PASS" in url
    assert "brightgreen" in url


def test_badge_url_warn():
    url = _verdict_badge_url("WARN")
    assert "WARN" in url
    assert "yellow" in url


def test_badge_url_fail():
    url = _verdict_badge_url("FAIL")
    assert "FAIL" in url
    assert "red" in url


def test_build_badge_md_contains_shields():
    md = _build_badge_md("PASS")
    assert "shields.io" in md
    assert "agentkit certified" in md


def test_build_badge_md_format():
    md = _build_badge_md("PASS")
    assert md.startswith("![agentkit certified](")


# ---------------------------------------------------------------------------
# README inject
# ---------------------------------------------------------------------------

def test_inject_badge_creates_badge_in_readme(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text("# My Project\n\nSome content.\n")
    result = _make_result("PASS")
    _inject_badge(result, tmp_path)
    content = readme.read_text()
    assert "agentkit certified" in content
    assert "PASS" in content


def test_inject_badge_idempotent(tmp_path):
    readme = tmp_path / "README.md"
    badge_line = "![agentkit certified](https://img.shields.io/badge/agentkit-PASS-brightgreen)"
    readme.write_text(f"{badge_line}\n\n# My Project\n")
    result = _make_result("PASS")
    _inject_badge(result, tmp_path)
    content = readme.read_text()
    # Should not have duplicate badges
    assert content.count("agentkit certified") == 1


def test_inject_badge_updates_verdict(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text("![agentkit certified](https://img.shields.io/badge/agentkit-PASS-brightgreen)\n\n# Repo\n")
    result = _make_result("FAIL", score=20, redteam=10, freshness=10)
    _inject_badge(result, tmp_path)
    content = readme.read_text()
    assert "FAIL" in content


def test_inject_badge_dry_run_does_not_write(tmp_path):
    readme = tmp_path / "README.md"
    original = "# My Project\n\nContent.\n"
    readme.write_text(original)
    result = _make_result("PASS")
    _inject_badge(result, tmp_path, dry_run=True)
    assert readme.read_text() == original


def test_inject_badge_no_readme_safe(tmp_path):
    """Should not raise if README.md doesn't exist."""
    result = _make_result("PASS")
    # No README in tmp_path — should complete without error
    _inject_badge(result, tmp_path)


# ---------------------------------------------------------------------------
# CLI --badge integration
# ---------------------------------------------------------------------------

def test_cli_badge_dry_run(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text("# Test\n")
    result_obj = _make_result("PASS")
    with patch("agentkit_cli.commands.certify_cmd.CertEngine") as MockEngine:
        MockEngine.return_value.certify.return_value = result_obj
        result = runner.invoke(app, ["certify", "--badge", "--dry-run", str(tmp_path)])
    assert result.exit_code == 0
    # README should be unchanged
    assert readme.read_text() == "# Test\n"


def test_cli_badge_injects(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text("# Test\n")
    result_obj = _make_result("PASS")
    with patch("agentkit_cli.commands.certify_cmd.CertEngine") as MockEngine:
        MockEngine.return_value.certify.return_value = result_obj
        result = runner.invoke(app, ["certify", "--badge", str(tmp_path)])
    assert result.exit_code == 0
    assert "agentkit certified" in readme.read_text()
