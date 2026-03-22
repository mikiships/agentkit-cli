"""D1 tests for FrameworkDetector and FrameworkChecker."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentkit_cli.frameworks import (
    DetectedFramework,
    FrameworkChecker,
    FrameworkDetector,
    FrameworkCoverage,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def write_file(root: Path, name: str, content: str) -> Path:
    p = root / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return p


# ---------------------------------------------------------------------------
# FrameworkDetector tests
# ---------------------------------------------------------------------------

class TestFrameworkDetectorNextJs:
    def test_next_config_js(self, tmp_path):
        write_file(tmp_path, "next.config.js", "module.exports = {}")
        result = FrameworkDetector().detect(tmp_path)
        names = [f.name for f in result]
        assert "Next.js" in names

    def test_next_config_ts(self, tmp_path):
        write_file(tmp_path, "next.config.ts", "export default {}")
        result = FrameworkDetector().detect(tmp_path)
        assert any(f.name == "Next.js" for f in result)

    def test_package_json_next_dep(self, tmp_path):
        pkg = {"dependencies": {"next": "^14.0.0", "react": "^18.0.0"}}
        write_file(tmp_path, "package.json", json.dumps(pkg))
        result = FrameworkDetector().detect(tmp_path)
        names = [f.name for f in result]
        assert "Next.js" in names
        # React should NOT appear separately when Next.js is detected
        assert "React" not in names

    def test_confidence_high_with_config_and_dep(self, tmp_path):
        write_file(tmp_path, "next.config.js", "module.exports = {}")
        pkg = {"dependencies": {"next": "^14.0.0"}}
        write_file(tmp_path, "package.json", json.dumps(pkg))
        result = FrameworkDetector().detect(tmp_path)
        nxt = next(f for f in result if f.name == "Next.js")
        assert nxt.confidence == "high"


class TestFrameworkDetectorPython:
    def test_fastapi_requirements(self, tmp_path):
        write_file(tmp_path, "requirements.txt", "fastapi>=0.100\nuvicorn\n")
        result = FrameworkDetector().detect(tmp_path)
        assert any(f.name == "FastAPI" for f in result)

    def test_django_manage_py(self, tmp_path):
        write_file(tmp_path, "manage.py", "#!/usr/bin/env python\n")
        result = FrameworkDetector().detect(tmp_path)
        assert any(f.name == "Django" for f in result)

    def test_django_requirements(self, tmp_path):
        write_file(tmp_path, "requirements.txt", "Django>=4.2\n")
        result = FrameworkDetector().detect(tmp_path)
        assert any(f.name == "Django" for f in result)

    def test_flask_requirements(self, tmp_path):
        write_file(tmp_path, "requirements.txt", "flask>=3.0\n")
        result = FrameworkDetector().detect(tmp_path)
        assert any(f.name == "Flask" for f in result)

    def test_fastapi_pyproject(self, tmp_path):
        write_file(tmp_path, "pyproject.toml", '[project]\ndependencies = ["fastapi>=0.100"]\n')
        result = FrameworkDetector().detect(tmp_path)
        assert any(f.name == "FastAPI" for f in result)


class TestFrameworkDetectorOther:
    def test_rails_gemfile(self, tmp_path):
        write_file(tmp_path, "Gemfile", "gem 'rails', '~> 7.1'\n")
        result = FrameworkDetector().detect(tmp_path)
        assert any(f.name == "Rails" for f in result)

    def test_express_package_json(self, tmp_path):
        pkg = {"dependencies": {"express": "^4.18.0"}}
        write_file(tmp_path, "package.json", json.dumps(pkg))
        result = FrameworkDetector().detect(tmp_path)
        assert any(f.name == "Express" for f in result)

    def test_vue_package_json(self, tmp_path):
        pkg = {"dependencies": {"vue": "^3.0.0"}}
        write_file(tmp_path, "package.json", json.dumps(pkg))
        result = FrameworkDetector().detect(tmp_path)
        assert any(f.name == "Vue" for f in result)

    def test_nuxt_config(self, tmp_path):
        write_file(tmp_path, "nuxt.config.ts", "export default defineNuxtConfig({})")
        result = FrameworkDetector().detect(tmp_path)
        assert any(f.name == "Nuxt" for f in result)

    def test_laravel_composer(self, tmp_path):
        composer = {"require": {"laravel/framework": "^10.0"}}
        write_file(tmp_path, "composer.json", json.dumps(composer))
        result = FrameworkDetector().detect(tmp_path)
        assert any(f.name == "Laravel" for f in result)

    def test_empty_project_no_frameworks(self, tmp_path):
        result = FrameworkDetector().detect(tmp_path)
        assert result == []

    def test_detection_files_populated(self, tmp_path):
        write_file(tmp_path, "next.config.js", "module.exports = {}")
        result = FrameworkDetector().detect(tmp_path)
        nxt = next(f for f in result if f.name == "Next.js")
        assert "next.config.js" in nxt.detection_files


# ---------------------------------------------------------------------------
# FrameworkChecker tests
# ---------------------------------------------------------------------------

class TestFrameworkChecker:
    def _make_framework(self, name: str) -> DetectedFramework:
        return DetectedFramework(name=name, version_hint=None, confidence="high", detection_files=[])

    def test_no_context_file_score_zero(self, tmp_path):
        fw = self._make_framework("Next.js")
        checker = FrameworkChecker()
        cov = checker.check(fw, context_file=None)
        assert cov.score == 0
        assert "setup" in cov.missing_required

    def test_full_coverage_score_100(self, tmp_path):
        content = """# My Project

