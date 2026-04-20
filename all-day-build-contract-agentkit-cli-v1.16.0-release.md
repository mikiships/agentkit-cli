# All-Day Build Contract: agentkit-cli v1.16.0 release completion

Status: In Progress
Date: 2026-04-20
Owner: OpenClaw sub-agent execution pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Take the already validated local `agentkit-cli v1.16.0 reconcile` branch from truthful `RELEASE-READY` to truthful `SHIPPED` by completing the four-surface release checklist from this repo. The product work is done. This pass is only allowed to succeed if tests stay green, the branch and tag land on origin, PyPI `agentkit-cli==1.16.0` is live, and the repo’s report surfaces are reconciled so the shipped commit, branch chronology head, and registry state all tell one coherent story.

This contract is complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Full release truth requires all four surfaces: tests green, push confirmed, tag confirmed, registry live.
4. Never claim `SHIPPED` from local repo state alone.
5. Never modify files outside `/Users/mordecai/repos/agentkit-cli-v1.16.0-reconcile-lanes`.
6. Commit after each completed deliverable that mutates repo state.
7. If stuck on the same issue for 3 attempts, stop and write a blocker report.
8. Do not refactor product code or add features. This is release completion only.
9. Read the current `BUILD-REPORT.md`, `FINAL-SUMMARY.md`, `progress-log.md`, and version metadata before changing anything.
10. If push/tag/publish succeed but chronology/report cleanup remains, finish the cleanup instead of stopping at half-true shipped state.
11. Before trusting any inherited release prose, verify source-of-truth surfaces directly.

## 3. Deliverables

### D1. Recall and contradiction audit

Refresh release context, then verify the local branch is truthfully release-ready before any irreversible action.

Required:
- `BUILD-REPORT.md`
- `FINAL-SUMMARY.md`
- `progress-log.md`

- [ ] Run `bash /Users/mordecai/.openclaw/workspace/scripts/pre-action-recall.sh release agentkit-cli /Users/mordecai/repos/agentkit-cli-v1.16.0-reconcile-lanes`
- [ ] Run `bash /Users/mordecai/.openclaw/workspace/scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.16.0-reconcile-lanes`
- [ ] Verify repo is clean except intentional contract artifacts
- [ ] Confirm version surfaces target `1.16.0`
- [ ] Record the exact pre-release truth in `progress-log.md`

### D2. Validation rerun from this repo

Re-run the exact validation needed to justify release from this repo, not from memory.

Required:
- repo-local validation commands

- [ ] Re-run the focused reconcile slice or release slice used for final confidence
- [ ] Re-run the full test suite from this repo
- [ ] If any failure appears, fix only truthful release-surface or packaging issues and re-run
- [ ] Record exact passing results in `progress-log.md`

### D3. Git release surfaces

Complete the source-control part of the four-surface checklist.

Required:
- git branch/tag state

- [ ] Push the branch to origin
- [ ] Create annotated tag `v1.16.0`
- [ ] Push the tag to origin
- [ ] Verify remote branch head and remote tag target explicitly
- [ ] Record branch-head vs tag-target chronology honestly in `progress-log.md`

### D4. Registry publish

Build and publish `agentkit-cli==1.16.0`, then verify the registry-live surface directly.

Required:
- dist artifacts
- PyPI live proof

- [ ] Build wheel and sdist for `1.16.0`
- [ ] Publish using the supported local auth path available on this machine
- [ ] Verify `https://pypi.org/pypi/agentkit-cli/1.16.0/json` returns live artifacts
- [ ] Record the exact registry proof in `progress-log.md`

### D5. Shipped chronology reconciliation

After all four surfaces are true, reconcile the repo reports so the next session inherits one coherent shipped story.

Required:
- `BUILD-REPORT.md`
- `BUILD-REPORT-v1.16.0.md`
- `FINAL-SUMMARY.md`
- `progress-log.md`
- `CHANGELOG.md` if needed

- [ ] Update release/report surfaces to say `SHIPPED` only after D1-D4 are actually complete
- [ ] Distinguish the shipped release commit from any later docs-only chronology cleanup commit if the branch advances
- [ ] Run `bash /Users/mordecai/.openclaw/workspace/scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.16.0-reconcile-lanes`
- [ ] Leave the repo clean except intentional contract files
- [ ] Write final summary or blocker report with exact remaining truth

## 4. Test Requirements

- [ ] Focused reconcile or release slice passes
- [ ] Full suite passes from this repo
- [ ] Existing release-surface checks still pass after chronology cleanup
- [ ] All existing tests still pass

## 5. Reports

- Write progress to `progress-log.md` after each deliverable
- Include: what was verified or changed, what tests pass, what remains, and any blockers
- If contradictory release prose appears, stop and reconcile it before summarizing
- Before final summary, run `scripts/post-agent-hygiene-check.sh` on this repo
- If release cannot reach truthful shipped state, write `blocker-report-v1.16.0-release.md`

## 6. Stop Conditions

- All deliverables checked and all four release surfaces verified -> DONE
- 3 consecutive failed attempts on same issue -> STOP, write blocker report
- New scope or feature work required -> STOP, report the new requirement
- Push/tag/publish succeed but reports still lie -> continue until chronology is truthful
