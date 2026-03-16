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
