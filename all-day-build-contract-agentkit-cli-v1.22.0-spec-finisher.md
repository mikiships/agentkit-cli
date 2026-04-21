# All-Day Build Contract: agentkit-cli v1.22.0 spec finisher

Status: In Progress
Date: 2026-04-21
Owner: Codex execution pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Finish `agentkit-cli v1.22.0 spec` from its current truthful midpoint. D1 through D3 are already landed locally. The remaining job is to close D4 without fiction: reconcile docs and release surfaces, run the required validation from the current tree, fix anything the real validation exposes, and leave the repo either truthfully `RELEASE-READY (LOCAL-ONLY)` for `v1.22.0` or stopped with an exact blocker report. The concrete outcome is a clean local repo whose status files match the actual code and tests for the new `source -> audit -> map -> spec -> contract` lane.

This contract is complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when every checklist item below is checked.
3. Treat D1 through D3 as already done unless real validation proves otherwise. Do not reopen scope gratuitously.
4. No push, tag, publish, or remote mutation in this pass.
5. Do not modify files outside `/Users/mordecai/repos/agentkit-cli-v1.22.0-spec`.
6. Commit after each completed deliverable, not just at the end.
7. If stuck on the same blocker for 3 attempts, stop and write a blocker report.
8. Read existing docs/tests/status files before editing them.
9. Do not add new product features beyond what is needed to make `agentkit spec` truthful, tested, and locally release-ready.
10. Before any final status claim, verify tests and repo surfaces directly from this repo.

## 3. Feature Deliverables

### D1. Reconcile release surfaces to v1.22.0 truth

Required:
- `BUILD-REPORT.md`
- `BUILD-REPORT-v1.22.0.md`
- `FINAL-SUMMARY.md`
- `progress-log.md`
- any version/docs surface needed to keep status truthful

- [ ] Read the current repo state and keep only truthful `v1.22.0` local-build language in the active report surfaces.
- [ ] Ensure `BUILD-REPORT.md`, `BUILD-REPORT-v1.22.0.md`, and `FINAL-SUMMARY.md` agree on status, scope, supported lane, and exact remaining claim (`VALIDATING` vs `RELEASE-READY (LOCAL-ONLY)`).
- [ ] Keep explicit mention that no push/tag/publish happened in this pass.
- [ ] Preserve older-format compatibility expectations used by tests where needed, but do not carry stale `v1.21.0` shipped prose forward.

### D2. Real validation from the current tree

Required:
- focused validation rerun
n- full-suite rerun
- contradiction check
- hygiene check or equivalent note

- [ ] Run release recall and contradiction checks before trusting prose.
- [ ] Re-run the focused `spec` validation slice from the current tree and update surfaces if numbers changed.
- [ ] Run the full suite from the current tree.
- [ ] If validation exposes real defects, fix them and re-run the affected checks until the repo is either honestly green or honestly blocked.

### D3. Truthful local closeout

Required:
- clean or intentionally explained working tree
- final report surfaces
- blocker report if needed

- [ ] Leave the repo either truthfully `RELEASE-READY (LOCAL-ONLY)` for `v1.22.0` or stopped with an exact blocker report naming the failing path.
- [ ] Append a final `progress-log.md` entry summarizing what changed, exact validation outcomes, and the final repo truth.
- [ ] Remove transient noise like `.agentkit-last-run.json` if it is only a runner artifact, or explain why it is intentional.
- [ ] If release-ready, ensure the final surfaces record the exact supported lane: `source -> audit -> map -> spec -> contract`.

## 4. Test Requirements

- [ ] `python3 -m pytest -q tests/test_source_audit.py tests/test_source_audit_workflow.py tests/test_map.py tests/test_spec_cmd.py tests/test_spec_workflow.py tests/test_contract_d2.py tests/test_main.py`
- [ ] `uv run python -m pytest -q`
- [ ] Status/conflict scan clean, or exact contradiction fixed and rechecked.
- [ ] Any test failures introduced during closeout are fixed before completion claims.

## 5. Reports

- Append progress to `progress-log.md` after each completed deliverable.
- Before trusting release/status prose, run `bash /Users/mordecai/.openclaw/workspace/scripts/pre-action-recall.sh release agentkit-cli /Users/mordecai/repos/agentkit-cli-v1.22.0-spec`.
- Run `bash /Users/mordecai/.openclaw/workspace/scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.22.0-spec`.
- Run `bash /Users/mordecai/.openclaw/workspace/scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.22.0-spec` before final summary if available.
- If a required command fails for environmental reasons, note the exact failure and continue with an equivalent direct verification path.
- Final summary must say one of two things only: `RELEASE-READY (LOCAL-ONLY)` with supporting evidence, or `BLOCKED` with the exact blocker.

## 6. Stop Conditions

- All deliverables checked and repo left truthfully local release-ready -> DONE.
- 3 consecutive failed attempts on the same blocker -> STOP and write blocker report.
- Any mismatch between tests and status surfaces that cannot be reconciled safely -> STOP and report the exact mismatch.
- If the repo cannot reach local release-ready without new product scope, STOP and write the exact scope gap instead of improvising.
