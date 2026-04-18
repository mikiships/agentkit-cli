# All-Day Build Contract: agentkit-cli v0.98.0 optimize sweep

Status: In Progress
Date: 2026-04-18
Owner: Sub-agent execution pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Extend `agentkit optimize` from a good single-file point tool into a repo-level workflow. The concrete outcome is: one command can discover multiple context files in a repo, render an aggregated review, support a safe repo-wide apply flow, and expose deterministic machine-readable output that teams can use in CI or follow-on tooling.

This contract is complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when every deliverable below is checked.
3. Full test suite must pass at the end.
4. Do not push, tag, publish, or touch GitHub/PyPI.
5. Never modify files outside `/Users/mordecai/repos/agentkit-cli-rc-v0.97.2-optimize-unblock`.
6. Keep scope tightly bounded to repo-level optimize sweep plus docs/tests/report/version updates needed for that feature.
7. Commit after each completed deliverable, not just at the end.
8. If stuck on the same issue for 3 attempts, stop and write a blocker report.
9. Do not absorb unrelated cleanup, refactors, or feature work.
10. Read the current optimize engine/tests/docs before changing code.
11. Preserve current single-file behavior unless a test-backed improvement requires a narrow change.
12. Summarize findings in prose in `progress-log.md`, never paste raw command dumps.

## 3. Starting State

Current shipped optimize surface:
- single-target `agentkit optimize` review/apply flow
- deterministic verdicts, protected-section preservation, no-op detection, smoke coverage
- improve/run integration via `--optimize-context`
- release-ready local state for `v0.97.2`

Current gap:
- optimize works on one file at a time, which is weak for monorepos and mixed `CLAUDE.md`/`AGENTS.md` surfaces
- no repo-level aggregated review or deterministic multi-file summary exists yet
- no safe check-mode for CI-style “fail if optimize would meaningfully rewrite context files” workflow exists yet

## 4. Feature Deliverables

### D1. Repo-level optimize sweep engine

Required files as needed:
- `agentkit_cli/optimize.py`
- `agentkit_cli/models.py`
- new helper module(s) only if clearly justified

Build deterministic discovery and aggregation for multiple context files inside a repo.

- [ ] Add a deterministic context-file discovery path for repo sweeps (`CLAUDE.md` and `AGENTS.md`, including nested repo surfaces if supported)
- [ ] Add result models for multi-file optimize sweep output, including per-file stats/verdicts and top-level aggregate summary
- [ ] Preserve existing single-file optimize behavior unchanged when sweep mode is not requested
- [ ] Add focused unit tests for discovery, aggregation, and no-context edge cases
- [ ] Commit D1 when the new sweep core is green

### D2. CLI sweep and check workflow

Required files:
- `agentkit_cli/commands/optimize_cmd.py`
- `agentkit_cli/main.py`

Build the user-facing repo workflow.

- [ ] Add explicit sweep UX such as `--all` and a deterministic check mode such as `--check`
- [ ] Make `--check` exit non-zero only when meaningful rewrites are available in at least one target file
- [ ] Keep `--apply` safe in sweep mode, with narrow behavior for no-op files and a clear per-file summary
- [ ] Add CLI tests covering dry-run sweep, apply sweep, and check-mode exit behavior
- [ ] Commit D2 when CLI coverage is green

### D3. Aggregated review rendering

Required files:
- `agentkit_cli/renderers/optimize_renderer.py`
- tests for renderer behavior

Build deterministic multi-file review output that is genuinely useful to a maintainer.

- [ ] Add aggregated text/markdown review output for sweep mode
- [ ] Include per-file verdicts, key deltas, protected-section signals, and concise totals
- [ ] Keep single-file renderer output stable unless explicitly improved with updated tests
- [ ] Add renderer tests for both text and markdown sweep output
- [ ] Commit D3 when renderer tests are green

### D4. Pipeline integration and safety polish

Required files as needed:
- `agentkit_cli/commands/run_cmd.py`
- `agentkit_cli/improve_engine.py`
- any narrow integration surface needed for optimize workflow

Make the new sweep mode usable from the rest of agentkit without broad scope creep.

- [ ] If the current improve/run integration benefits from sweep semantics, wire the smallest safe integration surface
- [ ] Ensure multi-file optimize failures remain bounded and do not corrupt broader improve/run flows
- [ ] Add focused integration tests for any changed workflow surface
- [ ] Commit D4 when targeted integration tests pass

### D5. Docs, reports, versioning

Required files:
- `README.md`
- `CHANGELOG.md`
- `BUILD-REPORT.md`
- `BUILD-REPORT-v0.98.0.md`
- `progress-log.md`
- `pyproject.toml`
- `agentkit_cli/__init__.py`

- [ ] Document repo-level optimize sweep usage, check mode, and safety caveats
- [ ] Add a concise `0.98.0` changelog entry
- [ ] Record focused test results and final full-suite result in build reports
- [ ] Bump version to `0.98.0`
- [ ] Commit D5 only after the full suite is green

## 5. Test Requirements

Minimum required validation sequence:
- [ ] `uv run pytest -q tests/test_optimize_d1.py tests/test_optimize_d2.py tests/test_optimize_d3.py tests/test_optimize_d4.py tests/test_optimize_realworld.py tests/test_optimize_d2_hardening.py tests/test_optimize_smoke.py`
- [ ] `uv run pytest -q tests/test_improve.py tests/test_run.py tests/test_run_command.py`
- [ ] `uv run pytest -q`

Add new targeted tests as needed, but do not skip the three gates above.

## 6. Reports

- Update `progress-log.md` after each deliverable
- Include what changed, what passed, what is next, and any blocker
- Final summary must include: deliverables completed, commit hashes, targeted test results, full-suite result, and whether `v0.98.0` is release-ready locally

## 7. Stop Conditions

- All deliverables checked and all tests passing -> DONE
- 3 consecutive failed attempts on the same issue -> STOP and write blocker report
- Scope creep detected beyond optimize sweep/check workflow -> STOP and report it
- Full suite remains red due to an unrelated failure class -> STOP and document the blocker precisely
