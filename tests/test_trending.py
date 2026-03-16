"""Tests for agentkit trending feature (D1, D2, D3)."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.trending import fetch_trending, fetch_popular, _date_cutoff, _normalize
from agentkit_cli.trending_report import generate_html

runner = CliRunner()

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_ITEMS = [
    {
        "full_name": "acme/cool-agent",
        "description": "A cool agent repo",
        "stargazers_count": 1500,
        "language": "Python",
        "html_url": "https://github.com/acme/cool-agent",
    },
    {
        "full_name": "beta/llm-toolkit",
        "description": "LLM toolkit",
        "stargazers_count": 800,
        "language": "TypeScript",
        "html_url": "https://github.com/beta/llm-toolkit",
    },
]

SAMPLE_API_RESPONSE = json.dumps({"items": SAMPLE_ITEMS, "total_count": 2}).encode()


# ---------------------------------------------------------------------------
# D1: trending.py unit tests
# ---------------------------------------------------------------------------

class TestDateCutoff:
    def test_returns_string(self):
        result = _date_cutoff(7)
        assert isinstance(result, str)
        assert len(result) == 10  # YYYY-MM-DD

    def test_day_is_shorter_than_week(self):
        day_cutoff = _date_cutoff(1)
        week_cutoff = _date_cutoff(7)
        assert week_cutoff < day_cutoff  # earlier date is lexicographically smaller


class TestNormalize:
    def test_basic(self):
        out = _normalize(SAMPLE_ITEMS)
        assert len(out) == 2
        assert out[0]["full_name"] == "acme/cool-agent"
        assert out[0]["stars"] == 1500
        assert out[0]["language"] == "Python"
        assert out[0]["url"] == "https://github.com/acme/cool-agent"

    def test_missing_fields_defaults(self):
        items = [{"full_name": "x/y"}]
        out = _normalize(items)
        assert out[0]["description"] == ""
        assert out[0]["stars"] == 0
        assert out[0]["language"] == ""


class TestFetchTrending:
    def _mock_urlopen(self):
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.read.return_value = SAMPLE_API_RESPONSE
        return ctx

    def test_returns_list_of_dicts(self):
        ctx = self._mock_urlopen()
        with patch("agentkit_cli.trending.urllib_request.urlopen", return_value=ctx):
            result = fetch_trending(period="week", limit=10)
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["full_name"] == "acme/cool-agent"

    def test_period_day(self):
        ctx = self._mock_urlopen()
        with patch("agentkit_cli.trending.urllib_request.urlopen", return_value=ctx) as mock_open:
            fetch_trending(period="day", limit=5)
        url_called = mock_open.call_args[0][0].full_url
        assert "created" in url_called

    def test_period_month(self):
        ctx = self._mock_urlopen()
        with patch("agentkit_cli.trending.urllib_request.urlopen", return_value=ctx):
            result = fetch_trending(period="month", limit=5)
        assert isinstance(result, list)

    def test_topic_filter(self):
        ctx = self._mock_urlopen()
        with patch("agentkit_cli.trending.urllib_request.urlopen", return_value=ctx) as mock_open:
            fetch_trending(period="week", topic="ai-agent", limit=5)
        url_called = mock_open.call_args[0][0].full_url
        assert "ai-agent" in url_called

    def test_limit_applied(self):
        big_response = json.dumps({"items": SAMPLE_ITEMS * 15}).encode()
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.read.return_value = big_response
        with patch("agentkit_cli.trending.urllib_request.urlopen", return_value=ctx):
            result = fetch_trending(period="week", limit=3)
        assert len(result) <= 3

    def test_invalid_period_raises(self):
        with pytest.raises(ValueError, match="period"):
            fetch_trending(period="decade")

    def test_rate_limit_returns_empty(self):
        from urllib import error as urllib_error
        with patch(
            "agentkit_cli.trending.urllib_request.urlopen",
            side_effect=urllib_error.HTTPError(None, 403, "Forbidden", {}, None),
        ):
            result = fetch_trending(period="week")
        assert result == []

    def test_network_error_returns_empty(self):
        from urllib import error as urllib_error
        with patch(
            "agentkit_cli.trending.urllib_request.urlopen",
            side_effect=urllib_error.URLError("connection refused"),
        ):
            result = fetch_trending(period="week")
        assert result == []

    def test_token_used_in_header(self):
        ctx = self._mock_urlopen()
        with patch("agentkit_cli.trending.urllib_request.urlopen", return_value=ctx) as mock_open:
            fetch_trending(period="week", token="mytoken123")
        req = mock_open.call_args[0][0]
        assert req.get_header("Authorization") == "Bearer mytoken123"

    def test_empty_results(self):
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.read.return_value = json.dumps({"items": []}).encode()
        with patch("agentkit_cli.trending.urllib_request.urlopen", return_value=ctx):
            result = fetch_trending(period="week")
        assert result == []


class TestFetchPopular:
    def _mock_urlopen(self):
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.read.return_value = SAMPLE_API_RESPONSE
        return ctx

    def test_ai_category(self):
        ctx = self._mock_urlopen()
        with patch("agentkit_cli.trending.urllib_request.urlopen", return_value=ctx):
            result = fetch_popular(category="ai", limit=5)
        assert isinstance(result, list)

    def test_python_category(self):
        ctx = self._mock_urlopen()
        with patch("agentkit_cli.trending.urllib_request.urlopen", return_value=ctx) as mock_open:
            fetch_popular(category="python", limit=5)
        url_called = mock_open.call_args[0][0].full_url
        assert "python" in url_called.lower()

    def test_all_category(self):
        ctx = self._mock_urlopen()
        with patch("agentkit_cli.trending.urllib_request.urlopen", return_value=ctx):
            result = fetch_popular(category="all", limit=5)
        assert isinstance(result, list)

    def test_invalid_category_raises(self):
        with pytest.raises(ValueError, match="category"):
            fetch_popular(category="fortran")

    def test_limit_applied(self):
        big = json.dumps({"items": SAMPLE_ITEMS * 20}).encode()
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.read.return_value = big
        with patch("agentkit_cli.trending.urllib_request.urlopen", return_value=ctx):
            result = fetch_popular(category="ai", limit=2)
        assert len(result) <= 2

    def test_rate_limit_returns_empty(self):
        from urllib import error as urllib_error
        with patch(
            "agentkit_cli.trending.urllib_request.urlopen",
            side_effect=urllib_error.HTTPError(None, 403, "Forbidden", {}, None),
        ):
            result = fetch_popular(category="ai")
        assert result == []


# ---------------------------------------------------------------------------
# D2: CLI command tests
# ---------------------------------------------------------------------------

MOCK_REPOS = [
    {
        "full_name": "acme/cool-agent",
        "description": "A cool agent",
        "stars": 1500,
        "language": "Python",
        "url": "https://github.com/acme/cool-agent",
    },
    {
        "full_name": "beta/llm-kit",
        "description": "LLM kit",
        "stars": 900,
        "language": "TypeScript",
        "url": "https://github.com/beta/llm-kit",
    },
]


class TestTrendingCLI:
    def test_no_analyze_table(self):
        with patch("agentkit_cli.commands.trending_cmd.fetch_trending", return_value=MOCK_REPOS), \
             patch("agentkit_cli.commands.trending_cmd.fetch_popular", return_value=[]):
            result = runner.invoke(app, ["trending", "--no-analyze", "--min-stars", "0"])
        assert result.exit_code == 0
        assert "acme/cool-agent" in result.output

    def test_no_analyze_json(self):
        with patch("agentkit_cli.commands.trending_cmd.fetch_trending", return_value=MOCK_REPOS), \
             patch("agentkit_cli.commands.trending_cmd.fetch_popular", return_value=[]):
            result = runner.invoke(app, ["trending", "--no-analyze", "--json", "--min-stars", "0"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "repos" in data
        assert isinstance(data["repos"], list)
        assert len(data["repos"]) > 0

    def test_json_schema(self):
        with patch("agentkit_cli.commands.trending_cmd.fetch_trending", return_value=MOCK_REPOS), \
             patch("agentkit_cli.commands.trending_cmd.fetch_popular", return_value=[]):
            result = runner.invoke(app, ["trending", "--no-analyze", "--json", "--min-stars", "0"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "period" in data
        assert "topic" in data
        repo = data["repos"][0]
        assert "rank" in repo
        assert "full_name" in repo
        assert "stars" in repo
        assert "score" in repo
        assert "grade" in repo
        assert "url" in repo

    def test_min_stars_filter(self):
        with patch("agentkit_cli.commands.trending_cmd.fetch_trending", return_value=MOCK_REPOS), \
             patch("agentkit_cli.commands.trending_cmd.fetch_popular", return_value=[]):
            result = runner.invoke(app, ["trending", "--no-analyze", "--json", "--min-stars", "1000"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        for r in data["repos"]:
            assert r["stars"] >= 1000

    def test_empty_after_filter(self):
        with patch("agentkit_cli.commands.trending_cmd.fetch_trending", return_value=MOCK_REPOS), \
             patch("agentkit_cli.commands.trending_cmd.fetch_popular", return_value=[]):
            result = runner.invoke(app, ["trending", "--no-analyze", "--min-stars", "999999"])
        assert result.exit_code == 0

    def test_limit_flag(self):
        with patch("agentkit_cli.commands.trending_cmd.fetch_trending", return_value=MOCK_REPOS), \
             patch("agentkit_cli.commands.trending_cmd.fetch_popular", return_value=[]):
            result = runner.invoke(app, ["trending", "--no-analyze", "--json", "--limit", "1", "--min-stars", "0"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data["repos"]) <= 1

    def test_period_flag(self):
        with patch("agentkit_cli.commands.trending_cmd.fetch_trending", return_value=MOCK_REPOS) as mock_fetch, \
             patch("agentkit_cli.commands.trending_cmd.fetch_popular", return_value=[]):
            result = runner.invoke(app, ["trending", "--no-analyze", "--period", "day", "--min-stars", "0"])
        assert result.exit_code == 0
        mock_fetch.assert_called_once()
        assert mock_fetch.call_args.kwargs.get("period") == "day" or mock_fetch.call_args[1].get("period") == "day" or "day" in str(mock_fetch.call_args)

    def test_topic_flag(self):
        with patch("agentkit_cli.commands.trending_cmd.fetch_trending", return_value=MOCK_REPOS) as mock_ft, \
             patch("agentkit_cli.commands.trending_cmd.fetch_popular", return_value=[]):
            result = runner.invoke(app, ["trending", "--no-analyze", "--topic", "ai-agent", "--min-stars", "0"])
        assert result.exit_code == 0

    def test_no_analyze_skips_scoring(self):
        with patch("agentkit_cli.commands.trending_cmd.fetch_trending", return_value=MOCK_REPOS), \
             patch("agentkit_cli.commands.trending_cmd.fetch_popular", return_value=[]), \
             patch("agentkit_cli.commands.trending_cmd._analyze_repo") as mock_analyze:
            runner.invoke(app, ["trending", "--no-analyze", "--min-stars", "0"])
        mock_analyze.assert_not_called()

    def test_analyze_called_when_not_skipped(self):
        mock_score = {"score": 75.0, "grade": "C"}
        with patch("agentkit_cli.commands.trending_cmd.fetch_trending", return_value=MOCK_REPOS[:1]), \
             patch("agentkit_cli.commands.trending_cmd.fetch_popular", return_value=[]), \
             patch("agentkit_cli.commands.trending_cmd._analyze_repo", return_value=mock_score) as mock_analyze:
            result = runner.invoke(app, ["trending", "--min-stars", "0"])
        assert result.exit_code == 0
        mock_analyze.assert_called()

    def test_share_flag_calls_publish(self):
        mock_score = {"score": 80.0, "grade": "B"}
        with patch("agentkit_cli.commands.trending_cmd.fetch_trending", return_value=MOCK_REPOS), \
             patch("agentkit_cli.commands.trending_cmd.fetch_popular", return_value=[]), \
             patch("agentkit_cli.commands.trending_cmd._analyze_repo", return_value=mock_score), \
             patch("agentkit_cli.trending_report.publish_report", return_value="https://here.now/abc") as mock_pub:
            result = runner.invoke(app, ["trending", "--share", "--min-stars", "0"])
        assert result.exit_code == 0
        mock_pub.assert_called_once()

    def test_share_fallback_on_publish_error(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        mock_score = {"score": 80.0, "grade": "B"}
        from agentkit_cli.publish import PublishError
        with patch("agentkit_cli.commands.trending_cmd.fetch_trending", return_value=MOCK_REPOS), \
             patch("agentkit_cli.commands.trending_cmd.fetch_popular", return_value=[]), \
             patch("agentkit_cli.commands.trending_cmd._analyze_repo", return_value=mock_score), \
             patch("agentkit_cli.trending_report.publish_report", side_effect=PublishError("server down")):
            result = runner.invoke(app, ["trending", "--share", "--min-stars", "0"])
        assert result.exit_code == 0
        assert (tmp_path / "trending-report.html").exists()

    def test_command_registered(self):
        result = runner.invoke(app, ["trending", "--help"])
        assert result.exit_code == 0
        assert "trending" in result.output.lower()


# ---------------------------------------------------------------------------
# D3: HTML report generation tests
# ---------------------------------------------------------------------------

SAMPLE_RESULTS = [
    {"rank": 1, "full_name": "acme/cool-agent", "stars": 1500, "score": 85.0, "grade": "B", "url": "https://github.com/acme/cool-agent"},
    {"rank": 2, "full_name": "beta/llm-kit", "stars": 900, "score": 62.0, "grade": "D", "url": "https://github.com/beta/llm-kit"},
    {"rank": 3, "full_name": "gamma/no-score", "stars": 500, "score": None, "grade": None, "url": "https://github.com/gamma/no-score"},
]


class TestGenerateHtml:
    def test_returns_string(self):
        html = generate_html(SAMPLE_RESULTS)
        assert isinstance(html, str)

    def test_contains_title(self):
        html = generate_html(SAMPLE_RESULTS)
        assert "Trending Repos" in html
        assert "Agent Quality Rankings" in html

    def test_contains_repo_names(self):
        html = generate_html(SAMPLE_RESULTS)
        assert "acme/cool-agent" in html
        assert "beta/llm-kit" in html

    def test_contains_links(self):
        html = generate_html(SAMPLE_RESULTS)
        assert "https://github.com/acme/cool-agent" in html

    def test_contains_stars(self):
        html = generate_html(SAMPLE_RESULTS)
        assert "1,500" in html or "1500" in html

    def test_contains_version(self):
        from agentkit_cli import __version__
        html = generate_html(SAMPLE_RESULTS)
        assert __version__ in html

    def test_contains_pip_install(self):
        html = generate_html(SAMPLE_RESULTS)
        assert "pip install agentkit-cli" in html

    def test_dark_theme_background(self):
        html = generate_html(SAMPLE_RESULTS)
        assert "#0d1117" in html

    def test_accent_color(self):
        html = generate_html(SAMPLE_RESULTS)
        assert "#58a6ff" in html

    def test_handles_no_score(self):
        results = [{"rank": 1, "full_name": "x/y", "stars": 100, "score": None, "grade": None, "url": "https://github.com/x/y"}]
        html = generate_html(results)
        assert "N/A" in html

    def test_summary_card_shows_count(self):
        html = generate_html(SAMPLE_RESULTS)
        assert str(len(SAMPLE_RESULTS)) in html

    def test_empty_results(self):
        html = generate_html([])
        assert isinstance(html, str)
        assert "<!DOCTYPE html>" in html

    def test_valid_html_structure(self):
        html = generate_html(SAMPLE_RESULTS)
        assert "<!DOCTYPE html>" in html
        assert "<html" in html
        assert "</html>" in html
        assert "<table" in html
        assert "</table>" in html


# ---------------------------------------------------------------------------
# Integration: --no-analyze end-to-end with mocked GitHub response
# ---------------------------------------------------------------------------

class TestNoAnalyzeEndToEnd:
    def test_end_to_end_no_analyze(self):
        repos = [
            {"full_name": "x/a", "description": "A", "stars": 200, "language": "Go", "url": "https://github.com/x/a"},
            {"full_name": "y/b", "description": "B", "stars": 150, "language": "Rust", "url": "https://github.com/y/b"},
        ]
        with patch("agentkit_cli.commands.trending_cmd.fetch_trending", return_value=repos), \
             patch("agentkit_cli.commands.trending_cmd.fetch_popular", return_value=[]):
            result = runner.invoke(app, ["trending", "--no-analyze", "--json", "--min-stars", "0"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data["repos"]) == 2
        for r in data["repos"]:
            assert r["score"] is None

    def test_single_repo(self):
        repos = [{"full_name": "solo/repo", "description": "", "stars": 500, "language": "Python", "url": "https://github.com/solo/repo"}]
        with patch("agentkit_cli.commands.trending_cmd.fetch_trending", return_value=repos), \
             patch("agentkit_cli.commands.trending_cmd.fetch_popular", return_value=[]):
            result = runner.invoke(app, ["trending", "--no-analyze", "--json", "--min-stars", "0"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data["repos"]) == 1

    def test_stars_below_min_filtered(self):
        repos = [{"full_name": "x/y", "description": "", "stars": 50, "language": "Python", "url": "https://github.com/x/y"}]
        with patch("agentkit_cli.commands.trending_cmd.fetch_trending", return_value=repos), \
             patch("agentkit_cli.commands.trending_cmd.fetch_popular", return_value=[]):
            result = runner.invoke(app, ["trending", "--no-analyze", "--min-stars", "100"])
        assert result.exit_code == 0
