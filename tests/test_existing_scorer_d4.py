"""Tests for D4 — Version, docs, and build artifacts (≥5 tests)."""
from __future__ import annotations

import pytest


def test_version_is_0780():
    from agentkit_cli import __version__
    assert __version__ == "0.80.0"


def test_existing_scorer_module_importable():
    import agentkit_cli.existing_scorer as m
    assert hasattr(m, "ExistingStateScorer")
    assert hasattr(m, "score_existing")
    assert hasattr(m, "DIMENSION_WEIGHTS")


def test_analyze_existing_importable_from_analyze():
    from agentkit_cli.analyze import analyze_existing
    assert callable(analyze_existing)


def test_daily_duel_engine_has_existing_attr():
    from agentkit_cli.daily_duel import DailyDuelEngine
    engine = DailyDuelEngine()
    assert hasattr(engine, "existing")


def test_repo_duel_engine_has_existing_attr():
    from agentkit_cli.repo_duel import RepoDuelEngine
    engine = RepoDuelEngine()
    assert hasattr(engine, "existing")


def test_daily_duel_cmd_has_existing_param():
    from agentkit_cli.commands.daily_duel_cmd import daily_duel_command
    import inspect
    sig = inspect.signature(daily_duel_command)
    assert "existing" in sig.parameters


def test_existing_scorer_all_dimensions_present():
    from agentkit_cli.existing_scorer import DIMENSION_WEIGHTS
    expected = {
        "agent_context", "readme_quality", "contributing",
        "changelog", "ci_config", "test_coverage", "type_annotations"
    }
    assert expected == set(DIMENSION_WEIGHTS.keys())
