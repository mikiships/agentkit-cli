# All-Day Build Contract: agentkit-cli v0.12.0 — `agentkit doctor`

Status: In Progress
Date: 2026-03-13
Owner: Codex execution pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Build `agentkit doctor`, a preflight diagnostics command that answers the question: "Is this repo and machine actually ready to use the agent quality stack?"

The command should inspect the local environment, repo state, context files, and toolchain availability, then emit a clear pass/warn/fail report with fix hints. This removes setup friction before `agentkit run`, `report`, `publish`, or `suggest`, and gives users a deterministic way to debug broken installs.

This contract is complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Full test suite must pass at the end.
4. New features must ship with docs and report addendum updates in the same pass.
5. CLI outputs must be deterministic and schema-backed where specified.
6. Never modify files outside the project directory.
7. Commit after each completed deliverable, not only at the end.
8. If stuck on the same issue for 3 attempts, stop and write a blocker report.
9. Do NOT refactor, restyle, or improve unrelated commands.
10. Read existing tests and docs before writing new code.
11. Do NOT publish to PyPI. Build-loop handles release.

## 3. Feature Deliverables

### D1. Core `doctor` command + result model

Create a new command that runs a fixed set of checks and renders a readable summary.

Required files:
- `agentkit_cli/commands/doctor_cmd.py`
- `agentkit_cli/doctor.py`
- `agentkit_cli/models.py` (only if needed for shared typed result models)

Required behavior:
- Add `agentkit doctor` to the Typer CLI.
- Run deterministic checks and collect structured results.
- Each check returns: `id`, `name`, `status` (`pass|warn|fail`), `summary`, `details`, `fix_hint`, `category`.
- Human output shows a compact summary table plus a final line like `Doctor: 8 pass, 2 warn, 1 fail`.
- Exit code behavior:
  - `0` when all pass or warn only
  - `1` when any fail unless `--no-fail-exit` is set

Checks for D1:
- repo is a git repo
- repo has at least one commit or gracefully warns if new repo
- working tree clean/dirty status
- README.md presence
- pyproject.toml presence
- context file presence (`CLAUDE.md`, `AGENTS.md`, or `.agents/`)

- [ ] `doctor_cmd.py` created and wired into `main.py`
- [ ] Structured result model implemented
- [ ] Core repo/context checks implemented
- [ ] Human-readable Rich output implemented
- [ ] Exit code policy implemented
- [ ] Tests for D1

### D2. Toolchain and dependency probes

Add checks for whether the local machine can actually run the downstream stack.

Required checks:
- `agentmd` available on PATH
- `agentlint` available on PATH
- `coderace` available on PATH
- `agentreflect` available on PATH
- optional: `git`, `python3`
- capture tool version where possible via `--version`

Behavior:
- Missing core toolkit binary = `fail`
- Missing optional binary = `warn`
- Version parsing must be resilient to noisy output and failures
- Human output should include version text when available

- [ ] Binary/path probes implemented
- [ ] Version collection implemented
- [ ] Missing-core vs missing-optional severity handled correctly
- [ ] Tests for successful, missing, and broken-version scenarios

### D3. Actionability checks with fix hints

Add checks that catch common real-world failure states before the user runs anything expensive.

Required checks:
- current directory contains at least one source file (`.py`, `.ts`, `.js`, `.tsx`, `.jsx`, configurable helper okay)
- context files are present but stale-looking (hook into `agentlint check-context --json` if available; if unavailable, degrade to warn with explicit note)
- report output directory sanity: if `agentkit-report/` or similar existing output path is unwritable, fail with exact fix hint
- publish readiness: if `HERENOW_API_KEY` is missing, warn not fail

Rules:
- Never invoke networked operations.
- If a dependent tool invocation fails, capture stderr briefly and degrade gracefully instead of crashing.
- Fix hints must be specific. Example: `Run 'agentmd generate .' to create a baseline CLAUDE.md`.

- [ ] Source-file presence check implemented
- [ ] Context freshness check implemented with graceful fallback
- [ ] Output-dir/access check implemented
- [ ] HERENOW_API_KEY readiness check implemented
- [ ] Specific fix hints added for each non-pass state
- [ ] Tests for D3

### D4. JSON mode, filtering, and CI ergonomics

Add machine-friendly output so `doctor` can be used in scripts and GitHub Actions.

Required flags:
- `--json` -> emit full JSON payload to stdout
- `--category <name>` -> filter to one category (`repo`, `toolchain`, `context`, `publish`)
- `--fail-on warn|fail` -> control threshold for exit code
- `--no-fail-exit` -> always exit 0 after printing results

Rules:
- JSON schema must be deterministic and documented in tests.
- Human output and JSON output must use the same underlying result objects.
- Filtering must affect both printed output and exit threshold calculation.

- [ ] `--json` implemented
- [ ] `--category` implemented
- [ ] `--fail-on` implemented
- [ ] `--no-fail-exit` implemented
- [ ] Tests for JSON schema, filtering, and exit codes

### D5. Docs, changelog, version bump, and build report

- [ ] Add `doctor` to README command table and usage examples
- [ ] Add a troubleshooting/preflight section to README
- [ ] CHANGELOG entry for v0.12.0
- [ ] Bump version to `0.12.0` in `pyproject.toml` and any version module
- [ ] Write `BUILD-REPORT.md` with deliverables, tests, and known limits

## 4. Test Requirements

- [ ] Unit tests for each check function
- [ ] Integration tests for CLI human output
- [ ] Integration tests for `--json`, `--category`, `--fail-on`, and `--no-fail-exit`
- [ ] Edge cases: not a git repo, empty repo, missing toolkit binaries, broken subprocess, no source files, missing context files
- [ ] All existing tests must still pass
- [ ] Target: 35+ new tests

## 5. Reports

- Update `progress-log.md` after each completed deliverable
- Write final `BUILD-REPORT.md` when all deliverables are done or if blocked
- Include: what was built, tests passing, open limits, exact commands run

## 6. Stop Conditions

- All deliverables checked and all tests passing -> DONE
- 3 consecutive failed attempts on same issue -> STOP and write blocker report
- Scope creep detected -> STOP and report what changed
- All tests passing but deliverables remain -> continue to next deliverable

## 7. What NOT to do

- Do NOT publish to PyPI
- Do NOT add autofix/remediation flows beyond printed fix hints
- Do NOT change behavior of existing commands unless required for wiring
- Do NOT touch other repos
- Do NOT modify files outside `~/repos/agentkit-cli/`
