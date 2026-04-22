# All-Day Build Contract: agentkit-cli v1.30.0 release completion

Status: In Progress
Date: 2026-04-21
Owner: OpenClaw sub-agent execution pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Take the truthfully local release-ready `agentkit-cli v1.30.0 flagship adjacent next step` lane through strict release completion. Prove all four release surfaces directly: tests green, branch pushed, annotated tag pushed, and PyPI live. Reconcile chronology across repo and workspace surfaces so future sessions do not confuse the shipped tag commit with any later docs-only closeout commits.

This contract is complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Re-run the required validation from the current tree before any release claim.
4. Verify branch, tag, and registry state from source-of-truth commands, not from prior notes.
5. Keep chronology truthful if the branch advances past the shipped tag commit for docs-only reconciliation.
6. Never modify files outside `/Users/mordecai/repos/agentkit-cli-v1.30.0-flagship-adjacent-next-step`.
7. Commit after each completed deliverable cluster, not only at the end.
8. If stuck on the same issue for 3 attempts, stop and write a blocker report.
9. Do not reopen planner feature work unless a release blocker proves the local-ready claim false.
10. Read existing release surfaces and progress log before mutating anything.

## 3. Feature Deliverables

### D1. Current-tree release truth verification

Ground the lane in the current repo state before any push or publish.

Required:
- `BUILD-REPORT.md`
- `BUILD-REPORT-v1.30.0.md`
- `FINAL-SUMMARY.md`
- `CHANGELOG.md`
- `progress-log.md`

- [ ] Verify current HEAD, branch name, and clean working tree.
- [ ] Re-run release-critical validation from the current tree.
- [ ] Reconcile stale prose or version surfaces before proceeding.
- [ ] Tests for D1 recorded in progress log.

### D2. Git release surfaces

Push the release branch and annotated tag, or prove they already exist and match the intended shipped commit.

Required:
- local git metadata
- `BUILD-REPORT.md`
- `BUILD-REPORT-v1.30.0.md`
- `FINAL-SUMMARY.md`
- `progress-log.md`

- [ ] Push the branch to origin.
- [ ] Create or verify annotated tag `v1.30.0` on the intended release commit.
- [ ] Push the tag and confirm remote refs match the shipped commit.
- [ ] Record any later docs-only chronology commit separately if needed.

### D3. Registry live proof

Publish `agentkit-cli==1.30.0` to PyPI and verify both project and version endpoints plus artifacts.

Required:
- distribution artifacts under `dist/`
- `BUILD-REPORT.md`
- `BUILD-REPORT-v1.30.0.md`
- `FINAL-SUMMARY.md`
- `progress-log.md`

- [ ] Build fresh release artifacts from a clean state.
- [ ] Publish only the `1.30.0` wheel and sdist.
- [ ] Verify PyPI project JSON and version JSON both report `1.30.0` live.
- [ ] Record artifact names and any auth-path quirks truthfully.

### D4. Shipped chronology and surface reconciliation

Close the lane with truthful shipped surfaces in repo and workspace-facing artifacts.

Required:
- `BUILD-REPORT.md`
- `BUILD-REPORT-v1.30.0.md`
- `FINAL-SUMMARY.md`
- `CHANGELOG.md`
- `progress-log.md`

- [ ] Mark shipped versus later chronology commits truthfully.
- [ ] Update final summary and reports to shipped state.
- [ ] Leave the repo clean at the end.
- [ ] Final release summary captured in progress log.

## 4. Test Requirements

- [ ] Focused release-critical validation from the current tree
- [ ] Full suite or previously proven current-tree full-suite truth explicitly referenced in final closeout with no stale contradiction
- [ ] Edge cases: tag already exists, branch already pushed, publish auth path, dist contamination from old artifacts, shipped commit vs docs-only chronology head, stale `1.29.0` version surfaces left in a `1.30.0` branch
- [ ] All existing tests must still pass

## 5. Reports

- Write progress to `progress-log.md` after each deliverable.
- Include what was verified, what shipped, what refs/artifacts changed, and any blockers.
- Before trusting release/status narrative, run `scripts/pre-action-recall.sh release agentkit-cli /Users/mordecai/repos/agentkit-cli-v1.30.0-flagship-adjacent-next-step`.
- Run `scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.30.0-flagship-adjacent-next-step` before final summary.
- Run `scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.30.0-flagship-adjacent-next-step` before final summary.
- If blocked, write `blocker-report-v1.30.0-release.md` with exact failure, attempts, and recommended next move.

## 6. Stop Conditions

- All deliverables checked and all release surfaces directly verified -> DONE
- 3 consecutive failed attempts on same issue -> STOP and write blocker report
- Scope creep discovered beyond release completion -> STOP and report the new requirement
- Any contradiction between repo truth and claimed shipped state -> STOP and reconcile before proceeding
