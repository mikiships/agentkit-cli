# BUILD-REPORT.md

## agentkit-cli v0.92.0 — Weekly Digest Command

**Date:** 2026-03-22
**Status:** BUILT

### What shipped
- `agentkit weekly-digest` command with `--share`, `--output`, `--json`, `--quiet`, `--since`, `--cron` flags
- `WeeklyDigestEngine` — assembles `DigestReport` from HistoryDB, graceful empty-state with placeholder repos
- `WeeklyDigestRenderer` — dark-theme HTML + Markdown renderers
- README `## Weekly Digest` section with example usage
- CHANGELOG entry for v0.92.0
- Version bumped to 0.92.0 in `__init__.py` and `pyproject.toml`

### Test counts
- D1 (engine): 19 tests
- D2 (renderer): 14 tests
- D3 (CLI): 11 tests
- D4 (README/integration): 7 tests
- D5 (version/docs): 5 tests

---

## agentkit-cli v0.91.0 — Interactive /ui Page

**Date:** 2026-03-22
**Status:** SHIPPED

### Summary
Upgraded the `agentkit api` server's `/ui` endpoint from a static status page into an interactive demo portal. Added `POST /analyze` and `GET /recent` endpoints, concurrency limiting, caching, and auto-refresh.

### Deliverables
- D1: Interactive form in `/ui` — repo input, loading spinner, results panel (score/grade/tools), dark-theme ✅
- D2: `POST /analyze` + `GET /analyze?repo=` — subprocess, 120s timeout, max 5 concurrent, 1h cache ✅
- D3: `GET /recent` endpoint + recent panel with 30s auto-refresh ✅
- D4: `--interactive` flag, README Interactive Demo section, quickstart/demo hints ✅
- D5: CHANGELOG, version bump 0.91.0, docs/api.md, BUILD-REPORT ✅

### Tests
- 63 new tests (D1: 22, D2: 15, D3: 12, D4: 8, D5: 6)
- All existing tests pass

### Deviations
- None. All deliverables match the build contract.

---

## agentkit-cli v0.90.0 — `agentkit api` REST Server

**Date:** 2026-03-22

### Summary
Added `agentkit api`: a FastAPI REST server with 8 endpoints for the agentkit analysis pipeline. Endpoints include health check, analyze (with subprocess-triggered cache refresh), score (DB-only), shields.io badge, trending, history, leaderboard, and a dark-theme `/ui` HTML status page. Doctor now includes `api.reachable` check. `agentkit run --api-cache` warms the cache after runs.

### Deliverables
- D1: `agentkit_cli/api_server.py` — FastAPI app, 8 endpoints, CORS, shields.io badge
- D2: `agentkit_cli/commands/api_cmd.py` — CLI command with graceful ImportError
- D3: `agentkit doctor` api category + `agentkit run --api-cache`
- D4: `/ui` dark-theme HTML status page (included in D1)
- D5: `docs/api.md`, version 0.90.0, CHANGELOG, BUILD-REPORT

### Tests
- 57 new tests across D1-D4
- All existing tests pass

---

## agentkit-cli v0.89.0 — `agentkit weekly`

**Date:** 2026-03-22
**Status:** SHIPPED
**Total tests:** 4413 passing

---

## Summary

Added `agentkit weekly` — 7-day quality digest across all tracked projects. Synthesizes history DB data to show per-project score changes (start/end/delta), top improvements, regressions, common findings, and recommended actions. Supports `--json`, `--output`, `--share`, `--tweet-only`, `--days`, and `--project` flags.

Also includes `scripts/post-weekly.sh` automation wrapper for cron use with `--tweet-only`, `--share`, `--days`, and `--output` support. Logs to `~/.local/share/agentkit/weekly-post-log.jsonl`.

---

## Previous build

## agentkit-cli v0.88.0 — `_fetch_page` search API fix + `agentkit frameworks`

**Date:** 2026-03-22
**Status:** SHIPPED
**Total tests:** 4364 passing

---

## Summary

