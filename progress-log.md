# Progress Log — agentkit-cli v1.2.0 contracts

## Release completion audit start — 2026-04-19

**Starting truth:**
- `pyproject.toml`, `agentkit_cli/__init__.py`, `BUILD-REPORT.md`, `BUILD-REPORT-v1.2.0.md`, and `CHANGELOG.md` already describe a local `1.2.0` contracts release state.
- Current branch is `feat/v1.2.0-contracts` at `c654381`, with a dirty working tree only because the release contract markdown files are untracked in the repo root.
- Remote audit found no `origin/feat/v1.2.0-contracts` branch and no local or remote `v1.2.0` tag.
- PyPI audit confirmed `https://pypi.org/pypi/agentkit-cli/1.2.0/json` returns 404, so `agentkit-cli==1.2.0` is not live yet.
- Local prose is contradictory right now because `BUILD-REPORT.md` says "COMPLETE, LOCALLY VERIFIED" while the required release surfaces are still incomplete.

**Next:** rerun focused and full validation from this repo, then complete the missing branch, tag, and PyPI surfaces truthfully.

---

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

---

## D3: source-aware scaffolding and useful defaults — COMPLETE

**Built:**
- Extended the contract engine defaults so a bare objective still yields a useful execution checklist, test requirements, report sections, and stop conditions.
- Added source-aware rule injection for canonical-source presence vs missing-source fallback, plus repo-derived command hints and directory boundaries.
- Added guardrail coverage for missing source, repo-aware defaults, pyproject-driven command inference, and explicit output-path writing.

**Tests:** `uv run pytest -q tests/test_contract_d1.py tests/test_contract_d2.py tests/test_contract_d3.py` -> `12 passed in 1.09s`

**Next:** D4 docs, versioning, and full validation.

---

## D4: docs, build report, versioning, and validation — COMPLETE

**Built and verified:**
- Added README usage/examples for `agentkit contract`.
- Updated `CHANGELOG.md`, `BUILD-REPORT.md`, `BUILD-REPORT-v1.2.0.md`, `progress-log.md`, and version metadata for `1.2.0`.
- Added end-to-end coverage in `tests/test_contract_d4.py` for temp-repo contract generation and key section validation.
- Verified there is no repo-local contradiction-scan helper, then manually reconciled local status/version surfaces instead.
- Closed the release-completion pass by fixing two stale validation surfaces: `tests/test_main.py` had a hard-coded `1.1.0` expectation, and `BUILD-REPORT.md` was still missing the final suite count required by `tests/test_daily_d5.py`.

**Tests and checks:**
- `uv run pytest -q tests/test_contract_d1.py tests/test_contract_d2.py tests/test_contract_d3.py tests/test_contract_d4.py` -> `13 passed in 10.28s`
- `uv run pytest -q tests/test_main.py tests/test_daily_d5.py` -> initially `1 failed, 19 passed in 0.39s`, then green after the release-surface fixes
- `uv run pytest -q` -> `4824 passed, 1 warning in 134.38s (0:02:14)`
- repo-local contradiction scan helper -> not present; manual coherence check used across README, CHANGELOG, BUILD-REPORT, `pyproject.toml`, `agentkit_cli/__init__.py`, and `uv.lock`
- repo-local hygiene helper -> not present; explicit repo-only merge-marker/artifact scan ran clean after excluding `.venv`, `__pycache__`, and `.git`

**Next:** repo-status capture and final release summary.

---

## Release completion validation rerun — 2026-04-19

**Validated:**
- Focused contracts slice still passes on the audited `1.2.0` branch head.
- Full repo suite still passes from this repo after the audit commit.
- Repo-local contradiction/hygiene equivalent was rerun deterministically inside the project directory by scanning for unresolved merge markers after excluding `.git`, `.venv`, `__pycache__`, and `.pytest_cache`.

**Tests and checks:**
- `uv run pytest -q tests/test_contract_d1.py tests/test_contract_d2.py tests/test_contract_d3.py tests/test_contract_d4.py` -> `13 passed in 0.38s`
- `uv run pytest -q` -> `4824 passed, 1 warning in 129.15s (0:02:09)`
- merge-marker hygiene scan -> `0 findings`

**Next:** build/publish the missing `1.2.0` release surfaces, then reconcile the local release reports from "locally verified" to the final shipped truth.

---

## Release completion surfaces and chronology — 2026-04-19

**Completed:**
- Pushed `feat/v1.2.0-contracts` to `origin`, with the tested release commit `33dce29` carrying the shipped package/tag state.
- Built fresh `dist/agentkit_cli-1.2.0.tar.gz` and `dist/agentkit_cli-1.2.0-py3-none-any.whl` artifacts from this repo.
- Published `agentkit-cli==1.2.0` to PyPI and verified the live registry JSON plus both uploaded filenames.
- Created and pushed annotated tag `v1.2.0`, anchored to the shipped release commit `33dce29`.
- Advanced the branch with docs-only follow-up commit `85377a7` so the repo reports the final shipped chronology truthfully.
- Reconciled `BUILD-REPORT.md`, `BUILD-REPORT-v1.2.0.md`, and `CHANGELOG.md` so they now distinguish the shipped tag/PyPI commit from the later branch-head docs reconciliation commit.

**Direct proof:**
- `git rev-parse HEAD` -> `85377a738d51eede4753534f05a55f2c48287935`
- `git ls-remote --heads origin feat/v1.2.0-contracts` -> `85377a738d51eede4753534f05a55f2c48287935 refs/heads/feat/v1.2.0-contracts`
- `git rev-parse v1.2.0^{}` -> `33dce2998acfd7af79aeaa02a4234e0d8496f4e5`
- `git ls-remote --tags origin refs/tags/v1.2.0 refs/tags/v1.2.0^{}` -> annotated tag object plus peeled commit `33dce2998acfd7af79aeaa02a4234e0d8496f4e5`
- `https://pypi.org/pypi/agentkit-cli/1.2.0/json` -> version `1.2.0` live with `agentkit_cli-1.2.0-py3-none-any.whl` and `agentkit_cli-1.2.0.tar.gz`

**Next:** keep the repo clean with only the intentionally untracked repo-root contract markdown files remaining.
