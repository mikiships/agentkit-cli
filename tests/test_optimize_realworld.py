from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from agentkit_cli.optimize import OptimizeEngine

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "optimize"


class _FakeReport:
    findings = []


def _load_fixture(name: str) -> tuple[str, dict]:
    text = (FIXTURE_DIR / f"{name}.md").read_text(encoding="utf-8")
    expected = json.loads((FIXTURE_DIR / f"{name}.json").read_text(encoding="utf-8"))
    return text, expected


@pytest.mark.parametrize(
    ("fixture_name", "target_name"),
    [
        ("bloated-rules", "CLAUDE.md"),
        ("already-tight", "CLAUDE.md"),
        ("risky-instructions", "AGENTS.md"),
        ("mixed-signal", "CLAUDE.md"),
    ],
)
@patch("agentkit_cli.optimize.get_adapter")
@patch("agentkit_cli.optimize.RedTeamScorer")
def test_realworld_optimize_fixtures(mock_redteam, mock_adapter, tmp_path: Path, fixture_name: str, target_name: str):
    source_text, expected = _load_fixture(fixture_name)
    target = tmp_path / target_name
    target.write_text(source_text, encoding="utf-8")
    mock_adapter.return_value.agentlint_check_context.return_value = None
    mock_redteam.return_value.score_resistance.return_value = _FakeReport()

    result = OptimizeEngine(tmp_path).optimize(file=target)

    for heading in expected["preserved_sections"]:
        assert heading in result.preserved_sections
    for heading in expected["removable_sections"]:
        assert heading in result.removed_bloat or heading not in result.optimized_text
    for line in expected["must_not_contain"]:
        assert line not in result.optimized_text
    if expected["should_shrink"]:
        assert result.optimized_stats.lines < result.original_stats.lines
    else:
        assert abs(result.line_delta) <= 1


@pytest.mark.parametrize("fixture_name", ["bloated-rules", "already-tight", "risky-instructions", "mixed-signal"])
@patch("agentkit_cli.optimize.get_adapter")
@patch("agentkit_cli.optimize.RedTeamScorer")
def test_realworld_optimize_is_idempotent_on_second_pass(mock_redteam, mock_adapter, tmp_path: Path, fixture_name: str):
    source_text, _ = _load_fixture(fixture_name)
    target = tmp_path / "CLAUDE.md"
    target.write_text(source_text, encoding="utf-8")
    mock_adapter.return_value.agentlint_check_context.return_value = None
    mock_redteam.return_value.score_resistance.return_value = _FakeReport()

    engine = OptimizeEngine(tmp_path)
    first = engine.optimize(file=target)
    target.write_text(first.optimized_text, encoding="utf-8")
    second = engine.optimize(file=target)

    assert second.optimized_stats.lines <= first.optimized_stats.lines
    assert abs(second.line_delta) <= 1
    assert abs(second.token_delta) <= 4
