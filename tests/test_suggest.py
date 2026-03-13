"""Tests for agentkit suggest command and suggest_engine."""
from __future__ import annotations

import json
import re
import textwrap
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from agentkit_cli.suggest_engine import (
    Finding,
    parse_agentlint_check_context,
    parse_agentlint_diff,
    prioritize,
    prioritize_findings,
)
from agentkit_cli.commands.suggest_cmd import (
    run_fixes,
    suggest_command,
    _extract_score,
    _collect_context_files,
    _fix_year_rot,
    _fix_trailing_whitespace,
    _fix_duplicate_blank_lines,
    _apply_fixes,
    _unified_diff,
)


# ---------------------------------------------------------------------------
# suggest_engine: parse_agentlint_check_context
# ---------------------------------------------------------------------------

class TestParseCheckContext:
    def test_empty_none(self):
        assert parse_agentlint_check_context(None) == []

    def test_empty_dict(self):
        assert parse_agentlint_check_context({}) == []

    def test_empty_issues(self):
        assert parse_agentlint_check_context({"issues": []}) == []

    def test_single_issue(self):
        data = {"issues": [{"type": "year-rot", "message": "Stale year 2021", "file": "CLAUDE.md"}]}
        findings = parse_agentlint_check_context(data)
        assert len(findings) == 1
        f = findings[0]
        assert f.category == "year-rot"
        assert f.severity == "critical"
        assert "2021" in f.description
        assert f.file == "CLAUDE.md"
        assert f.tool == "agentlint/check-context"

    def test_findings_key(self):
        data = {"findings": [{"type": "bloat", "message": "Score 45"}]}
        findings = parse_agentlint_check_context(data)
        assert len(findings) == 1
        assert findings[0].category == "bloat"
        assert findings[0].severity == "medium"

    def test_json_string_input(self):
        data = json.dumps({"issues": [{"type": "trailing-whitespace", "message": "trailing ws"}]})
        findings = parse_agentlint_check_context(data)
        assert len(findings) == 1
        assert findings[0].severity == "low"

    def test_invalid_json_string(self):
        assert parse_agentlint_check_context("not json") == []

    def test_multiple_issues(self):
        data = {
            "issues": [
                {"type": "year-rot", "message": "Old year"},
                {"type": "path-rot", "message": "Broken path"},
                {"type": "script-rot", "message": "Bad script"},
            ]
        }
        findings = parse_agentlint_check_context(data)
        assert len(findings) == 3

    def test_auto_fixable_year_rot_claude_md(self):
        data = {"issues": [{"type": "year-rot", "message": "Stale", "file": "CLAUDE.md"}]}
        findings = parse_agentlint_check_context(data)
        assert findings[0].auto_fixable is True

    def test_auto_fixable_year_rot_source_file_not_fixable(self):
        data = {"issues": [{"type": "year-rot", "message": "Stale", "file": "main.py"}]}
        findings = parse_agentlint_check_context(data)
        assert findings[0].auto_fixable is False

    def test_path_rot_not_auto_fixable(self):
        data = {"issues": [{"type": "path-rot", "message": "Broken"}]}
        findings = parse_agentlint_check_context(data)
        assert findings[0].auto_fixable is False


# ---------------------------------------------------------------------------
# suggest_engine: parse_agentlint_diff
# ---------------------------------------------------------------------------

class TestParseAgentlintDiff:
    def test_empty(self):
        assert parse_agentlint_diff(None) == []

    def test_basic(self):
        data = {"issues": [{"type": "stale-todo", "message": "TODO unresolved"}]}
        findings = parse_agentlint_diff(data)
        assert len(findings) == 1
        assert findings[0].tool == "agentlint/diff"
        assert findings[0].severity == "high"

    def test_json_string(self):
        data = json.dumps({"findings": [{"type": "mcp-security", "message": "Unsafe MCP"}]})
        findings = parse_agentlint_diff(data)
        assert len(findings) == 1
        assert findings[0].severity == "critical"


# ---------------------------------------------------------------------------
# suggest_engine: prioritize
# ---------------------------------------------------------------------------

