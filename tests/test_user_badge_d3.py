"""Tests for D3: --inject flag (≥10 tests)."""
from __future__ import annotations

import pytest

from agentkit_cli.user_badge import (
    inject_badge_into_readme,
    BADGE_START_SENTINEL,
    BADGE_END_SENTINEL,
)


SAMPLE_MD = "[![Agent Readiness](https://img.shields.io/badge/agent--readiness-A%2085%2F100-brightgreen)](https://pypi.org/project/agentkit-cli/)"


def test_inject_inserts_sentinels():
    content = "# Hello\n\nSome text.\n"
    result = inject_badge_into_readme(content, SAMPLE_MD)
    assert BADGE_START_SENTINEL in result
    assert BADGE_END_SENTINEL in result


def test_inject_includes_badge_markdown():
    content = "# Hello\n\nSome text.\n"
    result = inject_badge_into_readme(content, SAMPLE_MD)
    assert SAMPLE_MD in result


def test_inject_idempotent_count():
    content = "# Hello\n\nSome text.\n"
    once = inject_badge_into_readme(content, SAMPLE_MD)
    twice = inject_badge_into_readme(once, SAMPLE_MD)
    assert twice.count(BADGE_START_SENTINEL) == 1
    assert twice.count(BADGE_END_SENTINEL) == 1


def test_inject_updates_badge_url():
    content = "# Hello\n\nSome text.\n"
    first = inject_badge_into_readme(content, "[![old](old_url)](link)")
    second = inject_badge_into_readme(first, "[![new](new_url)](link)")
    assert "new_url" in second
    assert "old_url" not in second


def test_inject_preserves_existing_content():
    content = "# Hello\n\nSome text that should stay.\n"
    result = inject_badge_into_readme(content, SAMPLE_MD)
    assert "Some text that should stay." in result


def test_inject_after_h1_title():
    content = "# My Project\n\nIntro paragraph.\n"
    result = inject_badge_into_readme(content, SAMPLE_MD)
    lines = result.splitlines()
    h1_idx = next(i for i, l in enumerate(lines) if l.startswith("# "))
    badge_idx = next(i for i, l in enumerate(lines) if BADGE_START_SENTINEL in l)
    assert badge_idx > h1_idx


def test_inject_no_h1_inserts_at_top():
    content = "Some text without H1.\n"
    result = inject_badge_into_readme(content, SAMPLE_MD)
    assert BADGE_START_SENTINEL in result
    assert result.index(BADGE_START_SENTINEL) < result.index("Some text without H1.")


def test_inject_empty_readme():
    result = inject_badge_into_readme("", SAMPLE_MD)
    assert BADGE_START_SENTINEL in result
    assert SAMPLE_MD in result


def test_inject_multiline_existing_block():
    content = (
        "# Project\n\n"
        f"{BADGE_START_SENTINEL}\n"
        "line1\n"
        "line2\n"
        f"{BADGE_END_SENTINEL}\n"
        "\nOther content.\n"
    )
    new_md = "[![new](url)](link)"
    result = inject_badge_into_readme(content, new_md)
    assert "url" in result
    assert "line1" not in result
    assert "Other content." in result


def test_inject_returns_string():
    result = inject_badge_into_readme("# Hello\n", SAMPLE_MD)
    assert isinstance(result, str)
