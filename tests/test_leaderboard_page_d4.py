"""Tests for agentkit leaderboard-page D4 — --embed badge."""
from __future__ import annotations

import pytest

from agentkit_cli.leaderboard_page import render_embed_badge


def test_embed_badge_returns_string():
    result = render_embed_badge("owner/repo")
    assert isinstance(result, str)


def test_embed_badge_contains_shields_io():
    result = render_embed_badge("owner/repo")
    assert "shields.io" in result


def test_embed_badge_contains_repo_name():
    result = render_embed_badge("myorg/myrepo")
    assert "myorg/myrepo" in result


def test_embed_badge_contains_markdown_link():
    result = render_embed_badge("owner/repo")
    assert "[![" in result or "![" in result


def test_embed_badge_with_rank():
    result = render_embed_badge("owner/repo", rank=1, score=92.0)
    assert "#1" in result or "1" in result


def test_embed_badge_with_score():
    result = render_embed_badge("owner/repo", score=85.0)
    assert "85" in result


def test_embed_badge_contains_leaderboard_link():
    result = render_embed_badge("owner/repo")
    assert "leaderboard" in result


def test_embed_badge_with_ecosystem():
    result = render_embed_badge("owner/repo", ecosystem="rust")
    assert "rust" in result


def test_command_embed_outputs_markdown(capsys):
    from agentkit_cli.commands.leaderboard_page_cmd import leaderboard_page_command

    def _fake_repos(n=2):
        return [
            {"full_name": f"owner/repo{i+1}", "description": "desc", "stars": 1000, "stargazers_count": 1000}
            for i in range(n)
        ]

    leaderboard_page_command(
        embed="github:owner/repo1",
        embed_only=True,
        ecosystems="python",
        _repos_override={"python": _fake_repos()},
        _score_fn=lambda r, t, to: 80.0,
    )
    captured = capsys.readouterr()
    assert len(captured.out.strip()) > 0


def test_embed_badge_no_rank_no_score():
    result = render_embed_badge("owner/repo")
    # Should still produce a valid badge
    assert "agentkit" in result or "agent" in result


def test_embed_badge_markdown_image_syntax():
    result = render_embed_badge("owner/repo", rank=2, score=70.0)
    # Should have markdown image syntax
    assert "](" in result