class TestPrioritize:
    def _make(self, category: str, file: str = "CLAUDE.md", severity: str = None) -> Finding:
        from agentkit_cli.suggest_engine import _severity_for_category, _auto_fixable
        sev = severity or _severity_for_category(category)
        return Finding(
            tool="test",
            severity=sev,
            category=category,
            description="test",
            fix_hint="fix it",
            auto_fixable=_auto_fixable(category, file),
            file=file,
        )

    def test_empty(self):
        assert prioritize([]) == []

    def test_severity_sort(self):
        findings = [
            self._make("bloat"),           # medium
            self._make("year-rot"),         # critical
            self._make("stale-todo"),       # high
            self._make("trailing-whitespace"),  # low
        ]
        result = prioritize(findings)
        sevs = [f.severity for f in result]
        assert sevs == ["critical", "high", "medium", "low"]

    def test_dedup_same_category_same_file(self):
        findings = [
            self._make("year-rot", file="CLAUDE.md"),
            self._make("year-rot", file="CLAUDE.md"),
        ]
        result = prioritize(findings)
        assert len(result) == 1

    def test_dedup_different_files(self):
        findings = [
            self._make("year-rot", file="CLAUDE.md"),
            self._make("year-rot", file="AGENTS.md"),
        ]
        result = prioritize(findings)
        assert len(result) == 2

    def test_top_n(self):
        findings = [self._make(cat) for cat in ["year-rot", "path-rot", "bloat", "stale-todo", "trailing-whitespace", "cosmetic"]]
        result = prioritize(findings, top_n=3)
        assert len(result) == 3

    def test_dedup_keeps_highest_severity(self):
        # Same category + file, different severity — should keep critical
        f_low = Finding(tool="t", severity="low", category="year-rot", description="d", fix_hint="h", file="CLAUDE.md")
        f_crit = Finding(tool="t", severity="critical", category="year-rot", description="d2", fix_hint="h", file="CLAUDE.md")
        result = prioritize([f_low, f_crit])
        assert result[0].severity == "critical"


# ---------------------------------------------------------------------------
# suggest_engine: prioritize_findings (high-level)
# ---------------------------------------------------------------------------

class TestPrioritizeFindings:
    def test_list_input(self):
        raw = [{"type": "year-rot", "message": "Old", "file": "CLAUDE.md"}]
        result = prioritize_findings(raw)
        assert len(result) == 1
        assert result[0].severity == "critical"

    def test_dict_input(self):
        raw = {"issues": [{"type": "bloat", "message": "Bloated"}]}
        result = prioritize_findings(raw)
        assert len(result) == 1

    def test_empty(self):
        assert prioritize_findings([]) == []
        assert prioritize_findings({}) == []


# ---------------------------------------------------------------------------
# Auto-fix helpers
# ---------------------------------------------------------------------------

class TestFixYearRot:
    def test_updates_old_year(self):
        import datetime
        current = datetime.datetime.now().year
        text = f"Last updated: 2018. See docs."
        result = _fix_year_rot(text)
        assert str(current) in result
        assert "2018" not in result

    def test_does_not_change_recent_year(self):
        import datetime
        current = datetime.datetime.now().year
        text = f"Updated: {current}"
        result = _fix_year_rot(text)
        assert str(current) in result

    def test_multiple_years(self):
        import datetime
        current = datetime.datetime.now().year
        text = "From 2015 to 2019 and also 2020."
        result = _fix_year_rot(text)
        assert "2015" not in result
        assert "2019" not in result


class TestFixTrailingWhitespace:
    def test_strips_trailing_spaces(self):
        text = "hello   \nworld  \n"
        result = _fix_trailing_whitespace(text)
        assert result == "hello\nworld\n"

    def test_strips_trailing_tabs(self):
        text = "line\t\nother\n"
        result = _fix_trailing_whitespace(text)
        assert result == "line\nother\n"

    def test_empty_string(self):
        assert _fix_trailing_whitespace("") == ""

    def test_preserves_content(self):
        text = "no trailing\n"
        assert _fix_trailing_whitespace(text) == text


class TestFixDuplicateBlankLines:
    def test_collapses_many_blanks(self):
        text = "a\n\n\n\n\nb"
        result = _fix_duplicate_blank_lines(text)
        assert "\n\n\n\n" not in result

    def test_allows_two_blanks(self):
        text = "a\n\n\nb"
        result = _fix_duplicate_blank_lines(text)
        # 3 newlines = 2 blank lines — the regex catches 4+
        assert result == text or "\n\n\n\n" not in result

    def test_no_blanks(self):
        text = "a\nb\nc\n"
        assert _fix_duplicate_blank_lines(text) == text


class TestApplyFixes:
    def test_all_fixes(self):
        import datetime
        current = datetime.datetime.now().year
        text = "Updated 2015  \n\n\n\n\nend"
        result = _apply_fixes(text)
        assert str(current) in result
        assert "  " not in result or not result.endswith("  \n")
        assert "\n\n\n\n\n" not in result


