# All-Day Build Contract: agentkit-cli v1.5.0 release completion

Status: In Progress
Date: 2026-04-20
Owner: OpenClaw execution pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Take the completed `agentkit source-audit` feature in `/Users/mordecai/repos/agentkit-cli-v1.5.0-source-audit` from local release-ready state to truthful shipped-or-blocked release truth. The feature build is done, but the release surfaces are not. This pass must verify the exact repo state, execute the four-surface release checklist if all gates pass, and leave every status/report file telling one coherent story.

This contract is complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Do not claim SHIPPED unless tests are green, origin refs are pushed, tag is pushed, and PyPI is live.
4. Never modify files outside `/Users/mordecai/repos/agentkit-cli-v1.5.0-source-audit`.
5. Commit after each completed deliverable, not only at the end.
6. If stuck on the same issue for 3 attempts, stop and write a blocker report.
7. Do not refactor unrelated code.
8. Read existing release docs/tests/report surfaces before editing them.
9. Verify downstream truth after each irreversible step. Do not batch push/tag/publish and trust exit codes.
10. Keep secrets out of logs and reports.

## 3. Feature Deliverables

### D1. Release-state audit and repo cleanup

Audit the current branch, version metadata, dirty files, and release narratives so the pass starts from source-of-truth state instead of stale prose.

Required:
- `BUILD-REPORT.md`
- `BUILD-REPORT-v1.5.0.md`
- `progress-log.md`
- `CHANGELOG.md`
- repo status / tag state

- [ ] Run release recall plus contradiction checks before trusting any narrative
- [ ] Reconcile dirty repo state and any version/report drift
- [ ] Confirm the intended release commit and version are explicit and coherent
- [ ] Tests/checks for D1

### D2. Validation baseline

Re-run the exact validation needed for release confidence from this repo state.

Required:
- targeted source-audit validation slice
- full suite

- [ ] Re-run the focused `agentkit source-audit` validation slice
- [ ] Re-run the full supported test suite
- [ ] Record exact results in report surfaces
- [ ] Tests/checks for D2

### D3. Git release surfaces

Push the release branch/commit and the annotated tag once validation is green and the repo state is clean.

Required:
- git branch on origin
- annotated `v1.5.0` tag on origin

- [ ] Push the release branch or current release commit to origin
- [ ] Create or verify the annotated `v1.5.0` tag at the tested release commit
- [ ] Push tags and verify origin sees the exact expected refs
- [ ] Tests/checks for D3

### D4. PyPI publish and registry verification

Build and publish the package using the supported local path, then verify the registry live state directly.

Required:
- `dist/` artifacts
- PyPI JSON/page proof for `agentkit-cli==1.5.0`

- [ ] Build wheel and sdist from the tested release state
- [ ] Publish `agentkit-cli==1.5.0` via the supported authenticated path
- [ ] Verify version-specific PyPI truth directly, including both artifacts
- [ ] Tests/checks for D4

### D5. Final chronology reconciliation

After external surfaces are true, make the repo reports match reality and leave a clean final handoff.

Required:
- `BUILD-REPORT.md`
- `BUILD-REPORT-v1.5.0.md`
- `progress-log.md`
- blocker report if release stops short

- [ ] Reconcile report surfaces to one truthful final state, shipped or blocked
- [ ] Run hygiene/conflict checks on the final repo state
- [ ] Leave the repo clean except for intentional, documented artifacts
- [ ] Final summary with exact tests, refs, and registry proof

## 4. Test Requirements

- [ ] Focused source-audit validation slice passes
- [ ] Full test suite passes under the repo's supported environment
- [ ] Release contradiction scan passes or all findings are reconciled
- [ ] Hygiene check passes or all findings are documented intentional
- [ ] Registry verification confirms both wheel and sdist for `1.5.0`

## 5. Reports

- Write progress to `progress-log.md` after each deliverable
- Include what changed, exact validation results, and what remains
- Before trusting any release/status narrative, run:
  - `bash /Users/mordecai/.openclaw/workspace/scripts/pre-action-recall.sh release agentkit-cli /Users/mordecai/repos/agentkit-cli-v1.5.0-source-audit`
  - `bash /Users/mordecai/.openclaw/workspace/scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.5.0-source-audit`
- Before final summary, run:
  - `bash /Users/mordecai/.openclaw/workspace/scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.5.0-source-audit`
- If a managed runner or tool emits contradictory shipped/blocker prose, log the anomaly before cleanup.

## 6. Stop Conditions

- All deliverables checked and all validations green -> DONE
- 3 consecutive failed attempts on the same issue -> STOP and write blocker report
- Missing auth or external publish permissions block release -> STOP and document exact blocker
- Any contradiction remains unresolved between tests, origin refs, and registry state -> STOP until source-of-truth is verified
