"""Tests for SpotlightHTMLRenderer (D3 — ≥10 tests)."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from agentkit_cli.commands.spotlight_cmd import SpotlightResult
from agentkit_cli.renderers.spotlight_renderer import SpotlightHTMLRenderer, _escape


def _make_result(**kwargs) -> SpotlightResult:
    defaults = dict(
        repo="acme/cool-agent",
        score=82.5,
        grade="B",
        top_findings=["[agentlint] Missing AGENTS.md", "[agentmd] Score: 75"],
        run_date=datetime.now(timezone.utc).isoformat(),
        repo_description="A cool agent repository",
        repo_stars=1200,
        repo_language="Python",
    )
    defaults.update(kwargs)
    return SpotlightResult(**defaults)


class TestSpotlightHTMLRenderer:
    def setup_method(self):
        self.renderer = SpotlightHTMLRenderer()

    def test_renders_valid_html(self):
        result = _make_result()
        html = self.renderer.render(result)
        assert "<!DOCTYPE html>" in html
        assert "<html" in html
        assert "</html>" in html

    def test_contains_repo_name(self):
        result = _make_result()
        html = self.renderer.render(result)
        assert "acme/cool-agent" in html

    def test_contains_score(self):
        result = _make_result(score=82.5)
        html = self.renderer.render(result)
        assert "82.5" in html

    def test_contains_grade_badge(self):
        result = _make_result(grade="B")
        html = self.renderer.render(result)
        assert ">B<" in html

    def test_contains_repo_description(self):
        result = _make_result()
        html = self.renderer.render(result)
        assert "A cool agent repository" in html

    def test_contains_star_count(self):
        result = _make_result(repo_stars=1200)
        html = self.renderer.render(result)
        assert "1,200" in html

    def test_contains_language(self):
        result = _make_result(repo_language="Python")
        html = self.renderer.render(result)
        assert "Python" in html

    def test_contains_findings(self):
        result = _make_result(top_findings=["[agentlint] Missing AGENTS.md"])
        html = self.renderer.render(result)
        assert "Missing AGENTS.md" in html

    def test_contains_version_footer(self):
        from agentkit_cli import __version__
        result = _make_result()
        html = self.renderer.render(result)
        assert __version__ in html
        assert "agentkit-cli" in html

    def test_no_external_css_deps(self):
        result = _make_result()
        html = self.renderer.render(result)
        # No external stylesheet links (link tags)
        import re
        assert not re.search(r'<link[^>]+rel=["\']stylesheet', html)

    def test_redteam_section_when_deep(self):
        result = _make_result(redteam_resistance=72.0)
        html = self.renderer.render(result)
        assert "RedTeam" in html
        assert "72.0" in html

    def test_no_redteam_section_without_deep(self):
        result = _make_result(redteam_resistance=None)
        html = self.renderer.render(result)
        assert "RedTeam" not in html

    def test_cert_box_when_cert_id(self):
        result = _make_result(cert_id="abcd1234")
        html = self.renderer.render(result)
        assert "CERT-abcd1234" in html
        assert "Certified" in html

    def test_no_cert_box_without_cert_id(self):
        result = _make_result(cert_id=None)
        html = self.renderer.render(result)
        assert "CERT-" not in html

    def test_grade_color_a(self):
        result = _make_result(grade="A", score=92.0)
        html = self.renderer.render(result)
        assert "#4caf50" in html  # green

    def test_grade_color_f(self):
        result = _make_result(grade="F", score=40.0)
        html = self.renderer.render(result)
        assert "#f44336" in html  # red

    def test_no_broken_template_vars(self):
        result = _make_result()
        html = self.renderer.render(result)
        assert "{" not in html or "%" in html  # CSS % is OK, template { is not
        # More precisely: no unresolved Python format vars
        import re
        # Look for {word} that aren't inside CSS (which uses { block syntax)
        assert not re.search(r'\{[a-z_]+\}', html)

    def test_escape_function(self):
        assert _escape("<script>") == "&lt;script&gt;"
        assert _escape("a&b") == "a&amp;b"
        assert _escape('"quoted"') == "&quot;quoted&quot;"

    def test_renders_without_optional_fields(self):
        result = SpotlightResult(
            repo="x/y",
            score=None,
            grade=None,
            top_findings=[],
            run_date="2026-01-01T00:00:00+00:00",
        )
        html = self.renderer.render(result)
        assert "<!DOCTYPE html>" in html
        assert "x/y" in html
