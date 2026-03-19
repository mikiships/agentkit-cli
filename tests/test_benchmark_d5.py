"""Tests for D5 — docs, version bump, and correctness checks."""
from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent


def test_version_in_init():
    import agentkit_cli
    assert agentkit_cli.__version__ == "0.56.0"


def test_version_in_pyproject():
    pyproject = (REPO_ROOT / "pyproject.toml").read_text()
    assert 'version = "0.56.0"' in pyproject


def test_changelog_has_entry():
    changelog = (REPO_ROOT / "CHANGELOG.md").read_text()
    assert "0.56.0" in changelog
    assert "benchmark" in changelog.lower()


def test_readme_has_benchmark_section():
    readme = (REPO_ROOT / "README.md").read_text()
    assert "benchmark" in readme.lower()
    assert "agentkit benchmark" in readme


def test_build_report_exists():
    assert (REPO_ROOT / "BUILD-REPORT.md").exists()


def test_benchmark_module_importable():
    from agentkit_cli.benchmark import BenchmarkEngine, BenchmarkReport, BenchmarkConfig
    assert BenchmarkEngine is not None


def test_benchmark_report_module_importable():
    from agentkit_cli.benchmark_report import BenchmarkReportRenderer, publish_benchmark
    assert BenchmarkReportRenderer is not None
