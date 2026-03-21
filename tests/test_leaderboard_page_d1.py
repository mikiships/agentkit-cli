"""Tests for agentkit leaderboard-page D1 — engine, scoring, rendering."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from agentkit_cli.leaderboard_page import (
    ECOSYSTEMS,
    ECOSYSTEM_LANGUAGE_MAP,
    LeaderboardEntry,
    LeaderboardPageEngine,
    LeaderboardPageResult,
    EcosystemLeaderboard,
    _FALLBACK_REPOS,
    _score_repo_heuristic,
    render_leaderboard_html,
    render_embed_badge,
    search_ecosystem_repos,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _fake_repos(n: int = 3, language: str = "Python") -> list[dict]:
    return [
        {
            "full_name": f"owner/repo{i+1}",
            "description": f"Description {i+1}",
            "stars": 1000 * (n - i),
            "stargazers_count": 1000 * (n - i),
            "language": language,
        }
        for i in range(n)
    ]


def _mock_score(repo, token, timeout):
    idx = int(repo.get("full_name", "owner/repo1").replace("owner/repo", "") or "1")
    return float(80 - idx * 5)


def _make_engine(ecosystems=None, repos_override=None, score_fn=None):
    return LeaderboardPageEngine(
        ecosystems=ecosystems or ["python"],
        limit=5,
        _repos_override=repos_override or {"python": _fake_repos(3)},
        _score_fn=score_fn or _mock_score,
    )


# ---------------------------------------------------------------------------
# ECOSYSTEMS constant
# ---------------------------------------------------------------------------

def test_ecosystems_has_five():
    assert len(ECOSYSTEMS) == 5


def test_ecosystems_contains_python():
    assert "python" in ECOSYSTEMS


def test_ecosystems_contains_typescript():
    assert "typescript" in ECOSYSTEMS


def test_ecosystems_contains_rust():
    assert "rust" in ECOSYSTEMS


def test_ecosystems_contains_go():
    assert "go" in ECOSYSTEMS


def test_ecosystems_contains_javascript():
    assert "javascript" in ECOSYSTEMS


# ---------------------------------------------------------------------------
# ECOSYSTEM_LANGUAGE_MAP
# ---------------------------------------------------------------------------

def test_language_map_python():
    assert ECOSYSTEM_LANGUAGE_MAP["python"] == "Python"


def test_language_map_typescript():
    assert ECOSYSTEM_LANGUAGE_MAP["typescript"] == "TypeScript"


def test_language_map_rust():
    assert ECOSYSTEM_LANGUAGE_MAP["rust"] == "Rust"


# ---------------------------------------------------------------------------
# _score_repo_heuristic
# ---------------------------------------------------------------------------

def test_heuristic_score_high_stars():
    repo = {"full_name": "a/b", "stars": 100000, "stargazers_count": 100000}
    score = _score_repo_heuristic(repo)
    assert score >= 50


def test_heuristic_score_returns_float():
    repo = {"full_name": "a/b", "stars": 500}
    score = _score_repo_heuristic(repo)
    assert isinstance(score, float)


def test_heuristic_score_max_100():
    repo = {"full_name": "a/b", "stars": 999999, "stargazers_count": 999999, "topics": ["agent-ready", "llm", "ai", "claude", "openai", "langchain", "agents"], "description": "very long description", "has_wiki": True, "has_issues": True}
    score = _score_repo_heuristic(repo)
    assert score <= 100.0


def test_heuristic_score_with_agent_topics():
    repo = {"full_name": "a/b", "stars": 5000, "topics": ["agent-ready", "llm"]}
    score = _score_repo_heuristic(repo)
    assert score > _score_repo_heuristic({"full_name": "a/b", "stars": 5000, "topics": []})


# ---------------------------------------------------------------------------
# LeaderboardPageEngine
# ---------------------------------------------------------------------------

def test_engine_runs():
    engine = _make_engine()
    result = engine.run()
    assert isinstance(result, LeaderboardPageResult)


def test_engine_result_has_ecosystems():
    engine = _make_engine()
    result = engine.run()
    assert len(result.ecosystems) == 1
    assert result.ecosystems[0].ecosystem == "python"


def test_engine_result_entries_sorted():
    engine = _make_engine()
    result = engine.run()
    scores = [e.score for e in result.ecosystems[0].entries]
    assert scores == sorted(scores, reverse=True)


def test_engine_result_ranks():
    engine = _make_engine()
    result = engine.run()
    ranks = [e.rank for e in result.ecosystems[0].entries]
    assert ranks[0] == 1


def test_engine_limit_respected():
    engine = LeaderboardPageEngine(
        ecosystems=["python"],
        limit=2,
        _repos_override={"python": _fake_repos(5)},
        _score_fn=_mock_score,
    )
    result = engine.run()
    assert len(result.ecosystems[0].entries) <= 2


def test_engine_limit_max_25():
    engine = LeaderboardPageEngine(
        ecosystems=["python"],
        limit=99,
        _repos_override={"python": _fake_repos(3)},
        _score_fn=_mock_score,
    )
    assert engine.limit <= 25


def test_engine_multiple_ecosystems():
    engine = LeaderboardPageEngine(
        ecosystems=["python", "rust"],
        limit=3,
        _repos_override={
            "python": _fake_repos(3),
            "rust": _fake_repos(3, language="Rust"),
        },
        _score_fn=_mock_score,
    )
    result = engine.run()
    assert len(result.ecosystems) == 2


def test_engine_generated_at_present():
    engine = _make_engine()
    result = engine.run()
    assert result.generated_at
    assert "T" in result.generated_at


def test_engine_entry_has_grade():
    engine = _make_engine()
    result = engine.run()
    for entry in result.ecosystems[0].entries:
        assert entry.grade in ("A", "B", "C", "D", "F")


def test_engine_to_dict():
    engine = _make_engine()
    result = engine.run()
    d = result.to_dict()
    assert "ecosystems" in d
    assert "generated_at" in d


# ---------------------------------------------------------------------------
# HTML rendering
# ---------------------------------------------------------------------------

def test_html_contains_dark_background():
    engine = _make_engine()
    result = engine.run()
    html = render_leaderboard_html(result)
    assert "#0d1117" in html


def test_html_contains_powered_by_badge():
    engine = _make_engine()
    result = engine.run()
    html = render_leaderboard_html(result)
    assert "agentkit-cli" in html


def test_html_contains_last_updated():
    engine = _make_engine()
    result = engine.run()
    html = render_leaderboard_html(result)
    assert "Last updated" in html


def test_html_is_string():
    engine = _make_engine()
    result = engine.run()
    html = render_leaderboard_html(result)
    assert isinstance(html, str)
    assert len(html) > 100


def test_html_contains_repo_name():
    engine = _make_engine()
    result = engine.run()
    html = render_leaderboard_html(result)
    assert "owner/repo1" in html


# ---------------------------------------------------------------------------
# leaderboard_page_command integration
# ---------------------------------------------------------------------------

def test_command_writes_html(tmp_path):
    from agentkit_cli.commands.leaderboard_page_cmd import leaderboard_page_command
    out = str(tmp_path / "lb.html")
    leaderboard_page_command(
        output=out,
        ecosystems="python",
        limit=3,
        _repos_override={"python": _fake_repos(3)},
        _score_fn=_mock_score,
    )
    assert Path(out).exists()
    content = Path(out).read_text()
    assert "#0d1117" in content


def test_command_json_output(capsys):
    from agentkit_cli.commands.leaderboard_page_cmd import leaderboard_page_command
    leaderboard_page_command(
        ecosystems="python",
        limit=2,
        json_output=True,
        _repos_override={"python": _fake_repos(2)},
        _score_fn=_mock_score,
    )
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "ecosystems" in data


def test_command_pages_flag(tmp_path, monkeypatch):
    from agentkit_cli.commands.leaderboard_page_cmd import leaderboard_page_command
    monkeypatch.chdir(tmp_path)
    leaderboard_page_command(
        pages=True,
        ecosystems="python",
        limit=2,
        _repos_override={"python": _fake_repos(2)},
        _score_fn=_mock_score,
    )
    assert (tmp_path / "docs" / "leaderboard.html").exists()


def test_command_embed_only(capsys):
    from agentkit_cli.commands.leaderboard_page_cmd import leaderboard_page_command
    leaderboard_page_command(
        embed="github:owner/myrepo",
        embed_only=True,
        _repos_override={"python": _fake_repos(2)},
        _score_fn=_mock_score,
    )
    captured = capsys.readouterr()
    assert "shields.io" in captured.out or "agentkit" in captured.out


def test_command_ecosystems_csv(tmp_path):
    from agentkit_cli.commands.leaderboard_page_cmd import leaderboard_page_command
    out = str(tmp_path / "lb.html")
    leaderboard_page_command(
        output=out,
        ecosystems="python,rust",
        limit=2,
        _repos_override={
            "python": _fake_repos(2),
            "rust": _fake_repos(2, language="Rust"),
        },
        _score_fn=_mock_score,
    )
    content = Path(out).read_text()
    assert "python" in content.lower() or "rust" in content.lower()
