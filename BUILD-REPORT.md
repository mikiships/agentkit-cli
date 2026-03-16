# BUILD-REPORT: agentkit-cli v0.34.0

## Summary

Resolved M34 architectural debt: centralized all quartet tool invocations into a single ToolAdapter class, added a golden smoke test suite, and integrated smoke tests into the release-check pipeline.

## Deliverables

| # | Deliverable | Status |
|---|-------------|--------|
| D1 | ToolAdapter class in tools.py | ✅ Complete |
| D2 | Migrate all hand-rolled quartet calls | ✅ Complete |
| D3 | Golden smoke test suite (9 tests) | ✅ Complete |
| D4 | SmokeTestCheck in release_check.py | ✅ Complete |
| D5 | Docs, CHANGELOG, version bump, reports | ✅ Complete |

## Test Results

- **Total tests:** 1330 passed
- **New tests:** 49 (34 ToolAdapter + 9 smoke + 6 SmokeTestCheck)
- **Existing tests:** 1281 (all passing, no regressions)
- **Requirement:** >= 1325 ✅

## Files Changed

- `agentkit_cli/tools.py` — added ToolAdapter class (7 methods + helpers)
- `agentkit_cli/report_runner.py` — delegates to ToolAdapter
- `agentkit_cli/commands/suggest_cmd.py` — migrated to ToolAdapter
- `agentkit_cli/commands/compare_cmd.py` — migrated to ToolAdapter
- `agentkit_cli/doctor.py` — migrated check_context_freshness
- `agentkit_cli/analyze.py` — migrated pipeline steps
- `agentkit_cli/release_check.py` — added check_smoke_tests
- `tests/test_tool_adapter.py` — 34 new tests
- `tests/test_smoke_integration.py` — 9 smoke tests
- `tests/test_release_check.py` — 6 new SmokeTestCheck tests
- `tests/test_report.py` — updated mock paths
- `tests/test_doctor.py` — updated mock paths
- `tests/fixtures/smoke_project/` — fixture project
- `CHANGELOG.md` — v0.34.0 entry
- `README.md` — Architecture section
- `pyproject.toml` — version bump + pytest markers

ALL DELIVERABLES COMPLETE. Tests: 1330 passed.

---

## v0.35.0 Addendum — agentkit quickstart

**Date:** 2026-03-16
**Contract:** all-day-build-contract-agentkit-cli-v0.35.0-quickstart.md

### Deliverables

| # | Deliverable | Status |
|---|-------------|--------|
| D1 | `agentkit_cli/commands/quickstart_cmd.py` core command + 19 tests | ✅ Complete |
| D2 | `agentkit_cli/main.py` wiring + quickstart prominent in help | ✅ Complete |
| D3 | README Quick Start + Commands section updated | ✅ Complete |
| D4 | Show HN draft updated with quickstart as primary onboarding command | ✅ Complete |
| D5 | CHANGELOG v0.35.0, version bump, BUILD-REPORT addendum | ✅ Complete |

### Validation Gates

- [x] `python3 -m pytest -q` passes (1349 tests, no regressions)
- [x] `agentkit quickstart --help` exits 0
- [x] New tests: 19 (requirement: 15+)
- [x] Version in pyproject.toml = "0.35.0"
- [x] CHANGELOG has v0.35.0 entry
- [x] BUILD-REPORT.md has v0.35.0 addendum
- [x] Show HN draft updated with `agentkit quickstart` as primary onboarding command

### Test Results

- **Total tests:** 1349 passed (up from 1330)
- **New tests:** 19 (all in tests/test_quickstart.py)
- **Regressions:** 0

### Files Changed

- `agentkit_cli/commands/quickstart_cmd.py` — new quickstart command
- `agentkit_cli/main.py` — quickstart registered + listed first
- `tests/test_quickstart.py` — 19 new tests
- `README.md` — quickstart elevated as onboarding entry point
- `CHANGELOG.md` — v0.35.0 entry
- `pyproject.toml` — version bump to 0.35.0
- `/Users/mordecai/.openclaw/workspace/memory/drafts/show-hn-quartet.md` — updated (external)

ALL DELIVERABLES COMPLETE. Status: BUILT (local, not published to PyPI).
