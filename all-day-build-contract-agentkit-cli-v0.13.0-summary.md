# All-Day Build Contract: agentkit-cli v0.13.0 — summary command

Status: In Progress
Date: 2026-03-13
Owner: Codex execution pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Build `agentkit summary`, a maintainer-facing markdown summary generator that turns agentkit results into clean GitHub-ready output. The command should make the toolkit legible in CI and PR workflows by producing a concise summary of overall score, per-tool status, key regressions, and top suggested fixes. It should work both as a direct CLI command and as a reusable artifact generator for GitHub Actions.

This contract is considered complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Full test suite must pass at the end.
4. New features must ship with docs and report addendum updates in the same pass.
5. CLI outputs must be deterministic and schema-backed where specified.
6. Never modify files outside the project directory.
7. Commit after each completed deliverable, not only at the end.
8. If stuck on the same issue for 3 attempts, stop and write a blocker report.
9. Do NOT refactor, restyle, or improve code outside the deliverables.
10. Read existing tests and docs before writing new code.
11. Do not post to GitHub, PyPI, or any external service. Build the feature only.

## 3. Feature Deliverables

### D1. Core `agentkit summary` command

Add a new Typer command that generates a markdown summary from agentkit outputs. It must support either reading an existing JSON result file or running the local project analysis first when given a project path.

Required:
- `agentkit_cli/main.py`
- `agentkit_cli/commands/summary_cmd.py`
- `tests/test_summary.py`

- [ ] Add `agentkit summary` command wiring in `main.py`
- [ ] Implement command entrypoint with deterministic markdown output
- [ ] Support `--path` and `--json-input` modes
- [ ] Tests for command registration and basic markdown rendering

### D2. Maintainer-focused summary sections

The markdown should emphasize what a maintainer cares about first: overall score, verdict, noteworthy regressions or warnings, and top fix suggestions. Reuse existing compare/suggest/report logic where sensible instead of inventing parallel scoring.

Required:
- `agentkit_cli/commands/summary_cmd.py`
- `agentkit_cli/suggest_engine.py` (only if needed)
- `tests/test_summary.py`

- [ ] Include overall score header and per-tool status table/list
- [ ] Include a “Top fixes” section based on highest-priority suggestions
- [ ] Include optional compare section when base/head refs are provided
- [ ] Tests for no-findings, warning-heavy, and degraded-compare cases

### D3. GitHub-friendly output targets

Make the feature useful in CI without requiring network writes. It should generate markdown to stdout by default and optionally write to files suitable for GitHub job summaries or PR comment workflows.

Required:
- `agentkit_cli/commands/summary_cmd.py`
- `tests/test_summary.py`
- `README.md`

- [ ] Support `--output <path>` to write markdown file
- [ ] Support `--job-summary` to write/append to `GITHUB_STEP_SUMMARY` when available
- [ ] Fail clearly when `--job-summary` is requested outside GitHub without target path
- [ ] Tests for stdout, file output, and job-summary behavior

### D4. Structured JSON mode + robust plumbing

Add structured JSON output so other tools can consume the same summary data. Keep schema simple and deterministic: overall score, verdict, per-tool status, top fixes, compare metadata, markdown body.

Required:
- `agentkit_cli/commands/summary_cmd.py`
- `tests/test_summary.py`

- [ ] Support `--json` structured output mode
- [ ] Include markdown body in JSON output for downstream reuse
- [ ] Validate mutually exclusive or invalid flag combinations
- [ ] Tests for JSON schema shape and invalid argument handling

### D5. Docs, changelog, version bump, build report

Document the new command as a first-class part of the product. Treat this as a user-facing release.

Required:
- `README.md`
- `CHANGELOG.md`
- `BUILD-REPORT.md`
- `pyproject.toml`

- [ ] README usage section with CLI examples
- [ ] GitHub Actions section updated with summary workflow example
- [ ] CHANGELOG entry for v0.13.0
- [ ] Version bump to `0.13.0`
- [ ] BUILD-REPORT updated with deliverables, tests, and final status

## 4. Test Requirements

- [ ] Unit tests for each deliverable
- [ ] Integration coverage for a realistic summary generation flow
- [ ] Edge cases: empty suggestions, missing compare refs, invalid JSON input, missing `GITHUB_STEP_SUMMARY`, no issues found
- [ ] All existing tests must still pass
- [ ] Final suite target: baseline 469 passing + new summary coverage

## 5. Reports

- Write progress to `progress-log.md` after each deliverable
- Include: what was built, what tests pass, what is next, any blockers
- Final summary when all deliverables are done or the pass stops

## 6. Stop Conditions

- All deliverables checked and all tests passing -> DONE
- 3 consecutive failed attempts on same issue -> STOP, write blocker report
- Scope creep detected (new requirements discovered) -> STOP, report what is new
- All tests passing but deliverables remain -> continue to next deliverable
