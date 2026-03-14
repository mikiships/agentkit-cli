"""Tests for action.yml GitHub Action definition and supporting scripts."""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import yaml

REPO_ROOT = Path(__file__).parent.parent
ACTION_PATH = REPO_ROOT / "action.yml"
SCRIPTS_DIR = REPO_ROOT / "scripts"
EXAMPLES_DIR = REPO_ROOT / "examples"
RUN_SCRIPT = SCRIPTS_DIR / "run-agentkit-action.py"
POST_SCRIPT = SCRIPTS_DIR / "post-pr-comment.py"
EXAMPLE_WORKFLOW = EXAMPLES_DIR / "agentkit-quality.yml"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_action():
    with open(ACTION_PATH) as f:
        return yaml.safe_load(f)


def _load_module(path: Path, module_name: str) -> types.ModuleType:
    """Load a Python script as a module without executing __main__."""
    spec = importlib.util.spec_from_file_location(module_name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# D1 — action.yml structure tests
# ---------------------------------------------------------------------------

def test_action_yml_exists():
    assert ACTION_PATH.exists()


def test_action_is_composite():
    data = _load_action()
    assert data["runs"]["using"] == "composite"


def test_action_has_name_and_description():
    data = _load_action()
    assert "name" in data
    assert "description" in data


def test_action_has_required_inputs():
    data = _load_action()
    inputs = data["inputs"]
    assert "python-version" in inputs
    assert "min-lint-score" in inputs
    assert "post-comment" in inputs
    assert "github-token" in inputs


def test_action_github_token_required():
    data = _load_action()
    assert data["inputs"]["github-token"].get("required") is True


def test_action_default_python_version():
    data = _load_action()
    assert data["inputs"]["python-version"]["default"] == "3.11"


def test_action_default_min_lint_score():
    data = _load_action()
    assert data["inputs"]["min-lint-score"]["default"] == "70"


def test_action_default_post_comment():
    data = _load_action()
    assert data["inputs"]["post-comment"]["default"] == "true"


def test_action_has_outputs():
    data = _load_action()
    outputs = data.get("outputs", {})
    assert "lint-score" in outputs
    assert "drift-status" in outputs
    assert "review-summary" in outputs


def test_action_has_steps():
    data = _load_action()
    assert len(data["runs"]["steps"]) >= 3


# ---------------------------------------------------------------------------
# D1 — run-agentkit-action.py tests
# ---------------------------------------------------------------------------

def test_run_script_exists():
    assert RUN_SCRIPT.exists()


def test_post_script_exists():
    assert POST_SCRIPT.exists()


def _load_run_module():
    return _load_module(RUN_SCRIPT, "run_agentkit_action")


def test_find_context_file_returns_none_when_missing(tmp_path):
    mod = _load_run_module()
    result = mod.find_context_file(tmp_path)
    assert result is None


def test_find_context_file_finds_agents_md(tmp_path):
    agents = tmp_path / "AGENTS.md"
    agents.write_text("# Agents")
    mod = _load_run_module()
    result = mod.find_context_file(tmp_path)
    assert result == agents


def test_find_context_file_finds_claude_md(tmp_path):
    claude = tmp_path / "CLAUDE.md"
    claude.write_text("# Claude")
    mod = _load_run_module()
    result = mod.find_context_file(tmp_path)
    assert result == claude


def test_run_agentlint_skipped_when_no_context():
    mod = _load_run_module()
    result = mod.run_agentlint(None)
    assert result["status"] == "skipped"
    assert result["score"] == 0


def test_run_agentlint_parses_score(tmp_path, monkeypatch):
    context_file = tmp_path / "AGENTS.md"
    context_file.write_text("# Agents")
    mod = _load_run_module()

    fake_result = MagicMock()
    fake_result.returncode = 0
    fake_result.stdout = "Score: 85/100\nAll checks passed."
    fake_result.stderr = ""

    with patch.object(mod, "run", return_value=fake_result):
        result = mod.run_agentlint(context_file)

    assert result["score"] == 85
    assert result["status"] == "ok"


def test_run_agentmd_drift_skipped_when_no_context():
    mod = _load_run_module()
    result = mod.run_agentmd_drift(None)
    assert result["drift_status"] == "skipped"


def test_run_agentmd_drift_detects_fresh(tmp_path, monkeypatch):
    context_file = tmp_path / "AGENTS.md"
    context_file.write_text("# Agents")
    mod = _load_run_module()

    fake_result = MagicMock()
    fake_result.returncode = 0
    fake_result.stdout = "Context is fresh. No drift detected."
    fake_result.stderr = ""

    with patch.object(mod, "run", return_value=fake_result):
        result = mod.run_agentmd_drift(context_file)

    assert result["drift_status"] == "fresh"


def test_run_agentmd_drift_detects_drifted(tmp_path):
    context_file = tmp_path / "AGENTS.md"
    context_file.write_text("# Agents")
    mod = _load_run_module()

    fake_result = MagicMock()
    fake_result.returncode = 0
    fake_result.stdout = "Drift detected in context."
    fake_result.stderr = ""

    with patch.object(mod, "run", return_value=fake_result):
        result = mod.run_agentmd_drift(context_file)

    assert result["drift_status"] == "drifted"


def test_run_coderace_skipped_when_not_pr(monkeypatch):
    mod = _load_run_module()
    # IS_PR is set at module load time from env — patch the module attribute
    monkeypatch.setattr(mod, "IS_PR", False)
    result = mod.run_coderace()
    assert result["status"] == "skipped"
    assert "not a PR" in result["reason"]


def test_run_coderace_returns_ok(tmp_path, monkeypatch):
    mod = _load_run_module()
    monkeypatch.setattr(mod, "IS_PR", True)

    fake_result = MagicMock()
    fake_result.returncode = 0
    fake_result.stdout = "3 issues found (2 medium, 1 low)"
    fake_result.stderr = ""

    with patch.object(mod, "run", return_value=fake_result):
        result = mod.run_coderace()

    assert result["status"] == "ok"
    assert "issue" in result["summary"].lower()


def test_run_coderace_handles_missing_tool(monkeypatch):
    mod = _load_run_module()
    monkeypatch.setattr(mod, "IS_PR", True)

    fake_result = MagicMock()
    fake_result.returncode = 1
    fake_result.stdout = ""
    fake_result.stderr = "coderace: command not found"

    with patch.object(mod, "run", return_value=fake_result):
        result = mod.run_coderace()

    assert result["status"] == "skipped"


def test_set_output_writes_to_github_output(tmp_path):
    mod = _load_run_module()
    output_file = tmp_path / "github_output"
    output_file.touch()

    with patch.dict(os.environ, {"GITHUB_OUTPUT": str(output_file)}):
        mod.set_output("lint-score", "85")

    assert "lint-score=85" in output_file.read_text()


def test_main_exits_1_when_below_threshold(tmp_path, monkeypatch):
    mod = _load_run_module()

    # Patch everything to return low score
    monkeypatch.setattr(mod, "find_context_file", lambda base=Path("."): tmp_path / "AGENTS.md")
    monkeypatch.setattr(mod, "run_agentlint", lambda f: {"score": 50, "status": "ok"})
    monkeypatch.setattr(mod, "run_agentmd_drift", lambda f: {"drift_status": "fresh"})
    monkeypatch.setattr(mod, "run_coderace", lambda: {"status": "skipped", "reason": "not PR"})
    monkeypatch.setattr(mod, "set_output", lambda n, v: None)
    monkeypatch.setattr(mod, "MIN_LINT_SCORE", 70)
    monkeypatch.setattr(mod, "SUMMARY_FILE", tmp_path / "summary.json")

    rc = mod.main()
    assert rc == 1


def test_main_exits_0_when_above_threshold(tmp_path, monkeypatch):
    mod = _load_run_module()

    monkeypatch.setattr(mod, "find_context_file", lambda base=Path("."): tmp_path / "AGENTS.md")
    monkeypatch.setattr(mod, "run_agentlint", lambda f: {"score": 85, "status": "ok"})
    monkeypatch.setattr(mod, "run_agentmd_drift", lambda f: {"drift_status": "fresh"})
    monkeypatch.setattr(mod, "run_coderace", lambda: {"status": "skipped", "reason": "not PR"})
    monkeypatch.setattr(mod, "set_output", lambda n, v: None)
    monkeypatch.setattr(mod, "MIN_LINT_SCORE", 70)
    monkeypatch.setattr(mod, "SUMMARY_FILE", tmp_path / "summary.json")

    rc = mod.main()
    assert rc == 0


def test_main_writes_summary_json(tmp_path, monkeypatch):
    mod = _load_run_module()
    summary_file = tmp_path / "summary.json"

    monkeypatch.setattr(mod, "find_context_file", lambda base=Path("."): None)
    monkeypatch.setattr(mod, "run_agentlint", lambda f: {"score": 0, "status": "skipped"})
    monkeypatch.setattr(mod, "run_agentmd_drift", lambda f: {"drift_status": "skipped"})
    monkeypatch.setattr(mod, "run_coderace", lambda: {"status": "skipped", "reason": "not PR"})
    monkeypatch.setattr(mod, "set_output", lambda n, v: None)
    monkeypatch.setattr(mod, "MIN_LINT_SCORE", 70)
    monkeypatch.setattr(mod, "SUMMARY_FILE", summary_file)

    mod.main()
    assert summary_file.exists()
    data = json.loads(summary_file.read_text())
    assert "aggregated" in data
    assert "lint" in data
    assert "drift" in data
    assert "coderace" in data


def test_build_comment_contains_score():
    mod = _load_run_module()
    comment = mod._build_comment(85, "fresh", {"summary": "3 issues found", "status": "ok"})
    assert "85/100" in comment
    assert "🔬 Agent Quality Report" in comment


# ---------------------------------------------------------------------------
# D1 — post-pr-comment.py tests
# ---------------------------------------------------------------------------

def _load_post_module():
    return _load_module(POST_SCRIPT, "post_pr_comment")


def test_post_script_skips_when_no_token(tmp_path, monkeypatch, capsys):
    mod = _load_post_module()
    monkeypatch.setattr(mod, "SUMMARY_FILE", tmp_path / "dummy.json")
    with patch.dict(os.environ, {}, clear=True):
        rc = mod.main()
    assert rc == 0  # non-fatal


def test_post_script_skips_when_no_pr_number(tmp_path, monkeypatch):
    mod = _load_post_module()
    summary_file = tmp_path / "summary.json"
    summary_file.write_text(json.dumps({"aggregated": {}, "comment_markdown": ""}))
    monkeypatch.setattr(mod, "SUMMARY_FILE", summary_file)
    with patch.dict(os.environ, {"GITHUB_TOKEN": "ghp_fake", "REPO": "owner/repo"}, clear=True):
        rc = mod.main()
    assert rc == 0


def test_build_comment_body_includes_marker():
    mod = _load_post_module()
    summary = {
        "comment_markdown": "## 🔬 Agent Quality Report\n\nSome content",
        "aggregated": {}
    }
    body = mod.build_comment_body(summary)
    assert mod.MARKER in body
    assert "Agent Quality Report" in body


def test_build_comment_body_fallback():
    mod = _load_post_module()
    summary = {
        "aggregated": {
            "lint_score": 75,
            "drift_status": "fresh",
            "review_summary": "All good",
        }
    }
    body = mod.build_comment_body(summary)
    assert "75/100" in body
    assert mod.MARKER in body


def test_post_comment_creates_new(tmp_path, monkeypatch):
    mod = _load_post_module()
    summary_file = tmp_path / "summary.json"
    summary_file.write_text(json.dumps({
        "comment_markdown": "## 🔬 Agent Quality Report\n| Check | Result |",
        "aggregated": {"lint_score": 80, "drift_status": "fresh", "review_summary": "ok"}
    }))
    monkeypatch.setattr(mod, "SUMMARY_FILE", summary_file)

    with patch.object(mod, "list_comments", return_value=[]), \
         patch.object(mod, "create_comment", return_value={"id": 123}) as mock_create, \
         patch.dict(os.environ, {
             "GITHUB_TOKEN": "ghp_fake",
             "REPO": "owner/repo",
             "PR_NUMBER": "42",
         }):
        rc = mod.main()

    assert rc == 0
    mock_create.assert_called_once()


def test_post_comment_updates_existing(tmp_path, monkeypatch):
    mod = _load_post_module()
    summary_file = tmp_path / "summary.json"
    summary_file.write_text(json.dumps({
        "comment_markdown": "## 🔬 Agent Quality Report\n| Check | Result |",
        "aggregated": {}
    }))
    monkeypatch.setattr(mod, "SUMMARY_FILE", summary_file)

    existing = [{"id": 999, "body": f"{mod.MARKER}\nOld content"}]

    with patch.object(mod, "list_comments", return_value=existing), \
         patch.object(mod, "update_comment", return_value={"id": 999}) as mock_update, \
         patch.dict(os.environ, {
             "GITHUB_TOKEN": "ghp_fake",
             "REPO": "owner/repo",
             "PR_NUMBER": "42",
         }):
        rc = mod.main()

    assert rc == 0
    mock_update.assert_called_once()
    assert mock_update.call_args[0][1] == 999  # correct comment id


def test_post_script_fails_when_summary_missing(tmp_path, monkeypatch):
    mod = _load_post_module()
    monkeypatch.setattr(mod, "SUMMARY_FILE", tmp_path / "nonexistent.json")

    with patch.dict(os.environ, {
        "GITHUB_TOKEN": "ghp_fake",
        "REPO": "owner/repo",
        "PR_NUMBER": "1",
    }):
        rc = mod.main()
    assert rc == 1


# ---------------------------------------------------------------------------
# D2 — Example workflow tests
# ---------------------------------------------------------------------------

def test_example_workflow_exists():
    assert EXAMPLE_WORKFLOW.exists()


def test_example_workflow_valid_yaml():
    with open(EXAMPLE_WORKFLOW) as f:
        data = yaml.safe_load(f)
    assert "jobs" in data


def test_example_workflow_uses_action():
    with open(EXAMPLE_WORKFLOW) as f:
        data = yaml.safe_load(f)
    steps = list(data["jobs"].values())[0]["steps"]
    action_steps = [s for s in steps if "mikiships/agentkit-cli" in s.get("uses", "")]
    assert len(action_steps) == 1


def test_example_workflow_has_github_token():
    with open(EXAMPLE_WORKFLOW) as f:
        data = yaml.safe_load(f)
    steps = list(data["jobs"].values())[0]["steps"]
    action_step = next(s for s in steps if "mikiships/agentkit-cli" in s.get("uses", ""))
    assert "github-token" in action_step.get("with", {})


def test_readme_has_github_action_section():
    readme = (REPO_ROOT / "README.md").read_text()
    assert "GitHub Action" in readme
    assert "mikiships/agentkit-cli@v0.7.0" in readme


# ---------------------------------------------------------------------------
# D4 — History integration tests
# ---------------------------------------------------------------------------

class TestActionHistoryIntegration(unittest.TestCase):
    """Tests for save-history input and history-json output in action.yml."""

    def test_action_has_save_history_input(self):
        data = _load_action()
        assert "save-history" in data["inputs"]

    def test_save_history_default_is_false(self):
        data = _load_action()
        assert data["inputs"]["save-history"]["default"] == "false"

    def test_save_history_is_not_required(self):
        data = _load_action()
        save_history_input = data["inputs"]["save-history"]
        assert save_history_input.get("required") is not True

    def test_action_has_history_json_output(self):
        data = _load_action()
        assert "history-json" in data["outputs"]

    def test_history_json_output_has_description(self):
        data = _load_action()
        assert data["outputs"]["history-json"].get("description")

    def test_example_ci_workflow_exists(self):
        assert EXAMPLES_DIR.exists()
        ci_file = EXAMPLES_DIR / "agentkit-ci.yml"
        assert ci_file.exists(), "examples/agentkit-ci.yml should exist"

    def test_example_ci_workflow_has_save_history(self):
        ci_file = EXAMPLES_DIR / "agentkit-ci.yml"
        content = ci_file.read_text()
        assert "save-history" in content

    def test_example_ci_workflow_is_valid_yaml(self):
        ci_file = EXAMPLES_DIR / "agentkit-ci.yml"
        import yaml
        data = yaml.safe_load(ci_file.read_text())
        assert isinstance(data, dict)
        assert "jobs" in data