class TestUnifiedDiff:
    def test_produces_diff(self):
        orig = "line1\nline2\n"
        mod = "line1\nline2 changed\n"
        diff = _unified_diff(orig, mod, "test.md")
        assert "---" in diff
        assert "+++" in diff

    def test_no_diff_for_identical(self):
        text = "same\n"
        diff = _unified_diff(text, text, "test.md")
        assert diff == ""


# ---------------------------------------------------------------------------
# run_fixes (integration with temp files)
# ---------------------------------------------------------------------------

class TestRunFixes:
    def test_dry_run_no_write(self, tmp_path):
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("Updated 2015  \n\n\n\n\nend\n")
        changed = run_fixes(tmp_path, dry_run=True)
        # File unchanged
        assert "2015" in claude_md.read_text()
        assert len(changed) > 0

    def test_actual_fix_writes(self, tmp_path):
        import datetime
        current = datetime.datetime.now().year
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("Updated 2015  \nend\n")
        changed = run_fixes(tmp_path, dry_run=False)
        content = claude_md.read_text()
        assert str(current) in content
        assert len(changed) == 1

    def test_no_context_files(self, tmp_path):
        changed = run_fixes(tmp_path, dry_run=False)
        assert changed == []

    def test_source_file_not_touched(self, tmp_path):
        src = tmp_path / "main.py"
        src.write_text("# copyright 2015\n")
        changed = run_fixes(tmp_path, dry_run=False)
        assert "main.py" not in [str(c) for c in changed]
        assert "2015" in src.read_text()

    def test_agents_md_fixed(self, tmp_path):
        import datetime
        current = datetime.datetime.now().year
        agents_md = tmp_path / "AGENTS.md"
        agents_md.write_text("Last: 2016  \n")
        changed = run_fixes(tmp_path, dry_run=False)
        assert len(changed) == 1
        assert str(current) in agents_md.read_text()

    def test_dot_agents_dir(self, tmp_path):
        import datetime
        current = datetime.datetime.now().year
        agents_dir = tmp_path / ".agents"
        agents_dir.mkdir()
        md_file = agents_dir / "tools.md"
        md_file.write_text("Installed 2017  \n")
        changed = run_fixes(tmp_path, dry_run=False)
        assert len(changed) == 1
        assert str(current) in md_file.read_text()


# ---------------------------------------------------------------------------
# _extract_score
# ---------------------------------------------------------------------------

class TestExtractScore:
    def test_freshness_score(self):
        assert _extract_score({"freshness_score": 72}) == 72

    def test_score_key(self):
        assert _extract_score({"score": 55}) == 55

    def test_none_input(self):
        assert _extract_score(None) is None

    def test_empty_dict(self):
        assert _extract_score({}) is None


# ---------------------------------------------------------------------------
# _collect_context_files
# ---------------------------------------------------------------------------

class TestCollectContextFiles:
    def test_finds_claude_md(self, tmp_path):
        (tmp_path / "CLAUDE.md").write_text("hi")
        files = _collect_context_files(tmp_path)
        assert any("CLAUDE.md" in str(f) for f in files)

    def test_finds_agents_md(self, tmp_path):
        (tmp_path / "AGENTS.md").write_text("hi")
        files = _collect_context_files(tmp_path)
        assert any("AGENTS.md" in str(f) for f in files)

    def test_empty_dir(self, tmp_path):
        files = _collect_context_files(tmp_path)
        assert files == []


# ---------------------------------------------------------------------------
# suggest_command: JSON output
# ---------------------------------------------------------------------------

class TestSuggestCommandJson:
    def test_json_output_valid(self, tmp_path, capsys):
        """suggest_command with --json and mocked agentlint."""
        cc_data = {
            "freshness_score": 68,
            "issues": [
                {"type": "year-rot", "message": "Stale 2020", "file": "CLAUDE.md"},
                {"type": "bloat", "message": "Too big"},
            ],
        }
        with patch("agentkit_cli.commands.suggest_cmd._run_agentlint_check_context", return_value=cc_data):
            with patch("agentkit_cli.commands.suggest_cmd._run_agentlint_diff", return_value=None):
                suggest_command(path=tmp_path, json_output=True)
        captured = capsys.readouterr()
        out = json.loads(captured.out)
        assert "findings" in out
        assert out["score"] == 68
        assert len(out["findings"]) >= 2

    def test_json_empty_findings(self, tmp_path, capsys):
        with patch("agentkit_cli.commands.suggest_cmd._run_agentlint_check_context", return_value=None):
            with patch("agentkit_cli.commands.suggest_cmd._run_agentlint_diff", return_value=None):
                suggest_command(path=tmp_path, json_output=True)
        captured = capsys.readouterr()
        out = json.loads(captured.out)
        assert out["findings"] == []

    def test_json_schema_keys(self, tmp_path, capsys):
        cc_data = {"issues": [{"type": "path-rot", "message": "Broken ref", "file": "AGENTS.md"}]}
        with patch("agentkit_cli.commands.suggest_cmd._run_agentlint_check_context", return_value=cc_data):
            with patch("agentkit_cli.commands.suggest_cmd._run_agentlint_diff", return_value=None):
                suggest_command(path=tmp_path, json_output=True)
        out = json.loads(capsys.readouterr().out)
        f = out["findings"][0]
        for key in ("tool", "severity", "category", "description", "fix_hint", "auto_fixable"):
            assert key in f


