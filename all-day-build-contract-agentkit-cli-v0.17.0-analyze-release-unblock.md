# All-Day Build Contract: agentkit-cli v0.17.0 release unblock — watch debounce race

Status: In Progress
Date: 2026-03-14
Owner: Sub-agent repair pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Unblock the v0.17.0 `agentkit analyze` release by fixing the existing `agentkit watch` debounce race that causes the full suite to fail intermittently.

The observed failure is:
- `tests/test_watch.py::TestChangeHandler::test_debounce_resets_on_rapid_changes`
- Expected: 1 fire after rapid changes
- Observed: 2 fires (`file3.py`, `file4.py`)

This contract is complete only when the debounce logic is deterministic, the targeted watch tests pass repeatedly, and the full suite passes again without regressing the new analyze work.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Full test suite must pass at the end.
4. Do not change analyze feature scope except where required to keep v0.17.0 releasable.
5. Do not publish to PyPI.
6. Do not push to GitHub.
7. Do not modify files outside `/Users/mordecai/repos/agentkit-cli`.
8. If stuck on the same issue for 3 attempts, stop and write a blocker note.
9. Prefer root-cause fix over sleep-padding or test weakening.
10. Read the existing watch implementation and tests before editing.

## 3. Feature Deliverables

### D1. Root-cause diagnosis + deterministic debounce fix

Identify why cancelled timers can still fire during rapid modifications and implement a deterministic fix in the watch handler.

Likely acceptable approaches:
- generation/token check so stale timers no-op
- single worker/deadline pattern
- another thread-safe mechanism that guarantees only the latest event fires

Not acceptable:
- increasing sleeps in tests only
- loosening assertions to hide duplicate fires
- removing debounce behavior

Required files:
- `agentkit_cli/commands/watch.py`
- `tests/test_watch.py`

Checklist:
- [ ] Root cause identified in progress log
- [ ] Debounce logic changed to prevent stale timer fires
- [ ] Existing watch behavior preserved for normal use
- [ ] No test-only hacks

### D2. Regression coverage for the race

Strengthen tests so the failure mode is specifically covered and less timing-fragile.

Checklist:
- [ ] Existing failing test passes reliably
- [ ] Add or improve regression coverage for stale cancelled timer no-op behavior
- [ ] Keep tests deterministic and fast

### D3. Full-suite release unblock verification

Checklist:
- [ ] Targeted watch tests pass
- [ ] Full suite passes with `python3 -m pytest -q`
- [ ] `agentkit analyze` tests still pass
- [ ] BUILD-REPORT updated with unblock note or addendum
- [ ] progress-log updated with diagnosis, fix, and verification

## 4. Test Requirements

- [ ] `python3 -m pytest -q tests/test_watch.py`
- [ ] `python3 -m pytest -q tests/test_analyze.py`
- [ ] `python3 -m pytest -q`
- [ ] If the debounce fix introduces new branches, add focused tests for them

## 5. Reports

Update `progress-log.md` with:
- the exact failure observed
- the root cause
- what code changed
- what tests passed
- whether the repo is now release-ready

Update `BUILD-REPORT.md` with a short unblock addendum for v0.17.0.

## 6. Stop Conditions

- All deliverables checked and full suite passes -> DONE
- 3 consecutive failed attempts on same issue -> STOP and write blocker report
- Any regression in analyze behavior -> STOP and document it
- If a fix requires broader watch-command redesign beyond this scope -> STOP and explain the minimal next contract

## 7. Important Context

- Repo: `/Users/mordecai/repos/agentkit-cli`
- Current release candidate already includes v0.17.0 analyze work
- Full-suite failure observed during release verification, not during analyze tests
- Prior failure:
  - `AssertionError: assert 2 == 1`
  - duplicate calls from rapid changes in `test_debounce_resets_on_rapid_changes`
- Do not commit or publish; leave changes in the working tree with updated reports
