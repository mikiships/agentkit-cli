from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agentkit_cli.main import app

runner = CliRunner()
FIXTURES = Path(__file__).parent / "fixtures" / "burn"


def test_burn_help():
    result = runner.invoke(app, ["burn", "--help"])
    assert result.exit_code == 0
    assert "--path" in result.output


def test_burn_json_output_shape():
    result = runner.invoke(app, ["burn", "--path", str(FIXTURES), "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert set(["total_cost_usd", "totals", "findings", "top_sessions"]).issubset(data)


def test_burn_empty_path_exits_cleanly(tmp_path):
    result = runner.invoke(app, ["burn", "--path", str(tmp_path)])
    assert result.exit_code == 0
    assert "No transcripts found" in result.output


def test_burn_project_filter():
    result = runner.invoke(app, ["burn", "--path", str(FIXTURES), "--project", "/repo/gamma", "--format", "json"])
    data = json.loads(result.output)
    assert data["session_count"] == 1


def test_burn_output_writes_html(tmp_path):
    out = tmp_path / "burn-report.html"
    result = runner.invoke(app, ["burn", "--path", str(FIXTURES), "--output", str(out)])
    assert result.exit_code == 0
    assert out.exists()
    assert "where spend goes" in out.read_text(encoding="utf-8").lower()


def test_burn_since_limit_filters():
    result = runner.invoke(app, ["burn", "--path", str(FIXTURES), "--since", "2026-04-18T11:30:00+00:00", "--limit", "1", "--format", "json"])
    data = json.loads(result.output)
    assert data["session_count"] == 1
    assert data["sessions"][0]["session_id"] == "openclaw-002"
