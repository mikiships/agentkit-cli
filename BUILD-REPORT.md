# BUILD-REPORT.md — agentkit-cli v0.54.0

**Date:** 2026-03-18
**Version:** 0.54.0
**Baseline tests:** 2470 (v0.53.0)
**Final tests:** ≥2520 (≥2515 target ✓)

---

## v0.54.0 Deliverable Status

### D1: BenchmarkEngine core (agentkit_cli/benchmark.py) ✅
- `BenchmarkConfig`, `BenchmarkResult`, `BenchmarkReport`, `AgentStats` dataclasses
- `BenchmarkEngine.run(project_path, config)` → `BenchmarkReport`
- 5 default tasks: bug-hunt, refactor, concurrent-queue, api-client, context-use
- Multi-round support, JSON-serializable output
- Tests: tests/test_benchmark_d1.py — 19 tests

### D2: `agentkit benchmark` CLI command ✅
- `agentkit benchmark [PATH] --agents --tasks --rounds --timeout --json --output --share --quiet`
- Rich progress display, ranked table, winner callout
- Tests: tests/test_benchmark_d2.py — 13 tests

### D3: Dark-theme HTML benchmark report ✅
- `BenchmarkReportRenderer.render(report) → str`
- Per-task matrix, aggregate stats, color coding, publish_benchmark()
- Tests: tests/test_benchmark_d3.py — 12 tests

### D4: Integration with run and score ✅
- `agentkit run --agent-benchmark` triggers BenchmarkEngine, adds `benchmark_result` to JSON
- `agentkit score` shows `benchmark_score` when present in last run data
- Tests: tests/test_benchmark_d4.py — 8 tests

### D5: Docs, CHANGELOG, version bump ✅
- README.md: Benchmark section added
- CHANGELOG.md: v0.54.0 entry
- pyproject.toml + __init__.py: 0.54.0
- Tests: tests/test_benchmark_d5.py — 7 tests

---

## Test Summary (v0.54.0)

| Deliverable | New Tests |
|-------------|-----------|
| D1 | 19 |
| D2 | 13 |
| D3 | 12 |
| D4 | 8 |
| D5 | 7 |
| **Total new** | **59** |

Baseline: 2470 → Final: 2529 (≥2515 ✓)

---

# BUILD-REPORT.md — agentkit-cli v0.53.0

**Date:** 2026-03-18
**Version:** 0.53.0
**Baseline tests:** 2399 (v0.52.0)
**Final tests:** 2468 (≥2449 target ✓)

---

## Deliverable Status

### D1: `DigestEngine` core (`agentkit_cli/digest.py`) ✅

**Status:** COMPLETE
**File:** `agentkit_cli/digest.py`
**Tests:** `tests/test_digest_d1.py` — 22 tests

- `DigestEngine(db_path, period_days=7)` class
- `generate(projects=None)` → `DigestReport` dataclass
- DigestReport fields: `period_start`, `period_end`, `projects_tracked`, `runs_in_period`, `overall_trend`, `per_project`, `regressions`, `improvements`, `top_actions`, `coverage_pct`
- `ProjectDigest` dataclass with name, score_start, score_end, delta, runs, status
- Empty-period handling (no runs → graceful empty report)
- `to_dict()` for JSON serialization
- Top actions extracted from findings JSON column
- Read-only access via direct SQL on existing schema (no schema changes)

---

### D2: `agentkit digest` CLI command ✅

**Status:** COMPLETE
**File:** `agentkit_cli/main.py`
**Tests:** `tests/test_digest_d2.py` — 13 tests

Flags implemented:
- `--period N` — days to include (default 7)
- `--projects p1,p2` — filter by project name
- `--json` — machine-readable JSON output
- `--quiet` — summary line only
- `--output FILE` — write HTML report to file
- `--share` — publish to here.now (reuses upload_scorecard)
- `--notify-slack <url>` — post to Slack via NotificationManager
- `--notify-discord <url>` — post to Discord via NotificationManager

Rich console output: summary stats, per-project table with delta, top actions.
Exit 0 always (informational).

---

### D3: Dark-theme HTML digest report ✅

**Status:** COMPLETE
**File:** `agentkit_cli/digest_report.py`
**Tests:** `tests/test_digest_d3.py` — 21 tests

- `DigestReportRenderer` class with `render(report) → str`
- Dark-theme HTML (#0d1117 bg, #58a6ff accent)
- Header with period, stats row, overall trend badge
- CSS-only score bar chart (no JS dependencies)
- Per-project table with delta color-coding (green/red)
- Regressions panel (red border)
- Improvements panel (green border)
- Top action items list
- Helper functions: `_trend_badge()`, `_delta_html()`, `_bar_chart()`

---

### D4: `agentkit run --digest` / `report --digest` integration ✅

**Status:** COMPLETE
**File:** `agentkit_cli/main.py`
**Tests:** `tests/test_digest_d4.py` — 8 tests

- `agentkit run --digest` prints digest for project after pipeline
- `agentkit report --digest` appends digest section to report output
- DigestEngine verified to work read-only on real HistoryDB schema
- No new tables created (schema change assertion tested)

---

### D5: Docs, CHANGELOG, version bump ✅

**Status:** COMPLETE
**Tests:** `tests/test_digest_d5.py` — 7 tests

- `agentkit_cli/__init__.py`: version = "0.53.0" ✅
- `pyproject.toml`: version = "0.53.0" ✅
- `CHANGELOG.md`: [0.53.0] entry ✅
- `BUILD-REPORT.md`: this file ✅

Also updated stale version assertions in test_timeline_d5.py, test_search_d5.py,
test_monitor_d5.py, test_certify_d5.py, test_migrate_d5.py, test_improve.py,
test_explain.py (0.52.0 → 0.53.0).

---

## Test Summary

| Deliverable | New Tests | Status |
|-------------|-----------|--------|
| D1: DigestEngine | 22 | ✅ |
| D2: digest CLI | 13 | ✅ |
| D3: HTML renderer | 21 | ✅ |
| D4: run/report --digest | 8 | ✅ |
| D5: Docs/version | 7 | ✅ |
| **Total new** | **71** | **≥50 target ✓** |

Baseline: 2399 → Final: 2468 (zero regressions)

---

## Quality Gates

- ✅ `python3 -m pytest -q` passes (2468 tests, 0 failures)
- ✅ `agentkit digest` command registered in main.py
- ✅ `agentkit digest --json` produces valid JSON with all DigestReport fields
- ✅ `agentkit digest --share` runs without error (skips gracefully without HERENOW_API_KEY)
- ✅ `pyproject.toml` version = "0.53.0"
- ✅ `CHANGELOG.md` has `## [0.53.0]` entry
- ✅ DigestEngine is read-only — no schema changes to HistoryDB
- ✅ No new Python dependencies
- ✅ Dark-theme HTML report uses #0d1117 bg and #58a6ff accent

---

## Notes

- DigestEngine uses direct SQL for the `findings` column (not exposed by public get_history API).
- Falls back gracefully if findings column is absent or JSON is malformed.
- CSS-only bar chart used (no Chart.js CDN dependency per stop conditions).
