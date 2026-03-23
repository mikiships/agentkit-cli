"""D2 tests: WeeklyDigestRenderer — ≥8 tests."""
from __future__ import annotations

from agentkit_cli.weekly_digest_engine import DigestReport
from agentkit_cli.renderers.weekly_digest_renderer import render_html, render_markdown


def _make_report(total: int = 3, avg: float = 75.0, top: str = "best/repo") -> DigestReport:
    return DigestReport(
        top_repos=[
            {"repo": "owner/alpha", "score": 90.0, "grade": "A+"},
            {"repo": "owner/beta", "score": 70.0, "grade": "B"},
        ],
        week_stats={"total_analyses": total, "avg_score": avg, "top_scorer": top},
        generated_at="2026-03-22T10:00:00+00:00",
    )


class TestRenderHtml:
    def test_returns_string(self):
        report = _make_report()
        html = render_html(report)
        assert isinstance(html, str)

    def test_hero_header_present(self):
        report = _make_report()
        html = render_html(report)
        assert "State of AI Agent Readiness" in html

    def test_week_of_in_header(self):
        report = _make_report()
        html = render_html(report)
        assert "March" in html  # 2026-03-22

    def test_top_repos_in_table(self):
        report = _make_report()
        html = render_html(report)
        assert "owner/alpha" in html
        assert "owner/beta" in html

    def test_grade_badge_present(self):
        report = _make_report()
        html = render_html(report)
        assert "grade-badge" in html
        assert "A+" in html

    def test_stats_section_shows_total(self):
        report = _make_report(total=42)
        html = render_html(report)
        assert "42" in html

    def test_cta_pip_install(self):
        report = _make_report()
        html = render_html(report)
        assert "pip install agentkit-cli" in html

    def test_dark_theme_css_present(self):
        report = _make_report()
        html = render_html(report)
        assert "#0d1117" in html  # dark background color

    def test_html_structure(self):
        report = _make_report()
        html = render_html(report)
        assert "<!DOCTYPE html>" in html
        assert "</html>" in html


class TestRenderMarkdown:
    def test_returns_string(self):
        report = _make_report()
        md = render_markdown(report)
        assert isinstance(md, str)

    def test_header_present(self):
        report = _make_report()
        md = render_markdown(report)
        assert "State of AI Agent Readiness" in md

    def test_top_repos_table(self):
        report = _make_report()
        md = render_markdown(report)
        assert "owner/alpha" in md
        assert "|" in md

    def test_stats_in_markdown(self):
        report = _make_report(total=5, avg=80.0)
        md = render_markdown(report)
        assert "5" in md
        assert "80.0" in md

    def test_cta_in_markdown(self):
        report = _make_report()
        md = render_markdown(report)
        assert "pip install agentkit-cli" in md
