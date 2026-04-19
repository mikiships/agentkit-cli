# All-Day Build Contract: agentkit-cli v0.99.0 mainline release candidate

Status: In Progress
Date: 2026-04-19
Owner: OpenClaw build-loop sub-agent
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Create a clean, mainline-based release-candidate branch for `agentkit-cli` v0.99.0 that preserves the completed context-projections feature set, repairs the current documentation/contract drift, and ends in a release-ready local state with trustworthy reports. The outcome is not a publish. The outcome is a clean repo branch that can be published without hand-wavy chronology or missing-contract confusion.

This contract is considered complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Full test suite must pass at the end.
4. New or repaired release/report surfaces must land in the same pass.
5. Do not modify files outside `/Users/mordecai/repos/agentkit-cli-v0.99.0-context-projections`.
6. Commit after each completed deliverable, not just at the end.
7. If stuck on the same issue for 3 attempts, stop and write a blocker report.
8. Do not publish, push, tag, or change remote state.
9. Do not add unrelated features beyond the release-candidate convergence work.
10. Read the existing build report, progress log, and relevant tests before changing anything.

## 3. Feature Deliverables

### D1. Mainline RC branch and provenance map

Create a fresh local branch in this repo for the release-candidate pass. Establish the exact commit provenance from the existing `feat/v0.99.0-context-projections` branch and the known sync point `f2bc687`, then record the plan in repo-local docs so the final chronology is explicit.

Required:
- `progress-log.md`
- `BUILD-REPORT-v0.99.0.md`
- `all-day-build-contract-agentkit-cli-v0.99.0-mainline-rc.md`

- [ ] Create a new local RC branch from the current clean repo state
- [ ] Record the provenance and intended convergence path in `progress-log.md`
- [ ] Add/refresh a short section in `BUILD-REPORT-v0.99.0.md` describing the RC objective
- [ ] Commit D1

### D2. Release-candidate convergence cleanup

Repair the local release trail so the branch itself contains the missing explicit contract/report context and no contradictory status narrative. If the current state is already coherent, make the minimum edits needed to prove that.

Required:
- `BUILD-REPORT-v0.99.0.md`
- `BUILD-REPORT.md`
- `progress-log.md`
- any missing contract/report files required to make the release trail self-contained

- [ ] Ensure the explicit release-ready contract/history gap is closed in repo files
- [ ] Reconcile any contradictory or incomplete v0.99.0 status prose across report surfaces
- [ ] Keep the narrative precise: local release-ready, not shipped
- [ ] Commit D2

### D3. RC validation hardening

Run the correct validation slices for the projection/init/migrate surfaces plus the full suite. If failures appear, fix only what is required to restore a trustworthy v0.99.0 RC state.

Required:
- projection/init/migrate targeted tests
- full test suite
- repo-local notes in `progress-log.md`

- [ ] Run targeted validation for projection/init/migrate surfaces
- [ ] Fix any regressions required for a clean RC
- [ ] Run the full suite to green
- [ ] Record exact test outcomes in `progress-log.md`
- [ ] Commit D3 if code/docs changed during validation repair

### D4. Hygiene and final handoff surfaces

Make the branch clean and reviewable. Ensure final surfaces tell one coherent story and the repo can hand off to a later publish pass without archaeology.

Required:
- `BUILD-REPORT-v0.99.0.md`
- `BUILD-REPORT.md`
- `progress-log.md`
- optional blocker report if needed

- [ ] Run a repo-local contradiction scan or equivalent manual check across release/report files
- [ ] Run a hygiene pass for merge markers, unresolved TODO/comment slop, and untracked noise
- [ ] Leave the working tree clean
- [ ] Write a final summary in the report/log surfaces with branch name, HEAD, test counts, and whether the RC is blocked or release-ready locally
- [ ] Commit D4

## 4. Test Requirements

- [ ] Unit and integration coverage for any code changes made during the pass
- [ ] Targeted projection/init/migrate validation slice passes
- [ ] Full test suite passes
- [ ] Existing release/report-related tests still pass
- [ ] Edge cases considered: missing contract-history references, contradictory release prose, validation drift after docs cleanup

## 5. Reports

- Write progress to `progress-log.md` after each deliverable
- Include what changed, what tests pass, what is next, and any blockers
- Before trusting release/status narrative, inspect repo-local report surfaces and reconcile contradictions before summarizing them
- Final summary must include: branch name, HEAD commit, working-tree cleanliness, targeted test result, full-suite result, and whether v0.99.0 is release-ready locally or blocked

## 6. Stop Conditions

- All deliverables checked and all tests passing -> DONE
- 3 consecutive failed attempts on same issue -> STOP and write blocker report
- Scope creep discovered beyond RC convergence -> STOP and report the new requirement
- Full suite green but report surfaces still contradictory -> continue until narrative is coherent
