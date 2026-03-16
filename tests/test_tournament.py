"""Tests for agentkit tournament engine, CLI command, HTML report, and publish."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from agentkit_cli.analyze import AnalyzeResult
from agentkit_cli.duel import DuelResult
from agentkit_cli.tournament import (
    StandingEntry,
    TournamentResult,
    _build_standings,
    _score_for_repo,
    run_tournament,
)
from agentkit_cli.tournament_report import generate_tournament_html, publish_tournament
from agentkit_cli.main import app

runner = CliRunner()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REPOS_4 = ["github:owner/r1", "github:owner/r2", "github:owner/r3", "github:owner/r4"]
REPOS_3 = ["github:owner/a", "github:owner/b", "github:owner/c"]
REPOS_5 = ["github:owner/r1", "github:owner/r2", "github:owner/r3", "github:owner/r4", "github:owner/r5"]


def _make_duel(
    left: str,
    right: str,
    left_score: float = 80.0,
    right_score: float = 60.0,
    winner: str = "left",
) -> DuelResult:
    return DuelResult(
        left_target=left,
        right_target=right,
        left_score=left_score,
        right_score=right_score,
        left_breakdown={},
        right_breakdown={},
        winner=winner,
        delta=abs(left_score - right_score) if winner not in ("error", "tie") else None,
        timestamp="2026-01-01 00:00 UTC",
        left_repo_name=left.split("/")[-1],
        right_repo_name=right.split("/")[-1],
    )


def _mock_duel(target1: str, target2: str, **kwargs) -> DuelResult:
    """Return a deterministic mock duel: first arg always wins with score 80 vs 60."""
    return _make_duel(target1, target2, left_score=80.0, right_score=60.0, winner="left")


def _make_tournament_result(repos=None) -> TournamentResult:
    repos = repos or REPOS_4
    import itertools
    duels = [
        _make_duel(r1, r2)
        for r1, r2 in itertools.combinations(repos, 2)
    ]
    standings = _build_standings(repos, duels)
    return TournamentResult(
        repos=repos,
        rounds=[duels],
        standings=standings,
        winner=standings[0].repo,
        total_duels=len(duels),
        timestamp="2026-01-01 00:00 UTC",
    )


# ---------------------------------------------------------------------------
# D1 — Round-robin pairing logic
# ---------------------------------------------------------------------------

class TestRoundRobinPairings:
    """3 repos → 3 pairs, 4 repos → 6 pairs, 5 repos → 10 pairs."""

    def test_3_repos_gives_3_pairs(self):
        import itertools
        pairs = list(itertools.combinations(REPOS_3, 2))
        assert len(pairs) == 3

    def test_4_repos_gives_6_pairs(self):
        import itertools
        pairs = list(itertools.combinations(REPOS_4, 2))
        assert len(pairs) == 6

    def test_5_repos_gives_10_pairs(self):
        import itertools
        pairs = list(itertools.combinations(REPOS_5, 2))
        assert len(pairs) == 10

    def test_n_repos_formula(self):
        import itertools
        for n in range(3, 9):
            repos = [f"github:owner/r{i}" for i in range(n)]
            expected = n * (n - 1) // 2
            assert len(list(itertools.combinations(repos, 2))) == expected

    def test_each_pair_unique(self):
        import itertools
        pairs = list(itertools.combinations(REPOS_4, 2))
        # No duplicates
        assert len(set(pairs)) == len(pairs)

    def test_every_repo_appears_as_left_or_right(self):
        import itertools
        pairs = list(itertools.combinations(REPOS_4, 2))
        seen = set()
        for l, r in pairs:
            seen.add(l)
            seen.add(r)
        assert seen == set(REPOS_4)


# ---------------------------------------------------------------------------
# D1 — TournamentResult dataclass
# ---------------------------------------------------------------------------

class TestTournamentResultDataclass:
    def test_to_dict_keys(self):
        tr = _make_tournament_result()
        d = tr.to_dict()
        for key in ("repos", "rounds", "standings", "winner", "total_duels", "timestamp"):
            assert key in d

    def test_to_dict_standings_keys(self):
        tr = _make_tournament_result()
        d = tr.to_dict()
        assert len(d["standings"]) == len(REPOS_4)
        for s in d["standings"]:
            for key in ("repo", "wins", "losses", "avg_score", "rank"):
                assert key in s

    def test_total_duels_matches_rounds(self):
        tr = _make_tournament_result()
        assert tr.total_duels == 6  # 4C2

    def test_winner_is_top_standing(self):
        tr = _make_tournament_result()
        assert tr.winner == tr.standings[0].repo


# ---------------------------------------------------------------------------
# D1 — _build_standings
# ---------------------------------------------------------------------------

class TestBuildStandings:
    def test_wins_counted_correctly(self):
        duels = [
            _make_duel("github:owner/A", "github:owner/B", winner="left"),
            _make_duel("github:owner/A", "github:owner/C", winner="left"),
            _make_duel("github:owner/B", "github:owner/C", winner="left"),
        ]
        repos = ["github:owner/A", "github:owner/B", "github:owner/C"]
        standings = _build_standings(repos, duels)
        wins = {s.repo: s.wins for s in standings}
        assert wins["github:owner/A"] == 2
        assert wins["github:owner/B"] == 1
        assert wins["github:owner/C"] == 0

    def test_losses_counted_correctly(self):
        duels = [
            _make_duel("github:owner/A", "github:owner/B", winner="left"),
            _make_duel("github:owner/A", "github:owner/C", winner="left"),
            _make_duel("github:owner/B", "github:owner/C", winner="left"),
        ]
        repos = ["github:owner/A", "github:owner/B", "github:owner/C"]
        standings = _build_standings(repos, duels)
        losses = {s.repo: s.losses for s in standings}
        assert losses["github:owner/C"] == 2
        assert losses["github:owner/B"] == 1
        assert losses["github:owner/A"] == 0

    def test_ranking_by_wins_desc(self):
        duels = [
            _make_duel("github:owner/A", "github:owner/B", winner="left"),
            _make_duel("github:owner/A", "github:owner/C", winner="left"),
            _make_duel("github:owner/B", "github:owner/C", winner="left"),
        ]
        repos = ["github:owner/A", "github:owner/B", "github:owner/C"]
        standings = _build_standings(repos, duels)
        assert standings[0].repo == "github:owner/A"
        assert standings[0].rank == 1

    def test_tiebreak_by_avg_score(self):
        # A and B both win 1, but A has higher avg score
        duels = [
            _make_duel("github:owner/A", "github:owner/C", left_score=90.0, right_score=50.0, winner="left"),
            _make_duel("github:owner/B", "github:owner/C", left_score=70.0, right_score=50.0, winner="left"),
            _make_duel("github:owner/A", "github:owner/B", left_score=90.0, right_score=70.0, winner="tie"),
        ]
        repos = ["github:owner/A", "github:owner/B", "github:owner/C"]
        standings = _build_standings(repos, duels)
        # A and B both 1 win (tie doesn't add wins); A has higher avg so ranks first
        a_entry = next(s for s in standings if s.repo == "github:owner/A")
        b_entry = next(s for s in standings if s.repo == "github:owner/B")
        assert a_entry.avg_score > b_entry.avg_score

    def test_rank_field_assigned(self):
        duels = [_make_duel("github:owner/A", "github:owner/B", winner="left")]
        standings = _build_standings(["github:owner/A", "github:owner/B"], duels)
        ranks = [s.rank for s in standings]
        assert 1 in ranks
        assert 2 in ranks

    def test_avg_score_computed(self):
        duels = [_make_duel("github:owner/A", "github:owner/B", left_score=80.0, right_score=60.0, winner="left")]
        standings = _build_standings(["github:owner/A", "github:owner/B"], duels)
        a = next(s for s in standings if s.repo == "github:owner/A")
        assert a.avg_score == 80.0


# ---------------------------------------------------------------------------
# D1 — _score_for_repo
# ---------------------------------------------------------------------------

class TestScoreForRepo:
    def test_left_side_score(self):
        d = _make_duel("github:owner/A", "github:owner/B", left_score=80.0, right_score=60.0)
        assert _score_for_repo("github:owner/A", [d]) == 80.0

    def test_right_side_score(self):
        d = _make_duel("github:owner/A", "github:owner/B", left_score=80.0, right_score=60.0)
        assert _score_for_repo("github:owner/B", [d]) == 60.0

    def test_multiple_duels_avg(self):
        d1 = _make_duel("github:owner/A", "github:owner/B", left_score=80.0, right_score=60.0)
        d2 = _make_duel("github:owner/A", "github:owner/C", left_score=60.0, right_score=70.0)
        assert _score_for_repo("github:owner/A", [d1, d2]) == 70.0

    def test_missing_score_excluded(self):
        d = _make_duel("github:owner/A", "github:owner/B")
        d.left_score = None
        assert _score_for_repo("github:owner/A", [d]) == 0.0


# ---------------------------------------------------------------------------
# D1 — run_tournament validation
# ---------------------------------------------------------------------------

class TestRunTournamentValidation:
    def test_fewer_than_4_repos_raises(self):
        with pytest.raises((ValueError, SystemExit)):
            run_tournament(["github:owner/a", "github:owner/b", "github:owner/c"])

    def test_more_than_16_repos_raises(self):
        repos = [f"github:owner/r{i}" for i in range(17)]
        with pytest.raises((ValueError, SystemExit)):
            run_tournament(repos)

    def test_exactly_4_repos_allowed(self):
        with patch("agentkit_cli.tournament.run_duel", side_effect=_mock_duel):
            result = run_tournament(REPOS_4, parallel=False, quiet=True)
        assert result.total_duels == 6

    def test_result_has_all_repos(self):
        with patch("agentkit_cli.tournament.run_duel", side_effect=_mock_duel):
            result = run_tournament(REPOS_4, parallel=False, quiet=True)
        assert set(result.repos) == set(REPOS_4)


# ---------------------------------------------------------------------------
# D1 — Parallel vs sequential execution
# ---------------------------------------------------------------------------

class TestParallelVsSequential:
    def test_sequential_returns_same_structure(self):
        with patch("agentkit_cli.tournament.run_duel", side_effect=_mock_duel):
            result = run_tournament(REPOS_4, parallel=False, quiet=True)
        assert result.total_duels == 6
        assert len(result.standings) == 4

    def test_parallel_returns_same_structure(self):
        with patch("agentkit_cli.tournament.run_duel", side_effect=_mock_duel):
            result = run_tournament(REPOS_4, parallel=True, quiet=True)
        assert result.total_duels == 6
        assert len(result.standings) == 4

    def test_winner_same_parallel_vs_sequential(self):
        with patch("agentkit_cli.tournament.run_duel", side_effect=_mock_duel):
            seq = run_tournament(REPOS_4, parallel=False, quiet=True)
        with patch("agentkit_cli.tournament.run_duel", side_effect=_mock_duel):
            par = run_tournament(REPOS_4, parallel=True, quiet=True)
        # In both cases the same repos run; winner should be the same
        assert seq.winner == par.winner


# ---------------------------------------------------------------------------
# D1 — Partial failure handling
# ---------------------------------------------------------------------------

class TestPartialFailure:
    def test_one_failing_pairing_continues(self):
        call_count = [0]

        def _sometimes_fail(t1, t2, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise RuntimeError("Simulated failure")
            return _mock_duel(t1, t2)

        with patch("agentkit_cli.tournament.run_duel", side_effect=_sometimes_fail):
            result = run_tournament(REPOS_4, parallel=False, quiet=True)

        # All 6 duels completed despite one failure
        assert result.total_duels == 6
        assert len(result.rounds[0]) == 6

    def test_error_duels_do_not_crash_standings(self):
        call_count = [0]

        def _sometimes_fail(t1, t2, **kwargs):
            call_count[0] += 1
            if call_count[0] <= 2:
                raise RuntimeError("Simulated failure")
            return _mock_duel(t1, t2)

        with patch("agentkit_cli.tournament.run_duel", side_effect=_sometimes_fail):
            result = run_tournament(REPOS_4, parallel=False, quiet=True)

        assert len(result.standings) == 4

    def test_all_failing_pairings_still_returns_result(self):
        def _always_fail(t1, t2, **kwargs):
            raise RuntimeError("All failed")

        with patch("agentkit_cli.tournament.run_duel", side_effect=_always_fail):
            result = run_tournament(REPOS_4, parallel=False, quiet=True)

        assert result.total_duels == 6


# ---------------------------------------------------------------------------
# D3 — HTML report generation
# ---------------------------------------------------------------------------

class TestHTMLReport:
    def test_html_contains_winner(self):
        tr = _make_tournament_result()
        html = generate_tournament_html(tr)
        winner_short = tr.winner.split("/")[-1]
        assert winner_short in html

    def test_html_contains_standings_header(self):
        tr = _make_tournament_result()
        html = generate_tournament_html(tr)
        assert "Standings" in html

    def test_html_contains_all_repos(self):
        tr = _make_tournament_result()
        html = generate_tournament_html(tr)
        for repo in REPOS_4:
            assert repo.split("/")[-1] in html

    def test_html_contains_tournament_title(self):
        tr = _make_tournament_result()
        html = generate_tournament_html(tr)
        assert "Agent-Readiness Tournament" in html

    def test_html_contains_n_repos(self):
        tr = _make_tournament_result()
        html = generate_tournament_html(tr)
        assert str(len(REPOS_4)) in html

    def test_html_contains_n_duels(self):
        tr = _make_tournament_result()
        html = generate_tournament_html(tr)
        assert str(tr.total_duels) in html

    def test_html_contains_winner_banner(self):
        tr = _make_tournament_result()
        html = generate_tournament_html(tr)
        assert "winner-banner" in html

    def test_html_contains_trophy_emoji(self):
        tr = _make_tournament_result()
        html = generate_tournament_html(tr)
        assert "🏆" in html

    def test_html_is_valid_string(self):
        tr = _make_tournament_result()
        html = generate_tournament_html(tr)
        assert isinstance(html, str)
        assert len(html) > 500

    def test_html_starts_with_doctype(self):
        tr = _make_tournament_result()
        html = generate_tournament_html(tr)
        assert html.startswith("<!DOCTYPE html>")

    def test_html_contains_match_results(self):
        tr = _make_tournament_result()
        html = generate_tournament_html(tr)
        assert "Match Results" in html

    def test_html_contains_wl_column(self):
        tr = _make_tournament_result()
        html = generate_tournament_html(tr)
        assert "W-L" in html


# ---------------------------------------------------------------------------
# D3 — publish_tournament (mock here.now)
# ---------------------------------------------------------------------------

class TestPublishTournament:
    def _mock_publish_chain(self):
        """Return mock objects for the 3-step publish flow."""
        mock_post = MagicMock(return_value={
            "upload": {
                "uploads": [{"url": "https://upload.example.com/idx"}],
                "finalizeUrl": "https://api.here.now/finalize/123",
                "versionId": "v123",
            },
            "siteUrl": "https://xyz.here.now",
        })
        mock_put = MagicMock()
        mock_finalize = MagicMock(return_value={"url": "https://xyz.here.now"})
        return mock_post, mock_put, mock_finalize

    def test_publish_returns_url(self):
        tr = _make_tournament_result()
        mock_post, mock_put, mock_finalize = self._mock_publish_chain()
        with patch("agentkit_cli.tournament_report._json_post", mock_post), \
             patch("agentkit_cli.tournament_report._put_file", mock_put), \
             patch("agentkit_cli.tournament_report._finalize", mock_finalize):
            url = publish_tournament(tr)
        assert url == "https://xyz.here.now"

    def test_publish_calls_put_with_html(self):
        tr = _make_tournament_result()
        mock_post, mock_put, mock_finalize = self._mock_publish_chain()
        with patch("agentkit_cli.tournament_report._json_post", mock_post), \
             patch("agentkit_cli.tournament_report._put_file", mock_put), \
             patch("agentkit_cli.tournament_report._finalize", mock_finalize):
            publish_tournament(tr)
        assert mock_put.called

    def test_publish_failure_returns_none(self):
        tr = _make_tournament_result()
        with patch("agentkit_cli.tournament_report._json_post", side_effect=Exception("network error")):
            url = publish_tournament(tr)
        assert url is None


# ---------------------------------------------------------------------------
# D2 — CLI integration
# ---------------------------------------------------------------------------

class TestCLITournamentCommand:
    def test_tournament_with_4_repos_runs(self):
        with patch("agentkit_cli.commands.tournament_cmd.run_tournament") as mock_run:
            mock_run.return_value = _make_tournament_result()
            result = runner.invoke(app, ["tournament"] + REPOS_4)
        assert result.exit_code == 0

    def test_tournament_json_output(self):
        with patch("agentkit_cli.commands.tournament_cmd.run_tournament") as mock_run:
            mock_run.return_value = _make_tournament_result()
            result = runner.invoke(app, ["tournament", "--json"] + REPOS_4)
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "standings" in data
        assert "winner" in data
        assert "total_duels" in data

    def test_tournament_json_contains_all_repos(self):
        with patch("agentkit_cli.commands.tournament_cmd.run_tournament") as mock_run:
            mock_run.return_value = _make_tournament_result()
            result = runner.invoke(app, ["tournament", "--json"] + REPOS_4)
        data = json.loads(result.output)
        assert set(data["repos"]) == set(REPOS_4)

    def test_tournament_fewer_than_4_repos_exits_nonzero(self):
        result = runner.invoke(app, ["tournament"] + REPOS_3)
        assert result.exit_code != 0

    def test_tournament_more_than_16_repos_exits_nonzero(self):
        repos = [f"github:owner/r{i}" for i in range(17)]
        result = runner.invoke(app, ["tournament"] + repos)
        assert result.exit_code != 0

    def test_tournament_share_flag_calls_publish(self):
        with patch("agentkit_cli.commands.tournament_cmd.run_tournament") as mock_run, \
             patch("agentkit_cli.commands.tournament_cmd.publish_tournament") as mock_pub:
            mock_run.return_value = _make_tournament_result()
            mock_pub.return_value = "https://example.here.now"
            result = runner.invoke(app, ["tournament", "--share"] + REPOS_4)
        assert mock_pub.called

    def test_tournament_no_share_does_not_call_publish(self):
        with patch("agentkit_cli.commands.tournament_cmd.run_tournament") as mock_run, \
             patch("agentkit_cli.commands.tournament_cmd.publish_tournament") as mock_pub:
            mock_run.return_value = _make_tournament_result()
            result = runner.invoke(app, ["tournament"] + REPOS_4)
        assert not mock_pub.called

    def test_tournament_share_url_in_json_output(self):
        with patch("agentkit_cli.commands.tournament_cmd.run_tournament") as mock_run, \
             patch("agentkit_cli.commands.tournament_cmd.publish_tournament") as mock_pub:
            mock_run.return_value = _make_tournament_result()
            mock_pub.return_value = "https://example.here.now"
            result = runner.invoke(app, ["tournament", "--share", "--json"] + REPOS_4)
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data.get("share_url") == "https://example.here.now"

    def test_tournament_quiet_suppresses_output(self):
        with patch("agentkit_cli.commands.tournament_cmd.run_tournament") as mock_run:
            mock_run.return_value = _make_tournament_result()
            result = runner.invoke(app, ["tournament", "--quiet"] + REPOS_4)
        assert result.exit_code == 0

    def test_tournament_output_writes_file(self, tmp_path):
        out = tmp_path / "report.html"
        with patch("agentkit_cli.commands.tournament_cmd.run_tournament") as mock_run:
            mock_run.return_value = _make_tournament_result()
            result = runner.invoke(app, ["tournament", "--output", str(out)] + REPOS_4)
        assert result.exit_code == 0
        assert out.exists()
        content = out.read_text()
        assert "Agent-Readiness Tournament" in content

    def test_tournament_parallel_flag_passed(self):
        with patch("agentkit_cli.commands.tournament_cmd.run_tournament") as mock_run:
            mock_run.return_value = _make_tournament_result()
            runner.invoke(app, ["tournament", "--no-parallel"] + REPOS_4)
        call_kwargs = mock_run.call_args
        assert call_kwargs is not None
        # parallel=False should have been passed
        assert call_kwargs.kwargs.get("parallel") is False or \
               (call_kwargs.args and False in call_kwargs.args)

    def test_tournament_registered_in_app(self):
        result = runner.invoke(app, ["--help"])
        assert "tournament" in result.output
