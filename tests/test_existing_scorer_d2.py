"""Tests for D2 — Integration of ExistingStateScorer into analyze and duel (≥12 tests).

Verifies:
- analyze_existing function works
- RepoDuelEngine supports existing=True
- DailyDuelEngine defaults to existing=True
- Scores differ between well-documented and sparse repos
"""
from __future__ import annotations

import textwrap
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from agentkit_cli.existing_scorer import ExistingStateScorer
from agentkit_cli.repo_duel import RepoDuelEngine, RepoDuelResult
from agentkit_cli.daily_duel import DailyDuelEngine


# ---------------------------------------------------------------------------
# analyze_existing function
# ---------------------------------------------------------------------------

def test_analyze_existing_importable():
    from agentkit_cli.analyze import analyze_existing
    assert callable(analyze_existing)


def test_analyze_existing_local_path(tmp_path):
    from agentkit_cli.analyze import analyze_existing, AnalyzeResult
    # Create minimal local repo
    (tmp_path / "README.md").write_text("# Hello\n\nInstall: pip install foo\n```bash\nfoo run\n```\n")
    (tmp_path / "CHANGELOG.md").write_text("# Changelog\n")
    result = analyze_existing(str(tmp_path))
    assert isinstance(result, AnalyzeResult)
    assert result.composite_score >= 0.0
    assert result.composite_score <= 100.0
    assert result.generated_context is False


def test_analyze_existing_returns_analyze_result(tmp_path):
    from agentkit_cli.analyze import analyze_existing, AnalyzeResult
    result = analyze_existing(str(tmp_path))
    assert isinstance(result, AnalyzeResult)


def test_analyze_existing_no_generation_flag(tmp_path):
    """analyze_existing should never generate context."""
    from agentkit_cli.analyze import analyze_existing
    result = analyze_existing(str(tmp_path))
    assert result.generated_context is False


def test_analyze_existing_tools_have_dimension_keys(tmp_path):
    from agentkit_cli.analyze import analyze_existing
    result = analyze_existing(str(tmp_path))
    expected_keys = {"agent_context", "readme_quality", "contributing", "changelog", "ci_config", "test_coverage", "type_annotations"}
    assert expected_keys.issubset(set(result.tools.keys()))


def test_analyze_existing_well_doc_beats_empty(tmp_path):
    from agentkit_cli.analyze import analyze_existing
    # Empty path
    empty = tmp_path / "empty"
    empty.mkdir()

    # Well-documented path
    well = tmp_path / "well"
    well.mkdir()
    (well / "CLAUDE.md").write_text("# Context\n")
    (well / "CHANGELOG.md").write_text("# Changelog\n")
    (well / "CONTRIBUTING.md").write_text("# Contributing\n")
    gha = well / ".github" / "workflows"
    gha.mkdir(parents=True)
    (gha / "ci.yml").write_text("name: CI\n")
    readme = textwrap.dedent("""\
        # Well Documented

        ## Installation

        ```bash
        pip install welldoc
        ```

        ## Usage

        ```python
        import welldoc
        ```
    """)
    (well / "README.md").write_text(readme * 10)

    well_result = analyze_existing(str(well))
    empty_result = analyze_existing(str(empty))
    assert well_result.composite_score > empty_result.composite_score


# ---------------------------------------------------------------------------
# RepoDuelEngine existing mode
# ---------------------------------------------------------------------------

def test_repo_duel_engine_accepts_existing_flag():
    engine = RepoDuelEngine(existing=True)
    assert engine.existing is True


def test_repo_duel_engine_existing_defaults_false():
    engine = RepoDuelEngine()
    assert engine.existing is False


def test_repo_duel_engine_existing_uses_analyze_existing(tmp_path):
    """When existing=True, engine should call analyze_existing (via factory)."""
    called_with_existing = []

    def fake_factory(target, timeout):
        called_with_existing.append(target)
        r = MagicMock()
        r.composite_score = 42.0
        r.grade = "B"
        r.tools = {}
        return r

    engine = RepoDuelEngine(existing=True, _analyze_factory=fake_factory)
    engine.run_duel("repo/a", "repo/b")
    assert len(called_with_existing) == 2


def test_repo_duel_existing_produces_result(tmp_path):
    """run_duel with existing=True should return a RepoDuelResult."""
    def fake_factory(target, timeout):
        score = 70.0 if "ruff" in target else 40.0
        r = MagicMock()
        r.composite_score = score
        r.grade = "B" if score > 50 else "C"
        r.tools = {}
        return r

    engine = RepoDuelEngine(existing=True, _analyze_factory=fake_factory)
    result = engine.run_duel("astral-sh/ruff", "PyCQA/pylint")
    assert isinstance(result, RepoDuelResult)
    assert result.repo1_score != result.repo2_score


# ---------------------------------------------------------------------------
# DailyDuelEngine defaults to existing=True
# ---------------------------------------------------------------------------

def test_daily_duel_engine_defaults_existing_true():
    engine = DailyDuelEngine()
    assert engine.existing is True


def test_daily_duel_engine_existing_false_override():
    engine = DailyDuelEngine(existing=False)
    assert engine.existing is False


def test_daily_duel_engine_passes_existing_to_repo_engine(tmp_path):
    """DailyDuelEngine should pass existing flag to RepoDuelEngine."""
    analyze_modes = []

    def fake_factory(target, timeout):
        analyze_modes.append(target)
        score = 75.0 if "ruff" in target else 35.0
        r = MagicMock()
        r.composite_score = score
        r.grade = "A" if score > 60 else "C"
        r.tools = {}
        return r

    engine = DailyDuelEngine(existing=True, _analyze_factory=fake_factory)
    # Use seed that gives ruff vs pylint
    result = engine.run_daily_duel(seed="2026-03-21")
    # Should have called analyze for both repos
    assert len(analyze_modes) == 2


def test_daily_duel_result_is_not_draw_with_different_scores():
    """When existing mode produces different scores, result should not be a draw."""
    def fake_factory(target, timeout):
        score = 80.0 if "ruff" in target else 30.0
        r = MagicMock()
        r.composite_score = score
        r.grade = "A" if score > 60 else "D"
        r.tools = {}
        return r

    engine = DailyDuelEngine(existing=True, _analyze_factory=fake_factory)
    result = engine.run_daily_duel(seed="2026-03-21")
    # Both repos have different scores
    assert result.repo1_score != result.repo2_score
    assert result.winner != "draw"
