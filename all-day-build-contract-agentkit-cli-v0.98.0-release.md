# All-Day Build Contract: agentkit-cli v0.98.0 release execution

Status: In Progress
Date: 2026-04-18
Owner: Codex execution pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Take the already-green `v0.98.0` optimize sweep RC in `/Users/mordecai/repos/agentkit-cli-rc-v0.97.2-optimize-unblock` from RELEASE-READY local state to an actually shipped release, with the four release surfaces verified: local tests green, GitHub push complete, tag live, and PyPI live. The concrete outcome is a trustworthy `v0.98.0` release plus updated release notes/reporting that explain exactly what shipped.

This contract is considered complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Full test suite must remain green at the release commit used for tagging.
4. Do not add net-new product features, refactors, or opportunistic cleanup.
5. Never modify files outside `/Users/mordecai/repos/agentkit-cli-rc-v0.97.2-optimize-unblock`.
6. Keep `.agentkit-last-run.json` and other local runtime noise out of release commits.
7. Commit after each completed deliverable, not just at the end.
8. If stuck on the same issue for 3 attempts, stop and write a blocker report.
9. Read the existing release docs, version files, and git state before mutating anything.
10. Summarize findings in prose in `progress-log.md`, never paste raw command output.
11. Follow the workspace release checklist literally: tests green, git push confirmed, tag confirmed, registry live.
12. If any release surface cannot be verified, stop and leave the repo in a truthful RELEASE-READY or BLOCKED state, not a fake shipped state.

## 3. Starting State

Current known state:
- RC worktree path: `/Users/mordecai/repos/agentkit-cli-rc-v0.97.2-optimize-unblock`
- Full suite is already green locally at `4764 passed, 1 warning`
- Release-prep commits already exist, including `8cf4c28` (`chore: finalize v0.98.0 optimize sweep`) and `63324f6` (`docs: add optimize build contracts and blocker reports`)
- The only known local noise is `.agentkit-last-run.json`, which must stay out of release commits
- `v0.98.0` is not yet pushed, tagged, or published

## 4. Feature Deliverables

### D1. Release surface audit and final release commit

Required files as needed:
- `pyproject.toml`
- `agentkit_cli/__init__.py`
- `CHANGELOG.md`
- `README.md`
- `BUILD-REPORT.md`
- `BUILD-REPORT-v0.98.0.md`
- `progress-log.md`

- [ ] Confirm branch, remotes, local cleanliness, and version metadata all point at `0.98.0`
- [ ] Exclude `.agentkit-last-run.json` or any other runtime noise from the release path
- [ ] Make only the smallest doc/report/version edits required to make the release truthful
- [ ] Re-run the full suite at the final release commit candidate
- [ ] Commit D1 only if a final release commit was needed

### D2. GitHub push and tag verification

Required files as needed:
- `progress-log.md`
- `BUILD-REPORT-v0.98.0.md`

- [ ] Push the release branch/commits to GitHub
- [ ] Create `v0.98.0` tag if missing, or correct the tag only if it points at the wrong release commit
- [ ] Push tags to GitHub
- [ ] Verify from git state that the release commit and tag both exist on origin
- [ ] Record the pushed commit hash and tag target in prose in `progress-log.md`
- [ ] Commit D2 only if report files changed during this verification step

### D3. PyPI publish and registry-live proof

Required files as needed:
- `BUILD-REPORT-v0.98.0.md`
- `progress-log.md`

- [ ] Publish `agentkit-cli` version `0.98.0` to PyPI from this RC worktree
- [ ] Verify the registry now serves `0.98.0` as the live version
- [ ] Record the exact four-surface release proof in `BUILD-REPORT-v0.98.0.md`
- [ ] Update `progress-log.md` with final shipped summary, including what changed in the optimize sweep release
- [ ] Commit D3 only if the report updates happened after publish verification

## 5. Test Requirements

Minimum required validation sequence:
- [ ] `uv run pytest -q`
- [ ] `git status --short`
- [ ] `git push`
- [ ] `git tag v0.98.0` (only if missing) and `git push --tags`
- [ ] registry verification that `agentkit-cli==0.98.0` is live on PyPI

Do not mark the contract complete unless all five gates pass and the four release surfaces are explicitly proven.

## 6. Reports

- Update `progress-log.md` after each deliverable
- Include what was verified, what changed, which commit/tag shipped, and whether each release surface is proven
- Final summary must include: final commit hash, tag hash, test result, push confirmation, PyPI confirmation, and any blocker or cleanup left behind

## 7. Stop Conditions

- All deliverables checked and all release gates verified -> DONE
- 3 consecutive failed attempts on the same issue -> STOP and write a blocker report
- Any test regression after the supposed release commit -> STOP and fix or revert before continuing
- Git push/tag works but PyPI publish or registry verification fails -> STOP and leave the repo marked RELEASE-READY, not SHIPPED
- Discovering version drift or missing release metadata beyond narrow release truthfulness -> STOP and report the exact drift
