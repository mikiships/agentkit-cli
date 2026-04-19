# Progress Log — agentkit-cli v1.1.0 burn observability

## D1: transcript adapters + normalized burn schema — COMPLETE

**Built:**
- Added `agentkit_cli/burn_adapters.py` with normalized burn models for sessions, turns, tool usage, and cost states.
- Implemented deterministic fixture adapters for Codex, Claude Code, and OpenClaw-style local transcript files.
- Added burn fixtures plus parser coverage for missing fields, malformed JSON/JSONL, estimated costs, and stable ordering.

**Tests:** `uv run pytest -q tests/test_burn_adapters.py` -> `8 passed in 0.03s`

**Next:** D2 burn analysis engine.

---

## D2: burn analysis engine — COMPLETE

**Built:**
- Added `agentkit_cli/burn.py` with session filtering, aggregation by project/model/provider/task/source, top-session ranking, and stable JSON-ready report output.
- Implemented waste finding detection for expensive no-tool turns, retry-loop patterns, and low one-shot success sessions.
- Added engine tests for aggregation math, deterministic sorting, filters, and waste detection.

**Tests:** `uv run pytest -q tests/test_burn_adapters.py tests/test_burn_engine.py` -> `13 passed in 0.04s`

**Next:** D3 `agentkit burn` CLI command.
