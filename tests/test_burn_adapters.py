from __future__ import annotations

from pathlib import Path

import pytest

from agentkit_cli.burn_adapters import BurnAdapterError, detect_adapter, load_sessions, parse_claude_file, parse_codex_file, parse_openclaw_file

FIXTURES = Path(__file__).parent / "fixtures" / "burn"


def test_detect_adapter_types():
    assert detect_adapter(FIXTURES / "sample.codex.json").__name__ == "parse_codex_file"
    assert detect_adapter(FIXTURES / "sample.claude.json").__name__ == "parse_claude_file"
    assert detect_adapter(FIXTURES / "sample.openclaw.jsonl").__name__ == "parse_openclaw_file"


def test_parse_codex_file_normalizes_cost_states():
    sessions = parse_codex_file(FIXTURES / "sample.codex.json")
    assert len(sessions) == 1
    turn1, turn2 = sessions[0].turns
    assert turn1.cost.state == "actual"
    assert turn1.cost.amount_usd == 0.03
    assert turn2.cost.state == "estimated"
    assert turn2.cost.estimated is True
    assert turn2.project_root == "/repo/alpha"


def test_parse_claude_file_handles_unknown_cost():
    sessions = parse_claude_file(FIXTURES / "sample.claude.json")
    assert sessions[0].provider == "anthropic"
    assert sessions[0].turns[1].cost.state == "unknown"
    assert sessions[0].turns[1].tool_uses[0].call_count == 2


def test_parse_openclaw_groups_multiple_sessions():
    sessions = parse_openclaw_file(FIXTURES / "sample.openclaw.jsonl")
    assert [session.session_id for session in sessions] == ["openclaw-001", "openclaw-002"]
    assert sessions[1].provider == "unknown"


def test_load_sessions_is_deterministic():
    sessions = load_sessions(FIXTURES)
    assert [session.session_id for session in sessions] == ["codex-001", "claude-001", "openclaw-001", "openclaw-002"]


def test_generated_turn_ids_and_sorting_are_deterministic(tmp_path):
    transcript = tmp_path / "generated.openclaw.jsonl"
    transcript.write_text(
        '\n'.join(
            [
                '{"session_id":"sess-1","model":"gpt-4.1","timestamp":"2026-04-18T12:03:00+00:00","input_tokens":5,"output_tokens":7}',
                '{"session_id":"sess-1","model":"gpt-4.1","timestamp":"2026-04-18T12:01:00+00:00","input_tokens":1,"output_tokens":2}',
            ]
        ),
        encoding="utf-8",
    )
    first = parse_openclaw_file(transcript)[0]
    second = parse_openclaw_file(transcript)[0]
    assert [turn.timestamp for turn in first.turns] == ["2026-04-18T12:01:00+00:00", "2026-04-18T12:03:00+00:00"]
    assert [turn.turn_id for turn in first.turns] == [turn.turn_id for turn in second.turns]
    assert all(turn.turn_id.startswith("turn-") for turn in first.turns)


def test_null_cost_fields_are_marked_missing(tmp_path):
    transcript = tmp_path / "missing-cost.codex.json"
    transcript.write_text(
        '{"session_id":"codex-missing","turns":[{"id":"t1","cost_usd":null}],"started_at":"2026-04-18T10:00:00+00:00"}',
        encoding="utf-8",
    )
    session = parse_codex_file(transcript)[0]
    assert session.turns[0].cost.state == "missing"
    assert session.turns[0].cost.amount_usd is None


def test_malformed_json_raises(tmp_path):
    broken = tmp_path / "bad.codex.json"
    broken.write_text("{", encoding="utf-8")
    with pytest.raises(BurnAdapterError):
        parse_codex_file(broken)


def test_malformed_jsonl_raises(tmp_path):
    broken = tmp_path / "bad.openclaw.jsonl"
    broken.write_text('{"session_id":"x"}\n{', encoding="utf-8")
    with pytest.raises(BurnAdapterError):
        parse_openclaw_file(broken)


def test_missing_fields_raise_adapter_error(tmp_path):
    broken = tmp_path / "missing.claude.json"
    broken.write_text('{"messages": []}', encoding="utf-8")
    with pytest.raises(BurnAdapterError):
        parse_claude_file(broken)
