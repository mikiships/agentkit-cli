"""Tests for agentkit duel engine, CLI command, HTML report, and publish."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from agentkit_cli.analyze import AnalyzeResult
from agentkit_cli.duel import DuelResult, _determine_winner, run_duel
from agentkit_cli.duel_report import generate_duel_html, publish_duel
from agentkit_cli.main import app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _analyze_result(
    target: str,
    score: float = 80.0,
    grade: str = "B",
    repo_name: str = "",
) -> AnalyzeResult:
    name = repo_name or target.split("/")[-1]
    return AnalyzeResult(
        target=target,
        repo_name=name,
        composite_score=score,
        grade=grade,
        tools={
            "agentmd": {"tool": "agentmd", "status": "pass", "score": score, "finding": "ok"},
            "agentlint": {"tool": "agentlint", "status": "pass", "score": score, "finding": "ok"},
            "agentreflect": {
                "tool": "agentreflect",
                "status": "pass",
                "score": score,
                "finding": "ok",
            },
        },
        generated_context=False,
    )


def _duel_result(
    left_score: float = 80.0,
    right_score: float = 60.0,
    winner: str = "left",
    delta: float = 20.0,
) -> DuelResult:
    return DuelResult(
        left_target="github:owner/repo1",
        right_target="github:owner/repo2",
        left_score=left_score,
        right_score=right_score,
        left_breakdown={},
        right_breakdown={},
        winner=winner,
        delta=delta,
        timestamp="2026-01-01 00:00 UTC",
        left_repo_name="repo1",
        right_repo_name="repo2",
        left_grade="B",
        right_grade="C",
    )


# ---------------------------------------------------------------------------
# D1 — DuelResult dataclass
# ---------------------------------------------------------------------------

class TestDuelResultDataclass:
    def test_fields_stored_correctly(self):
        r = _duel_result()
        assert r.left_target == "github:owner/repo1"
        assert r.right_target == "github:owner/repo2"
        assert r.left_score == 80.0
        assert r.right_score == 60.0
        assert r.winner == "left"
        assert r.delta == 20.0

    def test_to_dict_contains_all_keys(self):
        r = _duel_result()
        d = r.to_dict()
        for key in (
            "left_target", "right_target", "left_score", "right_score",
            "left_breakdown", "right_breakdown", "winner", "delta", "timestamp",
            "left_error", "right_error", "left_repo_name", "right_repo_name",
            "left_grade", "right_grade",
        ):
            assert key in d, f"Missing key: {key}"

    def test_to_dict_values_match(self):
        r = _duel_result(left_score=75.0, right_score=55.0, winner="left", delta=20.0)
        d = r.to_dict()
        assert d["left_score"] == 75.0
        assert d["right_score"] == 55.0
        assert d["winner"] == "left"

    def test_optional_fields_default_none(self):
        r = _duel_result()
        assert r.left_error is None
        assert r.right_error is None

    def test_error_fields_stored(self):
        r = DuelResult(
            left_target="t1", right_target="t2",
            left_score=None, right_score=80.0,
            left_breakdown={}, right_breakdown={},
            winner="right", delta=None,
            timestamp="2026-01-01 00:00 UTC",
            left_error="Clone failed",
        )
        assert r.left_error == "Clone failed"
        assert r.winner == "right"


# ---------------------------------------------------------------------------
# D1 — _determine_winner
# ---------------------------------------------------------------------------

class TestDetermineWinner:
    def test_left_wins_by_large_margin(self):
        winner, delta = _determine_winner(90.0, 60.0)
        assert winner == "left"
        assert delta == 30.0

    def test_right_wins_by_large_margin(self):
        winner, delta = _determine_winner(50.0, 80.0)
        assert winner == "right"
        assert delta == 30.0

    def test_tie_within_5_points(self):
        winner, delta = _determine_winner(80.0, 76.0)
        assert winner == "tie"
        assert delta == 4.0

    def test_tie_exactly_5_points(self):
        winner, delta = _determine_winner(80.0, 75.0)
        assert winner == "tie"
        assert delta == 5.0

    def test_left_wins_just_over_tie_threshold(self):
        winner, delta = _determine_winner(80.0, 74.0)
        assert winner == "left"
        assert delta == 6.0

    def test_both_none_returns_error(self):
        winner, delta = _determine_winner(None, None)
        assert winner == "error"
        assert delta is None

    def test_left_none_right_wins(self):
        winner, delta = _determine_winner(None, 80.0)
        assert winner == "right"
        assert delta is None

    def test_right_none_left_wins(self):
        winner, delta = _determine_winner(80.0, None)
        assert winner == "left"
        assert delta is None

    def test_equal_scores_tie(self):
        winner, delta = _determine_winner(70.0, 70.0)
        assert winner == "tie"
        assert delta == 0.0


# ---------------------------------------------------------------------------
# D1 — run_duel with mocked analyze_target
# ---------------------------------------------------------------------------

class TestRunDuel:
    @patch("agentkit_cli.duel.analyze_target")
    def test_both_succeed(self, mock_analyze):
        mock_analyze.side_effect = [
            _analyze_result("github:owner/repo1", score=85.0),
            _analyze_result("github:owner/repo2", score=65.0),
        ]
        result = run_duel("github:owner/repo1", "github:owner/repo2")
        assert result.left_score == 85.0
        assert result.right_score == 65.0
        assert result.winner == "left"
        assert result.delta == 20.0
        assert result.left_error is None
        assert result.right_error is None

    @patch("agentkit_cli.duel.analyze_target")
    def test_left_fails(self, mock_analyze):
        mock_analyze.side_effect = [
            RuntimeError("Clone failed"),
            _analyze_result("github:owner/repo2", score=70.0),
        ]
        result = run_duel("github:owner/repo1", "github:owner/repo2")
        assert result.left_score is None
        assert result.right_score == 70.0
        assert result.winner == "right"
        assert result.left_error is not None
        assert "Clone failed" in result.left_error

    @patch("agentkit_cli.duel.analyze_target")
    def test_right_fails(self, mock_analyze):
        mock_analyze.side_effect = [
            _analyze_result("github:owner/repo1", score=70.0),
            RuntimeError("Timeout"),
        ]
        result = run_duel("github:owner/repo1", "github:owner/repo2")
        assert result.left_score == 70.0
        assert result.right_score is None
        assert result.winner == "left"
        assert result.right_error is not None

    @patch("agentkit_cli.duel.analyze_target")
    def test_both_fail(self, mock_analyze):
        mock_analyze.side_effect = [
            RuntimeError("Fail 1"),
            RuntimeError("Fail 2"),
        ]
        result = run_duel("github:owner/repo1", "github:owner/repo2")
        assert result.left_score is None
        assert result.right_score is None
        assert result.winner == "error"
        assert result.left_error is not None
        assert result.right_error is not None

    @patch("agentkit_cli.duel.analyze_target")
    def test_tie_within_5(self, mock_analyze):
        mock_analyze.side_effect = [
            _analyze_result("github:owner/repo1", score=78.0),
            _analyze_result("github:owner/repo2", score=75.0),
        ]
        result = run_duel("github:owner/repo1", "github:owner/repo2")
        assert result.winner == "tie"

    @patch("agentkit_cli.duel.analyze_target")
    def test_timestamp_present(self, mock_analyze):
        mock_analyze.side_effect = [
            _analyze_result("t1"),
            _analyze_result("t2"),
        ]
        result = run_duel("t1", "t2")
        assert result.timestamp != ""
        assert "UTC" in result.timestamp

    @patch("agentkit_cli.duel.analyze_target")
    def test_repo_names_propagated(self, mock_analyze):
        mock_analyze.side_effect = [
            _analyze_result("github:owner/myfirst", score=90.0, repo_name="myfirst"),
            _analyze_result("github:owner/mysecond", score=70.0, repo_name="mysecond"),
        ]
        result = run_duel("github:owner/myfirst", "github:owner/mysecond")
        assert result.left_repo_name == "myfirst"
        assert result.right_repo_name == "mysecond"

    @patch("agentkit_cli.duel.analyze_target")
    def test_breakdown_propagated(self, mock_analyze):
        ar = _analyze_result("t1", score=80.0)
        mock_analyze.side_effect = [ar, _analyze_result("t2", score=60.0)]
        result = run_duel("t1", "t2")
        assert "agentmd" in result.left_breakdown


# ---------------------------------------------------------------------------
# D2 — CLI --json output
# ---------------------------------------------------------------------------

class TestDuelCLI:
    @patch("agentkit_cli.main.duel_command")
    def test_json_output_schema(self, mock_cmd):
        captured = {}
        def _fake(target1, target2, share, json_output, timeout, keep):
            import json as _json
            from rich.console import Console as _C
            _C().print(_json.dumps(_duel_result().to_dict(), indent=2))
        mock_cmd.side_effect = _fake
        result = runner.invoke(app, ["duel", "github:o/r1", "github:o/r2", "--json"])
        assert result.exit_code == 0
        # Find JSON in output (may have ANSI noise from rich)
        import re
        m = re.search(r'\{.*\}', result.output, re.DOTALL)
        assert m, f"No JSON found in: {result.output}"
        data = json.loads(m.group())
        assert "left_target" in data
        assert "right_target" in data
        assert "winner" in data
        assert "left_score" in data
        assert "right_score" in data

    @patch("agentkit_cli.commands.duel_cmd.run_duel")
    def test_json_winner_field(self, mock_run):
        mock_run.return_value = _duel_result(winner="left")
        result = runner.invoke(app, ["duel", "github:o/r1", "github:o/r2", "--json"])
        assert result.exit_code == 0
        import re
        m = re.search(r'\{.*\}', result.output, re.DOTALL)
        assert m
        data = json.loads(m.group())
        assert data["winner"] == "left"

    @patch("agentkit_cli.commands.duel_cmd.run_duel")
    @patch("agentkit_cli.commands.duel_cmd.publish_duel")
    def test_share_triggers_publish(self, mock_publish, mock_run):
        mock_run.return_value = _duel_result()
        mock_publish.return_value = "https://here.now/abc123"
        result = runner.invoke(app, ["duel", "github:o/r1", "github:o/r2", "--share"])
        assert result.exit_code == 0
        mock_publish.assert_called_once()

    @patch("agentkit_cli.commands.duel_cmd.run_duel")
    @patch("agentkit_cli.commands.duel_cmd.publish_duel")
    def test_no_share_skips_publish(self, mock_publish, mock_run):
        mock_run.return_value = _duel_result()
        result = runner.invoke(app, ["duel", "github:o/r1", "github:o/r2", "--no-share"])
        assert result.exit_code == 0
        mock_publish.assert_not_called()

    @patch("agentkit_cli.commands.duel_cmd.run_duel")
    @patch("agentkit_cli.commands.duel_cmd.publish_duel")
    def test_share_url_in_json(self, mock_publish, mock_run):
        mock_run.return_value = _duel_result()
        mock_publish.return_value = "https://here.now/xyz"
        result = runner.invoke(
            app, ["duel", "github:o/r1", "github:o/r2", "--share", "--json"]
        )
        assert result.exit_code == 0
        import re
        m = re.search(r'\{.*\}', result.output, re.DOTALL)
        assert m
        data = json.loads(m.group())
        assert data.get("share_url") == "https://here.now/xyz"

    @patch("agentkit_cli.commands.duel_cmd.run_duel")
    def test_default_output_not_json(self, mock_run):
        mock_run.return_value = _duel_result()
        result = runner.invoke(app, ["duel", "github:o/r1", "github:o/r2"])
        assert result.exit_code == 0
        # Should contain table-style output, not raw JSON
        assert "{" not in result.output or "agentkit duel" in result.output

    @patch("agentkit_cli.commands.duel_cmd.run_duel")
    def test_table_contains_repo_names(self, mock_run):
        mock_run.return_value = _duel_result()
        result = runner.invoke(app, ["duel", "github:o/r1", "github:o/r2"])
        assert "repo1" in result.output or "repo2" in result.output

    @patch("agentkit_cli.commands.duel_cmd.run_duel")
    def test_winner_announced_in_output(self, mock_run):
        mock_run.return_value = _duel_result(winner="left")
        result = runner.invoke(app, ["duel", "github:o/r1", "github:o/r2"])
        assert "win" in result.output.lower() or "🏆" in result.output

    @patch("agentkit_cli.commands.duel_cmd.run_duel")
    def test_tie_announcement(self, mock_run):
        mock_run.return_value = _duel_result(
            left_score=79.0, right_score=76.0, winner="tie", delta=3.0
        )
        result = runner.invoke(app, ["duel", "github:o/r1", "github:o/r2"])
        assert "tie" in result.output.lower() or "Tie" in result.output


# ---------------------------------------------------------------------------
# D3 — generate_duel_html
# ---------------------------------------------------------------------------

class TestGenerateDuelHtml:
    def test_returns_html_string(self):
        r = _duel_result()
        html = generate_duel_html(r)
        assert isinstance(html, str)
        assert html.startswith("<!DOCTYPE html>")

    def test_contains_both_repo_names(self):
        r = _duel_result()
        html = generate_duel_html(r)
        assert "repo1" in html
        assert "repo2" in html

    def test_contains_left_score(self):
        r = _duel_result(left_score=83.0)
        html = generate_duel_html(r)
        assert "83" in html

    def test_contains_right_score(self):
        r = _duel_result(right_score=61.0)
        html = generate_duel_html(r)
        assert "61" in html

    def test_winner_badge_present_for_left_win(self):
        r = _duel_result(winner="left")
        html = generate_duel_html(r)
        assert "WINNER" in html or "winner" in html.lower()

    def test_winner_badge_present_for_right_win(self):
        r = _duel_result(winner="right", left_score=60.0, right_score=80.0)
        html = generate_duel_html(r)
        assert "WINNER" in html or "winner" in html.lower()

    def test_tie_badge_present(self):
        r = _duel_result(winner="tie", left_score=78.0, right_score=75.0, delta=3.0)
        html = generate_duel_html(r)
        assert "TIE" in html or "tie" in html.lower() or "Tie" in html

    def test_dark_background_in_css(self):
        r = _duel_result()
        html = generate_duel_html(r)
        assert "#1e1e1e" in html

    def test_two_column_layout_marker(self):
        r = _duel_result()
        html = generate_duel_html(r)
        assert "duel-grid" in html or "grid" in html

    def test_agentkit_version_in_footer(self):
        from agentkit_cli import __version__
        r = _duel_result()
        html = generate_duel_html(r)
        assert __version__ in html

    def test_timestamp_in_html(self):
        r = _duel_result()
        html = generate_duel_html(r)
        assert r.timestamp in html

    def test_error_shown_when_left_fails(self):
        r = DuelResult(
            left_target="t1", right_target="t2",
            left_score=None, right_score=80.0,
            left_breakdown={}, right_breakdown={},
            winner="right", delta=None,
            timestamp="2026-01-01 00:00 UTC",
            left_error="Clone failed",
            left_repo_name="t1", right_repo_name="t2",
        )
        html = generate_duel_html(r)
        assert "Clone failed" in html

    def test_no_error_section_when_no_error(self):
        r = _duel_result()
        html = generate_duel_html(r)
        # error-note appears in CSS; check that no div uses it (no actual error displayed)
        import re
        error_divs = re.findall(r'<div[^>]*class="error-note"', html)
        assert len(error_divs) == 0

    def test_both_fail_renders_gracefully(self):
        r = DuelResult(
            left_target="t1", right_target="t2",
            left_score=None, right_score=None,
            left_breakdown={}, right_breakdown={},
            winner="error", delta=None,
            timestamp="2026-01-01 00:00 UTC",
            left_error="Fail", right_error="Fail",
            left_repo_name="t1", right_repo_name="t2",
        )
        html = generate_duel_html(r)
        assert "<!DOCTYPE html>" in html


# ---------------------------------------------------------------------------
# D3 — publish_duel (here.now API sequence)
# ---------------------------------------------------------------------------

class TestPublishDuel:
    @patch("agentkit_cli.duel_report._json_post")
    @patch("agentkit_cli.duel_report._put_file")
    @patch("agentkit_cli.duel_report._finalize")
    def test_publish_returns_url(self, mock_finalize, mock_put, mock_post):
        mock_post.return_value = {
            "siteUrl": "https://here.now/abc",
            "upload": {
                "versionId": "v1",
                "uploads": [{"url": "https://upload.example.com/file"}],
                "finalizeUrl": "https://api.here.now/finalize/v1",
            },
        }
        mock_finalize.return_value = {"url": "https://here.now/abc"}
        result = publish_duel(_duel_result())
        assert result == "https://here.now/abc"

    @patch("agentkit_cli.duel_report._json_post")
    @patch("agentkit_cli.duel_report._put_file")
    @patch("agentkit_cli.duel_report._finalize")
    def test_publish_calls_post_put_finalize_in_order(
        self, mock_finalize, mock_put, mock_post
    ):
        call_order = []
        mock_post.side_effect = lambda *a, **kw: call_order.append("post") or {
            "siteUrl": "https://here.now/abc",
            "upload": {
                "versionId": "v1",
                "uploads": [{"url": "https://up.example.com/f"}],
                "finalizeUrl": "https://api.here.now/fin",
            },
        }
        mock_put.side_effect = lambda *a, **kw: call_order.append("put")
        mock_finalize.side_effect = lambda *a, **kw: call_order.append("finalize") or {
            "url": "https://here.now/abc"
        }
        publish_duel(_duel_result())
        assert call_order == ["post", "put", "finalize"]

    @patch("agentkit_cli.duel_report._json_post")
    def test_publish_returns_none_on_api_error(self, mock_post):
        mock_post.side_effect = Exception("Network error")
        result = publish_duel(_duel_result())
        assert result is None

    @patch("agentkit_cli.duel_report._json_post")
    def test_publish_returns_none_on_missing_upload_urls(self, mock_post):
        mock_post.return_value = {"siteUrl": "https://here.now/abc"}
        result = publish_duel(_duel_result())
        assert result is None