# ---------------------------------------------------------------------------
# suggest_command: edge cases
# ---------------------------------------------------------------------------

class TestSuggestCommandEdgeCases:
    def test_no_agentlint_installed(self, tmp_path):
        """Gracefully handle agentlint not found."""
        with patch("agentkit_cli.commands.suggest_cmd._run_agentlint_check_context", return_value=None):
            with patch("agentkit_cli.commands.suggest_cmd._run_agentlint_diff", return_value=None):
                # Should not raise
                suggest_command(path=tmp_path)

    def test_top5_default(self, tmp_path, capsys):
        cc_data = {
            "issues": [
                {"type": "year-rot", "message": "y", "file": "CLAUDE.md"},
                {"type": "path-rot", "message": "p"},
                {"type": "bloat", "message": "b"},
                {"type": "stale-todo", "message": "t"},
                {"type": "trailing-whitespace", "message": "w", "file": "CLAUDE.md"},
                {"type": "mcp-security", "message": "m"},
            ]
        }
        with patch("agentkit_cli.commands.suggest_cmd._run_agentlint_check_context", return_value=cc_data):
            with patch("agentkit_cli.commands.suggest_cmd._run_agentlint_diff", return_value=None):
                suggest_command(path=tmp_path, json_output=True)
        out = json.loads(capsys.readouterr().out)
        assert len(out["findings"]) <= 5

    def test_show_all(self, tmp_path, capsys):
        cc_data = {
            "issues": [
                {"type": cat, "message": cat}
                for cat in ["year-rot", "path-rot", "bloat", "stale-todo", "trailing-whitespace", "mcp-security"]
            ]
        }
        with patch("agentkit_cli.commands.suggest_cmd._run_agentlint_check_context", return_value=cc_data):
            with patch("agentkit_cli.commands.suggest_cmd._run_agentlint_diff", return_value=None):
                suggest_command(path=tmp_path, json_output=True, show_all=True)
        out = json.loads(capsys.readouterr().out)
        assert len(out["findings"]) == 6

    def test_fix_dry_run(self, tmp_path):
        (tmp_path / "CLAUDE.md").write_text("Old year 2015  \n")
        with patch("agentkit_cli.commands.suggest_cmd._run_agentlint_check_context", return_value=None):
            with patch("agentkit_cli.commands.suggest_cmd._run_agentlint_diff", return_value=None):
                suggest_command(path=tmp_path, fix=True, dry_run=True)
        # File should not be modified
        assert "2015" in (tmp_path / "CLAUDE.md").read_text()

    def test_fix_applies(self, tmp_path):
        import datetime
        current = datetime.datetime.now().year
        (tmp_path / "CLAUDE.md").write_text("Old year 2015\n")
        with patch("agentkit_cli.commands.suggest_cmd._run_agentlint_check_context", return_value=None):
            with patch("agentkit_cli.commands.suggest_cmd._run_agentlint_diff", return_value=None):
                suggest_command(path=tmp_path, fix=True, dry_run=False)
        assert str(current) in (tmp_path / "CLAUDE.md").read_text()


# ---------------------------------------------------------------------------
# CLI smoke test via typer CliRunner
# ---------------------------------------------------------------------------

class TestSuggestCli:
    def test_cli_help(self):
        from typer.testing import CliRunner
        from agentkit_cli.main import app
        runner = CliRunner()
        result = runner.invoke(app, ["suggest", "--help"])
        assert result.exit_code == 0
        assert "suggest" in result.output.lower() or "prioritized" in result.output.lower()

    def test_cli_json(self, tmp_path):
        from typer.testing import CliRunner
        from agentkit_cli.main import app
        runner = CliRunner()
        with patch("agentkit_cli.commands.suggest_cmd._run_agentlint_check_context", return_value=None):
            with patch("agentkit_cli.commands.suggest_cmd._run_agentlint_diff", return_value=None):
                result = runner.invoke(app, ["suggest", "--path", str(tmp_path), "--json"])
        assert result.exit_code == 0
        out = json.loads(result.output)
        assert "findings" in out
