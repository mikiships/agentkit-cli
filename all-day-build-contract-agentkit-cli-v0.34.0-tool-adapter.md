# All-Day Build Contract: agentkit-cli v0.34.0 — ToolAdapter + Golden Smoke Suite

Status: In Progress
Date: 2026-03-16
Owner: Codex execution pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Fix the M34 architectural debt: every agentkit-cli command hand-rolls its own quartet tool invocations (agentmd, agentlint, coderace, agentreflect), so the same flag-wiring bug keeps reappearing in new subcommands. This led to v0.16.1, v0.16.2, and multiple hotfix passes.

The fix is two-part:
1. **Centralized ToolAdapter** — all quartet tool invocations go through a single module with the canonical correct flags for each tool/operation.
2. **Golden smoke test suite** — one integration test that exercises each orchestration command against a real fixture Python project, catching any flag-wiring bug before release.

This contract is considered complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Full test suite must pass at the end (run `python3 -m pytest -q`).
4. New features must ship with docs and report addendum updates in the same pass.
5. CLI outputs must be deterministic and schema-backed where specified.
6. Never modify files outside the project directory (`~/repos/agentkit-cli/`).
7. Commit after each completed deliverable (not at the end).
8. If stuck on same issue for 3 attempts, stop and write a blocker report.
9. Do NOT refactor, restyle, or "improve" code outside the deliverables.
10. Read existing tests and docs before writing new code.

## 3. Context

### Current State (audit as of Mar 16)

`agentkit_cli/tools.py` — has `run_tool()`, `which()`, `get_version()`, `tool_status()`. Used by doctor.py for version checks but NOT consistently used for actual tool invocations.

`agentkit_cli/report_runner.py` — has some centralized functions: `run_agentlint_check()`, `run_agentmd_score()`, `run_coderace_bench()`, `run_agentreflect_analyze()`. But these are only used by the report command; other commands bypass them.

**Files with hand-rolled subprocess quartet calls (the problem locations):**
- `agentkit_cli/commands/suggest_cmd.py` — hand-rolls `agentlint check-context --json` and bare `agentlint --json`
- `agentkit_cli/commands/compare_cmd.py` — hand-rolls coderace calls
- `agentkit_cli/commands/setup_ci_cmd.py` — hand-rolls agentlint/coderace calls
- `agentkit_cli/doctor.py` — has its own invocation patterns
- `agentkit_cli/analyze.py` — hand-rolls quartet calls
- `agentkit_cli/composite.py` — orchestrates calls from multiple tools

### Canonical Correct Flags (reference for ToolAdapter)

These are the CORRECT flags that caused bugs when hand-rolled wrong:
```
agentlint check-context . --format json       ← --format json, NOT --json
agentmd score . --json                        ← --json ok here
agentmd generate --json                       ← fallback for score
coderace benchmark history --format json      ← --format json
agentreflect generate --from-git --format markdown
agentreflect generate --from-notes NOTES.md --format markdown
```

## 4. Feature Deliverables

### D1. Extend `agentkit_cli/tools.py` into a full ToolAdapter

Consolidate ALL canonical quartet invocations into `agentkit_cli/tools.py`. The file already has `run_tool()` but needs typed, documented adapter methods.

Add to `tools.py`:
```python
class ToolAdapter:
    """Single source of truth for all quartet tool invocations.
    
    Every command that calls agentmd/agentlint/coderace/agentreflect 
    MUST use these methods. Never hand-roll subprocess calls to these tools.
    """
    
    def agentlint_check_context(self, path: str) -> Optional[dict]:
        """agentlint check-context . --format json"""
        
    def agentlint_diff(self, diff_content: str, path: str) -> Optional[dict]:
        """agentlint <diff> --format json (for CI use)"""
        
    def agentmd_score(self, path: str) -> Optional[dict]:
        """agentmd score . --json (with fallback to agentmd generate --json)"""
        
    def agentmd_generate(self, path: str, minimal: bool = False) -> Optional[dict]:
        """agentmd generate [--minimal] --json"""
        
    def coderace_benchmark_history(self, path: str) -> Optional[dict]:
        """coderace benchmark history --format json"""
        
    def agentreflect_from_git(self, path: str) -> Optional[dict]:
        """agentreflect generate --from-git --format markdown"""
        
    def agentreflect_from_notes(self, path: str, notes_file: str) -> Optional[dict]:
        """agentreflect generate --from-notes <file> --format markdown"""
```

- [ ] Add `ToolAdapter` class to `agentkit_cli/tools.py` with all 7 methods above
- [ ] Each method includes timeout, error handling, and returns `Optional[dict]` (None on failure)
- [ ] `report_runner.py` functions delegate to ToolAdapter (keep backward-compatible signatures)
- [ ] Tests for each ToolAdapter method (mock subprocess calls)

### D2. Migrate all hand-rolled quartet invocations to ToolAdapter

Migrate every file identified in the audit above to use `ToolAdapter` instead of hand-rolled subprocess calls.

