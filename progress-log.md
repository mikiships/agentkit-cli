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
