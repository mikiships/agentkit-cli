# All-Day Build Contract: agentkit-cli v0.99.0 release

Status: In Progress
Date: 2026-04-19
Owner: OpenClaw sub-agent execution pass
Scope type: Deliverable-gated release execution

## 1. Objective

Take the clean local `rc/v0.99.0-mainline` branch in `/Users/mordecai/repos/agentkit-cli-v0.99.0-context-projections` from release-ready local state to a verified real release. The outcome is not "looks done locally". The outcome is: source-of-truth release surfaces agree, tests are green from this exact repo, the release branch and tag are pushed to GitHub, `agentkit-cli` version `0.99.0` is live on PyPI, and the repo-local reports/progress log describe one coherent chronology with no shipped-vs-blocked contradiction.

This contract is complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Re-run the relevant validation from this exact repo before any push/tag/publish claim.
4. New release-state docs/report updates must land in the same pass as the release.
5. Never modify files outside the project directory.
6. Commit after each completed deliverable, not only at the end.
7. If stuck on the same issue for 3 attempts, stop and write a blocker report.
8. Do not refactor or broaden scope beyond this release execution path.
9. Read existing release/build docs before changing them.
10. Treat contradictory status prose as a stop signal. Verify tests, git refs, and registry state before summarizing.
11. Do not call the release shipped until all four surfaces are confirmed: tests green, push confirmed, tag confirmed, registry live.
12. Prefer existing trusted release mechanisms already used in this repo. If one publish path fails, use the established fallback only if it keeps the version and artifact state correct.

## 3. Release Deliverables

### D1. Release verification baseline and contradiction cleanup

Refresh the exact release baseline from the current RC branch before any external step.

Required surfaces:
- `BUILD-REPORT-v0.99.0.md`
- `BUILD-REPORT.md`
- `progress-log.md`
- `pyproject.toml`

- [ ] Read the current v0.99.0 build/report surfaces and confirm they all describe local release-ready state, not shipped state
- [ ] Run `bash /Users/mordecai/.openclaw/workspace/scripts/pre-action-recall.sh release agentkit-cli /Users/mordecai/repos/agentkit-cli-v0.99.0-context-projections`
- [ ] Run `bash /Users/mordecai/.openclaw/workspace/scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v0.99.0-context-projections` or an equivalent contradiction scan
- [ ] Re-run targeted validation relevant to context projections/init/migrate and record exact results
- [ ] Re-run the full test suite and record exact results
- [ ] If any report contains contradictory success/blocker language, reconcile it before moving on
- [ ] Commit D1 updates if any repo files changed

### D2. Release branch, tag, and GitHub state

Turn the local RC into a verified remote release state.

Required surfaces:
- local git branch `rc/v0.99.0-mainline`
- release tag `v0.99.0`
- GitHub remote refs

- [ ] Confirm working tree is clean before external release actions
- [ ] Push the release branch to origin
- [ ] Create or verify tag `v0.99.0` on the intended release commit
- [ ] Push the tag to origin
- [ ] Verify both branch and tag exist on the remote and point at the expected commit
- [ ] Commit any repo-local release-state updates required by this step before final publish, if applicable

### D3. Build artifacts and publish to PyPI

Produce the actual release artifacts and make `agentkit-cli 0.99.0` live in the registry.

Required surfaces:
- `dist/`
- PyPI project page / version-specific proof
- repo-local release notes surfaces if they need the final artifact proof

- [ ] Build sdist and wheel for version `0.99.0`
- [ ] Publish the artifacts using the working trusted path for this environment
- [ ] Verify the version-specific PyPI page or JSON shows `0.99.0` live
- [ ] If the primary publish path fails, use the established fallback and document exactly what happened
- [ ] Record artifact and registry-live proof in repo-local report surfaces

### D4. Final chronology, hygiene, and handoff

Leave the repo with one clean truthful story for the next wake-up.

Required surfaces:
- `BUILD-REPORT-v0.99.0.md`
- `BUILD-REPORT.md`
- `progress-log.md`
- optional blocker report only if needed

- [ ] Update report surfaces to say whether v0.99.0 is RELEASE-READY locally or SHIPPED, based on verified truth after D3
- [ ] Run `bash /Users/mordecai/.openclaw/workspace/scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v0.99.0-context-projections`
- [ ] Clean obvious merge markers, unresolved comment slop, and untracked noise, or explicitly document intentional leftovers
- [ ] Ensure final `git status --short` is clean
- [ ] Write a concise final summary in `progress-log.md` with: what shipped, exact test results, pushed refs, registry proof, and any caveats for the next pass
- [ ] If blocked, stop with a blocker report instead of optimistic prose

## 4. Test Requirements

- [ ] Targeted projection/init/migrate validation slice passes
- [ ] Full suite passes from this exact repo checkout
- [ ] Build artifact generation succeeds for version `0.99.0`
- [ ] Existing release/report surfaces remain internally consistent after updates
- [ ] Remote branch/tag verification succeeds
- [ ] Registry-live verification succeeds

## 5. Reports

- Write progress to `progress-log.md` after each deliverable
- Include: what changed, what tests passed, what external proof was verified, what is next, and any blockers
- Before trusting any release/status narrative, run the release recall + contradiction scan from D1
- Before final summary or release claims, run the hygiene check from D4
- If a managed runner, routed response, or tool emits contradictory impossible release claims, append an anomaly via `bash /Users/mordecai/.openclaw/workspace/scripts/log-router-anomaly.sh ...` with the relevant details before cleaning prose
- Final summary only when all deliverables are done or a stop condition fired

## 6. Stop Conditions

- All deliverables checked and all release gates verified -> DONE
- 3 consecutive failed attempts on the same issue -> STOP, write blocker report
- Scope creep discovered beyond release execution -> STOP, report the new scope
- Tests pass but push/tag/publish is still incomplete -> continue, do not mark shipped
- External auth/credential failure blocks publish -> STOP with exact blocker details and preserve truthful local state
