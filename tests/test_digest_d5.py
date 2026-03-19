"""Tests for D5 — version bump, CHANGELOG, README, version string checks."""
from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent


def test_version_string():
    from agentkit_cli import __version__
    assert __version__ == "0.56.0"


def test_pyproject_version():
    pyproject = (REPO_ROOT / "pyproject.toml").read_text()
    assert 'version = "0.56.0"' in pyproject


def test_changelog_has_053():
    changelog = (REPO_ROOT / "CHANGELOG.md").read_text()
    assert "## [0.53.0]" in changelog


def test_changelog_digest_mentioned():
    changelog = (REPO_ROOT / "CHANGELOG.md").read_text()
    assert "digest" in changelog.lower()


def test_cli_version_flag():
    from typer.testing import CliRunner
    from agentkit_cli.main import app
    runner = CliRunner()
    result = runner.invoke(app, ["--version"])
    assert "0.56.0" in result.output


def test_digest_module_importable():
    from agentkit_cli.digest import DigestEngine, DigestReport, ProjectDigest
    assert DigestEngine is not None
    assert DigestReport is not None
    assert ProjectDigest is not None


def test_digest_report_module_importable():
    from agentkit_cli.digest_report import DigestReportRenderer
    assert DigestReportRenderer is not None
