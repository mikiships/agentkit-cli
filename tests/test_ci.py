"""Tests for agentkit ci command."""
from __future__ import annotations

import yaml
from pathlib import Path
from typer.testing import CliRunner
from unittest.mock import patch

from agentkit_cli.main import app
from agentkit_cli.commands.ci import generate_workflow

runner = CliRunner()


# --- generate_workflow unit tests ---

def test_generate_workflow_returns_valid_yaml():
    """generate_workflow() returns parseable YAML."""
    raw = generate_workflow()
    data = yaml.safe_load(raw)
    assert isinstance(data, dict)
    assert "jobs" in data
    # PyYAML 1.1 parses bare 'on' as True; both forms are valid
    assert "on" in data or True in data


def test_generate_workflow_default_python_version():
    """Default python version is 3.12."""
    raw = generate_workflow()
    assert "3.12" in raw


def test_generate_workflow_custom_python_version():
    """Custom python version is embedded in workflow."""
    raw = generate_workflow(python_version="3.11")
    assert "3.11" in raw


def test_generate_workflow_triggers_pull_request():
    """Workflow triggers on pull_request by default."""
    raw = generate_workflow()
    # PyYAML parses bare 'on:' key as True (YAML 1.1)
    assert "pull_request" in raw


def test_generate_workflow_triggers_push_to_main():
    """Workflow triggers on push to main by default."""
    raw = generate_workflow()
    assert "push" in raw
    assert "main" in raw


def test_generate_workflow_no_benchmark_by_default():
    """Benchmark step is absent by default."""
    raw = generate_workflow(benchmark=False)
    assert "coderace benchmark" not in raw


def test_generate_workflow_with_benchmark():
    """--benchmark adds coderace benchmark step."""
    raw = generate_workflow(benchmark=True)
    assert "coderace benchmark" in raw


def test_generate_workflow_with_benchmark_valid_yaml():
    """Workflow with benchmark is valid YAML."""
    raw = generate_workflow(benchmark=True)
    data = yaml.safe_load(raw)
    assert isinstance(data, dict)


def test_generate_workflow_benchmark_includes_artifact():
    """Benchmark workflow includes artifact upload."""
    raw = generate_workflow(benchmark=True)
    assert "benchmark-summary" in raw or "benchmark" in raw
    assert "upload-artifact" in raw


def test_generate_workflow_with_min_score():
    """--min-score adds gating step."""
    raw = generate_workflow(min_score=80)
    assert "80" in raw
    assert "score" in raw.lower()


def test_generate_workflow_min_score_valid_yaml():
    """Workflow with min-score is valid YAML."""
    raw = generate_workflow(min_score=90)
    data = yaml.safe_load(raw)
    assert isinstance(data, dict)


def test_generate_workflow_installs_all_quartet_tools():
    """Generated workflow installs all four quartet tools."""
    raw = generate_workflow()
    assert "agentmd-gen" in raw
    assert "ai-agentlint" in raw
    assert "coderace" in raw
    assert "ai-agentreflect" in raw
    assert "agentkit-cli" in raw


def test_generate_workflow_runs_agentkit_run_ci():
    """Generated workflow runs `agentkit run --ci`."""
    raw = generate_workflow()
    assert "agentkit run --ci" in raw


def test_generate_workflow_checkout_step():
    """Workflow includes checkout step."""
    raw = generate_workflow()
    assert "checkout" in raw.lower()


def test_generate_workflow_setup_python_step():
    """Workflow includes setup-python step."""
    raw = generate_workflow()
    assert "setup-python" in raw


def test_generate_workflow_uploads_lint_report():
    """Generated workflow uploads lint report artifact."""
    raw = generate_workflow()
    assert "lint-report" in raw or "lint_report" in raw or "agentlint" in raw.lower()


# --- CLI integration tests ---

def test_ci_dry_run_prints_to_stdout(tmp_path):
    """agentkit ci --dry-run prints workflow to stdout."""
    result = runner.invoke(app, ["ci", "--dry-run"])
    assert result.exit_code == 0
    assert "name:" in result.output or "on:" in result.output


def test_ci_dry_run_valid_yaml(tmp_path):
    """agentkit ci --dry-run output is valid YAML."""
    result = runner.invoke(app, ["ci", "--dry-run"])
    assert result.exit_code == 0
    data = yaml.safe_load(result.output)
    assert isinstance(data, dict)


def test_ci_dry_run_benchmark_flag(tmp_path):
    """agentkit ci --dry-run --benchmark includes benchmark step."""
    result = runner.invoke(app, ["ci", "--dry-run", "--benchmark"])
    assert result.exit_code == 0
    assert "coderace" in result.output


def test_ci_dry_run_min_score(tmp_path):
    """agentkit ci --dry-run --min-score 80 adds gating step."""
    result = runner.invoke(app, ["ci", "--dry-run", "--min-score", "80"])
    assert result.exit_code == 0
    assert "80" in result.output


def test_ci_dry_run_python_version(tmp_path):
    """agentkit ci --dry-run --python-version 3.11."""
    result = runner.invoke(app, ["ci", "--dry-run", "--python-version", "3.11"])
    assert result.exit_code == 0
    assert "3.11" in result.output


def test_ci_writes_file(tmp_path):
    """agentkit ci writes workflow file to output-dir."""
    result = runner.invoke(app, [
        "ci",
        "--output-dir", str(tmp_path / "workflows"),
    ])
    assert result.exit_code == 0
    out_file = tmp_path / "workflows" / "agentkit.yml"
    assert out_file.exists()
    data = yaml.safe_load(out_file.read_text())
    assert isinstance(data, dict)


def test_ci_creates_output_dir(tmp_path):
    """agentkit ci creates output directory if it doesn't exist."""
    new_dir = tmp_path / "new" / "workflows"
    assert not new_dir.exists()
    result = runner.invoke(app, ["ci", "--output-dir", str(new_dir)])
    assert result.exit_code == 0
    assert new_dir.exists()


def test_ci_written_file_valid_yaml(tmp_path):
    """Written file is valid YAML."""
    result = runner.invoke(app, ["ci", "--output-dir", str(tmp_path)])
    assert result.exit_code == 0
    out_file = tmp_path / "agentkit.yml"
    assert out_file.exists()
    data = yaml.safe_load(out_file.read_text())
    assert isinstance(data, dict)
    assert "jobs" in data


def test_ci_help():
    """agentkit ci --help works."""
    result = runner.invoke(app, ["ci", "--help"])
    assert result.exit_code == 0
    assert "workflow" in result.output.lower() or "ci" in result.output.lower()
