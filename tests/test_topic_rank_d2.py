"""D2 tests — CLI command (topic_rank_cmd)."""
from __future__ import annotations

import json
from unittest.mock import patch, MagicMock

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.topic_rank import TopicRankResult, TopicRankEntry

runner = CliRunner()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_result(topic: str = "python", n: int = 3) -> TopicRankResult:
    entries = [
        TopicRankEntry(
            rank=i + 1,
            repo_full_name=f"owner/repo-{i}",
            score=round(90.0 - i * 10, 1),
            grade="A" if i == 0 else "B",
            stars=1000 - i * 100,
            description=f"Description for repo {i}",
        )
        for i in range(n)
    ]
    return TopicRankResult(
        topic=topic,
        entries=entries,
        generated_at="2026-03-20 00:00 UTC",
        total_analyzed=n,
    )


def _patch_engine(result: TopicRankResult):
    return patch(
        "agentkit_cli.commands.topic_rank_cmd.TopicRankEngine",
        return_value=MagicMock(run=MagicMock(return_value=result)),
    )


# ---------------------------------------------------------------------------
# Basic invocation
# ---------------------------------------------------------------------------


def test_topic_command_basic_output():
    result = _make_result("python")
    with _patch_engine(result):
        r = runner.invoke(app, ["topic", "python"])
    assert r.exit_code == 0
    assert "python" in r.output.lower()


def test_topic_command_shows_repos():
    result = _make_result("python")
    with _patch_engine(result):
        r = runner.invoke(app, ["topic", "python"])
    assert "owner/repo-0" in r.output


def test_topic_command_json_output():
    result = _make_result("python")
    with _patch_engine(result):
        r = runner.invoke(app, ["topic", "python", "--json"])
    assert r.exit_code == 0
    data = json.loads(r.output)
    assert data["topic"] == "python"
    assert len(data["entries"]) == 3


def test_topic_command_json_entries_fields():
    result = _make_result("llm")
    with _patch_engine(result):
        r = runner.invoke(app, ["topic", "llm", "--json"])
    data = json.loads(r.output)
    entry = data["entries"][0]
    assert "repo_full_name" in entry
    assert "score" in entry
    assert "grade" in entry
    assert "stars" in entry
    assert "rank" in entry


def test_topic_command_empty_results():
    result = TopicRankResult(topic="noresult", entries=[], generated_at="ts", total_analyzed=0)
    with _patch_engine(result):
        r = runner.invoke(app, ["topic", "noresult"])
    assert r.exit_code == 0
    assert "noresult" in r.output.lower()


# ---------------------------------------------------------------------------
# Options
# ---------------------------------------------------------------------------


def test_topic_command_limit_passed():
    result = _make_result("python", n=5)
    with patch("agentkit_cli.commands.topic_rank_cmd.TopicRankEngine") as MockEngine:
        MockEngine.return_value.run.return_value = result
        runner.invoke(app, ["topic", "python", "--limit", "5"])
    init_kwargs = MockEngine.call_args[1]
    assert init_kwargs["limit"] == 5


def test_topic_command_language_passed():
    result = _make_result("python")
    with patch("agentkit_cli.commands.topic_rank_cmd.TopicRankEngine") as MockEngine:
        MockEngine.return_value.run.return_value = result
        runner.invoke(app, ["topic", "python", "--language", "python"])
    init_kwargs = MockEngine.call_args[1]
    assert init_kwargs["language"] == "python"


def test_topic_command_quiet_suppresses_output():
    result = _make_result("python")
    with _patch_engine(result):
        r = runner.invoke(app, ["topic", "python", "--quiet"])
    # In quiet mode with no share, output should be minimal/empty
    assert "scoring" not in r.output.lower()


def test_topic_command_output_saves_html(tmp_path):
    out_file = str(tmp_path / "report.html")
    result = _make_result("python")
    with _patch_engine(result):
        r = runner.invoke(app, ["topic", "python", "--output", out_file])
    assert r.exit_code == 0
    import os
    assert os.path.exists(out_file)
    content = open(out_file).read()
    assert "<!DOCTYPE html>" in content


def test_topic_command_error_exit():
    with patch(
        "agentkit_cli.commands.topic_rank_cmd.TopicRankEngine",
        return_value=MagicMock(run=MagicMock(side_effect=RuntimeError("boom"))),
    ):
        r = runner.invoke(app, ["topic", "python"])
    assert r.exit_code != 0


def test_topic_command_grade_in_table():
    result = _make_result("python", n=2)
    with _patch_engine(result):
        r = runner.invoke(app, ["topic", "python"])
    # Grade should appear in the output
    assert "A" in r.output or "B" in r.output


def test_topic_command_drill_down_hint():
    result = _make_result("python")
    with _patch_engine(result):
        r = runner.invoke(app, ["topic", "python"])
    assert "agentkit topic python" in r.output
