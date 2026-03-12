"""Tests for action.yml GitHub Action definition."""
from __future__ import annotations

import yaml
from pathlib import Path

ACTION_PATH = Path(__file__).parent.parent / "action.yml"
WORKFLOW_PATH = Path(__file__).parent.parent / ".github/workflows/examples/agentkit-pipeline.yml"


def _load_action():
    with open(ACTION_PATH) as f:
        return yaml.safe_load(f)


def _load_workflow():
    with open(WORKFLOW_PATH) as f:
        return yaml.safe_load(f)


def test_action_yml_exists():
    assert ACTION_PATH.exists()


def test_action_has_required_inputs():
    data = _load_action()
    inputs = data["inputs"]
    assert "skip" in inputs
    assert "benchmark" in inputs
    assert "python-version" in inputs
    assert "fail-on-lint" in inputs


def test_action_is_composite():
    data = _load_action()
    assert data["runs"]["using"] == "composite"


def test_action_has_steps():
    data = _load_action()
    steps = data["runs"]["steps"]
    assert len(steps) >= 4


def test_action_has_name_and_description():
    data = _load_action()
    assert "name" in data
    assert "description" in data


def test_action_default_python_version():
    data = _load_action()
    assert data["inputs"]["python-version"]["default"] == "3.12"


def test_action_benchmark_default_false():
    data = _load_action()
    assert data["inputs"]["benchmark"]["default"] == "false"


def test_action_fail_on_lint_default_true():
    data = _load_action()
    assert data["inputs"]["fail-on-lint"]["default"] == "true"


def test_example_workflow_exists():
    assert WORKFLOW_PATH.exists()


def test_example_workflow_valid_yaml():
    data = _load_workflow()
    assert "jobs" in data
    # 'on' is parsed as True by PyYAML (YAML 1.1 bool quirk)
    assert "jobs" in data and len(data) >= 2
