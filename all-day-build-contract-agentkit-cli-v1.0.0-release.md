# All-Day Build Contract: agentkit-cli v1.0.0 release completion

Status: In Progress
Date: 2026-04-19
Owner: OpenClaw sub-agent execution pass
Scope type: Deliverable-gated release completion

## 1. Objective

Take the already-built `agentkit-cli` v1.0.0 canonical source kit in `/Users/mordecai/repos/agentkit-cli-v1.0.0-canonical-source-kit` from local release-ready state to one verified final truth. The repo currently has contradictory chronology risk: `memory/WORKING.md` says push, tag, and publish have not started, while local HEAD is `3685aab` with message `docs: record v1.0.0 shipped release`. This pass must verify source-of-truth release surfaces, complete any missing ones, and leave the repo and reports telling one coherent story.

This contract is complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Full test suite must pass at the end before any final shipped claim.
4. Docs, reports, and chronology must be updated in the same pass as release actions.
5. Never modify files outside this repo except the required workspace recall/check scripts and standard git/PyPI side effects.
6. Commit after each completed deliverable, not only at the end.
7. If stuck on the same issue for 3 attempts, stop and write a blocker report.
8. Do not refactor unrelated code.
9. Read existing release docs/tests before mutating release state.
10. Summarize tool output in prose inside reports, do not paste raw command dumps.
11. Treat any existing shipped/blocker contradiction as untrusted until verified against tests, git refs, and PyPI.

## 3. Feature Deliverables

### D1. Release truth audit + contradiction scan

Establish the real current state before acting.

Required:
- `BUILD-REPORT.md`
- `BUILD-REPORT-v1.0.0.md`
- `progress-log.md`
- `CHANGELOG.md`

- [ ] Run `bash /Users/mordecai/.openclaw/workspace/scripts/pre-action-recall.sh release agentkit-cli /Users/mordecai/repos/agentkit-cli-v1.0.0-canonical-source-kit`
- [ ] Run `bash /Users/mordecai/.openclaw/workspace/scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.0.0-canonical-source-kit`
- [ ] Verify local git truth: branch, HEAD, status, tags, and whether target branch/tag already exist on origin
- [ ] Verify registry truth directly from PyPI for `agentkit-cli==1.0.0`
- [ ] Write a short prose audit to `progress-log.md` stating what is already true vs still missing

### D2. Validation + hygiene gate

Confirm the repo is genuinely releaseable from the real runtime path.

Required:
- `tests/`
- `pyproject.toml`

- [ ] Run the focused canonical-source slice used by the build (`tests/test_context_projections.py tests/test_source_cmd.py tests/test_project_cmd.py tests/test_sync_projections.py tests/test_init_projections.py tests/test_init.py`)
- [ ] Run the full test suite
- [ ] Run `bash /Users/mordecai/.openclaw/workspace/scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.0.0-canonical-source-kit`
- [ ] If any failure or contradiction appears, resolve it before any shipped claim
- [ ] Record exact passing test counts and any hygiene findings in `progress-log.md`

### D3. Git release surfaces

If missing, complete the GitHub-facing release surfaces for v1.0.0.

Required:
- git branch/tag state
- repo release docs

- [ ] Push the correct release branch/commit to origin if not already present
- [ ] Create or verify the `v1.0.0` tag on the correct tested commit
- [ ] Push the tag if missing remotely
- [ ] Confirm the exact remote branch/tag refs now point to the intended commit
- [ ] Commit any chronology/report fixes needed after git release actions

### D4. PyPI release surface

If missing, publish `agentkit-cli==1.0.0` and verify it live.

Required:
- `dist/`
- PyPI project page / version JSON

- [ ] Build wheel and sdist cleanly from this repo
- [ ] Publish via the supported local path if the version is not already live
- [ ] Verify `https://pypi.org/pypi/agentkit-cli/1.0.0/json` shows both artifacts
- [ ] If PyPI already had 1.0.0 live before this pass, do not republish, just record that truth with proof
- [ ] If publishing/auth fails after 3 attempts, stop and write a blocker report instead of bluffing a shipped state

### D5. Final chronology reconciliation

Leave the repo telling one truthful final state and nothing contradictory.

Required:
- `BUILD-REPORT-v1.0.0.md`
- `BUILD-REPORT.md`
- `progress-log.md`
- `README.md` and `CHANGELOG.md` only if they truly need release-state updates

- [ ] Reconcile all release docs so they agree on BUILT, RELEASE-READY, or SHIPPED based on the verified four-surface checklist
- [ ] Ensure any pre-existing false shipped claim is corrected if the release is not actually complete
- [ ] Final summary in `progress-log.md` includes: tests, branch ref, tag ref, PyPI status, blockers if any
- [ ] Leave `git status` clean

## 4. Test Requirements

- [ ] Focused canonical-source slice passes
- [ ] Full suite passes
- [ ] Edge cases checked: pre-existing false shipped prose, remote branch missing, remote tag missing, PyPI already live, PyPI auth failure, dirty worktree risk
- [ ] All existing tests still pass after chronology cleanup

## 5. Reports

- Write progress to `progress-log.md` after each deliverable
- Include what was built or verified, what tests pass, what remains, and any blockers
- Before trusting any release/status narrative, run the recall and contradiction checks in D1 first
- Before final summary, run the hygiene check in D2 and clean or explain findings
- If a routed runner or intermediary produced impossible shipped/blocker claims during this pass, log it with `/Users/mordecai/.openclaw/workspace/scripts/log-router-anomaly.sh`

## 6. Stop Conditions

- All deliverables checked and all tests passing -> DONE
- 3 consecutive failed attempts on same issue -> STOP, write blocker report
- Scope creep detected -> STOP and report the new requirement
- PyPI or git auth unavailable -> STOP with a concrete blocker report after verifying which release surfaces remain missing
- If all four release surfaces were already complete at the start, do only chronology reconciliation and stop once docs match the verified truth