## Next.js Notes

### Setup
Install deps with npm install.

### Common Patterns
Use App Router.

### Known Gotchas
Server components can't use hooks.

### Testing Patterns
Use jest + testing-library.

### Deploy Patterns
Deploy to Vercel.
"""
        ctx = tmp_path / "CLAUDE.md"
        ctx.write_text(content)
        fw = self._make_framework("Next.js")
        cov = FrameworkChecker().check(fw, ctx)
        assert cov.score == 100
        assert cov.missing_required == []
        assert cov.missing_nice_to_have == []

    def test_partial_coverage_missing_required(self, tmp_path):
        content = "# Project\n\n## Next.js Notes\n\nSetup: npm install\n"
        ctx = tmp_path / "CLAUDE.md"
        ctx.write_text(content)
        fw = self._make_framework("Next.js")
        cov = FrameworkChecker().check(fw, ctx)
        assert 0 < cov.score < 100
        assert "common patterns" in cov.missing_required or "known gotchas" in cov.missing_required

    def test_score_weighted_80_20(self, tmp_path):
        # All required present, no nice-to-have -> score = 80
        content = "# Proj\n## FastAPI Notes\nSetup done.\nCommon patterns here.\nKnown gotchas listed.\n"
        ctx = tmp_path / "CLAUDE.md"
        ctx.write_text(content)
        fw = self._make_framework("FastAPI")
        cov = FrameworkChecker().check(fw, ctx)
        assert cov.score == 80

    def test_framework_not_mentioned_score_zero(self, tmp_path):
        content = "# Generic project\nThis is about React only.\n"
        ctx = tmp_path / "CLAUDE.md"
        ctx.write_text(content)
        fw = self._make_framework("Django")
        cov = FrameworkChecker().check(fw, ctx)
        assert cov.score == 0

    def test_check_all_multiple_frameworks(self, tmp_path):
        content = "# Project\n## FastAPI Notes\nSetup.\nCommon patterns.\nKnown gotchas.\n## Flask Notes\nSetup.\nCommon patterns.\nKnown gotchas.\n"
        ctx = tmp_path / "AGENTS.md"
        ctx.write_text(content)
        fws = [
            self._make_framework("FastAPI"),
            self._make_framework("Flask"),
        ]
        results = FrameworkChecker().check_all(fws, root=tmp_path, context_file=ctx)
        assert len(results) == 2
        assert all(isinstance(r, FrameworkCoverage) for r in results)

    def test_find_context_file_claude_md(self, tmp_path):
        (tmp_path / "CLAUDE.md").write_text("# Hello\n")
        ctx = FrameworkChecker().find_context_file(tmp_path)
        assert ctx is not None
        assert ctx.name == "CLAUDE.md"

    def test_find_context_file_agents_md(self, tmp_path):
        (tmp_path / "AGENTS.md").write_text("# Hello\n")
        ctx = FrameworkChecker().find_context_file(tmp_path)
        assert ctx is not None
        assert ctx.name == "AGENTS.md"

    def test_find_context_file_none(self, tmp_path):
        ctx = FrameworkChecker().find_context_file(tmp_path)
        assert ctx is None
