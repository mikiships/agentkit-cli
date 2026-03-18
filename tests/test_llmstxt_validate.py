"""Tests for agentkit llmstxt --validate and quality scoring (D4)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.llmstxt import validate_llms_txt, score_llms_txt

runner = CliRunner()

_VALID_LLMSTXT = """\
# MyProject v1.0

> A short description of my project.

## Docs

- [README](README.md): Project overview.
- [Guide](docs/guide.md): Getting started.

## API

- [API Reference](api/index.md): Full API docs.

## Examples

- [Basic Example](examples/basic.md): Simple usage.
"""

_MINIMAL_LLMSTXT = "# Minimal\n\n> Brief.\n\n## Docs\n\n- [A](a.md)\n- [B](b.md)\n- [C](c.md)\n\n## API\n\n- [X](x.py)\n"

_NO_TITLE = "> Description.\n\n## Docs\n\n- [A](a.md)\n"
_NO_BLOCKQUOTE = "# Title\n\n## Docs\n\n- [A](a.md)\n"
_FEW_LINKS = "# Title\n\n> Desc.\n\n## Docs\n\n- [A](a.md)\n"


# ---------------------------------------------------------------------------
# validate_llms_txt
# ---------------------------------------------------------------------------

class TestValidateLlmsTxt:
    def test_valid_passes_all_checks(self):
        checks = validate_llms_txt(_VALID_LLMSTXT)
        failed = [c for c in checks if not c["passed"]]
        assert len(failed) == 0

    def test_missing_title_fails(self):
        checks = validate_llms_txt(_NO_TITLE)
        titled = next(c for c in checks if "H1" in c["check"] or "title" in c["check"].lower())
        assert not titled["passed"]

    def test_missing_blockquote_fails(self):
        checks = validate_llms_txt(_NO_BLOCKQUOTE)
        bq = next(c for c in checks if "blockquote" in c["check"].lower() or "summary" in c["check"].lower())
        assert not bq["passed"]

    def test_few_links_fails(self):
        checks = validate_llms_txt(_FEW_LINKS)
        lc = next(c for c in checks if "link" in c["check"].lower())
        assert not lc["passed"]

    def test_single_section_fails(self):
        content = "# Title\n\n> Desc.\n\n## Docs\n\n- [A](a.md)\n- [B](b.md)\n- [C](c.md)\n"
        checks = validate_llms_txt(content)
        sc = next(c for c in checks if "section" in c["check"].lower())
        assert not sc["passed"]

    def test_returns_list_of_dicts(self):
        checks = validate_llms_txt(_VALID_LLMSTXT)
        assert isinstance(checks, list)
        assert all(isinstance(c, dict) for c in checks)
        assert all("check" in c and "passed" in c for c in checks)

    def test_absolute_path_fails(self):
        content = "# Title\n\n> Desc.\n\n## Docs\n\n- [A](/absolute/path.md)\n- [B](b.md)\n- [C](c.md)\n\n## API\n\n- [X](x.py)\n"
        checks = validate_llms_txt(content)
        path_check = next((c for c in checks if "path" in c["check"].lower()), None)
        if path_check:
            assert not path_check["passed"]

    def test_suggestions_provided_on_fail(self):
        checks = validate_llms_txt(_NO_TITLE)
        for c in checks:
            if not c["passed"]:
                assert c.get("suggestion"), f"No suggestion for failed check: {c['check']}"


# ---------------------------------------------------------------------------
# score_llms_txt
# ---------------------------------------------------------------------------

class TestScoreLlmsTxt:
    def test_full_score_valid(self):
        score = score_llms_txt(_VALID_LLMSTXT)
        assert score == 100

    def test_empty_score_low(self):
        score = score_llms_txt("")
        assert score <= 20  # only "no broken paths" can pass

    def test_score_range(self):
        for content in [_VALID_LLMSTXT, _NO_TITLE, _NO_BLOCKQUOTE, _FEW_LINKS, _MINIMAL_LLMSTXT]:
            s = score_llms_txt(content)
            assert 0 <= s <= 100

    def test_minimal_scores_high(self):
        score = score_llms_txt(_MINIMAL_LLMSTXT)
        assert score >= 80

    def test_no_title_loses_points(self):
        score_full = score_llms_txt(_VALID_LLMSTXT)
        score_no_title = score_llms_txt(_NO_TITLE)
        assert score_full > score_no_title


# ---------------------------------------------------------------------------
# CLI --validate and --score flags
# ---------------------------------------------------------------------------

class TestCliValidateScore:
    def test_validate_cli_passes_valid(self, tmp_path):
        (tmp_path / "llms.txt").write_text(_VALID_LLMSTXT)
        result = runner.invoke(app, ["llmstxt", str(tmp_path), "--validate"])
        assert result.exit_code == 0

    def test_validate_cli_json(self, tmp_path):
        (tmp_path / "llms.txt").write_text(_VALID_LLMSTXT)
        result = runner.invoke(app, ["llmstxt", str(tmp_path), "--validate", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "checks" in data
        assert "score" in data
        assert data["score"] == 100
