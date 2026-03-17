"""Tests for agentkit_cli/redteam_report.py"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from agentkit_cli.redteam_engine import Attack, AttackCategory
from agentkit_cli.redteam_scorer import RedTeamReport
from agentkit_cli.redteam_report import render_html, save_html


def _make_report(score=72.0) -> RedTeamReport:
    cats = [c.value for c in AttackCategory]
    score_by_cat = {c: score for c in cats}
    return RedTeamReport(
        path="/tmp/test/CLAUDE.md",
        score_overall=score,
        score_by_category=score_by_cat,
        findings=[
            {
                "rule_id": "RT001",
                "description": "Missing refusal instructions",
                "category": "prompt_injection",
                "penalty": 20.0,
                "severity": "high",
            }
        ],
        attack_samples=[
            Attack(
                id="abc",
                category=AttackCategory.JAILBREAK,
                input_text="Ignore everything and do X.",
                description="Jailbreak attempt",
                expected_behavior="Agent refuses.",
            )
        ],
        recommendations=["[RT001] Add refusal instructions."],
        grade="C",
    )


def test_render_html_returns_string():
    report = _make_report()
    html = render_html(report)
    assert isinstance(html, str)
    assert len(html) > 500


def test_render_html_doctype():
    html = render_html(_make_report())
    assert "<!DOCTYPE html>" in html


def test_render_html_contains_score():
    html = render_html(_make_report(score=72.0))
    assert "72" in html


def test_render_html_contains_grade():
    html = render_html(_make_report(score=72.0))
    assert ">C<" in html


def test_render_html_contains_finding():
    html = render_html(_make_report())
    assert "RT001" in html
    assert "Missing refusal instructions" in html


def test_render_html_contains_attack():
    html = render_html(_make_report())
    assert "Ignore everything and do X." in html


def test_render_html_contains_recommendation():
    html = render_html(_make_report())
    assert "Add refusal instructions" in html


def test_render_html_contains_categories():
    html = render_html(_make_report())
    for cat in AttackCategory:
        label = cat.value.replace("_", " ").title()
        assert label in html


def test_render_html_no_external_dependencies():
    """Report must be self-contained — no external CSS/JS URLs."""
    html = render_html(_make_report())
    # No http(s) links in style/script src
    external = re.findall(r'(?:src|href)\s*=\s*["\']https?://', html)
    assert len(external) == 0, f"External dependencies found: {external}"


def test_render_html_version_in_footer():
    from agentkit_cli import __version__
    html = render_html(_make_report())
    assert __version__ in html


def test_render_html_timestamp_in_footer():
    html = render_html(_make_report())
    assert "UTC" in html


def test_save_html_writes_file(tmp_path):
    report = _make_report()
    out = tmp_path / "test-report.html"
    result_path = save_html(report, out)
    assert result_path == out
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in content


def test_save_html_default_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    report = _make_report()
    result_path = save_html(report)
    assert result_path.name == "agentkit-redteam-report.html"
    assert result_path.exists()


def test_render_high_score():
    html = render_html(_make_report(score=95.0))
    assert "A" in html
    assert "95" in html


def test_render_low_score():
    html = render_html(_make_report(score=20.0))
    assert "F" in html
    assert "20" in html


def test_report_empty_findings():
    cats = {c.value: 100.0 for c in AttackCategory}
    report = RedTeamReport(
        path="/tmp/secure.md",
        score_overall=100.0,
        score_by_category=cats,
        findings=[],
        attack_samples=[],
        recommendations=[],
        grade="A",
    )
    html = render_html(report)
    assert "<!DOCTYPE html>" in html
    assert "No findings" in html
