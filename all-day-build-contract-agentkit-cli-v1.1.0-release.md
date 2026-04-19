# All-Day Build Contract: agentkit-cli v1.1.0 burn observability release completion

Status: In Progress
Date: 2026-04-19
Owner: OpenClaw build-loop release execution pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Promote the already-built `agentkit-cli v1.1.0 burn observability` work from local BUILT state to a fully verified shipped release. The feature work is already complete in `/Users/mordecai/repos/agentkit-cli-v1.1.0-burn-observability` on `feat/v1.1.0-burn-observability` at `a704a06`; this pass must verify the local state, reconcile any contradictory release prose, push the correct branch state to origin, create and push the `v1.1.0` tag, publish `agentkit-cli==1.1.0` to PyPI using the supported local auth path, and leave repo reports telling one truthful story.

This contract is considered complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Full test suite must pass at the end.
4. New release/report updates must ship in the same pass as the release work.
5. Release claims must be source-of-truth-backed, not inferred from local prose.
6. Never modify files outside the project directory.
7. Commit after each completed deliverable, when a deliverable requires repo changes.
8. If stuck on same issue for 3 attempts, stop and write a blocker report.
9. Do NOT reopen feature scope, refactor unrelated code, or polish beyond release completion.
10. Read existing tests, release docs, and build reports before mutating repo state.
11. Treat existing branch/tag/report prose as untrusted until verified against git refs, PyPI state, and current test results.
12. If the release is already fully shipped when verified, switch to chronology reconciliation and verification only. Do not republish blindly.

## 3. Feature Deliverables

### D1. Release-state audit and contradiction cleanup

Audit the repo and release surfaces before any mutation. Verify current branch, HEAD, worktree cleanliness, version metadata, existing tags, origin branch state, and whether PyPI already has `1.1.0`. Run the local contradiction checks before trusting any release narrative.

Required:
- `BUILD-REPORT.md`
- `BUILD-REPORT-v1.1.0.md`
- `progress-log.md`
- `pyproject.toml`
- `agentkit_cli/__init__.py`

- [ ] Run `scripts/pre-action-recall.sh release agentkit-cli-v1.1.0 /Users/mordecai/repos/agentkit-cli-v1.1.0-burn-observability`
- [ ] Run `scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.1.0-burn-observability`
- [ ] Verify git branch, HEAD, tag state, and origin state
- [ ] Verify whether PyPI `agentkit-cli==1.1.0` already exists
- [ ] If repo prose is contradictory, reconcile it to one truthful pre-release state before moving on
- [ ] Tests for D1: capture audit results in `progress-log.md`

### D2. Validation rerun on the exact release repo state

Rerun the meaningful validation slice from this repo, then rerun the full suite so the release proof is tied to the exact bits being shipped.

Required:
- `tests/test_burn_adapters.py`
- `tests/test_burn_engine.py`
- `tests/test_burn_command.py`
- `tests/test_burn_report.py`
- `tests/test_main.py`

- [ ] Run focused burn-validation slice and record the exact result
- [ ] Run the full test suite and record the exact result
- [ ] If tests fail, fix only release-blocking regressions within existing scope
- [ ] Update `BUILD-REPORT-v1.1.0.md` and `progress-log.md` with the final validation truth
- [ ] Tests for D2: focused slice green, full suite green

### D3. Push and tag completion

If D1 confirms the release is not already fully complete, push the correct branch state to GitHub, create the release tag for the tested commit, and verify both surfaces remotely. If branch/tag already exist correctly, verify them and avoid redundant mutations.

Required:
- git branch `feat/v1.1.0-burn-observability`
- git tag `v1.1.0`
- `BUILD-REPORT-v1.1.0.md`
- `BUILD-REPORT.md`

- [ ] Push the release branch to origin, or verify it is already correct
- [ ] Create annotated tag `v1.1.0` on the tested release commit if missing
- [ ] Push the tag to origin if missing
- [ ] Verify remote branch ref and remote tag ref point to the intended commit
- [ ] Update repo reports so they reflect branch/tag truth exactly
- [ ] Tests for D3: remote refs verified, no contradictory release prose remains

### D4. PyPI publish and registry verification

Publish `agentkit-cli==1.1.0` using the supported local auth path only if PyPI does not already have it. If it is already live, verify the artifacts and skip duplicate publish.

Required:
- `dist/*`
- `pyproject.toml`
- `BUILD-REPORT-v1.1.0.md`

- [ ] Build wheel and sdist from the exact tested repo state
- [ ] Publish `1.1.0` to PyPI, or verify it already exists and matches the intended version
- [ ] Verify registry-live state using the version-specific PyPI JSON or package page
- [ ] Record wheel/sdist presence in the report surfaces
- [ ] Tests for D4: PyPI shows `agentkit-cli==1.1.0` live with artifacts

### D5. Final chronology reconciliation and hygiene

Leave the repo in a clean, reviewable, post-release state with one coherent final story.

Required:
- `BUILD-REPORT.md`
- `BUILD-REPORT-v1.1.0.md`
- `progress-log.md`
- `all-day-build-contract-agentkit-cli-v1.1.0-release.md`

- [ ] Run `scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.1.0-burn-observability`
- [ ] Ensure `git status --short` is clean at the end
- [ ] Reconcile all report surfaces to the same shipped/release-ready truth
- [ ] Write final summary with branch, HEAD, tag, PyPI URL, and test counts
- [ ] Tests for D5: hygiene clean, worktree clean, final summary complete

## 4. Test Requirements

- [ ] Unit tests for burn adapters, engine, command, and report surfaces
- [ ] Integration-level CLI validation via the focused burn slice
- [ ] Edge cases: preexisting tag, preexisting PyPI release, contradictory report prose, clean-vs-dirty worktree detection, version already live on registry
- [ ] All existing tests must still pass

## 5. Reports

- Write progress to `progress-log.md` after each deliverable
- Include: what was built or verified, what tests pass, what's next, any blockers
- Before trusting any release/status narrative, run `scripts/pre-action-recall.sh release agentkit-cli-v1.1.0 /Users/mordecai/repos/agentkit-cli-v1.1.0-burn-observability` first, then run `scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.1.0-burn-observability`
- If a file contains both success and blocker language, stop, verify source-of-truth surfaces, and reconcile the prose before summarizing it
- Before final summary or release claims, run `scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.1.0-burn-observability`
- Final summary when all deliverables are done or the pass is stopped

## 6. Stop Conditions

- All deliverables checked and all tests passing -> DONE
- 3 consecutive failed attempts on same issue -> STOP, write blocker report
- Scope creep detected or feature work tries to reopen -> STOP, report what's new
- Release surface requires missing secrets or human approval beyond standing autonomy -> STOP, write exact blocker
- All tests passing but release surfaces still incomplete -> continue until branch, tag, registry, and reports are complete
