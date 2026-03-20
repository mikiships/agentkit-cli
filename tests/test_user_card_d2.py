"""Tests for D2: user-card CLI command (≥14 tests)."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.user_card import UserCardResult

runner = CliRunner()


def _make_result(username="alice", grade="B", avg_score=72.0):
    return UserCardResult(
        username=username,
        avatar_url=f"https://github.com/{username}.png",
        grade=grade,
        avg_score=avg_score,
        total_repos=10,
        analyzed_repos=8,
        context_coverage_pct=60.0,
        top_repo_name="best-repo",
        top_repo_score=90.0,
        agent_ready_count=3,
        summary_line=f"3/8 repos agent-ready · Grade {grade}",
    )


def _make_engine_cls(result):
    class _MockEngine:
        def __init__(self, *a, **kw):
            pass
        def run(self, user):
            return result
    return _MockEngine


# ---------------------------------------------------------------------------
# CLI parsing
# ---------------------------------------------------------------------------

def test_cli_bare_username():
    result = _make_result()
    with patch("agentkit_cli.commands.user_card_cmd.UserCardEngine", _make_engine_cls(result)):
        with patch("agentkit_cli.commands.user_card_cmd.record_run"):
            out = runner.invoke(app, ["user-card", "alice"])
    assert out.exit_code == 0


def test_cli_github_prefix():
    result = _make_result()
    with patch("agentkit_cli.commands.user_card_cmd.UserCardEngine", _make_engine_cls(result)):
        with patch("agentkit_cli.commands.user_card_cmd.record_run"):
            out = runner.invoke(app, ["user-card", "github:alice"])
    assert out.exit_code == 0


def test_cli_empty_username_exits_1():
    out = runner.invoke(app, ["user-card", ""])
    assert out.exit_code == 1


def test_cli_json_output():
    result = _make_result()
    with patch("agentkit_cli.commands.user_card_cmd.UserCardEngine", _make_engine_cls(result)):
        with patch("agentkit_cli.commands.user_card_cmd.record_run"):
            out = runner.invoke(app, ["user-card", "alice", "--json"])
    assert out.exit_code == 0
    data = json.loads(out.output)
    assert data["username"] == "alice"
    assert data["grade"] == "B"


def test_cli_json_has_all_fields():
    result = _make_result()
    with patch("agentkit_cli.commands.user_card_cmd.UserCardEngine", _make_engine_cls(result)):
        with patch("agentkit_cli.commands.user_card_cmd.record_run"):
            out = runner.invoke(app, ["user-card", "alice", "--json"])
    data = json.loads(out.output)
    for key in ("username", "grade", "avg_score", "top_repo_name", "top_repo_score",
                "agent_ready_count", "summary_line", "context_coverage_pct"):
        assert key in data


def test_cli_quiet_with_share_prints_url():
    result = _make_result()
    with patch("agentkit_cli.commands.user_card_cmd.UserCardEngine", _make_engine_cls(result)):
        with patch("agentkit_cli.commands.user_card_cmd.upload_user_card", return_value="https://here.now/x"):
            with patch("agentkit_cli.commands.user_card_cmd.record_run"):
                out = runner.invoke(app, ["user-card", "alice", "--share", "--quiet"])
    assert out.exit_code == 0
    assert "https://here.now/x" in out.output


def test_cli_share_prints_url():
    result = _make_result()
    with patch("agentkit_cli.commands.user_card_cmd.UserCardEngine", _make_engine_cls(result)):
        with patch("agentkit_cli.commands.user_card_cmd.upload_user_card", return_value="https://here.now/x"):
            with patch("agentkit_cli.commands.user_card_cmd.record_run"):
                out = runner.invoke(app, ["user-card", "alice", "--share"])
    assert out.exit_code == 0
    assert "here.now/x" in out.output


def test_cli_share_url_in_json():
    result = _make_result()
    with patch("agentkit_cli.commands.user_card_cmd.UserCardEngine", _make_engine_cls(result)):
        with patch("agentkit_cli.commands.user_card_cmd.upload_user_card", return_value="https://here.now/x"):
            with patch("agentkit_cli.commands.user_card_cmd.record_run"):
                out = runner.invoke(app, ["user-card", "alice", "--share", "--json"])
    data = json.loads(out.output)
    assert data["share_url"] == "https://here.now/x"


def test_cli_limit_option():
    result = _make_result()
    captured = {}
    class _CapEngine:
        def __init__(self, *a, **kw):
            captured["limit"] = kw.get("limit")
        def run(self, user):
            return result
    with patch("agentkit_cli.commands.user_card_cmd.UserCardEngine", _CapEngine):
        with patch("agentkit_cli.commands.user_card_cmd.record_run"):
            out = runner.invoke(app, ["user-card", "alice", "--limit", "15"])
    assert out.exit_code == 0
    assert captured["limit"] == 15


def test_cli_min_stars_option():
    result = _make_result()
    captured = {}
    class _CapEngine:
        def __init__(self, *a, **kw):
            captured["min_stars"] = kw.get("min_stars")
        def run(self, user):
            return result
    with patch("agentkit_cli.commands.user_card_cmd.UserCardEngine", _CapEngine):
        with patch("agentkit_cli.commands.user_card_cmd.record_run"):
            out = runner.invoke(app, ["user-card", "alice", "--min-stars", "5"])
    assert out.exit_code == 0
    assert captured["min_stars"] == 5


def test_cli_no_skip_forks():
    result = _make_result()
    captured = {}
    class _CapEngine:
        def __init__(self, *a, **kw):
            captured["skip_forks"] = kw.get("skip_forks")
        def run(self, user):
            return result
    with patch("agentkit_cli.commands.user_card_cmd.UserCardEngine", _CapEngine):
        with patch("agentkit_cli.commands.user_card_cmd.record_run"):
            out = runner.invoke(app, ["user-card", "alice", "--no-skip-forks"])
    assert out.exit_code == 0
    assert captured["skip_forks"] is False


def test_cli_records_history():
    result = _make_result()
    recorded = {}
    def _fake_record(**kw):
        recorded.update(kw)
    with patch("agentkit_cli.commands.user_card_cmd.UserCardEngine", _make_engine_cls(result)):
        with patch("agentkit_cli.commands.user_card_cmd.record_run", side_effect=_fake_record):
            out = runner.invoke(app, ["user-card", "alice"])
    assert recorded.get("tool") == "user-card"


def test_cli_help_contains_flags():
    out = runner.invoke(app, ["user-card", "--help"])
    assert out.exit_code == 0
    assert "--limit" in out.output
    assert "--share" in out.output
    assert "--json" in out.output
