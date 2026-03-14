# All-Day Build Contract: agentkit-cli v0.12.0 — `agentkit doctor` continuation

Status: In Progress
Date: 2026-03-13
Owner: builder continuation pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Finish `agentkit doctor` so it is a real preflight command, not just a repo smoke test. D1 is already committed on `main` in commit `db30c34` (`feat: add core doctor repo diagnostics`). This pass starts from that state and must complete D2-D5, expand test coverage, and leave the repo ready for build-loop to publish.

This contract is complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Full test suite must pass at the end.
4. New features must ship with docs and report updates in the same pass.
5. CLI outputs must be deterministic and schema-backed where specified.
6. Never modify files outside `/Users/mordecai/repos/agentkit-cli`.
7. Commit after each completed deliverable, not only at the end.
8. If stuck on the same issue for 3 attempts, stop and write a blocker report.
9. Do NOT refactor, restyle, or improve unrelated commands.
10. Read existing tests and docs before writing new code.
11. Do NOT publish to PyPI. Build-loop handles release.
12. Keep the human output readable. Do not turn `doctor` into a wall of JSON with a thin CLI wrapper.

## 3. Current Starting Point

Already done:
- D1 core doctor result model and repo/context checks
- D1 tests committed

Current repo expectations:
- Work from commit `db30c34`
- Update `progress-log.md` as you finish each deliverable
- Replace the current blocker-style `BUILD-REPORT.md` with a final ship report when complete

## 4. Feature Deliverables

### D2. Toolchain and dependency probes

Add checks that verify the local machine can run the agent quality stack.

Required checks:
- `agentmd` available on PATH
- `agentlint` available on PATH
- `coderace` available on PATH
- `agentreflect` available on PATH
- optional probes: `git`, `python3`
- capture version text where possible via `--version`

Rules:
- Missing core toolkit binary = `fail`
- Missing optional binary = `warn`
- Version parsing must handle noisy output and subprocess failures
- Human output should show version info when available without wrecking readability

- [ ] Binary/path probes implemented
- [ ] Version collection implemented
- [ ] Missing-core vs missing-optional severity handled correctly
- [ ] Tests for success, missing tool, noisy version output, and subprocess failure
- [ ] Commit for D2

### D3. Actionability checks with fix hints

Catch common states that make later commands fail.

Required checks:
- current directory contains at least one source file (`.py`, `.ts`, `.js`, `.tsx`, `.jsx`)
- context freshness via `agentlint check-context --json` when available; graceful fallback when unavailable or failing
- report output directory sanity for `agentkit-report/` or chosen report dir path if unwritable
- publish readiness: missing `HERENOW_API_KEY` should warn, not fail

Rules:
- Never invoke networked operations
- Dependent tool failures should degrade gracefully, not crash `doctor`
- Fix hints must be specific, actionable, and short

- [ ] Source-file presence check implemented
- [ ] Context freshness check implemented with graceful fallback
- [ ] Output-dir/access check implemented
- [ ] HERENOW_API_KEY readiness check implemented
- [ ] Specific fix hints added for each non-pass state
- [ ] Tests for D3
- [ ] Commit for D3

### D4. JSON mode, filtering, and CI ergonomics

Make `doctor` usable in scripts and GitHub Actions.

Required flags:
- `--json`
- `--category <name>` where category is one of `repo`, `toolchain`, `context`, `publish`
- `--fail-on warn|fail`
- `--no-fail-exit`

Rules:
- JSON payload must be deterministic and test-covered
- Human and JSON output must use the same underlying report objects
- Filtering must affect both displayed checks and exit threshold calculation

- [ ] `--json` implemented on final report model
- [ ] `--category` implemented
- [ ] `--fail-on` implemented
- [ ] `--no-fail-exit` implemented
- [ ] Tests for schema, filtering, and exit codes
- [ ] Commit for D4

### D5. Docs, changelog, version bump, and build report

Finish the ship surface.

- [ ] README command table updated with `doctor`
- [ ] README troubleshooting/preflight section added
- [ ] CHANGELOG entry for v0.12.0
- [ ] Version bumped to `0.12.0`
- [ ] `BUILD-REPORT.md` rewritten as final ship report, not blocker report
- [ ] Final commit for D5

## 5. Test Requirements

- [ ] Unit tests for each new check/helper
- [ ] Integration tests for CLI human output
- [ ] Integration tests for `--json`, `--category`, `--fail-on`, and `--no-fail-exit`
- [ ] Edge cases: not a git repo, empty repo, missing toolkit binaries, broken subprocess, no source files, missing context files, stale context fallback, unwritable output dir
- [ ] All existing tests must still pass
- [ ] Target: 35+ new tests beyond the D1 baseline

## 6. Reports

- Update `progress-log.md` after each completed deliverable
- Final `BUILD-REPORT.md` must include:
  - deliverables completed
  - exact test command(s)
  - final passing counts
  - known limitations
  - whether repo is clean except for intentional release files

## 7. Stop Conditions

- All deliverables checked and full suite passing -> DONE
- 3 consecutive failed attempts on the same issue -> STOP and write blocker report
- Scope creep detected -> STOP and report what changed
- Any temptation to publish -> STOP; publishing is out of scope
