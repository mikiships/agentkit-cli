from __future__ import annotations

from pathlib import Path

from agentkit_cli.burn import BurnAnalysisEngine

FIXTURES = Path(__file__).parent / "fixtures" / "burn"


def test_burn_engine_aggregates_totals():
    engine = BurnAnalysisEngine()
    report = engine.analyze(engine.load(FIXTURES))
    assert report.session_count == 4
    assert report.turn_count == 9
    assert report.total_cost_usd == 0.132
    assert report.totals["by_provider"][0]["key"] == "openai"


def test_burn_engine_filter_since_and_limit():
    engine = BurnAnalysisEngine()
    sessions = engine.load(FIXTURES)
    report = engine.analyze(sessions, since="2026-04-18T11:30:00+00:00", limit=1)
    assert report.session_count == 1
    assert report.sessions[0].session_id == "openclaw-002"


def test_burn_engine_project_filter():
    engine = BurnAnalysisEngine()
    report = engine.analyze(engine.load(FIXTURES), project="/repo/gamma")
    assert report.session_count == 1
    assert report.top_sessions[0]["project_root"] == "/repo/gamma"


def test_burn_engine_sorting_stability():
    engine = BurnAnalysisEngine()
    report = engine.analyze(engine.load(FIXTURES))
    keys = [row["key"] for row in report.totals["by_task_label"]]
    assert keys == ["ship report", "debug flaky test", "refactor parser", "triage incident"]


def test_burn_engine_detects_waste_patterns():
    engine = BurnAnalysisEngine()
    report = engine.analyze(engine.load(FIXTURES))
    finding_types = [finding.finding_type for finding in report.findings]
    assert "expensive_no_tool_turn" in finding_types
    assert "low_one_shot_success" in finding_types
