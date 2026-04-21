# All-Day Build Contract: agentkit-cli v1.22.0 release completion

Status: In Progress
Date: 2026-04-21
Owner: OpenClaw sub-agent execution pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Take the already-clean local `agentkit-cli v1.22.0 spec` branch from truthful `RELEASE-READY (LOCAL-ONLY)` to fully shipped truth, or stop with an exact blocker report. The concrete outcome is one release line whose four source-of-truth surfaces all agree: tests green, branch/tag pushed, PyPI live, and repo reports reconciled so future sessions inherit one coherent story for `agentkit-cli==1.22.0`.

This contract is complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when every checklist item below is checked.
3. Do not add product scope. This is release completion only.
4. Do not modify files outside `/Users/mordecai/repos/agentkit-cli-v1.22.0-spec` and the explicitly named workspace memory files in this contract.
5. Run the four-surface release checklist directly. Do not infer shipped state from local repo status alone.
6. Commit after each completed deliverable that changes the repo.
7. If stuck on the same blocker for 3 attempts, stop and write a blocker report.
8. Before trusting any release/status prose, run release recall and contradiction checks.
9. Keep tag truth separate from later docs-only chronology if reconciliation commits are needed.
10. No public-post drafting or outward messaging in this pass.

## 3. Deliverables

### D1. Pre-release truth sweep

Required:
- `BUILD-REPORT.md`
- `BUILD-REPORT-v1.22.0.md`
- `FINAL-SUMMARY.md`
- `progress-log.md`

- [ ] Run release recall for this repo before acting on release prose.
- [ ] Run contradiction scan and fix any conflicting shipped vs blocked/local-only wording before push/tag/publish.
- [ ] Confirm the repo is still clean and still truthfully local `RELEASE-READY (LOCAL-ONLY)` for `v1.22.0`.
- [ ] If any surface is stale, reconcile it before irreversible release steps.

### D2. Validation from the release tree

Required:
- focused spec slice
n- full suite
- hygiene check

- [ ] Re-run the focused `spec` validation slice from the current tree.
- [ ] Re-run the full suite from the current tree.
- [ ] Run the deterministic hygiene pass and resolve any non-intentional findings.
- [ ] If validation fails, fix the real failure path, rerun the affected checks, and keep the repo truthful.

### D3. Four-surface release completion

Required:
- git push
- annotated tag
- tag push
- PyPI publish
- live registry verification

- [ ] Push the release branch to origin.
- [ ] Create the annotated `v1.22.0` tag on the tested release commit.
- [ ] Push the tag to origin.
- [ ] Publish `agentkit-cli==1.22.0` to PyPI from this repo.
- [ ] Verify the PyPI project page and version JSON both show `1.22.0` live with wheel and sdist.

### D4. Post-release chronology reconciliation

Required:
- `BUILD-REPORT.md`
- `BUILD-REPORT-v1.22.0.md`
- `FINAL-SUMMARY.md`
- `progress-log.md`
- `/Users/mordecai/.openclaw/workspace/memory/WORKING.md`
- `/Users/mordecai/.openclaw/workspace/memory/temporal-facts.md`

- [ ] Reconcile repo report surfaces so they distinguish shipped tag truth from any later docs-only chronology commit.
- [ ] Append a final `progress-log.md` entry with the shipped commit, branch head, tag target, validation numbers, and registry proof.
- [ ] Update `memory/WORKING.md` so `active_build`, `last_shipped`, and the active-build section reflect shipped `v1.22.0` truth and the next slot is open.
- [ ] Update `memory/temporal-facts.md` with the new shipped line if it is used as a current-truth surface for `agentkit-cli` release state.

## 4. Test Requirements

- [ ] `python3 -m pytest -q tests/test_source_audit.py tests/test_source_audit_workflow.py tests/test_map.py tests/test_spec_cmd.py tests/test_spec_workflow.py tests/test_contract_d2.py tests/test_main.py`
- [ ] `uv run python -m pytest -q`
- [ ] `bash /Users/mordecai/.openclaw/workspace/scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.22.0-spec`
- [ ] PyPI project page and version JSON verified after publish

## 5. Reports

- Append progress to `progress-log.md` after each completed deliverable.
- Before trusting release/status prose, run `bash /Users/mordecai/.openclaw/workspace/scripts/pre-action-recall.sh release agentkit-cli /Users/mordecai/repos/agentkit-cli-v1.22.0-spec`.
- Run `bash /Users/mordecai/.openclaw/workspace/scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.22.0-spec` before irreversible release steps and again after chronology reconciliation if needed.
- If any managed-runner or tool anomaly creates contradictory release claims, log it via `bash /Users/mordecai/.openclaw/workspace/scripts/log-router-anomaly.sh ...` before cleanup.
- Final summary must say one of two things only: `SHIPPED` with the four surfaces proven, or `BLOCKED` with the exact blocker.

## 6. Stop Conditions

- All deliverables checked and four release surfaces proven -> DONE.
- 3 consecutive failed attempts on the same blocker -> STOP and write blocker report.
- Any irreversible release step succeeds while later proof is ambiguous -> STOP, verify source-of-truth surfaces, then reconcile prose before doing anything else.
- If publish is blocked by auth, network, or registry failure that cannot be resolved safely in-pass -> STOP and write the exact blocker.
