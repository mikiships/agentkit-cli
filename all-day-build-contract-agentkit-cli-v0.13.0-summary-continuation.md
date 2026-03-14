# All-Day Build Contract: agentkit-cli v0.13.0 — summary command (continuation)

Status: In Progress
Date: 2026-03-14
Owner: Codex execution pass
Scope type: Deliverable-gated (no hour promises)
Previous state: D1 complete at commit `d21de35`; continue from D2 only.

## 1. Objective

Finish `agentkit summary` as a maintainer-facing summary command for CI, PR, and release workflows. The command already exists in basic form. This pass must complete the user-facing feature by adding the maintainer-oriented sections, GitHub-friendly output targets, structured JSON mode, and release docs/versioning.

This contract is complete only when every remaining deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Full test suite must pass at the end.
4. New features must ship with docs and report addendum updates in the same pass.
5. CLI outputs must be deterministic and schema-backed where specified.
6. Never modify files outside `/Users/mordecai/repos/agentkit-cli`.
7. Commit after each completed deliverable, not only at the end.
8. If stuck on the same issue for 3 attempts, stop and write a blocker report.
9. Do not refactor, restyle, or improve unrelated code.
10. Read existing summary/report/compare/suggest tests and docs before writing code.
11. Do not publish to PyPI, GitHub releases, or any external service. Build only.
12. Do not touch already-complete D1 except as required for integration fixes.

## 3. Remaining Feature Deliverables

### D2. Maintainer-focused markdown sections

Expand the existing markdown beyond a bare status table. Make it legible for maintainers scanning CI output or a PR summary.

Required files:
- `agentkit_cli/commands/summary_cmd.py`
- `tests/test_summary.py`

- [ ] Add a clear verdict / overview section near the top
- [ ] Include per-tool status with concise, useful notes
- [ ] Include a deterministic “Top fixes” section derived from available findings/suggestions
- [ ] Include optional compare/regression section when compare-style input exists
- [ ] Tests for: no findings, warning-heavy results, degraded compare data

### D3. GitHub-friendly output targets

Make the command usable in CI without network writes.

Required files:
- `agentkit_cli/commands/summary_cmd.py`
- `tests/test_summary.py`
- `README.md`

- [ ] Support `--output <path>` to write markdown to a file
- [ ] Support `--job-summary` to write/append to `GITHUB_STEP_SUMMARY`
- [ ] Fail clearly when `--job-summary` is requested but no GitHub summary target is available
- [ ] Tests for stdout, file output, and job-summary behavior

### D4. Structured JSON mode + validation

Expose the same summary data to downstream tooling in deterministic JSON.

Required files:
- `agentkit_cli/commands/summary_cmd.py`
- `tests/test_summary.py`

- [ ] Support `--json` output mode
- [ ] Include overall score, verdict, per-tool status, top fixes, compare metadata, and markdown body
- [ ] Validate invalid/mutually-exclusive flag combinations cleanly
- [ ] Tests for JSON shape and invalid argument handling

### D5. Docs, versioning, and build report

Ship this as a user-facing release candidate in the repo.

Required files:
- `README.md`
- `CHANGELOG.md`
- `BUILD-REPORT.md`
- `pyproject.toml`
- `progress-log.md`

- [ ] README section for `agentkit summary` with examples
- [ ] README CI/GitHub Actions usage mention for job summaries
- [ ] CHANGELOG entry for v0.13.0
- [ ] Version bump to `0.13.0`
- [ ] BUILD-REPORT updated with final deliverables/tests/status
- [ ] `progress-log.md` updated after each deliverable and at finish

## 4. Test Requirements

- [ ] Unit tests for each remaining deliverable
- [ ] Integration coverage for realistic summary generation flow
- [ ] Edge cases: empty suggestions, missing compare refs, invalid JSON input, missing `GITHUB_STEP_SUMMARY`, invalid flag combos, no issues found
- [ ] All existing tests must still pass
- [ ] Final suite should be baseline 472 passing plus new summary coverage

## 5. Reporting Requirements

After each completed deliverable:
- append to `progress-log.md`
- include: what changed, tests run, next deliverable, blockers (if any)

At the end:
- update `BUILD-REPORT.md`
- leave the repo with a clean working tree except intentional release artifacts
- provide final commit hashes for D2, D3, D4, D5 in the report if possible

## 6. Stop Conditions

- All deliverables checked and full tests pass -> DONE
- 3 consecutive failed attempts on same issue -> STOP and write blocker report
- New requirements discovered outside scope -> STOP and report scope creep
- If only docs/versioning remain after code/tests pass -> continue until D5 is complete
