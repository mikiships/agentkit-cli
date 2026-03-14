# Progress Log — agentkit-cli v0.17.0

## 2026-03-14

### D1 — Core analyze command ✅

Built:
- `agentkit_cli/analyze.py`: `parse_target()`, `analyze_target()`, `AnalyzeResult`
- `agentkit_cli/commands/analyze_cmd.py`: CLI wiring with Rich output
- `main.py`: registered `analyze` command

Issues encountered:
- `CompositeScoreEngine` raises `ValueError` when all tool scores are None (all tools skipped). Fixed with try/except, fallback to 0.0/F.

Tests: 25 new tests in `tests/test_analyze.py` — all pass.

### D2 — Output formatting ✅

- Rich table with color-coded grades
- `--json` produces correct schema, suppresses console prefix
- JSON omits `temp_dir`/`report_url` when None

### D3 — Error handling ✅

- git not installed: clear RuntimeError
- clone failure: 1 retry + 5s backoff, then RuntimeError
- tool failure isolation: each tool wrapped in try/except
- timeout: tool returns status="error", analysis continues
- temp dir cleanup in all paths via try/finally

### D4 — README + docs ✅

- README: `## Analyze Any Repo (Zero Setup)` section
- CHANGELOG: v0.17.0 entry
- Version bumped to 0.17.0 in pyproject.toml + __init__.py
- Existing version assertions in tests updated to "0.17"

### D5 — Build report ✅

- `BUILD-REPORT.md` written

## Final test count: 651 passed (626 + 25 new)

---

## 2026-03-14 — Watch debounce race fix (release unblock)

### Failure observed
`tests/test_watch.py::TestChangeHandler::test_debounce_resets_on_rapid_changes`
- Expected: 1 fire after 5 rapid file changes (debounce=0.1s, 0.02s apart)
- Observed: 2 fires (file3.py and file4.py both fired)

### Root cause
`threading.Timer.cancel()` only prevents the callback if it hasn't started executing yet. With a short debounce and rapid events, a timer thread can be past its cancellation check window when `cancel()` is called, causing the old timer's `_fire()` to still execute even after a new timer was started.

### Fix
Added a generation counter (`self._generation`) to `_ChangeHandler`. On each `on_modified`, the generation is incremented and captured in a closure (`_guarded_fire`). The timer callback checks the captured generation against the current one before calling `_fire()`. If the generation has advanced (a newer event superseded this one), the callback is a no-op.

Key design: the generation check runs in `_guarded_fire` (a closure), not in `_fire()` itself. This preserves the `_fire()` override contract for subclasses used in tests.

**Changed file:** `agentkit_cli/commands/watch.py`

### Verification
- `python3 -m pytest -q tests/test_watch.py` — 17 passed
- `python3 -m pytest -q tests/test_analyze.py` — all passed
- `python3 -m pytest -q` — **651 passed, 0 failed**

Repo is release-ready. ✅

---

## 2026-03-14 — v0.18.0 sweep

### D1 — Core sweep engine + CLI wiring ✅

Built:
- `agentkit_cli/sweep.py`: target-file loading, dedupe, sequential batch runner, per-target failure isolation, sweep result dataclasses
- `agentkit_cli/commands/sweep_cmd.py`: `agentkit sweep` command wiring with positional targets and `--targets-file`
- `agentkit_cli/main.py`: registered `sweep` command
- `tests/test_sweep.py`: D1 coverage for target resolution, dedupe, CLI registration, and mixed success/failure batches

Tests:
- `python3 -m pytest -q tests/test_sweep.py` — 7 passed
- `python3 -m pytest -q tests/test_main.py` — 6 passed

Remains:
- D2 ranked Rich table, sorting controls, limit handling
- D3 JSON batch schema and deterministic machine output
- D4 docs/version/report updates and full release validation

Blockers:
- Sandbox cannot write inside `.git`, so the required D1 commit could not be created. Failed attempts:
  - `git add ...` -> `fatal: Unable to create '.git/index.lock': Operation not permitted`
  - `touch .git/codex-write-test` -> `Operation not permitted`
  - `git commit --allow-empty ...` -> `fatal: Unable to create '.git/index.lock': Operation not permitted`
