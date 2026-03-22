"""D3 tests for framework_templates and --generate flag."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from agentkit_cli.framework_templates import get_template, list_templates
from agentkit_cli.frameworks import DetectedFramework, FrameworkCoverage
from agentkit_cli.main import app

runner = CliRunner()


def write_file(root: Path, name: str, content: str) -> Path:
    p = root / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return p


# ---------------------------------------------------------------------------
# Template content tests
# ---------------------------------------------------------------------------

class TestFrameworkTemplates:
    def test_all_10_frameworks_have_templates(self):
        expected = [
            "Next.js", "FastAPI", "Django", "Rails", "React",
            "Vue", "Nuxt", "Flask", "Laravel", "Express",
        ]
        templates = list_templates()
        for fw in expected:
            assert fw in templates, f"Missing template for {fw}"

    def test_template_has_setup_section(self):
        for fw in list_templates():
            tmpl = get_template(fw)
            assert "setup" in tmpl.lower(), f"{fw} template missing setup section"

    def test_template_has_common_patterns_section(self):
        for fw in list_templates():
            tmpl = get_template(fw)
            assert "common patterns" in tmpl.lower(), f"{fw} missing common patterns"

    def test_template_has_known_gotchas_section(self):
        for fw in list_templates():
            tmpl = get_template(fw)
            assert "known gotchas" in tmpl.lower(), f"{fw} missing known gotchas"

    def test_template_has_framework_name_in_heading(self):
        for fw in list_templates():
            tmpl = get_template(fw)
            assert f"## {fw}" in tmpl, f"{fw} template missing ## heading"

    def test_get_template_returns_none_for_unknown(self):
        assert get_template("UnknownFramework") is None

    def test_template_is_string(self):
        tmpl = get_template("Next.js")
        assert isinstance(tmpl, str)
        assert len(tmpl) > 10


# ---------------------------------------------------------------------------
# --generate flag tests
# ---------------------------------------------------------------------------

class TestGenerateFlag:
    def test_generate_creates_sections_in_context_file(self, tmp_path):
        write_file(tmp_path, "requirements.txt", "fastapi>=0.100\n")
        ctx = tmp_path / "CLAUDE.md"
        ctx.write_text("# My Project\n")
        result = runner.invoke(app, ["frameworks", str(tmp_path), "--generate", "--context-file", str(ctx)])
        assert result.exit_code == 0
        content = ctx.read_text()
        assert "## FastAPI" in content

    def test_generate_is_idempotent(self, tmp_path):
        write_file(tmp_path, "requirements.txt", "flask>=3.0\n")
        ctx = tmp_path / "CLAUDE.md"
        ctx.write_text("# My Project\n\n## Flask Notes\nSetup.\nCommon patterns.\nKnown gotchas.\n")
        runner.invoke(app, ["frameworks", str(tmp_path), "--generate", "--context-file", str(ctx)])
        content_after_first = ctx.read_text()
        runner.invoke(app, ["frameworks", str(tmp_path), "--generate", "--context-file", str(ctx)])
        content_after_second = ctx.read_text()
        assert content_after_first == content_after_second

    def test_generate_skips_high_score_frameworks(self, tmp_path):
        # Flask has full coverage, so --generate should not add a new section
        write_file(tmp_path, "requirements.txt", "flask>=3.0\n")
        ctx = tmp_path / "CLAUDE.md"
        full_content = "# Proj\n## Flask Notes\nSetup.\nCommon patterns.\nKnown gotchas.\nTesting patterns.\nDeploy patterns.\n"
        ctx.write_text(full_content)
        runner.invoke(app, ["frameworks", str(tmp_path), "--generate", "--context-file", str(ctx)])
        # Content should be unchanged (no new sections needed)
        assert ctx.read_text() == full_content

    def test_generate_appends_not_prepends(self, tmp_path):
        write_file(tmp_path, "requirements.txt", "django>=4.2\n")
        ctx = tmp_path / "CLAUDE.md"
        ctx.write_text("# My Project\n\nOriginal content here.\n")
        runner.invoke(app, ["frameworks", str(tmp_path), "--generate", "--context-file", str(ctx)])
        content = ctx.read_text()
        orig_idx = content.index("Original content here")
        django_idx = content.index("## Django")
        assert django_idx > orig_idx

    def test_generate_no_context_file_warns(self, tmp_path):
        write_file(tmp_path, "requirements.txt", "flask>=3.0\n")
        # No CLAUDE.md or AGENTS.md
        result = runner.invoke(app, ["frameworks", str(tmp_path), "--generate"])
        assert result.exit_code == 0
        assert "Warning" in result.output or "no context file" in result.output.lower()

    def test_generate_multiple_frameworks(self, tmp_path):
        write_file(tmp_path, "requirements.txt", "fastapi>=0.100\nflask>=3.0\n")
        ctx = tmp_path / "CLAUDE.md"
        ctx.write_text("# My Project\n")
        runner.invoke(app, ["frameworks", str(tmp_path), "--generate", "--context-file", str(ctx)])
        content = ctx.read_text()
        assert "## FastAPI" in content
        assert "## Flask" in content

    def test_generate_template_min_score_respected(self, tmp_path):
        # With --min-score 0, nothing should be generated (since 0 is not < 0)
        write_file(tmp_path, "requirements.txt", "flask>=3.0\n")
        ctx = tmp_path / "CLAUDE.md"
        ctx.write_text("# My Project\n")
        runner.invoke(app, [
            "frameworks", str(tmp_path), "--generate",
            "--context-file", str(ctx), "--min-score", "0",
        ])
        content = ctx.read_text()
        # Nothing should be generated since score 0 is not < 0
        assert "## Flask" not in content


# ---------------------------------------------------------------------------
# Append logic and idempotency
# ---------------------------------------------------------------------------

class TestAppendLogic:
    def test_existing_heading_skipped(self, tmp_path):
        write_file(tmp_path, "requirements.txt", "fastapi>=0.100\n")
        ctx = tmp_path / "CLAUDE.md"
        ctx.write_text("# Proj\n\n## FastAPI Notes\n\nSome existing content.\n")
        runner.invoke(app, ["frameworks", str(tmp_path), "--generate", "--context-file", str(ctx)])
        content = ctx.read_text()
        # Should only have one ## FastAPI occurrence
        assert content.count("## FastAPI") == 1

    def test_template_added_for_below_threshold(self, tmp_path):
        write_file(tmp_path, "requirements.txt", "django>=4.2\n")
        ctx = tmp_path / "CLAUDE.md"
        ctx.write_text("# Proj\n")
        runner.invoke(app, ["frameworks", str(tmp_path), "--generate", "--context-file", str(ctx)])
        assert "## Django" in ctx.read_text()

    def test_generate_respects_agents_md(self, tmp_path):
        write_file(tmp_path, "Gemfile", "gem 'rails', '~> 7.1'\n")
        ctx = tmp_path / "AGENTS.md"
        ctx.write_text("# Proj\n")
        runner.invoke(app, ["frameworks", str(tmp_path), "--generate", "--context-file", str(ctx)])
        assert "## Rails" in ctx.read_text()
