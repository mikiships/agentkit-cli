# Progress Log — agentkit-cli v0.34.0

## D1 — ToolAdapter class ✅
Added `ToolAdapter` class to `agentkit_cli/tools.py` with 7 methods covering all quartet invocations. Each method has canonical correct flags, timeout, error handling. `report_runner.py` refactored to delegate. 34 new tests.

## D2 — Migration ✅
Migrated `suggest_cmd.py`, `compare_cmd.py`, `doctor.py`, `analyze.py` to use ToolAdapter. Updated test mocking paths in `test_report.py` and `test_doctor.py`. All 1315 tests passing after migration.

## D3 — Golden smoke suite ✅
Created `tests/fixtures/smoke_project/` with minimal Python project. 9 smoke tests covering doctor, score, analyze, suggest, report, gate (pass/fail), compare, summary. All mock ToolAdapter. Registered `smoke` marker. `pytest -m smoke` runs in ~5s.

## D4 — Release gate integration ✅
Added `check_smoke_tests()` to `release_check.py`. Runs `pytest -m smoke -q`. Included in `run_release_check()` as blocking check. 6 new tests. Verdict computation updated to require smoke pass.

## D5 — Docs, version, reports ✅
- Version bumped to 0.34.0 in `pyproject.toml` and `__init__.py`
- CHANGELOG.md: v0.34.0 entry with Added/Changed/Fixed sections
- README.md: Architecture section added
- BUILD-REPORT.md and this progress-log.md written
- pytest fixtures excluded from collection via conftest.py

## Final: 1330 passed

## v0.36.0 — 2026-03-16 (agentkit org)

### D1: GitHub org/user repo listing + core org command
- `agentkit_cli/github_api.py`: list_repos() with pagination, rate-limit awareness, org→user fallback
- `agentkit_cli/commands/org_cmd.py`: OrgCommand + org_command, Rich progress, ranked table, --json
- `agentkit_cli/main.py`: org command registered
- Tests: 42 new tests (D1/D2/D3 coverage)

### D2: HTML report
- `agentkit_cli/org_report.py`: OrgReport.render(), dark-theme HTML, summary stats, --output, --share

### D3: Parallel analysis + rate limiting
- ThreadPoolExecutor (--parallel N), rate-limit headers, per-repo timeout, summary counts
- All implemented alongside D1

### D4: Docs, CHANGELOG, version bump
- README: Quick Start + Org Analysis section added
- CHANGELOG: v0.36.0 entry
- pyproject.toml + __init__.py: 0.35.0 / 0.34.0 → 0.36.0

### Final: 1391 passed (1349 pre-existing + 42 new), 0 failures
