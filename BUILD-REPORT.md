# BUILD-REPORT.md — agentkit-cli v0.17.0

**Date:** 2026-03-14  
**Builder:** Claude (subagent)  
**Version bump:** 0.16.2 → 0.17.0  
**All tests passing:** 651 (626 original + 25 new)

---

## What Was Built

### D1 — Core `agentkit analyze` command

**New files:**
- `agentkit_cli/analyze.py` — `AnalyzeResult` dataclass + `analyze_target()` function + `parse_target()` helper
- `agentkit_cli/commands/analyze_cmd.py` — CLI wiring with Rich table output
- `agentkit_cli/main.py` — registered `@app.command("analyze")`

**Target parsing supported:**
- `github:owner/repo` → `https://github.com/owner/repo.git`
- `https://github.com/owner/repo[.git]` → normalized URL
- `owner/repo` (bare shorthand, exactly one slash, no spaces) → GitHub shorthand
- `./local`, `/abs`, `~/home` → local path, no clone

**Pipeline:**
1. `agentmd generate .` (unless `--no-generate` or context already exists)
2. `agentmd score .`
3. `agentlint check-context --format json`
4. `agentreflect generate .`
5. Composite score via `CompositeScoreEngine` (graceful fallback to 0.0/F when all tools skipped)

**Options implemented:**
- `--json` — machine-readable JSON (suppresses Rich console prefix)
- `--keep` — keep temp clone dir, include path in output/JSON
- `--publish` — publish HTML report to here.now (best-effort, doesn't abort on failure)
- `--timeout N` — clone + analysis timeout (default: 120s)
- `--no-generate` — skip agentmd generate

### D2 — Output formatting + JSON schema

Rich table: Tool | Status | Score | Key Finding  
Headline: `Agent Quality Score: X/100 (Grade)  repo: owner/repo`  
Color-coded grades (A/B=green, C=yellow, D/F=red)  
JSON schema matches spec exactly; `temp_dir`/`report_url` omitted when None.

### D3 — Error handling + graceful degradation

- Git not installed → `RuntimeError: git is not installed` with install hint
- Clone failure → `RuntimeError` with stderr, temp dir cleaned
- 1 retry with 5s backoff on clone
- Individual tool failure isolation (each tool wrapped in try/except, status="error", analysis continues)
- Timeout on tool → status="error", analysis continues with partial results
- `CompositeScoreEngine` ValueError (all tools skipped) → caught, returns 0.0/F
- All error paths use try/finally for temp dir cleanup

### D4 — README + docs update

- `README.md`: new `## Analyze Any Repo (Zero Setup)` section with examples, option list, and JSON schema
- `CHANGELOG.md`: v0.17.0 entry with full feature list
- `pyproject.toml`: version → 0.17.0
- `agentkit_cli/__init__.py`: `__version__` → 0.17.0
- `tests/test_main.py` + `tests/test_leaderboard.py`: version assertion updated from "0.16" to "0.17"

### D5 — Tests

**New test file:** `tests/test_analyze.py` — 25 tests

| Category | Tests |
|----------|-------|
| Target URL parsing (github:, https://, bare owner/repo, local paths, invalid) | 9 |
| Mock clone (remote target invokes git clone, local path skips mkdtemp) | 2 |
| Mock pipeline (all tools skipped, all pass, no_generate) | 3 |
| JSON output schema (required fields, temp_dir inclusion) | 2 |
| Rich table output | 1 |
| Error handling (git missing, clone failure exit code, tool timeout, temp dir cleanup) | 5 |
| AnalyzeResult.to_dict() schema | 3 |

---

## Deviations from Plan

1. **CompositeScoreEngine ValueError handling** — the engine raises `ValueError` when all tool scores are None. Not called out in the build contract. Added try/except to return score=0.0, grade="F" rather than crash. Correct behavior per D3 (graceful degradation).

2. **Version bump of existing test assertions** — `test_main.py` and `test_leaderboard.py` both had `assert "0.16" in result.output` which broke after version bump. Updated to "0.17" as required.

3. **JSON output console prefix** — the `--json` flag suppresses the "cloning…" console line to ensure stdout is pure JSON. Ensures `json.loads(result.output)` works in tests and pipelines.

---

## Follow-up Items

- `--publish` is best-effort and silently skips if `here.now` is unavailable or no report HTML exists. A future pass could generate a fresh HTML report from the analysis result before publishing.
- `agentreflect generate <path>` may need `--from-notes` or similar flags depending on tool version; the current implementation passes the work_dir as positional arg (matches `run_cmd.py` pattern).
- The composite score with all tools skipped returns 0.0/F which is technically correct but could be improved to show "N/A" when no tools are installed at all.

---

## Test Counts

| Suite | Count |
|-------|-------|
| Pre-build (existing) | 626 |
| New (test_analyze.py) | 25 |
| **Total passing** | **651** |

All 651 tests pass. No previously passing tests broken.

---

## Release Unblock Addendum — Watch Debounce Race (2026-03-14)

**Blocking failure:** `tests/test_watch.py::TestChangeHandler::test_debounce_resets_on_rapid_changes` (2 fires observed, 1 expected)

**Root cause:** `threading.Timer.cancel()` is not race-free. A timer thread that has already begun executing ignores subsequent `cancel()` calls, allowing stale timers to fire after a newer timer was started.

**Fix:** Generation counter in `_ChangeHandler`. Each `on_modified` call increments `_generation` and wraps the callback in a `_guarded_fire` closure that checks the captured generation before dispatching to `_fire()`. Stale timer callbacks silently no-op.

**Files changed:** `agentkit_cli/commands/watch.py` only.

**Post-fix verification:**
- `python3 -m pytest -q tests/test_watch.py` → 17 passed
- `python3 -m pytest -q` → **651 passed, 0 failed**

v0.17.0 is release-ready. ✅
