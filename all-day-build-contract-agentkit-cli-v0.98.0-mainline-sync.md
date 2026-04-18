# All-Day Build Contract: agentkit-cli v0.98.0 mainline sync

Status: In Progress
Date: 2026-04-18
Owner: OpenClaw sub-agent execution pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Bring the tested `v0.98.0` optimize/release-check work back onto a clean branch from `origin/main` so the main development line is no longer stranded behind the shipped release branch. The concrete outcome is a clean worktree branch that contains the shipped optimize functionality, the pages/site fixes needed for the release, updated version/docs/build reports, and a trustworthy validation report suitable for the next merge/release decision.

This contract is complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Full test suite must pass at the end.
4. New or recovered behavior must ship with docs and build-report updates in the same pass.
5. Never modify files outside `/Users/mordecai/repos/agentkit-cli-mainline-sync-v0.98.0`.
6. Commit after each completed deliverable, with concise descriptive commit messages.
7. If stuck on the same issue for 3 attempts, stop and write a blocker report.
8. Do not add unrelated features or speculative refactors.
9. Read existing optimize/release-check tests and docs before changing code.
10. Treat `v0.98.0` tag / `release/v0.98.0` as the source of truth for shipped behavior, but keep the result mergeable onto `origin/main`.
11. Summarize findings in prose. Do not paste raw command dumps into notes or reports.
12. Do not push, tag, or publish anything.

## 3. Feature Deliverables

### D1. Source-of-truth map and import plan

Identify the exact shipped surfaces from `v0.98.0` that must be carried onto the clean mainline branch. Produce a short written import plan before broad edits.

Required:
- `RELEASE-NEXT-STEP-v0.98.0-mainline-sync.md`
- `progress-log-v0.98.0-mainline-sync.md`

- [ ] Summarize the commit/diff surfaces from `origin/main...v0.98.0`
- [ ] Call out any files that should intentionally NOT be ported
- [ ] Record the merge/cherry-pick strategy in prose
- [ ] Tests or verification notes for D1

### D2. Optimize + release-check code sync

Port the shipped optimize command, renderer/model support, improve/run integration, and release-check hardening onto this clean branch.

Required:
- `agentkit_cli/optimize.py`
- `agentkit_cli/renderers/optimize_renderer.py`
- `agentkit_cli/commands/optimize_cmd.py`
- `agentkit_cli/commands/run_cmd.py`
- `agentkit_cli/commands/improve.py`
- `agentkit_cli/release_check.py`
- `agentkit_cli/commands/release_check_cmd.py`
- `agentkit_cli/models.py`
- `agentkit_cli/main.py`

- [ ] Port optimize core behavior and CLI wiring
- [ ] Port release-check hardening that shipped with the optimize line
- [ ] Keep imports, schemas, and command registration coherent on top of `origin/main`
- [ ] Add or reconcile tests for D2

### D3. Site/pages and docs reconciliation

Port only the site/doc changes that are necessary for the shipped behavior and release narrative, while avoiding stale generated noise.

Required:
- `README.md`
- `CHANGELOG.md`
- `BUILD-REPORT.md`
- `BUILD-REPORT-v0.98.0.md`
- `docs/index.html`
- `docs/data.json`
- `docs/leaderboard.html`
- `docs/repo/owner--repo2.html`
- `docs/topic/go.html`
- `docs/sitemap.xml`
- `agentkit_cli/site_engine.py`

- [ ] Reconcile README/changelog/version/build-report surfaces with the shipped optimize story
- [ ] Port the minimal pages/site fixes required to keep tests green
- [ ] Avoid dragging unrelated stale dist/cache artifacts into the branch
- [ ] Add or reconcile tests for D3

### D4. Validation, hygiene, and handoff

Prove the synced branch is trustworthy and leave a concise handoff for the next build/release pass.

Required:
- `progress-log-v0.98.0-mainline-sync.md`
- `BUILD-REPORT.md`
- optional blocker report if needed

- [ ] Run targeted optimize/release-check/pages tests
- [ ] Run the full test suite
- [ ] Run `scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-mainline-sync-v0.98.0`
- [ ] Write final summary with what changed, what passed, and any remaining risk

## 4. Test Requirements

- [ ] Unit tests for optimize, run/improve integration, and release-check surfaces
- [ ] Integration-level coverage for optimize workflow and release-check behavior
- [ ] Edge cases: protected sections preserved, no-op optimize verdicts, site markers stay present, release-check contradictions do not silently pass
- [ ] All existing tests must still pass

## 5. Reports

- Write progress to `progress-log-v0.98.0-mainline-sync.md` after each deliverable
- Include: what was built, what tests pass, what's next, and any blockers
- Before trusting any release/status narrative, run `scripts/pre-action-recall.sh release agentkit-cli /Users/mordecai/repos/agentkit-cli-mainline-sync-v0.98.0`
- Then run `scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-mainline-sync-v0.98.0`
- If a file contains both success and blocker language, stop, verify source-of-truth surfaces, and reconcile the prose before summarizing it
- Before final summary, run `scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-mainline-sync-v0.98.0`
- Final summary only when all deliverables are done or a real blocker stops work

## 6. Stop Conditions

- All deliverables checked and all tests passing -> DONE
- 3 consecutive failed attempts on the same issue -> STOP and write blocker report
- Scope creep detected (for example a new feature beyond v0.98.0 sync) -> STOP and report it
- Dirty generated artifacts with no product value -> revert them instead of carrying them forward
- Never push, tag, or publish from this pass