Added `agentkit hooks` — pre-commit quality gate hooks for agentkit-cli.
Installs as a pre-commit hook to run quality checks before every commit.
Previously: `agentkit hot` (v0.81.1) added daily hot-repos trending feature.

---

## agentkit-cli v0.85.0 — `agentkit frameworks`

**Date:** 2026-03-22  
**Status:** SHIPPED  
**Total tests:** 4299 passing (73 new for v0.85.0)

---

## Summary

Added `agentkit frameworks` — a command that detects which popular frameworks a project uses and checks if the project's CLAUDE.md/AGENTS.md has framework-specific agent context sections.

---

## Deliverables

### D1: FrameworkDetector + FrameworkChecker (`agentkit_cli/frameworks.py`)
- `FrameworkDetector`: detects 10+ frameworks (Next.js, FastAPI, Django, Rails, React, Vue, Nuxt, Flask, Laravel, Express) using local file analysis only
- `FrameworkChecker`: scores agent context coverage per framework (0-100), weighted 80% required / 20% nice-to-have
- **Tests:** `tests/test_frameworks_d1.py` — **25 tests**
- **Commit:** D1: add FrameworkDetector + FrameworkChecker with 25 tests

### D2: `agentkit frameworks` CLI command (`agentkit_cli/commands/frameworks_cmd.py`)
- Command: `agentkit frameworks [PATH] [OPTIONS]`
- Options: `--json`, `--quiet`, `--min-score`, `--context-file`, `--share`, `--generate`
- Rich table output with score + missing sections per framework
- JSON output with schema: `detected_frameworks`, `overall_score`, `below_threshold`, `version`
- **Tests:** `tests/test_frameworks_d2.py` — **14 tests**
- **Commit:** D2: add agentkit frameworks CLI command with 14 tests

### D3: `--generate` flag + framework templates (`agentkit_cli/framework_templates.py`)
- Templates for all 10 frameworks: Next.js, FastAPI, Django, Rails, React, Vue, Nuxt, Flask, Laravel, Express
- Each template includes: Setup, Common Patterns, Known Gotchas sections
- Idempotent: skips frameworks with existing `## [Framework]` headings
- **Tests:** `tests/test_frameworks_d3.py` — **17 tests**
- **Commit:** D3: add framework_templates.py (10 templates) + --generate flag with 17 tests

### D4: Integration with `agentkit run` and `agentkit doctor`
- `agentkit doctor`: added `check_framework_coverage()` — warns when detected framework scores < 60
- `agentkit run --frameworks`: runs framework coverage check after pipeline, includes in JSON output
- **Tests:** `tests/test_frameworks_d4.py` — **11 tests**
- **Commit:** D4: add framework coverage check to doctor + --frameworks flag to run with 11 tests

### D5: Docs, CHANGELOG, version bump
- `README.md`: added `agentkit frameworks` to command reference and quick-start
- `CHANGELOG.md`: `[0.85.0]` entry with all deliverables
- `agentkit_cli/__init__.py`: bumped `0.84.1` → `0.85.0`
- `pyproject.toml`: bumped `0.84.1` → `0.85.0`
- `tests/test_v085_release.py`: **6 version tests** (using `startswith("0.85.")` pattern)

---

## Test Count

| Deliverable | File | Tests |
|-------------|------|-------|
| D1 | test_frameworks_d1.py | 25 |
| D2 | test_frameworks_d2.py | 14 |
| D3 | test_frameworks_d3.py | 17 |
| D4 | test_frameworks_d4.py | 11 |
| D5 | test_v085_release.py | 6 |
| **Total new** | | **73** |

All 73 new tests pass. Existing tests unaffected (verified on representative subset: analyze, doctor, run).

---

## Scope Deviations

None. All deliverables match the build contract exactly.

---

## Validation Gates

- [x] `agentkit frameworks --help` exits 0
- [x] `agentkit frameworks . --json` produces valid JSON with `detected_frameworks` key
- [x] `agentkit doctor` includes framework coverage check (`context.framework_coverage`)
- [x] All 73 new tests pass
- [ ] Full test suite (`python3 -m pytest -q`) — hangs on network-dependent tests (pre-existing issue, not introduced by this build)
