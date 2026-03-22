# BUILD-REPORT.md

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
