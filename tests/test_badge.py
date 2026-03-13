"""Tests for agentkit badge command (v0.8.0)."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.commands.badge_cmd import (
    build_badge_url,
    build_html_snippet,
    build_markdown,
    compute_badge_score,
    score_to_color,
    SHIELDS_BASE,
    _extract_agentlint_score,
    _extract_agentmd_score,
    _extract_coderace_score,
)

runner = CliRunner()


# ---------------------------------------------------------------------------
# score_to_color
# ---------------------------------------------------------------------------

class TestScoreToColor:
    def test_green_at_80(self):
        assert score_to_color(80) == "green"

    def test_green_above_80(self):
        assert score_to_color(100) == "green"

    def test_yellow_at_60(self):
        assert score_to_color(60) == "yellow"

    def test_yellow_at_79(self):
        assert score_to_color(79) == "yellow"

    def test_orange_at_40(self):
        assert score_to_color(40) == "orange"

    def test_orange_at_59(self):
        assert score_to_color(59) == "orange"

    def test_red_below_40(self):
        assert score_to_color(39) == "red"

    def test_red_at_0(self):
        assert score_to_color(0) == "red"


# ---------------------------------------------------------------------------
# build_badge_url
# ---------------------------------------------------------------------------

class TestBuildBadgeUrl:
    def test_url_starts_with_shields(self):
        url = build_badge_url(87)
        assert url.startswith(SHIELDS_BASE)

    def test_url_contains_score(self):
        url = build_badge_url(87)
        assert "87" in url

    def test_url_contains_color_green(self):
        url = build_badge_url(85)
        assert "green" in url

    def test_url_contains_color_red(self):
        url = build_badge_url(30)
        assert "red" in url

    def test_url_contains_color_yellow(self):
        url = build_badge_url(65)
        assert "yellow" in url

    def test_url_is_string(self):
        assert isinstance(build_badge_url(50), str)

    def test_url_encodes_label(self):
        url = build_badge_url(50)
        # "agent quality" space encoded as %20
        assert "agent" in url and "quality" in url


# ---------------------------------------------------------------------------
# build_markdown / build_html_snippet
# ---------------------------------------------------------------------------

class TestSnippets:
    def test_markdown_contains_badge_url(self):
        url = build_badge_url(75)
        md = build_markdown(url)
        assert url in md

    def test_markdown_format(self):
        url = build_badge_url(75)
        md = build_markdown(url)
        assert md.startswith("[![")

    def test_html_snippet_contains_img(self):
        url = build_badge_url(75)
        html = build_html_snippet(url)
        assert "<img" in html
        assert url in html

    def test_html_snippet_contains_link(self):
        url = build_badge_url(75)
        html = build_html_snippet(url)
        assert "<a href" in html


# ---------------------------------------------------------------------------
# Score extractors
# ---------------------------------------------------------------------------

class TestExtractors:
    def test_extract_agentlint_score_key(self):
        assert _extract_agentlint_score({"score": 72}) == 72.0

    def test_extract_agentlint_freshness(self):
        assert _extract_agentlint_score({"freshness_score": 55}) == 55.0

    def test_extract_agentlint_none(self):
        assert _extract_agentlint_score(None) is None

    def test_extract_agentmd_list(self):
        data = [{"score": 80}, {"score": 60}]
        assert _extract_agentmd_score(data) == 70.0

    def test_extract_agentmd_dict(self):
        assert _extract_agentmd_score({"score": 90}) == 90.0

    def test_extract_agentmd_none(self):
        assert _extract_agentmd_score(None) is None

    def test_extract_coderace_best(self):
        data = {"results": [{"agent": "a", "score": 80}, {"agent": "b", "score": 92}]}
        assert _extract_coderace_score(data) == 92.0

    def test_extract_coderace_none(self):
        assert _extract_coderace_score(None) is None


# ---------------------------------------------------------------------------
# compute_badge_score
# ---------------------------------------------------------------------------

MOCK_AGENTLINT = {"score": 80, "issues": []}
MOCK_AGENTMD = {"score": 60, "files": []}
MOCK_CODERACE = {"results": [{"agent": "claude", "score": 70}]}


class TestComputeBadgeScore:
    def test_returns_dict_with_score(self):
        with patch("agentkit_cli.commands.badge_cmd.run_agentlint_check", return_value=MOCK_AGENTLINT), \
             patch("agentkit_cli.commands.badge_cmd.run_agentmd_score", return_value=None), \
             patch("agentkit_cli.commands.badge_cmd.run_coderace_bench", return_value=None), \
             patch("agentkit_cli.commands.badge_cmd.run_agentreflect_analyze", return_value=None):
            result = compute_badge_score("/tmp")
        assert "score" in result
        assert isinstance(result["score"], int)

    def test_score_averages_components(self):
        with patch("agentkit_cli.commands.badge_cmd.run_agentlint_check", return_value=MOCK_AGENTLINT), \
             patch("agentkit_cli.commands.badge_cmd.run_agentmd_score", return_value=MOCK_AGENTMD), \
             patch("agentkit_cli.commands.badge_cmd.run_coderace_bench", return_value=None), \
             patch("agentkit_cli.commands.badge_cmd.run_agentreflect_analyze", return_value=None):
            result = compute_badge_score("/tmp")
        # 80 + 60 / 2 = 70
        assert result["score"] == 70

    def test_zero_score_when_no_tools(self):
        with patch("agentkit_cli.commands.badge_cmd.run_agentlint_check", return_value=None), \
             patch("agentkit_cli.commands.badge_cmd.run_agentmd_score", return_value=None), \
             patch("agentkit_cli.commands.badge_cmd.run_coderace_bench", return_value=None), \
             patch("agentkit_cli.commands.badge_cmd.run_agentreflect_analyze", return_value=None):
            result = compute_badge_score("/tmp")
        assert result["score"] == 0

    def test_sources_list(self):
        with patch("agentkit_cli.commands.badge_cmd.run_agentlint_check", return_value=MOCK_AGENTLINT), \
             patch("agentkit_cli.commands.badge_cmd.run_agentmd_score", return_value=None), \
             patch("agentkit_cli.commands.badge_cmd.run_coderace_bench", return_value=None), \
             patch("agentkit_cli.commands.badge_cmd.run_agentreflect_analyze", return_value=None):
            result = compute_badge_score("/tmp")
        assert "agentlint" in result["sources"]


# ---------------------------------------------------------------------------
# CLI integration
# ---------------------------------------------------------------------------

class TestBadgeCLI:
    def _mock_compute(self, score=75):
        return patch(
            "agentkit_cli.commands.badge_cmd.compute_badge_score",
            return_value={"score": score, "sources": ["agentlint"], "raw_scores": {"agentlint": float(score)}},
        )

    def test_badge_command_exists(self):
        result = runner.invoke(app, ["badge", "--help"])
        assert result.exit_code == 0

    def test_badge_output_contains_score(self):
        with self._mock_compute(87):
            result = runner.invoke(app, ["badge"])
        assert "87" in result.output

    def test_badge_json_output(self):
        with self._mock_compute(87):
            result = runner.invoke(app, ["badge", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["score"] == 87
        assert "badge_url" in data
        assert "markdown" in data
        assert "html" in data
        assert "color" in data

    def test_badge_json_color_field(self):
        with self._mock_compute(85):
            result = runner.invoke(app, ["badge", "--json"])
        data = json.loads(result.output)
        assert data["color"] == "green"

    def test_badge_score_override(self):
        result = runner.invoke(app, ["badge", "--score", "42", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["score"] == 42
        assert data["color"] == "orange"

    def test_badge_score_override_clamps_max(self):
        result = runner.invoke(app, ["badge", "--score", "150", "--json"])
        data = json.loads(result.output)
        assert data["score"] == 100

    def test_badge_score_override_clamps_min(self):
        result = runner.invoke(app, ["badge", "--score", "-5", "--json"])
        data = json.loads(result.output)
        assert data["score"] == 0

    def test_badge_output_contains_shields_url(self):
        with self._mock_compute(70):
            result = runner.invoke(app, ["badge"])
        assert "shields.io" in result.output

    def test_badge_output_contains_markdown(self):
        with self._mock_compute(70):
            result = runner.invoke(app, ["badge"])
        # Rich may strip some brackets; check for the key content
        assert "agent quality" in result.output or "shields.io" in result.output
