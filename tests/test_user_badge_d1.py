"""Tests for D1: UserBadgeEngine core (≥12 tests)."""
from __future__ import annotations

import pytest

from agentkit_cli.user_badge import (
    UserBadgeEngine,
    UserBadgeResult,
    score_to_badge_grade,
    inject_badge_into_readme,
    BADGE_START_SENTINEL,
    BADGE_END_SENTINEL,
    PYPI_LINK,
)


# ---------------------------------------------------------------------------
# score_to_badge_grade
# ---------------------------------------------------------------------------

def test_grade_a_at_90():
    grade, color = score_to_badge_grade(90.0)
    assert grade == "A"
    assert color == "brightgreen"


def test_grade_b_at_75():
    grade, color = score_to_badge_grade(75.0)
    assert grade == "B"
    assert color == "green"


def test_grade_c_at_60():
    grade, color = score_to_badge_grade(60.0)
    assert grade == "C"
    assert color == "yellow"


def test_grade_d_at_45():
    grade, color = score_to_badge_grade(45.0)
    assert grade == "D"
    assert color == "orange"


def test_grade_f_below_45():
    grade, color = score_to_badge_grade(44.9)
    assert grade == "F"
    assert color == "red"


def test_grade_f_at_zero():
    grade, color = score_to_badge_grade(0.0)
    assert grade == "F"
    assert color == "red"


# ---------------------------------------------------------------------------
# UserBadgeEngine.generate_badge_url
# ---------------------------------------------------------------------------

def test_badge_url_contains_shields_io():
    engine = UserBadgeEngine()
    url = engine.generate_badge_url("torvalds", 85.0, "A")
    assert "img.shields.io/badge/" in url


def test_badge_url_contains_grade():
    engine = UserBadgeEngine()
    url = engine.generate_badge_url("torvalds", 85.0, "A")
    assert "A" in url


def test_badge_url_contains_color():
    engine = UserBadgeEngine()
    url = engine.generate_badge_url("torvalds", 85.0, "A")
    assert "brightgreen" in url


def test_badge_url_has_flat_square_style():
    engine = UserBadgeEngine()
    url = engine.generate_badge_url("alice", 70.0, "B")
    assert "flat-square" in url


# ---------------------------------------------------------------------------
# UserBadgeEngine.generate_markdown
# ---------------------------------------------------------------------------

def test_markdown_contains_badge_url():
    engine = UserBadgeEngine()
    md = engine.generate_markdown("alice", 70.0, "B")
    badge_url = engine.generate_badge_url("alice", 70.0, "B")
    assert badge_url in md


def test_markdown_links_to_pypi():
    engine = UserBadgeEngine()
    md = engine.generate_markdown("alice", 70.0, "B")
    assert PYPI_LINK in md


def test_markdown_is_image_link_format():
    engine = UserBadgeEngine()
    md = engine.generate_markdown("alice", 70.0, "B")
    assert md.startswith("[![")


# ---------------------------------------------------------------------------
# UserBadgeEngine.generate_json
# ---------------------------------------------------------------------------

def test_generate_json_has_required_keys():
    engine = UserBadgeEngine()
    data = engine.generate_json("alice", 75.0, "B")
    assert "username" in data
    assert "score" in data
    assert "grade" in data
    assert "badge_url" in data
    assert "badge_markdown" in data
    assert "readme_snippet" in data
    assert "anybadge" in data


def test_generate_json_anybadge_has_label():
    engine = UserBadgeEngine()
    data = engine.generate_json("alice", 75.0, "B")
    assert data["anybadge"]["label"] == "agent-readiness"


# ---------------------------------------------------------------------------
# UserBadgeEngine.run
# ---------------------------------------------------------------------------

def test_run_returns_user_badge_result():
    engine = UserBadgeEngine()
    result = engine.run("alice", 80.0)
    assert isinstance(result, UserBadgeResult)


def test_run_infers_grade_from_score():
    engine = UserBadgeEngine()
    result = engine.run("alice", 92.0)
    assert result.grade == "A"


def test_run_uses_explicit_grade():
    engine = UserBadgeEngine()
    result = engine.run("alice", 92.0, grade="C")
    assert result.grade == "C"


def test_run_to_dict_roundtrip():
    engine = UserBadgeEngine()
    result = engine.run("alice", 80.0)
    d = result.to_dict()
    assert d["username"] == "alice"
    assert d["score"] == 80.0


# ---------------------------------------------------------------------------
# inject_badge_into_readme
# ---------------------------------------------------------------------------

def test_inject_adds_sentinels():
    content = "# My README\n\nSome text.\n"
    md = "[![badge](url)](link)"
    result = inject_badge_into_readme(content, md)
    assert BADGE_START_SENTINEL in result
    assert BADGE_END_SENTINEL in result


def test_inject_is_idempotent():
    content = "# My README\n\nSome text.\n"
    md = "[![badge](url)](link)"
    once = inject_badge_into_readme(content, md)
    twice = inject_badge_into_readme(once, md)
    # Should not duplicate sentinels
    assert twice.count(BADGE_START_SENTINEL) == 1


def test_inject_updates_existing_badge():
    content = (
        "# My README\n\n"
        f"{BADGE_START_SENTINEL}\n"
        "[![old badge](old_url)](link)\n"
        f"{BADGE_END_SENTINEL}\n"
        "\nSome text.\n"
    )
    new_md = "[![new badge](new_url)](link)"
    result = inject_badge_into_readme(content, new_md)
    assert "new_url" in result
    assert "old_url" not in result


def test_inject_after_h1():
    content = "# My Project\n\nSome intro.\n"
    md = "[![badge](url)](link)"
    result = inject_badge_into_readme(content, md)
    lines = result.splitlines()
    h1_idx = next(i for i, l in enumerate(lines) if l.startswith("# "))
    badge_idx = next(i for i, l in enumerate(lines) if BADGE_START_SENTINEL in l)
    assert badge_idx > h1_idx
