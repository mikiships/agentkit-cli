# All-Day Build Contract: agentkit-cli v0.97.2 optimize unblock and finalize

Status: In Progress
Date: 2026-04-18
Owner: Sub-agent execution pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Start from the last good optimize repo-surface commit (`4725cae`) where D1-D3 are complete, repair the stale pages/docs surface that blocks the full suite, and then finish the held-back D4 handoff for the optimize smoke-and-guardrails release candidate. The concrete outcome is a full green suite on top of the optimize work, plus the missing v0.97.2 docs/report/version handoff committed cleanly.

This contract is complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Full test suite must pass at the end.
4. Do not push, tag, publish, or touch GitHub/PyPI.
5. Never modify files outside `/Users/mordecai/repos/agentkit-cli-rc-v0.97.2-optimize-unblock`.
6. Keep scope tightly bounded to: pages/docs sync repair that unblocks tests, then the held-back v0.97.2 handoff files.
7. Commit after each completed deliverable, not just at the end.
8. If stuck on the same issue for 3 attempts, stop and write a blocker report.
9. Do not absorb unrelated repo cleanup, refactors, or feature work.
10. Read the blocker report, relevant page-sync tests, and the optimize smoke contract before changing code.
11. If `docs/index.html` is generated from another source, fix the source-of-truth path too. Do not paper over generated drift blindly.
12. Summarize findings in prose in `progress-log.md`, never paste raw command dumps.

## 3. Starting State

Known good optimize state:
- D1 commit: `b94dc94` (`Add optimize smoke harness`)
- D2 commit: `5f754bf` (`Guard optimize applies around protected sections`)
- D3 commit: `4725cae` (`Expand optimize repo-surface coverage`)

Known blocker:
- `uv run pytest -q` failed with 10 pages/docs assertions unrelated to optimize logic
- Failing surfaces: `tests/test_pages_refresh.py` and `tests/test_pages_sync_d4.py`
- Common root: stale `docs/index.html` content missing recently-scored fetch/render hooks, source badges, and scored-stat elements

Held-back handoff work:
- v0.97.2 D4 docs/report/version files were prepared in the previous pass but not committed because D4 requires a green full suite

## 4. Feature Deliverables

### D1. Diagnose and repair the pages/docs source of truth

Required files as needed:
- `docs/index.html`
- source generator/template files directly responsible for `docs/index.html`
- any narrow helper or script directly used for page generation

- [ ] Identify the true source of the stale `docs/index.html` drift
- [ ] Restore the missing recently-scored fetch/render behavior and scored stat elements expected by tests
- [ ] Restore the missing source-badge/community stat surface expected by tests
- [ ] Keep the repair minimal and consistent with the existing pages feature set
- [ ] Commit D1 once the pages/docs blocker tests pass

### D2. Validation sweep for the repaired pages surface

Required files:
- relevant tests only if expectations must be updated to match legitimate current behavior

- [ ] Run targeted pages/docs tests and get them green
- [ ] Run the optimize-focused smoke/regression targets again to ensure the repair did not regress optimize work
- [ ] Run the full suite and get it green
- [ ] Commit D2 only if the validation gates are satisfied

### D3. Finish the held-back v0.97.2 handoff

Required files:
- `progress-log.md`
- `BUILD-REPORT.md`
- `BUILD-REPORT-v0.97.2.md`
- `README.md`
- `CHANGELOG.md`
- `pyproject.toml`
- `agentkit_cli/__init__.py`

- [ ] Document the optimize smoke/guardrail claims and the pages/docs unblock note
- [ ] Add a concise `0.97.2` changelog entry
- [ ] Bump version to `0.97.2`
- [ ] Record focused test results and final full-suite result in the build report
- [ ] Commit D3 only after the full suite is green

## 5. Test Requirements

Minimum required validation sequence:
- [ ] `uv run pytest -q tests/test_pages_refresh.py tests/test_pages_sync_d4.py`
- [ ] `uv run pytest -q tests/test_optimize_smoke.py tests/test_optimize_d2_hardening.py tests/test_optimize_realworld.py tests/test_optimize_d4.py`
- [ ] `uv run pytest -q`

If additional focused tests are needed, run them, but do not skip the three gates above.

## 6. Reports

- Update `progress-log.md` after each deliverable
- Include what changed, what passed, what is next, and any blocker
- Final summary must include: deliverables completed, commit hashes, targeted test results, full-suite result, and whether v0.97.2 is now release-ready locally

## 7. Stop Conditions

- All deliverables checked and all tests passing -> DONE
- 3 consecutive failed attempts on the same issue -> STOP and write blocker report
- Scope creep detected beyond pages/docs unblock plus v0.97.2 handoff -> STOP and report it
- Full suite remains red for a second unrelated failure class after the pages repair -> STOP and document the new blocker precisely
