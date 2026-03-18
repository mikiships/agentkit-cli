"""Tests for agentkit_cli.checks_formatter."""
from __future__ import annotations

import pytest

from agentkit_cli.checks_formatter import (
    _build_annotations,
    _build_tool_table,
    _score_status,
    format_check_output,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sample_components() -> dict:
    return {
        "agentmd": {"raw_score": 90.0, "weight": 0.25, "contribution": 22.5},
        "agentlint": {"raw_score": 75.0, "weight": 0.25, "contribution": 18.75},
        "coderace": {"raw_score": 50.0, "weight": 0.30, "contribution": 15.0},
        "agentreflect": {"raw_score": 85.0, "weight": 0.20, "contribution": 17.0},
    }


def _sample_result(score: float = 73.0, grade: str = "C") -> dict:
    return {
        "score": score,
        "grade": grade,
        "components": _sample_components(),
    }


# ---------------------------------------------------------------------------
# _score_status
# ---------------------------------------------------------------------------

class TestScoreStatus:
    def test_pass(self):
        assert _score_status(80) == "pass"
        assert _score_status(100) == "pass"

    def test_warn(self):
        assert _score_status(60) == "warn"
        assert _score_status(79) == "warn"

    def test_fail(self):
        assert _score_status(0) == "fail"
        assert _score_status(59) == "fail"


# ---------------------------------------------------------------------------
# _build_tool_table
# ---------------------------------------------------------------------------

class TestBuildToolTable:
    def test_markdown_header(self):
        table = _build_tool_table(_sample_components())
        assert "| Tool |" in table
        assert "|------|" in table

    def test_all_tools_present(self):
        table = _build_tool_table(_sample_components())
        for tool in ("agentmd", "agentlint", "coderace", "agentreflect"):
            assert tool in table

    def test_empty_components(self):
        table = _build_tool_table({})
        assert "| Tool |" in table  # header still present


# ---------------------------------------------------------------------------
# _build_annotations
# ---------------------------------------------------------------------------

class TestBuildAnnotations:
    def test_annotates_failing_tools(self):
        annotations = _build_annotations(_sample_components())
        tools_annotated = {a["title"].split(":")[0] for a in annotations}
        # agentlint (75) and coderace (50) are below 80
        assert "agentlint" in tools_annotated
        assert "coderace" in tools_annotated

    def test_does_not_annotate_passing_tools(self):
        annotations = _build_annotations(_sample_components())
        tools_annotated = {a["title"].split(":")[0] for a in annotations}
        assert "agentmd" not in tools_annotated
        assert "agentreflect" not in tools_annotated

    def test_failure_level_below_60(self):
        annotations = _build_annotations(_sample_components())
        coderace_ann = [a for a in annotations if "coderace" in a["title"]][0]
        assert coderace_ann["annotation_level"] == "failure"

    def test_warning_level_60_to_80(self):
        annotations = _build_annotations(_sample_components())
        lint_ann = [a for a in annotations if "agentlint" in a["title"]][0]
        assert lint_ann["annotation_level"] == "warning"

    def test_max_50_annotations(self):
        many = {f"tool_{i}": {"raw_score": 10.0, "weight": 0.01} for i in range(100)}
        annotations = _build_annotations(many)
        assert len(annotations) <= 50

    def test_empty_components_no_annotations(self):
        assert _build_annotations({}) == []


# ---------------------------------------------------------------------------
# format_check_output
# ---------------------------------------------------------------------------

class TestFormatCheckOutput:
    def test_returns_required_keys(self):
        out = format_check_output(_sample_result())
        assert "title" in out
        assert "summary" in out
        assert "text" in out
        assert "annotations" in out

    def test_title_contains_score_and_grade(self):
        out = format_check_output(_sample_result(87, "B"))
        assert "87" in out["title"]
        assert "B" in out["title"]

    def test_summary_contains_score(self):
        out = format_check_output(_sample_result(92, "A"))
        assert "92" in out["summary"]

    def test_gate_pass_in_summary(self):
        out = format_check_output(
            _sample_result(),
            gate_result={"passed": True, "failure_reasons": []},
        )
        assert "PASS" in out["summary"]

    def test_gate_fail_with_reasons(self):
        out = format_check_output(
            _sample_result(),
            gate_result={"passed": False, "failure_reasons": ["score too low"]},
        )
        assert "FAIL" in out["summary"]
        assert "score too low" in out["summary"]

    def test_share_url_in_summary(self):
        out = format_check_output(
            _sample_result(),
            share_url="https://example.com/card",
        )
        assert "https://example.com/card" in out["summary"]

    def test_text_has_tool_table(self):
        out = format_check_output(_sample_result())
        assert "agentmd" in out["text"]
        assert "| Tool |" in out["text"]

    def test_missing_components(self):
        out = format_check_output({"score": 50, "grade": "D"})
        assert out["annotations"] == []
        assert "No per-tool breakdown" in out["text"]

    def test_grade_computed_when_missing(self):
        out = format_check_output({"score": 95, "components": {}})
        assert "A" in out["title"]
