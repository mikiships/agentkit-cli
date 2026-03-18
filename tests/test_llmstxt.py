"""Tests for LlmsTxtGenerator (D1)."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from agentkit_cli.llmstxt import (
    LlmsTxtGenerator,
    RepoInfo,
    DocFile,
    validate_llms_txt,
    score_llms_txt,
    _extract_description,
    _extract_version,
    _title_from_filename,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_repo(tmp_path: Path, readme: str | None = "# MyRepo\n\nA great project.", docs: bool = False,
              examples: bool = False, changelog: bool = False, agent_ctx: bool = False,
              pyproject_version: str | None = None) -> Path:
    if readme is not None:
        (tmp_path / "README.md").write_text(readme)
    if changelog:
        (tmp_path / "CHANGELOG.md").write_text("## [1.0.0]\n- Initial release")
    if docs:
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "guide.md").write_text("# Guide\n\nDetails here.")
        (docs_dir / "api.md").write_text("# API\n\nAPI reference.")
    if examples:
        ex_dir = tmp_path / "examples"
        ex_dir.mkdir()
        (ex_dir / "basic.py").write_text("print('hello')")
        (ex_dir / "advanced.md").write_text("# Advanced\n\nDetails.")
    if agent_ctx:
        (tmp_path / "CLAUDE.md").write_text("# Claude context\n\nProject instructions.")
    if pyproject_version:
        (tmp_path / "pyproject.toml").write_text(f'[tool.poetry]\nversion = "{pyproject_version}"\n')
    return tmp_path


# ---------------------------------------------------------------------------
# D1: scan_repo
# ---------------------------------------------------------------------------

class TestScanRepo:
    def test_scan_minimal_repo(self, tmp_path):
        make_repo(tmp_path)
        gen = LlmsTxtGenerator()
        info = gen.scan_repo(str(tmp_path))
        assert info.project_name == tmp_path.name
        assert info.readme_path == "README.md"
        assert info.root == str(tmp_path)

    def test_scan_detects_changelog(self, tmp_path):
        make_repo(tmp_path, changelog=True)
        gen = LlmsTxtGenerator()
        info = gen.scan_repo(str(tmp_path))
        assert info.changelog_path == "CHANGELOG.md"

    def test_scan_detects_docs(self, tmp_path):
        make_repo(tmp_path, docs=True)
        gen = LlmsTxtGenerator()
        info = gen.scan_repo(str(tmp_path))
        assert len(info.docs_files) >= 2

    def test_scan_detects_examples(self, tmp_path):
        make_repo(tmp_path, examples=True)
        gen = LlmsTxtGenerator()
        info = gen.scan_repo(str(tmp_path))
        # Only .md/.txt/.rst/.html picked up by default
        assert any(df.path.endswith(".md") for df in info.examples_files)

    def test_scan_detects_agent_ctx(self, tmp_path):
        make_repo(tmp_path, agent_ctx=True)
        gen = LlmsTxtGenerator()
        info = gen.scan_repo(str(tmp_path))
        assert any("CLAUDE.md" in df.path for df in info.agent_context_files)

    def test_scan_empty_repo(self, tmp_path):
        gen = LlmsTxtGenerator()
        info = gen.scan_repo(str(tmp_path))
        assert info.readme_path is None
        assert info.changelog_path is None
        assert info.docs_files == []

    def test_scan_extracts_description(self, tmp_path):
        make_repo(tmp_path, readme="# MyRepo\n\nThis is my awesome project description.")
        gen = LlmsTxtGenerator()
        info = gen.scan_repo(str(tmp_path))
        assert "awesome project" in info.description

    def test_scan_extracts_version(self, tmp_path):
        make_repo(tmp_path, pyproject_version="1.2.3")
        gen = LlmsTxtGenerator()
        info = gen.scan_repo(str(tmp_path))
        assert info.version == "1.2.3"

    def test_scan_no_version(self, tmp_path):
        make_repo(tmp_path)
        gen = LlmsTxtGenerator()
        info = gen.scan_repo(str(tmp_path))
        assert info.version == ""

    def test_scan_returns_repo_info_type(self, tmp_path):
        gen = LlmsTxtGenerator()
        info = gen.scan_repo(str(tmp_path))
        assert isinstance(info, RepoInfo)

    def test_scan_readme_rst(self, tmp_path):
        (tmp_path / "README.rst").write_text("MyRepo\n======\n\nA cool library.")
        gen = LlmsTxtGenerator()
        info = gen.scan_repo(str(tmp_path))
        assert info.readme_path == "README.rst"


# ---------------------------------------------------------------------------
# D1: generate_llms_txt
# ---------------------------------------------------------------------------

class TestGenerateLlmsTxt:
    def test_has_h1_title(self, tmp_path):
        make_repo(tmp_path)
        gen = LlmsTxtGenerator()
        info = gen.scan_repo(str(tmp_path))
        out = gen.generate_llms_txt(info)
        assert out.startswith("# ")

    def test_has_blockquote(self, tmp_path):
        make_repo(tmp_path, readme="# Proj\n\nSome description here.")
        gen = LlmsTxtGenerator()
        info = gen.scan_repo(str(tmp_path))
        out = gen.generate_llms_txt(info)
        assert "> " in out

    def test_includes_readme_link(self, tmp_path):
        make_repo(tmp_path)
        gen = LlmsTxtGenerator()
        info = gen.scan_repo(str(tmp_path))
        out = gen.generate_llms_txt(info)
        assert "README.md" in out

    def test_includes_docs_section(self, tmp_path):
        make_repo(tmp_path, docs=True)
        gen = LlmsTxtGenerator()
        info = gen.scan_repo(str(tmp_path))
        out = gen.generate_llms_txt(info)
        assert "## Docs" in out

    def test_includes_examples_section(self, tmp_path):
        make_repo(tmp_path, examples=True)
        gen = LlmsTxtGenerator()
        info = gen.scan_repo(str(tmp_path))
        out = gen.generate_llms_txt(info)
        assert "## Examples" in out

    def test_includes_agent_context_section(self, tmp_path):
        make_repo(tmp_path, agent_ctx=True)
        gen = LlmsTxtGenerator()
        info = gen.scan_repo(str(tmp_path))
        out = gen.generate_llms_txt(info)
        assert "## Agent Context" in out

    def test_ends_with_newline(self, tmp_path):
        make_repo(tmp_path)
        gen = LlmsTxtGenerator()
        info = gen.scan_repo(str(tmp_path))
        out = gen.generate_llms_txt(info)
        assert out.endswith("\n")

    def test_version_in_title(self, tmp_path):
        make_repo(tmp_path, pyproject_version="2.0.0")
        gen = LlmsTxtGenerator()
        info = gen.scan_repo(str(tmp_path))
        out = gen.generate_llms_txt(info)
        assert "v2.0.0" in out

    def test_empty_repo_still_valid(self, tmp_path):
        gen = LlmsTxtGenerator()
        info = gen.scan_repo(str(tmp_path))
        out = gen.generate_llms_txt(info)
        assert out.startswith("# ")


# ---------------------------------------------------------------------------
# D1: generate_llms_full_txt
# ---------------------------------------------------------------------------

class TestGenerateLlmsFullTxt:
    def test_includes_readme_content(self, tmp_path):
        make_repo(tmp_path, readme="# MyProject\n\nHello world content here.")
        gen = LlmsTxtGenerator()
        info = gen.scan_repo(str(tmp_path))
        out = gen.generate_llms_full_txt(info)
        assert "Hello world content here." in out

    def test_includes_separator(self, tmp_path):
        make_repo(tmp_path)
        gen = LlmsTxtGenerator()
        info = gen.scan_repo(str(tmp_path))
        out = gen.generate_llms_full_txt(info)
        assert "---" in out

    def test_skips_large_files(self, tmp_path):
        make_repo(tmp_path)
        # Create a file >100KB
        big = tmp_path / "docs"
        big.mkdir()
        (big / "big.md").write_text("x" * (101 * 1024))
        gen = LlmsTxtGenerator()
        info = gen.scan_repo(str(tmp_path))
        out = gen.generate_llms_full_txt(info)
        assert "too large" in out

    def test_includes_changelog_content(self, tmp_path):
        make_repo(tmp_path, changelog=True)
        gen = LlmsTxtGenerator()
        info = gen.scan_repo(str(tmp_path))
        out = gen.generate_llms_full_txt(info)
        assert "Initial release" in out


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

class TestUtilities:
    def test_title_from_filename_basic(self):
        assert _title_from_filename("docs/getting_started.md") == "Getting Started"

    def test_title_from_filename_hyphen(self):
        assert _title_from_filename("api-reference.md") == "Api Reference"

    def test_extract_description_skips_badges(self, tmp_path):
        (tmp_path / "README.md").write_text("# Title\n\n[![badge](url)](link)\n\nReal description here.")
        desc = _extract_description("README.md", str(tmp_path))
        assert "Real description" in desc

    def test_extract_description_empty_file(self, tmp_path):
        (tmp_path / "README.md").write_text("")
        desc = _extract_description("README.md", str(tmp_path))
        assert desc == ""

    def test_extract_version_pyproject(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text('version = "3.1.4"\n')
        v = _extract_version(str(tmp_path))
        assert v == "3.1.4"

    def test_extract_version_not_found(self, tmp_path):
        v = _extract_version(str(tmp_path))
        assert v == ""
