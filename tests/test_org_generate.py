"""Tests for agentkit org --generate feature (D4)."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch, call
from typing import Optional

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.commands.org_cmd import (
    OrgCommand,
    _analyze_repo,
    _generate_for_repo,
    _delta_color,
    _score_color,
    _score_to_grade,
)
from agentkit_cli.org_report import OrgReport

runner = CliRunner()

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

SAMPLE_REPOS_API = [
    {
        "full_name": "acme/alpha",
        "name": "alpha",
        "description": "Alpha repo",
        "stars": 200,
        "fork": False,
        "archived": False,
    },
    {
        "full_name": "acme/beta",
        "name": "beta",
        "description": "Beta repo",
        "stars": 50,
        "fork": False,
        "archived": False,
    },
]


def _make_before_result(score: float) -> dict:
    return {
        "score": score,
        "grade": _score_to_grade(score),
        "top_finding": "No CLAUDE.md found",
        "status": "ok",
    }


def _make_after_result(before_score: float, after_score: float) -> dict:
    delta = after_score - before_score
    return {
        "score": after_score,
        "grade": _score_to_grade(after_score),
        "top_finding": "Context generated",
        "status": "ok",
        "score_before": before_score,
        "score_after": after_score,
        "grade_before": _score_to_grade(before_score),
        "grade_after": _score_to_grade(after_score),
        "delta": delta,
        "generated": True,
    }


# ---------------------------------------------------------------------------
# D1: --generate flag wiring
# ---------------------------------------------------------------------------

class TestGenerateFlagWiring:
    """Tests that --generate is wired through to OrgCommand."""

    def test_org_command_accepts_generate_flag(self):
        cmd = OrgCommand(owner="acme", generate=True)
        assert cmd.generate is True

    def test_org_command_default_generate_false(self):
        cmd = OrgCommand(owner="acme")
        assert cmd.generate is False

    def test_org_command_generate_only_below_default(self):
        cmd = OrgCommand(owner="acme")
        assert cmd.generate_only_below == 80

    def test_org_command_generate_only_below_custom(self):
        cmd = OrgCommand(owner="acme", generate_only_below=60)
        assert cmd.generate_only_below == 60

    def test_cli_generate_flag_recognized(self):
        with patch("agentkit_cli.commands.org_cmd.OrgCommand") as mock_cls:
            mock_inst = MagicMock()
            mock_inst.run.return_value = {"owner": "acme", "repo_count": 0, "ranked": []}
            mock_cls.return_value = mock_inst
            with patch("agentkit_cli.github_api.list_repos", return_value=[]):
                result = runner.invoke(app, ["org", "acme", "--generate"])
            assert result.exit_code == 0

    def test_cli_generate_only_below_flag_recognized(self):
        with patch("agentkit_cli.commands.org_cmd.OrgCommand") as mock_cls:
            mock_inst = MagicMock()
            mock_inst.run.return_value = {"owner": "acme", "repo_count": 0, "ranked": []}
            mock_cls.return_value = mock_inst
            with patch("agentkit_cli.github_api.list_repos", return_value=[]):
                result = runner.invoke(app, ["org", "acme", "--generate", "--generate-only-below", "60"])
            assert result.exit_code == 0


# ---------------------------------------------------------------------------
# D1: _generate_for_repo logic
# ---------------------------------------------------------------------------

class TestGenerateForRepo:
    """Tests for _generate_for_repo function."""

    def test_skips_generation_when_above_threshold(self):
        """Repos at or above threshold should not be regenerated."""
        with patch("agentkit_cli.commands.org_cmd._analyze_repo") as mock_analyze:
            mock_analyze.return_value = {"score": 85.0, "grade": "B", "top_finding": "", "status": "ok"}
            result = _generate_for_repo("acme/alpha", timeout=30, generate_threshold=80)
        assert result["generated"] is False
        assert result["score_before"] == 85.0
        assert result["score_after"] == 85.0
        assert result["delta"] == 0.0

    def test_generates_when_below_threshold(self):
        """Repos below threshold should trigger generation."""
        with patch("agentkit_cli.commands.org_cmd._analyze_repo") as mock_analyze, \
             patch("agentkit_cli.analyze.parse_target") as mock_parse, \
             patch("agentkit_cli.analyze._clone") as mock_clone, \
             patch("agentkit_cli.tools.get_adapter") as mock_adapter, \
             patch("agentkit_cli.analyze.analyze_target") as mock_at, \
             patch("tempfile.mkdtemp", return_value="/tmp/test"), \
             patch("shutil.rmtree"):

            mock_analyze.return_value = {"score": 25.0, "grade": "F", "top_finding": "No context", "status": "ok"}
            mock_parse.return_value = ("https://github.com/acme/alpha.git", "alpha")
            mock_clone.return_value = None

            mock_ad = MagicMock()
            mock_ad.agentmd_generate.return_value = {"generated": True}
            mock_adapter.return_value = mock_ad

            after_result = MagicMock()
            after_result.composite_score = 88.0
            after_result.tools = {}
            mock_at.return_value = after_result

            result = _generate_for_repo("acme/alpha", timeout=30, generate_threshold=80)

        assert result["generated"] is True
        assert result["score_before"] == 25.0
        assert result["score_after"] == 88.0
        assert result["delta"] == pytest.approx(63.0)

    def test_delta_computed_correctly(self):
        """Delta should be after - before."""
        with patch("agentkit_cli.commands.org_cmd._analyze_repo") as mock_analyze, \
             patch("agentkit_cli.analyze.parse_target") as mock_parse, \
             patch("agentkit_cli.analyze._clone") as mock_clone, \
             patch("agentkit_cli.tools.get_adapter") as mock_adapter, \
             patch("agentkit_cli.analyze.analyze_target") as mock_at, \
             patch("tempfile.mkdtemp", return_value="/tmp/test"), \
             patch("shutil.rmtree"):

            mock_analyze.return_value = {"score": 40.0, "grade": "F", "top_finding": "", "status": "ok"}
            mock_parse.return_value = ("https://github.com/acme/alpha.git", "alpha")
            mock_clone.return_value = None
            mock_ad = MagicMock()
            mock_ad.agentmd_generate.return_value = {"ok": True}
            mock_adapter.return_value = mock_ad
            after_obj = MagicMock()
            after_obj.composite_score = 92.0
            after_obj.tools = {}
            mock_at.return_value = after_obj

            result = _generate_for_repo("acme/alpha", generate_threshold=80)

        assert result["delta"] == pytest.approx(52.0)

    def test_generate_failure_graceful(self):
        """When agentmd generate returns None, fall back to before score."""
        with patch("agentkit_cli.commands.org_cmd._analyze_repo") as mock_analyze, \
             patch("agentkit_cli.analyze.parse_target") as mock_parse, \
             patch("agentkit_cli.analyze._clone") as mock_clone, \
             patch("agentkit_cli.tools.get_adapter") as mock_adapter, \
             patch("tempfile.mkdtemp", return_value="/tmp/test"), \
             patch("shutil.rmtree"):

            mock_analyze.return_value = {"score": 30.0, "grade": "F", "top_finding": "missing", "status": "ok"}
            mock_parse.return_value = ("https://github.com/acme/alpha.git", "alpha")
            mock_clone.return_value = None
            mock_ad = MagicMock()
            mock_ad.agentmd_generate.return_value = None  # generate failed
            mock_adapter.return_value = mock_ad

            result = _generate_for_repo("acme/alpha", generate_threshold=80)

        assert result["generated"] is False
        assert result["score_before"] == 30.0
        assert result["score_after"] == 30.0

    def test_clone_failure_graceful(self):
        """Clone failure should return error dict without crashing."""
        with patch("agentkit_cli.commands.org_cmd._analyze_repo") as mock_analyze, \
             patch("agentkit_cli.analyze.parse_target") as mock_parse, \
             patch("agentkit_cli.analyze._clone") as mock_clone, \
             patch("tempfile.mkdtemp", return_value="/tmp/test"), \
             patch("shutil.rmtree"):

            mock_analyze.return_value = {"score": 20.0, "grade": "F", "top_finding": "", "status": "ok"}
            mock_parse.return_value = ("https://github.com/acme/alpha.git", "alpha")
            mock_clone.side_effect = RuntimeError("clone failed")

            result = _generate_for_repo("acme/alpha", generate_threshold=80)

        assert result["generated"] is False
        assert "generate_error" in result or result["score_before"] == 20.0


# ---------------------------------------------------------------------------
# D1: Before/after data structure
# ---------------------------------------------------------------------------

class TestBeforeAfterDataStructure:
    """Tests for the before/after result dict shape."""

    def test_result_has_score_before(self):
        r = _make_after_result(30.0, 85.0)
        assert "score_before" in r
        assert r["score_before"] == 30.0

    def test_result_has_score_after(self):
        r = _make_after_result(30.0, 85.0)
        assert "score_after" in r
        assert r["score_after"] == 85.0

    def test_result_has_delta(self):
        r = _make_after_result(30.0, 85.0)
        assert "delta" in r
        assert r["delta"] == pytest.approx(55.0)

    def test_result_has_grade_before_and_after(self):
        r = _make_after_result(30.0, 92.0)
        assert r["grade_before"] == "F"
        assert r["grade_after"] == "A"

    def test_result_generated_flag(self):
        r = _make_after_result(30.0, 85.0)
        assert r["generated"] is True


# ---------------------------------------------------------------------------
# D2: CLI table display
# ---------------------------------------------------------------------------

class TestBeforeAfterCliDisplay:
    """Tests for CLI table output in generate mode."""

    def _run_org_generate(self, ranked: list[dict]) -> str:
        with patch("agentkit_cli.github_api.list_repos", return_value=SAMPLE_REPOS_API), \
             patch("agentkit_cli.commands.org_cmd._generate_for_repo") as mock_gen:

            def side_effect(full_name, **kwargs):
                for r in ranked:
                    if r.get("full_name") == full_name:
                        return {k: v for k, v in r.items() if k not in ("rank",)}
                return {"score": None, "grade": None, "top_finding": "", "status": "error",
                        "score_before": None, "score_after": None, "grade_before": None,
                        "grade_after": None, "delta": None, "generated": False}

            mock_gen.side_effect = side_effect
            result = runner.invoke(app, ["org", "acme", "--generate"])
        return result.output

    def test_before_column_shown(self):
        ranked = [
            {"full_name": "acme/alpha", "name": "alpha", "score": 88.0, "score_before": 28.0,
             "score_after": 88.0, "grade_before": "F", "grade_after": "B", "delta": 60.0,
             "generated": True, "status": "ok", "top_finding": ""},
            {"full_name": "acme/beta", "name": "beta", "score": 30.0, "score_before": 30.0,
             "score_after": 30.0, "grade_before": "F", "grade_after": "F", "delta": 0.0,
             "generated": False, "status": "ok", "top_finding": ""},
        ]
        output = self._run_org_generate(ranked)
        assert "Before" in output

    def test_after_column_shown(self):
        ranked = [
            {"full_name": "acme/alpha", "name": "alpha", "score": 88.0, "score_before": 28.0,
             "score_after": 88.0, "grade_before": "F", "grade_after": "B", "delta": 60.0,
             "generated": True, "status": "ok", "top_finding": ""},
        ]
        output = self._run_org_generate(ranked)
        assert "After" in output

    def test_delta_column_shown(self):
        ranked = [
            {"full_name": "acme/alpha", "name": "alpha", "score": 88.0, "score_before": 28.0,
             "score_after": 88.0, "grade_before": "F", "grade_after": "B", "delta": 60.0,
             "generated": True, "status": "ok", "top_finding": ""},
        ]
        output = self._run_org_generate(ranked)
        assert "Delta" in output

    def test_summary_line_shown(self):
        ranked = [
            {"full_name": "acme/alpha", "name": "alpha", "score": 88.0, "score_before": 28.0,
             "score_after": 88.0, "grade_before": "F", "grade_after": "B", "delta": 60.0,
             "generated": True, "status": "ok", "top_finding": ""},
        ]
        output = self._run_org_generate(ranked)
        assert "Generated context" in output

    def test_avg_score_lift_in_summary(self):
        ranked = [
            {"full_name": "acme/alpha", "name": "alpha", "score": 90.0, "score_before": 30.0,
             "score_after": 90.0, "grade_before": "F", "grade_after": "A", "delta": 60.0,
             "generated": True, "status": "ok", "top_finding": ""},
        ]
        output = self._run_org_generate(ranked)
        assert "pts" in output

    def test_no_generate_shows_normal_table(self):
        with patch("agentkit_cli.github_api.list_repos", return_value=SAMPLE_REPOS_API), \
             patch("agentkit_cli.commands.org_cmd._analyze_repo") as mock_analyze:
            mock_analyze.return_value = {"score": 75.0, "grade": "C", "top_finding": "ok", "status": "ok"}
            result = runner.invoke(app, ["org", "acme"])
        assert "Score" in result.output
        assert "Grade" in result.output


# ---------------------------------------------------------------------------
# D2: Delta color coding
# ---------------------------------------------------------------------------

class TestDeltaColorCoding:
    """Tests for delta color logic."""

    def test_delta_green_when_ge_10(self):
        assert _delta_color(10.0) == "green"
        assert _delta_color(50.0) == "green"

    def test_delta_yellow_when_lt_10_and_positive(self):
        assert _delta_color(5.0) == "yellow"
        assert _delta_color(0.1) == "yellow"

    def test_delta_red_when_zero(self):
        assert _delta_color(0.0) == "red"

    def test_delta_red_when_negative(self):
        assert _delta_color(-5.0) == "red"

    def test_delta_dim_when_none(self):
        assert _delta_color(None) == "dim"


# ---------------------------------------------------------------------------
# D2: HTML report before/after columns
# ---------------------------------------------------------------------------

class TestOrgReportGenerateMode:
    """Tests for HTML report with generate_mode=True."""

    def _make_results_with_generate(self) -> list[dict]:
        return [
            {
                "rank": 1,
                "full_name": "acme/alpha",
                "repo": "alpha",
                "score": 90.0,
                "score_before": 28.0,
                "score_after": 90.0,
                "grade_before": "F",
                "grade_after": "A",
                "delta": 62.0,
                "generated": True,
                "status": "ok",
                "top_finding": "Context generated",
            },
            {
                "rank": 2,
                "full_name": "acme/beta",
                "repo": "beta",
                "score": 75.0,
                "score_before": 75.0,
                "score_after": 75.0,
                "grade_before": "C",
                "grade_after": "C",
                "delta": 0.0,
                "generated": False,
                "status": "ok",
                "top_finding": "",
            },
        ]

    def test_html_has_before_column_header(self):
        report = OrgReport(owner="acme", results=self._make_results_with_generate(), generate_mode=True)
        html = report.render()
        assert "<th>Before</th>" in html

    def test_html_has_after_column_header(self):
        report = OrgReport(owner="acme", results=self._make_results_with_generate(), generate_mode=True)
        html = report.render()
        assert "<th>After</th>" in html

    def test_html_has_delta_column_header(self):
        report = OrgReport(owner="acme", results=self._make_results_with_generate(), generate_mode=True)
        html = report.render()
        assert "<th>Delta</th>" in html

    def test_html_no_score_grade_columns_in_generate_mode(self):
        report = OrgReport(owner="acme", results=self._make_results_with_generate(), generate_mode=True)
        html = report.render()
        # In generate mode, the table header should not contain Score/Grade
        assert "<th>Score</th>" not in html

    def test_html_normal_mode_has_score_column(self):
        results = [
            {"rank": 1, "full_name": "acme/alpha", "repo": "alpha", "score": 75.0,
             "grade": "C", "status": "ok", "top_finding": "ok"},
        ]
        report = OrgReport(owner="acme", results=results, generate_mode=False)
        html = report.render()
        assert "<th>Score</th>" in html

    def test_html_delta_green_class_when_ge_10(self):
        report = OrgReport(owner="acme", results=self._make_results_with_generate(), generate_mode=True)
        html = report.render()
        assert "delta-green" in html

    def test_html_before_score_appears(self):
        report = OrgReport(owner="acme", results=self._make_results_with_generate(), generate_mode=True)
        html = report.render()
        assert "28.0" in html

    def test_html_after_score_appears(self):
        report = OrgReport(owner="acme", results=self._make_results_with_generate(), generate_mode=True)
        html = report.render()
        assert "90.0" in html

    def test_html_delta_value_appears(self):
        report = OrgReport(owner="acme", results=self._make_results_with_generate(), generate_mode=True)
        html = report.render()
        assert "62.0" in html

    def test_html_zero_delta_uses_red_or_na(self):
        results = [
            {"rank": 1, "full_name": "acme/beta", "repo": "beta", "score": 75.0,
             "score_before": 75.0, "score_after": 75.0, "grade_before": "C", "grade_after": "C",
             "delta": 0.0, "generated": False, "status": "ok", "top_finding": ""},
        ]
        report = OrgReport(owner="acme", results=results, generate_mode=True)
        html = report.render()
        assert "delta-red" in html or "delta-na" in html

    def test_html_null_delta_uses_na(self):
        results = [
            {"rank": 1, "full_name": "acme/gamma", "repo": "gamma", "score": None,
             "score_before": None, "score_after": None, "grade_before": None, "grade_after": None,
             "delta": None, "generated": False, "status": "error", "top_finding": ""},
        ]
        report = OrgReport(owner="acme", results=results, generate_mode=True)
        html = report.render()
        assert "delta-na" in html


# ---------------------------------------------------------------------------
# D1: generate_summary in JSON output
# ---------------------------------------------------------------------------

class TestGenerateSummaryJson:
    """Tests for JSON output when --generate is active."""

    def test_json_output_has_generate_summary(self):
        with patch("agentkit_cli.github_api.list_repos", return_value=SAMPLE_REPOS_API), \
             patch("agentkit_cli.commands.org_cmd._generate_for_repo") as mock_gen:

            mock_gen.return_value = {
                "score": 90.0, "grade": "A", "top_finding": "", "status": "ok",
                "score_before": 30.0, "score_after": 90.0, "grade_before": "F",
                "grade_after": "A", "delta": 60.0, "generated": True,
            }
            result = runner.invoke(app, ["org", "acme", "--generate", "--json"])

        data = json.loads(result.output)
        assert "generate_summary" in data
        assert "generated_count" in data["generate_summary"]
        assert "avg_score_lift" in data["generate_summary"]

    def test_json_generate_summary_counts_generated(self):
        with patch("agentkit_cli.github_api.list_repos", return_value=SAMPLE_REPOS_API[:1]), \
             patch("agentkit_cli.commands.org_cmd._generate_for_repo") as mock_gen:

            mock_gen.return_value = {
                "score": 90.0, "grade": "A", "top_finding": "", "status": "ok",
                "score_before": 30.0, "score_after": 90.0, "grade_before": "F",
                "grade_after": "A", "delta": 60.0, "generated": True,
            }
            result = runner.invoke(app, ["org", "acme", "--generate", "--json"])

        data = json.loads(result.output)
        assert data["generate_summary"]["generated_count"] == 1

    def test_json_no_generate_no_summary(self):
        with patch("agentkit_cli.github_api.list_repos", return_value=SAMPLE_REPOS_API[:1]), \
             patch("agentkit_cli.commands.org_cmd._analyze_repo") as mock_analyze:

            mock_analyze.return_value = {"score": 75.0, "grade": "C", "top_finding": "", "status": "ok"}
            result = runner.invoke(app, ["org", "acme", "--json"])

        data = json.loads(result.output)
        assert "generate_summary" not in data

    def test_json_ranked_repos_have_before_after_when_generate(self):
        with patch("agentkit_cli.github_api.list_repos", return_value=SAMPLE_REPOS_API[:1]), \
             patch("agentkit_cli.commands.org_cmd._generate_for_repo") as mock_gen:

            mock_gen.return_value = {
                "score": 88.0, "grade": "B", "top_finding": "", "status": "ok",
                "score_before": 25.0, "score_after": 88.0, "grade_before": "F",
                "grade_after": "B", "delta": 63.0, "generated": True,
            }
            result = runner.invoke(app, ["org", "acme", "--generate", "--json"])

        data = json.loads(result.output)
        assert len(data["ranked"]) > 0
        repo = data["ranked"][0]
        assert "score_before" in repo
        assert "score_after" in repo
        assert "delta" in repo

    def test_avg_lift_calculated_correctly(self):
        # Two repos: delta 60 and 40 => avg = 50
        repos = SAMPLE_REPOS_API[:2]
        with patch("agentkit_cli.github_api.list_repos", return_value=repos), \
             patch("agentkit_cli.commands.org_cmd._generate_for_repo") as mock_gen:

            deltas = [60.0, 40.0]
            call_count = [0]

            def side_effect(full_name, **kwargs):
                d = deltas[call_count[0] % len(deltas)]
                call_count[0] += 1
                return {"score": 80.0, "grade": "B", "top_finding": "", "status": "ok",
                        "score_before": 80.0 - d, "score_after": 80.0, "grade_before": "F",
                        "grade_after": "B", "delta": d, "generated": True}

            mock_gen.side_effect = side_effect
            result = runner.invoke(app, ["org", "acme", "--generate", "--json"])

        data = json.loads(result.output)
        assert data["generate_summary"]["avg_score_lift"] == pytest.approx(50.0, abs=0.1)


# ---------------------------------------------------------------------------
# D1: threshold enforcement
# ---------------------------------------------------------------------------

class TestThresholdEnforcement:
    """Tests for --generate-only-below threshold behavior."""

    def test_repos_at_threshold_not_generated(self):
        """Repos with score == threshold should not be generated."""
        with patch("agentkit_cli.commands.org_cmd._analyze_repo") as mock_analyze:
            mock_analyze.return_value = {"score": 80.0, "grade": "B", "top_finding": "", "status": "ok"}
            result = _generate_for_repo("acme/alpha", generate_threshold=80)
        assert result["generated"] is False

    def test_repos_just_below_threshold_generated(self):
        """Repos just below threshold should trigger generation."""
        with patch("agentkit_cli.commands.org_cmd._analyze_repo") as mock_analyze, \
             patch("agentkit_cli.analyze.parse_target") as mock_parse, \
             patch("agentkit_cli.analyze._clone") as mock_clone, \
             patch("agentkit_cli.tools.get_adapter") as mock_adapter, \
             patch("agentkit_cli.analyze.analyze_target") as mock_at, \
             patch("tempfile.mkdtemp", return_value="/tmp/test"), \
             patch("shutil.rmtree"):

            mock_analyze.return_value = {"score": 79.9, "grade": "C", "top_finding": "", "status": "ok"}
            mock_parse.return_value = ("https://github.com/acme/alpha.git", "alpha")
            mock_clone.return_value = None
            mock_ad = MagicMock()
            mock_ad.agentmd_generate.return_value = {"ok": True}
            mock_adapter.return_value = mock_ad
            after_obj = MagicMock()
            after_obj.composite_score = 90.0
            after_obj.tools = {}
            mock_at.return_value = after_obj

            result = _generate_for_repo("acme/alpha", generate_threshold=80)

        assert result["generated"] is True

    def test_custom_threshold_respected(self):
        """Custom threshold should override default 80."""
        with patch("agentkit_cli.commands.org_cmd._analyze_repo") as mock_analyze:
            # Score 65 is above custom threshold 60, should not generate
            mock_analyze.return_value = {"score": 65.0, "grade": "D", "top_finding": "", "status": "ok"}
            result = _generate_for_repo("acme/alpha", generate_threshold=60)
        assert result["generated"] is False


# ---------------------------------------------------------------------------
# D2: OrgReport generate_mode=True initialization
# ---------------------------------------------------------------------------

class TestOrgReportInit:
    """Tests for OrgReport generate_mode parameter."""

    def test_default_generate_mode_false(self):
        report = OrgReport(owner="acme", results=[])
        assert report.generate_mode is False

    def test_generate_mode_true_stored(self):
        report = OrgReport(owner="acme", results=[], generate_mode=True)
        assert report.generate_mode is True

    def test_generate_mode_false_renders_normal_report(self):
        results = [{"rank": 1, "full_name": "acme/alpha", "repo": "alpha",
                    "score": 75.0, "grade": "C", "status": "ok", "top_finding": ""}]
        report = OrgReport(owner="acme", results=results, generate_mode=False)
        html = report.render()
        assert "<th>Score</th>" in html
        assert "<th>Before</th>" not in html

    def test_generate_mode_true_renders_generate_report(self):
        results = [{"rank": 1, "full_name": "acme/alpha", "repo": "alpha",
                    "score": 90.0, "score_before": 28.0, "score_after": 90.0,
                    "grade_before": "F", "grade_after": "A", "delta": 62.0,
                    "generated": True, "status": "ok", "top_finding": ""}]
        report = OrgReport(owner="acme", results=results, generate_mode=True)
        html = report.render()
        assert "<th>Before</th>" in html
        assert "<th>Score</th>" not in html
