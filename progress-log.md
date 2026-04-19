# Progress Log — agentkit-cli v1.2.0 contracts

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

**Built and verified:**
- Confirmed the release metadata still reports `1.1.0` in `pyproject.toml` and `agentkit_cli/__init__.py`.
- Re-ran the contradiction scan and hygiene check from the workspace support scripts, both clean.
- Re-ran the focused burn validation slice plus `tests/test_main.py`, then re-ran the full suite on the current branch state.
- Verified the shipped registry state directly from the version-specific PyPI JSON for `agentkit-cli==1.1.0`.
- Reconciled `BUILD-REPORT.md` and `BUILD-REPORT-v1.1.0.md` to the actual chronology: branch head is now `0c47a5a`, while the shipped `v1.1.0` tag and PyPI release remain on `a704a06`.

**Tests and checks:**
- `uv run pytest -q tests/test_burn_adapters.py tests/test_burn_engine.py tests/test_burn_command.py tests/test_burn_report.py tests/test_main.py` -> `31 passed in 0.80s`
- `uv run pytest -q` -> `4811 passed, 1 warning in 128.98s (0:02:08)`
- `bash /Users/mordecai/.openclaw/workspace/scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.1.0-burn-observability` -> `0 findings`
- `bash /Users/mordecai/.openclaw/workspace/scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.1.0-burn-observability` -> `0 findings`
- PyPI verification -> live with `agentkit_cli-1.1.0.tar.gz` and `agentkit_cli-1.1.0-py3-none-any.whl`

**Audit notes:**
- The contract referenced repo-local helper scripts, but this repo does not contain them. The equivalent workspace support scripts were used for the required contradiction and hygiene checks.
- The branch and tag no longer point to the same commit. That is now documented explicitly instead of being reported as one commit.

**Final status:** shipped and reconciled. The release is live, validation is green, and the report surfaces now match the actual branch, tag, and PyPI state.

---

## D1: contract engine + schema-backed rendering — COMPLETE

**Built:**
- Added `agentkit_cli/contracts.py` with a deterministic contract spec, markdown renderer, source loading, slug generation, and repo-hint inference.
- Reused the canonical-source detection flow so contracts prefer `.agentkit/source.md` and fall back to legacy context files.
- Added D1 coverage for dedicated-source loading, legacy fallback, deterministic rendering, and output slug stability.

**Tests:** `uv run pytest -q tests/test_contract_d1.py` -> `4 passed`

**Next:** D2 `agentkit contract` CLI wiring.

---

## D2: `agentkit contract` CLI command — COMPLETE

**Built:**
- Added `agentkit_cli/commands/contract_cmd.py` and wired `agentkit contract <objective>` into `agentkit_cli/main.py`.
- Added support for `--path`, `--output`, `--title`, repeated `--deliverable`, repeated `--test-requirement`, and deterministic `--json` metadata.
- Added guardrails for missing paths and overwrite refusal when the destination contract already exists.

**Tests:** `uv run pytest -q tests/test_contract_d1.py tests/test_contract_d2.py` -> `8 passed in 1.94s`

**Next:** D3 source-aware scaffolding and defaults.
