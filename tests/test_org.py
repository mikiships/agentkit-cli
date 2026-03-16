"""Tests for agentkit org feature (D1, D2, D3)."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch, call
from typing import Optional

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.github_api import list_repos, _build_headers, _check_rate_limit
from agentkit_cli.org_report import OrgReport, _grade, _score_class

runner = CliRunner()

# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

SAMPLE_REPOS = [
    {
        "full_name": "acme/alpha",
        "name": "alpha",
        "description": "Alpha repo",
        "stargazers_count": 200,
        "language": "Python",
        "html_url": "https://github.com/acme/alpha",
        "fork": False,
        "archived": False,
        "size": 100,
    },
    {
        "full_name": "acme/beta",
        "name": "beta",
        "description": "Beta repo",
        "stargazers_count": 50,
        "language": "TypeScript",
        "html_url": "https://github.com/acme/beta",
        "fork": False,
        "archived": False,
        "size": 50,
    },
    {
        "full_name": "acme/gamma",
        "name": "gamma",
        "description": "Gamma (fork)",
        "stargazers_count": 10,
        "language": "Go",
        "html_url": "https://github.com/acme/gamma",
        "fork": True,
        "archived": False,
        "size": 20,
    },
    {
        "full_name": "acme/delta",
        "name": "delta",
        "description": "Delta (archived)",
        "stargazers_count": 5,
        "language": "Rust",
        "html_url": "https://github.com/acme/delta",
        "fork": False,
        "archived": True,
        "size": 30,
    },
    {
        "full_name": "acme/epsilon",
        "name": "epsilon",
        "description": "",
        "stargazers_count": 0,
        "language": "Python",
        "html_url": "https://github.com/acme/epsilon",
        "fork": False,
        "archived": False,
        "size": 0,  # empty repo
    },
]


def _make_mock_response(data, headers=None):
    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=ctx)
    ctx.__exit__ = MagicMock(return_value=False)
    ctx.read.return_value = json.dumps(data).encode()
    ctx.headers = headers or {}
    return ctx


# ---------------------------------------------------------------------------
# D1: github_api.py tests
# ---------------------------------------------------------------------------

class TestBuildHeaders:
    def test_no_token(self):
        with patch.dict("os.environ", {}, clear=False):
            import os
            os.environ.pop("GITHUB_TOKEN", None)
            headers = _build_headers(token=None)
        assert "Authorization" not in headers
        assert headers["Accept"] == "application/vnd.github+json"

    def test_with_token(self):
        headers = _build_headers(token="mytoken")
        assert headers["Authorization"] == "Bearer mytoken"

    def test_env_token(self):
        with patch.dict("os.environ", {"GITHUB_TOKEN": "envtoken"}):
            headers = _build_headers()
        assert headers["Authorization"] == "Bearer envtoken"


class TestCheckRateLimit:
    def test_no_sleep_when_remaining_ok(self):
        with patch("time.sleep") as mock_sleep:
            _check_rate_limit({"X-RateLimit-Remaining": "100"})
            mock_sleep.assert_not_called()

    def test_sleeps_when_near_zero(self):
        import time as _time
        future_reset = str(int(_time.time()) + 30)
        with patch("time.sleep") as mock_sleep:
            _check_rate_limit({"X-RateLimit-Remaining": "2", "X-RateLimit-Reset": future_reset})
            mock_sleep.assert_called_once()

    def test_no_crash_on_bad_headers(self):
        _check_rate_limit({})
        _check_rate_limit({"X-RateLimit-Remaining": "bad"})


class TestListRepos:
    def _mock_page(self, data, next_url=None):
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.read.return_value = json.dumps(data).encode()
        link_header = f'<{next_url}>; rel="next"' if next_url else ""
        ctx.headers = {"Link": link_header} if link_header else {}
        return ctx

    def test_filters_forks_by_default(self):
        with patch("urllib.request.urlopen", return_value=self._mock_page(SAMPLE_REPOS)):
            repos = list_repos("acme", include_forks=False, include_archived=False)
        names = [r["name"] for r in repos]
        assert "gamma" not in names  # fork
        assert "alpha" in names

    def test_include_forks(self):
        with patch("urllib.request.urlopen", return_value=self._mock_page(SAMPLE_REPOS)):
            repos = list_repos("acme", include_forks=True, include_archived=False)
        names = [r["name"] for r in repos]
        assert "gamma" in names

    def test_filters_archived_by_default(self):
        with patch("urllib.request.urlopen", return_value=self._mock_page(SAMPLE_REPOS)):
            repos = list_repos("acme", include_forks=False, include_archived=False)
        names = [r["name"] for r in repos]
        assert "delta" not in names  # archived

    def test_include_archived(self):
        with patch("urllib.request.urlopen", return_value=self._mock_page(SAMPLE_REPOS)):
            repos = list_repos("acme", include_forks=False, include_archived=True)
        names = [r["name"] for r in repos]
        assert "delta" in names

    def test_filters_empty_repos(self):
        with patch("urllib.request.urlopen", return_value=self._mock_page(SAMPLE_REPOS)):
            repos = list_repos("acme")
        names = [r["name"] for r in repos]
        assert "epsilon" not in names  # size == 0

    def test_limit(self):
        with patch("urllib.request.urlopen", return_value=self._mock_page(SAMPLE_REPOS)):
            repos = list_repos("acme", limit=1)
        assert len(repos) <= 1

    def test_normalized_keys(self):
        with patch("urllib.request.urlopen", return_value=self._mock_page(SAMPLE_REPOS)):
            repos = list_repos("acme")
        assert repos
        r = repos[0]
        for key in ["full_name", "name", "description", "stars", "language", "url", "fork", "archived", "size"]:
            assert key in r

    def test_org_404_falls_back_to_user(self):
        from urllib.error import HTTPError
        import io

        call_count = [0]

        def side_effect(req, timeout=None):
            call_count[0] += 1
            if call_count[0] == 1:
                raise HTTPError(req.full_url, 404, "Not Found", {}, io.BytesIO(b""))
            ctx = MagicMock()
            ctx.__enter__ = MagicMock(return_value=ctx)
            ctx.__exit__ = MagicMock(return_value=False)
            ctx.read.return_value = json.dumps([SAMPLE_REPOS[0]]).encode()
            ctx.headers = {}
            return ctx

        with patch("urllib.request.urlopen", side_effect=side_effect):
            repos = list_repos("acme")
        assert len(repos) >= 1

    def test_both_404_raises_valueerror(self):
        from urllib.error import HTTPError
        import io

        def side_effect(req, timeout=None):
            raise HTTPError(req.full_url, 404, "Not Found", {}, io.BytesIO(b""))

        with patch("urllib.request.urlopen", side_effect=side_effect):
            with pytest.raises(ValueError, match="not found"):
                list_repos("nonexistent-owner-xyz")


# ---------------------------------------------------------------------------
# D1: OrgCommand tests
# ---------------------------------------------------------------------------

class TestOrgCommand:
    def _make_analyze_result(self, score: float):
        from agentkit_cli.commands.org_cmd import _analyze_repo
        return {
            "score": score,
            "grade": "A" if score >= 90 else "B" if score >= 80 else "C",
            "top_finding": "test finding",
            "status": "ok",
        }

    def test_parses_github_prefix(self):
        from agentkit_cli.commands.org_cmd import org_command
        with patch("agentkit_cli.github_api.list_repos", return_value=[]) as mock_lr:
            with patch("agentkit_cli.commands.org_cmd.console"):
                org_command(target="github:acme")
            mock_lr.assert_called_once()
            args, kwargs = mock_lr.call_args
            assert (args and args[0] == "acme") or kwargs.get("owner") == "acme"

    def test_bare_owner(self):
        from agentkit_cli.commands.org_cmd import org_command
        with patch("agentkit_cli.github_api.list_repos", return_value=[]) as mock_lr:
            with patch("agentkit_cli.commands.org_cmd.console"):
                org_command(target="acme")
            mock_lr.assert_called_once()

    def test_ranked_output_sorted_by_score(self):
        from agentkit_cli.commands.org_cmd import OrgCommand

        fake_repos = [
            {"full_name": "acme/low", "name": "low", "stars": 10, "description": ""},
            {"full_name": "acme/high", "name": "high", "stars": 20, "description": ""},
        ]

        def fake_analyze(full_name, timeout=120):
            if "high" in full_name:
                return {"score": 90.0, "grade": "A", "top_finding": "great", "status": "ok"}
            return {"score": 50.0, "grade": "F", "top_finding": "bad", "status": "ok"}

        with patch("agentkit_cli.github_api.list_repos", return_value=fake_repos):
            with patch("agentkit_cli.commands.org_cmd._analyze_repo", side_effect=fake_analyze):
                cmd = OrgCommand(owner="acme", json_output=True, parallel=1)
                result = cmd.run()

        ranked = result["ranked"]
        assert ranked[0]["repo"] == "high"
        assert ranked[0]["score"] == 90.0
        assert ranked[0]["rank"] == 1
        assert ranked[1]["rank"] == 2

    def test_json_output_structure(self, capsys):
        from agentkit_cli.commands.org_cmd import OrgCommand

        fake_repos = [{"full_name": "acme/repo1", "name": "repo1", "stars": 5, "description": "test"}]

        with patch("agentkit_cli.github_api.list_repos", return_value=fake_repos):
            with patch("agentkit_cli.commands.org_cmd._analyze_repo",
                       return_value={"score": 75.0, "grade": "C", "top_finding": "ok", "status": "ok"}):
                cmd = OrgCommand(owner="acme", json_output=True, parallel=1)
                result = cmd.run()

        assert result["owner"] == "acme"
        assert result["repo_count"] == 1
        assert "ranked" in result
        assert len(result["ranked"]) == 1
        r = result["ranked"][0]
        assert r["repo"] == "repo1"
        assert r["score"] == 75.0

    def test_empty_org(self, capsys):
        from agentkit_cli.commands.org_cmd import OrgCommand

        with patch("agentkit_cli.github_api.list_repos", return_value=[]):
            cmd = OrgCommand(owner="empty-acme", json_output=True, parallel=1)
            result = cmd.run()

        assert result["repo_count"] == 0
        assert result["ranked"] == []

    def test_include_forks_flag_passed_to_api(self):
        from agentkit_cli.commands.org_cmd import OrgCommand

        with patch("agentkit_cli.github_api.list_repos", return_value=[]) as mock_lr:
            cmd = OrgCommand(owner="acme", include_forks=True, json_output=True)
            cmd.run()
        _, kwargs = mock_lr.call_args
        assert kwargs.get("include_forks") is True

    def test_error_handling_in_analyze(self):
        from agentkit_cli.commands.org_cmd import OrgCommand

        fake_repos = [{"full_name": "acme/broken", "name": "broken", "stars": 0, "description": ""}]

        def fail_analyze(full_name, timeout=120):
            raise RuntimeError("clone failed")

        with patch("agentkit_cli.github_api.list_repos", return_value=fake_repos):
            with patch("agentkit_cli.commands.org_cmd._analyze_repo", side_effect=fail_analyze):
                cmd = OrgCommand(owner="acme", json_output=True, parallel=1)
                result = cmd.run()

        assert result["ranked"][0]["status"] == "error"
        assert result["ranked"][0]["score"] is None


# ---------------------------------------------------------------------------
# D2: OrgReport HTML tests
# ---------------------------------------------------------------------------

class TestOrgReport:
    def _make_results(self):
        return [
            {"rank": 1, "repo": "alpha", "full_name": "acme/alpha", "score": 88.0, "grade": "B", "top_finding": "good docs", "status": "ok"},
            {"rank": 2, "repo": "beta", "full_name": "acme/beta", "score": 62.0, "grade": "D", "top_finding": "missing AGENTS.md", "status": "ok"},
            {"rank": 3, "repo": "gamma", "full_name": "acme/gamma", "score": None, "grade": None, "top_finding": "clone failed", "status": "error"},
        ]

    def test_render_returns_html(self):
        report = OrgReport(owner="acme", results=self._make_results())
        html = report.render()
        assert "<!DOCTYPE html>" in html
        assert "acme" in html

    def test_render_contains_repo_names(self):
        report = OrgReport(owner="acme", results=self._make_results())
        html = report.render()
        assert "acme/alpha" in html
        assert "acme/beta" in html

    def test_render_contains_scores(self):
        report = OrgReport(owner="acme", results=self._make_results())
        html = report.render()
        assert "88.0" in html
        assert "62.0" in html

    def test_render_contains_grades(self):
        report = OrgReport(owner="acme", results=self._make_results())
        html = report.render()
        assert "grade-B" in html

    def test_render_contains_summary_stats(self):
        report = OrgReport(owner="acme", results=self._make_results())
        html = report.render()
        # Should have avg score and repo count
        assert "75.0" in html or "Avg Score" in html

    def test_render_top_repo_banner(self):
        report = OrgReport(owner="acme", results=self._make_results())
        html = report.render()
        assert "acme/alpha" in html
        assert "88.0" in html

    def test_render_no_results(self):
        report = OrgReport(owner="empty", results=[])
        html = report.render()
        assert "<!DOCTYPE html>" in html
        assert "empty" in html

    def test_grade_helper(self):
        assert _grade(95.0) == "A"
        assert _grade(85.0) == "B"
        assert _grade(75.0) == "C"
        assert _grade(65.0) == "D"
        assert _grade(50.0) == "F"
        assert _grade(None) == "-"

    def test_score_class_helper(self):
        assert _score_class(90.0) == "score-green"
        assert _score_class(70.0) == "score-yellow"
        assert _score_class(40.0) == "score-red"
        assert _score_class(None) == "score-na"


# ---------------------------------------------------------------------------
# D2: --output flag test
# ---------------------------------------------------------------------------

class TestOrgOutputFlag:
    def test_output_writes_file(self, tmp_path):
        from agentkit_cli.commands.org_cmd import OrgCommand

        fake_repos = [{"full_name": "acme/repo1", "name": "repo1", "stars": 5, "description": ""}]
        out_file = str(tmp_path / "report.html")

        with patch("agentkit_cli.github_api.list_repos", return_value=fake_repos):
            with patch("agentkit_cli.commands.org_cmd._analyze_repo",
                       return_value={"score": 75.0, "grade": "C", "top_finding": "ok", "status": "ok"}):
                cmd = OrgCommand(owner="acme", output=out_file, parallel=1)
                cmd.run()

        import os
        assert os.path.exists(out_file)
        content = open(out_file).read()
        assert "<!DOCTYPE html>" in content


# ---------------------------------------------------------------------------
# D3: Parallel + timeout tests
# ---------------------------------------------------------------------------

class TestParallelAnalysis:
    def test_parallel_flag_used(self):
        from agentkit_cli.commands.org_cmd import OrgCommand
        import concurrent.futures

        fake_repos = [
            {"full_name": "acme/r1", "name": "r1", "stars": 1, "description": ""},
            {"full_name": "acme/r2", "name": "r2", "stars": 2, "description": ""},
            {"full_name": "acme/r3", "name": "r3", "stars": 3, "description": ""},
        ]

        with patch("agentkit_cli.github_api.list_repos", return_value=fake_repos):
            with patch("agentkit_cli.commands.org_cmd._analyze_repo",
                       return_value={"score": 70.0, "grade": "C", "top_finding": "ok", "status": "ok"}):
                with patch("agentkit_cli.commands.org_cmd.ThreadPoolExecutor", wraps=concurrent.futures.ThreadPoolExecutor) as mock_ex:
                    cmd = OrgCommand(owner="acme", parallel=2, json_output=True)
                    cmd.run()
                    # ThreadPoolExecutor should have been called with max_workers=2
                    calls = mock_ex.call_args_list
                    assert any(c.kwargs.get("max_workers") == 2 for c in calls)

    def test_result_aggregation(self):
        from agentkit_cli.commands.org_cmd import OrgCommand

        fake_repos = [{"full_name": f"acme/r{i}", "name": f"r{i}", "stars": i, "description": ""} for i in range(5)]
        scores = [80.0, 70.0, 60.0, 50.0, 40.0]

        def fake_analyze(full_name, timeout=120):
            idx = int(full_name.split("r")[1])
            return {"score": scores[idx], "grade": "B", "top_finding": "ok", "status": "ok"}

        with patch("agentkit_cli.github_api.list_repos", return_value=fake_repos):
            with patch("agentkit_cli.commands.org_cmd._analyze_repo", side_effect=fake_analyze):
                cmd = OrgCommand(owner="acme", parallel=3, json_output=True)
                result = cmd.run()

        assert result["analyzed"] == 5
        assert len(result["ranked"]) == 5

    def test_timeout_field_passed(self):
        from agentkit_cli.commands.org_cmd import OrgCommand

        fake_repos = [{"full_name": "acme/r1", "name": "r1", "stars": 1, "description": ""}]
        captured_timeout = []

        def fake_analyze(full_name, timeout=120):
            captured_timeout.append(timeout)
            return {"score": 75.0, "grade": "C", "top_finding": "ok", "status": "ok"}

        with patch("agentkit_cli.github_api.list_repos", return_value=fake_repos):
            with patch("agentkit_cli.commands.org_cmd._analyze_repo", side_effect=fake_analyze):
                cmd = OrgCommand(owner="acme", timeout=60, json_output=True)
                cmd.run()

        assert 60 in captured_timeout

    def test_summary_counts(self):
        from agentkit_cli.commands.org_cmd import OrgCommand

        fake_repos = [
            {"full_name": "acme/ok", "name": "ok", "stars": 1, "description": ""},
            {"full_name": "acme/err", "name": "err", "stars": 1, "description": ""},
        ]

        def fake_analyze(full_name, timeout=120):
            if "err" in full_name:
                return {"score": None, "grade": None, "top_finding": "error", "status": "error"}
            return {"score": 80.0, "grade": "B", "top_finding": "ok", "status": "ok"}

        with patch("agentkit_cli.github_api.list_repos", return_value=fake_repos):
            with patch("agentkit_cli.commands.org_cmd._analyze_repo", side_effect=fake_analyze):
                cmd = OrgCommand(owner="acme", json_output=True, parallel=1)
                result = cmd.run()

        assert result["analyzed"] == 1
        assert result["failed"] == 1


# ---------------------------------------------------------------------------
# CLI integration test
# ---------------------------------------------------------------------------

class TestOrgCLI:
    def test_cli_org_json(self):
        fake_repos = [{"full_name": "acme/repo1", "name": "repo1", "stars": 5, "description": "test"}]

        with patch("agentkit_cli.github_api.list_repos", return_value=fake_repos):
            with patch("agentkit_cli.commands.org_cmd._analyze_repo",
                       return_value={"score": 80.0, "grade": "B", "top_finding": "ok", "status": "ok"}):
                result = runner.invoke(app, ["org", "github:acme", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["owner"] == "acme"
        assert data["repo_count"] == 1

    def test_cli_org_no_target(self):
        result = runner.invoke(app, ["org"])
        # Should fail with usage error (missing required argument)
        assert result.exit_code != 0

    def test_cli_org_limit(self):
        fake_repos = [{"full_name": "acme/r1", "name": "r1", "stars": 1, "description": ""}]

        with patch("agentkit_cli.github_api.list_repos", return_value=fake_repos) as mock_lr:
            with patch("agentkit_cli.commands.org_cmd._analyze_repo",
                       return_value={"score": 75.0, "grade": "C", "top_finding": "ok", "status": "ok"}):
                result = runner.invoke(app, ["org", "acme", "--limit", "5", "--json"])

        assert result.exit_code == 0
        _, kwargs = mock_lr.call_args
        assert kwargs.get("limit") == 5

    def test_cli_org_include_forks(self):
        with patch("agentkit_cli.github_api.list_repos", return_value=[]) as mock_lr:
            runner.invoke(app, ["org", "acme", "--include-forks", "--json"])
        _, kwargs = mock_lr.call_args
        assert kwargs.get("include_forks") is True

    def test_cli_org_include_archived(self):
        with patch("agentkit_cli.github_api.list_repos", return_value=[]) as mock_lr:
            runner.invoke(app, ["org", "acme", "--include-archived", "--json"])
        _, kwargs = mock_lr.call_args
        assert kwargs.get("include_archived") is True

    def test_integration_five_repos(self):
        """Integration test: mock full org run with 5 fake repos, verify ranked JSON."""
        fake_repos = [
            {"full_name": f"acme/repo{i}", "name": f"repo{i}", "stars": i * 10, "description": f"Repo {i}"}
            for i in range(5)
        ]
        scores = [85.0, 72.0, 91.0, 60.0, 45.0]

        def fake_analyze(full_name, timeout=120):
            idx = int(full_name.split("repo")[1])
            s = scores[idx]
            grade = "A" if s >= 90 else "B" if s >= 80 else "C" if s >= 70 else "D" if s >= 60 else "F"
            return {"score": s, "grade": grade, "top_finding": f"finding for repo{idx}", "status": "ok"}

        with patch("agentkit_cli.github_api.list_repos", return_value=fake_repos):
            with patch("agentkit_cli.commands.org_cmd._analyze_repo", side_effect=fake_analyze):
                result = runner.invoke(app, ["org", "acme", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["owner"] == "acme"
        assert data["repo_count"] == 5
        assert data["analyzed"] == 5
        ranked = data["ranked"]
        assert len(ranked) == 5
        # Verify sorted by score descending
        scores_out = [r["score"] for r in ranked]
        assert scores_out == sorted(scores_out, reverse=True)
        assert ranked[0]["rank"] == 1
        assert ranked[0]["score"] == 91.0  # repo2 is highest
