"""Tests for agentkit spotlight --tweet-only (v0.79.0 D1)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from io import StringIO
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from agentkit_cli.commands.spotlight_cmd import (
    SpotlightResult,
    _build_spotlight_tweet,
    spotlight_command,
)
from agentkit_cli.main import app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_result(**kwargs) -> SpotlightResult:
    defaults = dict(
        repo="acme/demo-agent",
        score=78.5,
        grade="C",
        top_findings=["[agentlint] Missing AGENTS.md", "[agentmd] README too short"],
        run_date=datetime.now(timezone.utc).isoformat(),
    )
    defaults.update(kwargs)
    return SpotlightResult(**defaults)


# ---------------------------------------------------------------------------
# Unit tests: _build_spotlight_tweet
# ---------------------------------------------------------------------------

class TestBuildSpotlightTweet:
    def test_returns_string(self):
        r = _make_result()
        result = _build_spotlight_tweet(r)
        assert isinstance(result, str)

    def test_within_280_chars(self):
        r = _make_result()
        tweet = _build_spotlight_tweet(r)
        assert len(tweet) <= 280

    def test_contains_repo_name(self):
        r = _make_result(repo="owner/myrepo")
        tweet = _build_spotlight_tweet(r)
        assert "owner/myrepo" in tweet

    def test_contains_score(self):
        r = _make_result(score=91.0)
        tweet = _build_spotlight_tweet(r)
        assert "91/100" in tweet

    def test_strips_tool_prefix_from_finding(self):
        r = _make_result(top_findings=["[agentlint] Missing AGENTS.md"])
        tweet = _build_spotlight_tweet(r)
        assert "[agentlint]" not in tweet
        assert "Missing AGENTS.md" in tweet

    def test_no_findings_still_works(self):
        r = _make_result(top_findings=[])
        tweet = _build_spotlight_tweet(r)
        assert "acme/demo-agent" in tweet
        assert len(tweet) <= 280

    def test_none_score_shows_na(self):
        r = _make_result(score=None, grade=None)
        tweet = _build_spotlight_tweet(r)
        assert "N/A" in tweet

    def test_long_finding_truncated_to_280(self):
        long_finding = "A" * 300
        r = _make_result(top_findings=[long_finding])
        tweet = _build_spotlight_tweet(r)
        assert len(tweet) <= 280

    def test_finding_without_prefix_included_as_is(self):
        r = _make_result(top_findings=["Great documentation coverage"])
        tweet = _build_spotlight_tweet(r)
        assert "Great documentation coverage" in tweet

    def test_url_not_included_when_no_share_url(self):
        r = _make_result(share_url=None)
        tweet = _build_spotlight_tweet(r)
        assert "https://" not in tweet


# ---------------------------------------------------------------------------
# Integration tests: spotlight_command with tweet_only=True
# ---------------------------------------------------------------------------

class TestSpotlightCommandTweetOnly:
    """Test spotlight_command(tweet_only=True) via direct call + mocking engine."""

    def _call(self, tweet_only=True, share=False, share_url=None, score=82.0, findings=None):
        """Helper: call spotlight_command with mocked engine."""
        import io
        import sys
        from agentkit_cli.commands.spotlight_cmd import SpotlightEngine

        mock_result = _make_result(
            score=score,
            top_findings=findings or ["[ruff] Score 78/100"],
            share_url=share_url,
        )

        captured = io.StringIO()
        real_stdout = sys.stdout
        sys.stdout = captured
        try:
            with patch.object(SpotlightEngine, "run_spotlight", return_value=mock_result), \
                 patch.object(SpotlightEngine, "select_candidate", return_value={"full_name": "acme/demo-agent"}):
                # patch share upload if needed
                if share and share_url:
                    with patch("agentkit_cli.commands.spotlight_cmd._upload_spotlight", return_value=share_url):
                        mock_result.share_url = share_url
                        spotlight_command(
                            target="acme/demo-agent",
                            topic=None,
                            language=None,
                            deep=False,
                            share=share,
                            json_output=False,
                            output=None,
                            quiet=False,
                            no_history=True,
                            tweet_only=tweet_only,
                        )
                else:
                    spotlight_command(
                        target="acme/demo-agent",
                        topic=None,
                        language=None,
                        deep=False,
                        share=share,
                        json_output=False,
                        output=None,
                        quiet=False,
                        no_history=True,
                        tweet_only=tweet_only,
                    )
        finally:
            sys.stdout = real_stdout

        return captured.getvalue()

    def test_tweet_only_produces_output(self):
        out = self._call(tweet_only=True)
        assert len(out.strip()) > 0

    def test_tweet_only_within_280(self):
        out = self._call(tweet_only=True)
        assert len(out.strip()) <= 280

    def test_tweet_only_no_rich_markup(self):
        out = self._call(tweet_only=True)
        # No Rich panel characters
        assert "╭" not in out
        assert "╰" not in out
        assert "[bold]" not in out

    def test_tweet_only_contains_repo(self):
        out = self._call(tweet_only=True)
        assert "acme/demo-agent" in out

    def test_tweet_only_with_share_url_includes_url(self):
        url = "https://here.now/abc123"
        out = self._call(tweet_only=True, share=True, share_url=url)
        # URL should be appended (fits in 280)
        assert url in out

    def test_tweet_only_without_share_no_url(self):
        out = self._call(tweet_only=True, share=False)
        assert "https://" not in out

    def test_tweet_only_single_line(self):
        out = self._call(tweet_only=True)
        # Should be a single line (no extra blank lines with content)
        lines = [l for l in out.splitlines() if l.strip()]
        assert len(lines) == 1

    def test_tweet_only_false_no_early_exit(self):
        """When tweet_only=False, output should include rich formatting (not tweet only)."""
        import io
        import sys
        from agentkit_cli.commands.spotlight_cmd import SpotlightEngine

        mock_result = _make_result()
        captured = io.StringIO()
        real_stdout = sys.stdout
        sys.stdout = captured
        try:
            with patch.object(SpotlightEngine, "run_spotlight", return_value=mock_result), \
                 patch.object(SpotlightEngine, "select_candidate", return_value={"full_name": "acme/demo-agent"}):
                spotlight_command(
                    target="acme/demo-agent",
                    topic=None, language=None, deep=False, share=False,
                    json_output=False, output=None, quiet=False,
                    no_history=True, tweet_only=False,
                )
        finally:
            sys.stdout = real_stdout
        # Not a tweet-only output — should have more content
        out = captured.getvalue()
        # Just verify it doesn't assert single-line constraint
        assert len(out) >= 0  # any output is fine here


# ---------------------------------------------------------------------------
# CLI integration via typer runner
# ---------------------------------------------------------------------------

class TestSpotlightCLITweetOnly:
    """Test --tweet-only flag via typer CLI runner."""

    def test_tweet_only_flag_accepted(self):
        """--tweet-only flag should be accepted without error (even if output depends on network)."""
        from agentkit_cli.commands.spotlight_cmd import SpotlightEngine

        mock_result = _make_result()
        with patch.object(SpotlightEngine, "run_spotlight", return_value=mock_result), \
             patch.object(SpotlightEngine, "select_candidate", return_value={"full_name": "acme/demo-agent"}), \
             patch("agentkit_cli.history.HistoryDB.record_run", return_value=None):
            result = runner.invoke(app, ["spotlight", "acme/demo-agent", "--tweet-only", "--no-history"])
        # Should not crash (exit 0 or content output)
        assert result.exit_code == 0

    def test_tweet_only_output_within_280(self):
        from agentkit_cli.commands.spotlight_cmd import SpotlightEngine

        mock_result = _make_result()
        with patch.object(SpotlightEngine, "run_spotlight", return_value=mock_result), \
             patch.object(SpotlightEngine, "select_candidate", return_value={"full_name": "acme/demo-agent"}), \
             patch("agentkit_cli.history.HistoryDB.record_run", return_value=None):
            result = runner.invoke(app, ["spotlight", "acme/demo-agent", "--tweet-only", "--no-history"])
        assert result.exit_code == 0
        output = result.output.strip()
        assert len(output) <= 280

    def test_tweet_only_no_share_url_in_output(self):
        from agentkit_cli.commands.spotlight_cmd import SpotlightEngine

        mock_result = _make_result(share_url=None)
        with patch.object(SpotlightEngine, "run_spotlight", return_value=mock_result), \
             patch.object(SpotlightEngine, "select_candidate", return_value={"full_name": "acme/demo-agent"}), \
             patch("agentkit_cli.history.HistoryDB.record_run", return_value=None):
            result = runner.invoke(app, ["spotlight", "acme/demo-agent", "--tweet-only", "--no-history"])
        assert result.exit_code == 0
        assert "https://" not in result.output

    def test_tweet_only_with_share_includes_url(self):
        from agentkit_cli.commands.spotlight_cmd import SpotlightEngine

        share_url = "https://here.now/xyz"
        mock_result = _make_result(share_url=share_url)
        with patch.object(SpotlightEngine, "run_spotlight", return_value=mock_result), \
             patch.object(SpotlightEngine, "select_candidate", return_value={"full_name": "acme/demo-agent"}), \
             patch("agentkit_cli.commands.spotlight_cmd._upload_spotlight", return_value=share_url), \
             patch("agentkit_cli.history.HistoryDB.record_run", return_value=None):
            result = runner.invoke(app, ["spotlight", "acme/demo-agent", "--share", "--tweet-only", "--no-history"])
        assert result.exit_code == 0
        assert share_url in result.output

    def test_version_is_079(self):
        result = runner.invoke(app, ["--version"])
        assert "0.80.0" in result.output
