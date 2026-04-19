# Progress Log — agentkit-cli v1.1.0 burn observability

## D1: transcript adapters + normalized burn schema — COMPLETE

**Built:**
- Added `agentkit_cli/burn_adapters.py` with normalized burn models for sessions, turns, tool usage, and cost states.
- Implemented deterministic fixture adapters for Codex, Claude Code, and OpenClaw-style local transcript files.
- Added burn fixtures plus parser coverage for missing fields, malformed JSON/JSONL, estimated costs, and stable ordering.

**Tests:** `uv run pytest -q tests/test_burn_adapters.py` -> `10 passed in 0.04s`

**Refinement:** tightened deterministic normalization by replacing process-randomized fallback turn IDs with stable SHA-256-derived IDs and sorting normalized turns by timestamp/id.

**Next:** D2 burn analysis engine.

---

## D2: burn analysis engine — COMPLETE

**Built:**
- Added `agentkit_cli/burn.py` with session filtering, aggregation by project/model/provider/task/source, top-session ranking, and stable JSON-ready report output.
- Implemented waste finding detection for expensive no-tool turns, retry-loop patterns, and low one-shot success sessions.
- Added engine tests for aggregation math, deterministic sorting, filters, and waste detection.

**Tests:** `uv run pytest -q tests/test_burn_adapters.py tests/test_burn_engine.py` -> `13 passed in 0.04s`

**Next:** D3 `agentkit burn` CLI command.

---

## D3: `agentkit burn` CLI command — COMPLETE

**Built:**
- Added `agentkit_cli/commands/burn.py` with `--path`, `--format`, `--since`, `--limit`, `--project`, and `--output` support.
- Added rich terminal output, stable JSON output, and clean empty-directory handling.
- Added CLI tests for happy path, filters, empty path, JSON shape, and HTML writing.

**Tests:** `uv run pytest -q tests/test_burn_adapters.py tests/test_burn_engine.py tests/test_burn_command.py tests/test_burn_report.py` -> `22 passed in 1.00s`

**Next:** D4 HTML report + narrative summary.

---

## D4: HTML burn report + narrative summary — COMPLETE

**Built:**
- Added `agentkit_cli/renderers/burn_report.py` with dark-theme HTML and markdown-ready burn summaries.
- Added renderer tests for report sections, styling markers, and markdown summary content.

**Tests:** `uv run pytest -q tests/test_burn_adapters.py tests/test_burn_engine.py tests/test_burn_command.py tests/test_burn_report.py` -> `22 passed in 1.00s`

**Next:** D5 docs, versioning, and final validation.

---

## D5: docs, build report, versioning, and final validation — COMPLETE

**Built:**
- Updated `README.md`, `CHANGELOG.md`, `BUILD-REPORT.md`, and added `BUILD-REPORT-v1.1.0.md` for the burn observability release candidate.
- Bumped version metadata to `1.1.0` in `pyproject.toml`, `agentkit_cli/__init__.py`, and the editable package entry in `uv.lock`.
- Reconciled the build-report surface with the existing suite, updated the main version test, and ran the contract helper scripts before final status.

**Tests:**
- `uv run pytest -q tests/test_burn_adapters.py tests/test_burn_engine.py tests/test_burn_command.py tests/test_burn_report.py` -> `22 passed in 0.34s`
- `uv run pytest -q` -> `4809 passed, 1 warning in 131.87s (0:02:11)`
- `bash /Users/mordecai/.openclaw/workspace/scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.1.0-burn-observability` -> `0 findings`
- `bash /Users/mordecai/.openclaw/workspace/scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.1.0-burn-observability` -> `0 findings`

**Final status:** all contract deliverables completed locally with a clean validation pass and no blocker report triggered.
