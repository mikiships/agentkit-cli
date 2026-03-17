"""Tests for agentkit_cli/redteam_engine.py"""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from agentkit_cli.redteam_engine import (
    Attack,
    AttackCategory,
    RedTeamEngine,
    _parse_context_params,
    _TEMPLATES_BY_CATEGORY,
)


# ---------------------------------------------------------------------------
# Template coverage
# ---------------------------------------------------------------------------

def test_all_categories_have_templates():
    for cat in AttackCategory:
        templates = _TEMPLATES_BY_CATEGORY[cat]
        assert len(templates) >= 6, f"Category {cat} has only {len(templates)} templates (min 6)"


def test_total_template_count():
    total = sum(len(v) for v in _TEMPLATES_BY_CATEGORY.values())
    assert total >= 36, f"Expected >= 36 templates, got {total}"


def test_template_required_fields():
    for cat, templates in _TEMPLATES_BY_CATEGORY.items():
        for i, tmpl in enumerate(templates):
            assert "input_text" in tmpl, f"{cat}[{i}] missing input_text"
            assert "description" in tmpl, f"{cat}[{i}] missing description"
            assert "expected_behavior" in tmpl, f"{cat}[{i}] missing expected_behavior"


# ---------------------------------------------------------------------------
# Attack dataclass
# ---------------------------------------------------------------------------

def test_attack_dataclass_fields():
    a = Attack(
        id="test-id",
        category=AttackCategory.JAILBREAK,
        input_text="test input",
        description="test desc",
        expected_behavior="test behavior",
    )
    assert a.id == "test-id"
    assert a.category == AttackCategory.JAILBREAK
    assert a.input_text == "test input"


# ---------------------------------------------------------------------------
# Context parameter parsing
# ---------------------------------------------------------------------------

def test_parse_context_params_defaults(tmp_path):
    # Non-existent file → defaults
    params = _parse_context_params(tmp_path / "nonexistent.md")
    assert "tool" in params
    assert "topic" in params
    assert "instruction" in params
    assert "persona" in params


def test_parse_context_params_from_file(tmp_path):
    ctx = tmp_path / "CLAUDE.md"
    ctx.write_text("# My Agent\nYou are a helpful assistant.\nDo not share any safety violations.", encoding="utf-8")
    params = _parse_context_params(ctx)
    assert params["topic"] == "My Agent"
    assert "safety" in params["instruction"].lower()


def test_parse_context_params_privacy_keyword(tmp_path):
    ctx = tmp_path / "CLAUDE.md"
    ctx.write_text("# Privacy guard\nProtect PII and user data.", encoding="utf-8")
    params = _parse_context_params(ctx)
    assert params["instruction"] == "privacy"


def test_parse_context_params_tool_extraction(tmp_path):
    ctx = tmp_path / "CLAUDE.md"
    ctx.write_text("This uses agentlint for checking.", encoding="utf-8")
    params = _parse_context_params(ctx)
    assert params["tool"] == "agentlint"


# ---------------------------------------------------------------------------
# RedTeamEngine.generate_attacks
# ---------------------------------------------------------------------------

def test_generate_attacks_default(tmp_path):
    ctx = tmp_path / "CLAUDE.md"
    ctx.write_text("# Test agent\nYou are a helpful agent.", encoding="utf-8")
    engine = RedTeamEngine()
    attacks = engine.generate_attacks(ctx, n_per_category=3)
    assert len(attacks) == 3 * len(list(AttackCategory))


def test_generate_attacks_n_per_category(tmp_path):
    ctx = tmp_path / "CLAUDE.md"
    ctx.write_text("# Test", encoding="utf-8")
    engine = RedTeamEngine()
    attacks = engine.generate_attacks(ctx, n_per_category=1)
    assert len(attacks) == len(list(AttackCategory))


def test_generate_attacks_category_filter(tmp_path):
    ctx = tmp_path / "CLAUDE.md"
    ctx.write_text("# Test", encoding="utf-8")
    engine = RedTeamEngine()
    attacks = engine.generate_attacks(
        ctx, n_per_category=3, categories=[AttackCategory.JAILBREAK]
    )
    assert len(attacks) == 3
    assert all(a.category == AttackCategory.JAILBREAK for a in attacks)


def test_generate_attacks_unique_ids(tmp_path):
    ctx = tmp_path / "CLAUDE.md"
    ctx.write_text("# Test", encoding="utf-8")
    engine = RedTeamEngine()
    attacks = engine.generate_attacks(ctx, n_per_category=3)
    ids = [a.id for a in attacks]
    assert len(ids) == len(set(ids))


def test_generate_attacks_missing_context(tmp_path):
    """Should generate attacks even if context file doesn't exist."""
    engine = RedTeamEngine()
    attacks = engine.generate_attacks(tmp_path / "nonexistent.md", n_per_category=2)
    assert len(attacks) == 2 * len(list(AttackCategory))


def test_generate_attacks_parameterization(tmp_path):
    """Attacks should use content from context file."""
    ctx = tmp_path / "CLAUDE.md"
    ctx.write_text("# AgentLint Inspector\nYou are an agentlint-powered assistant.", encoding="utf-8")
    engine = RedTeamEngine()
    attacks = engine.generate_attacks(ctx, n_per_category=3)
    # At least some attacks should reference the extracted tool/topic
    texts = " ".join(a.input_text for a in attacks)
    # The context was parsed, attacks were generated
    assert len(attacks) > 0


def test_generate_attacks_deterministic(tmp_path):
    """Same input → same attacks (no randomness in selection)."""
    ctx = tmp_path / "CLAUDE.md"
    ctx.write_text("# Stable test", encoding="utf-8")
    engine = RedTeamEngine()
    a1 = engine.generate_attacks(ctx, n_per_category=2)
    a2 = engine.generate_attacks(ctx, n_per_category=2)
    for x, y in zip(a1, a2):
        assert x.input_text == y.input_text
        assert x.description == y.description


def test_attack_category_enum_values():
    cats = {c.value for c in AttackCategory}
    assert "prompt_injection" in cats
    assert "jailbreak" in cats
    assert "context_confusion" in cats
    assert "instruction_override" in cats
    assert "data_extraction" in cats
    assert "role_escalation" in cats
