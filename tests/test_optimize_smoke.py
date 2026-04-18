from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app

runner = CliRunner()
FIXTURE_DIR = Path(__file__).parent / "fixtures" / "optimize"


class _FakeReport:
    findings = []


@pytest.mark.parametrize(
    ("fixture_name", "target_name"),
    [
        ("bloated-rules", "CLAUDE.md"),
        ("already-tight", "CLAUDE.md"),
        ("risky-instructions", "AGENTS.md"),
    ],
)
@patch("agentkit_cli.optimize.get_adapter")
@patch("agentkit_cli.optimize.RedTeamScorer")
def test_optimize_smoke_dry_run_realistic_files(mock_redteam, mock_adapter, tmp_path: Path, fixture_name: str, target_name: str):
    target = tmp_path / target_name
    target.write_text((FIXTURE_DIR / f"{fixture_name}.md").read_text(encoding="utf-8"), encoding="utf-8")
    expected = json.loads((FIXTURE_DIR / f"{fixture_name}.json").read_text(encoding="utf-8"))
    mock_adapter.return_value.agentlint_check_context.return_value = None
    mock_redteam.return_value.score_resistance.return_value = _FakeReport()

    result = runner.invoke(app, ["optimize", "--path", str(tmp_path)])

    assert result.exit_code == 0
    verdict = "Verdict: Safe no-op" if expected["should_be_noop"] else "Verdict: Meaningful rewrite available"
    assert verdict in result.output
    for heading in expected["preserved_sections"]:
        assert f"- {heading}" in result.output


@patch("agentkit_cli.optimize.get_adapter")
@patch("agentkit_cli.optimize.RedTeamScorer")
def test_optimize_smoke_apply_changes_file_once_then_noops(mock_redteam, mock_adapter, tmp_path: Path):
    target = tmp_path / "CLAUDE.md"
    original = (FIXTURE_DIR / "bloated-rules.md").read_text(encoding="utf-8")
    target.write_text(original, encoding="utf-8")
    mock_adapter.return_value.agentlint_check_context.return_value = None
    mock_redteam.return_value.score_resistance.return_value = _FakeReport()

    first = runner.invoke(app, ["optimize", "--path", str(tmp_path), "--apply"])

    assert first.exit_code == 0
    assert "Applied optimized context to" in first.output
    first_applied = target.read_text(encoding="utf-8")
    assert first_applied != original

    second = runner.invoke(app, ["optimize", "--path", str(tmp_path), "--apply"])

    assert second.exit_code == 0
    assert "Safe no-op" in second.output
    assert "No rewrite needed" in second.output
    assert target.read_text(encoding="utf-8") == first_applied