Files to migrate:
- `agentkit_cli/commands/suggest_cmd.py`
- `agentkit_cli/commands/compare_cmd.py`
- `agentkit_cli/commands/setup_ci_cmd.py`
- `agentkit_cli/doctor.py` (agentlint/agentmd calls only, NOT git/python3 calls)
- `agentkit_cli/analyze.py`
- `agentkit_cli/composite.py` (if any quartet calls)

Rules:
- Import `ToolAdapter` from `agentkit_cli.tools`
- Replace hand-rolled subprocess calls with adapter method calls
- Do NOT change any CLI interface, output format, or test expectations
- If a file's existing subprocess calls are for git/python/other non-quartet tools, leave them alone

- [ ] All 6 files migrated
- [ ] No new hand-rolled agentlint/agentmd/coderace/agentreflect subprocess calls outside tools.py
- [ ] All existing tests still pass after migration

### D3. Golden smoke test suite (`tests/test_smoke_integration.py`)

Create a minimal but complete integration test that exercises every orchestration command against a real fixture project. This catches flag-wiring bugs before release.

Fixture project: create `tests/fixtures/smoke_project/` — a minimal Python project with:
- `src/main.py` (a few functions)
- `tests/test_main.py` (a few tests)
- `CLAUDE.md` (a real context file, maybe 10 lines)
- `README.md`
- `pyproject.toml`

Smoke tests to add (`@pytest.mark.smoke`):
```python
def test_smoke_doctor()          # agentkit doctor → exit 0 or known codes
def test_smoke_score()           # agentkit score <fixture> → JSON with "score" key
def test_smoke_analyze()         # agentkit analyze <fixture> → score returned
def test_smoke_suggest()         # agentkit suggest <fixture> → no exception
def test_smoke_report()          # agentkit report <fixture> → produces HTML
def test_smoke_gate_pass()       # agentkit gate <fixture> --min-score 0 → exit 0
def test_smoke_gate_fail()       # agentkit gate <fixture> --min-score 200 → exit 1
def test_smoke_compare()         # agentkit compare HEAD HEAD <fixture> → no exception
def test_smoke_summary()         # agentkit summary → no exception (with mock history)
```

Requirements:
- Smoke tests must NOT require network access or real coderace/agentmd API calls — mock the ToolAdapter methods to return fixture JSON
- Tests run fast (< 30 seconds total)
- Add `pytest.mark.smoke` marker to each test
- Add `[tool:smoke]` section to `pyproject.toml` so `pytest -m smoke` runs only smoke suite
- Document: "Run `pytest -m smoke` before any release to catch flag-wiring bugs"

- [ ] `tests/fixtures/smoke_project/` created with realistic content
- [ ] `tests/test_smoke_integration.py` with all 9 smoke tests
- [ ] All smoke tests pass with `pytest -m smoke`
- [ ] pytest.ini_options updated with `smoke` marker registration

### D4. Release gate integration

Add a pre-release check: `agentkit release-check` (v0.27.0 feature) should now include a smoke suite pass as one of its checks.

Update `agentkit_cli/release_check.py`:
- Add a new check class `SmokeTestCheck` that runs `pytest -m smoke -q` in the project root
- Add it to the check list with severity "warning" (failing smoke = block release)
- Output: "Smoke tests: PASS (9/9)" or "Smoke tests: FAIL (X/9 failed)"

- [ ] `SmokeTestCheck` added to `release_check.py`
- [ ] `agentkit release-check` output includes smoke test result
- [ ] Tests for SmokeTestCheck (mock subprocess)

### D5. Docs, CHANGELOG, version bump to v0.34.0, BUILD-REPORT

- [ ] Update `CHANGELOG.md` with v0.34.0 entry (ToolAdapter, smoke suite, release-check integration)
- [ ] Update `README.md`: add "Architecture" note — "All quartet tool invocations go through ToolAdapter in tools.py. Run `pytest -m smoke` before any release."
- [ ] Bump version to `0.34.0` in `pyproject.toml`
- [ ] Write `BUILD-REPORT.md` with summary, test count, deliverable status
- [ ] Write `progress-log.md` after each deliverable

## 5. Test Requirements

- [ ] All existing 1281 tests still pass
- [ ] 20+ new tests for ToolAdapter methods (D1)
- [ ] Migration regression tests — verify each migrated command still produces correct output (D2)
- [ ] All 9 smoke tests pass (D3)
- [ ] SmokeTestCheck tests (D4)
- [ ] Final test count ≥ 1325

## 6. Stop Conditions

- All deliverables checked and all tests passing → DONE
- 3 consecutive failed attempts on same issue → STOP, write blocker report
- Scope creep detected (new requirements discovered) → STOP, report what's new
- Tests passing but deliverables remain → continue to next deliverable

## 7. Definition of Done

The M34 architectural debt is resolved when:
1. There is exactly ONE place in the codebase where quartet tool flags are defined (ToolAdapter)
2. There is a smoke suite that exercises the full orchestration layer
3. `agentkit release-check` now includes smoke pass as a blocking check
4. Full suite ≥ 1325 tests, all passing
