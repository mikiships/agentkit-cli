# All-Day Build Contract: agentkit-cli v0.18.0 — `agentkit sweep`

Status: In Progress
Date: 2026-03-14
Owner: Codex execution pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Build `agentkit sweep`, a multi-target wrapper around the new `agentkit analyze` flow so one command can evaluate several repos in a batch and rank them by score.

Why this matters: `agentkit analyze github:owner/repo` is good for zero-friction demos, but the higher-leverage use case is comparison. Josh can use batch analysis to score several repos, generate quick research tables, and create stronger public artifacts than one-off screenshots. This should feel like a natural next step from v0.17.0, not a separate product.

This contract is complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Full test suite must pass at the end.
4. Do not publish to PyPI.
5. Do not push to GitHub.
6. Never modify files outside `/Users/mordecai/repos/agentkit-cli`.
7. Commit after each completed deliverable.
8. If stuck on the same issue for 3 attempts, stop and write a blocker report.
9. Do NOT refactor unrelated commands or change existing CLI semantics outside the sweep/analyze path.
10. Read the current `analyze` implementation, tests, README, and CLI wiring before changing anything.

## 3. Feature Deliverables

### D1. Core sweep engine + CLI wiring

Build a batch runner that accepts multiple analysis targets and executes the existing analyze pipeline for each target.

Required files:
- `agentkit_cli/sweep.py`
- `agentkit_cli/commands/sweep_cmd.py`
- `agentkit_cli/main.py`

Required behavior:
- Accept multiple positional targets like `agentkit sweep github:psf/requests github:pallets/flask .`
- Support `--targets-file PATH` with one target per line
- Deduplicate repeated targets while preserving input order
- Reuse the existing analyze/parsing logic instead of re-implementing clone + scoring behavior
- Failure isolation: one bad target should not crash the whole batch

Checklist:
- [ ] Sweep engine created
- [ ] CLI command registered
- [ ] Multiple targets supported
- [ ] `--targets-file` supported
- [ ] Deduping + failure isolation implemented
- [ ] Tests for D1

### D2. Ranked output + useful summary views

Create a ranked terminal view that makes batch analysis immediately useful.

Required files:
- `agentkit_cli/commands/sweep_cmd.py`
- `agentkit_cli/sweep.py`

Required behavior:
- Rich table sorted by composite score descending by default
- Show at minimum: rank, target, score, grade, successful tools, and report URL if available
- Include clear handling for partial failures / missing tool data
- Add `--sort-by` with at least `score` and `target`
- Add `--limit N` for top-N display without changing JSON completeness

Checklist:
- [ ] Ranked Rich table exists
- [ ] Partial failures display cleanly
- [ ] `--sort-by` supported
- [ ] `--limit` supported
- [ ] Tests for D2

### D3. Machine-readable batch output

Make the command useful for scripts and future GitHub workflows.

Required files:
- `agentkit_cli/sweep.py`
- `agentkit_cli/commands/sweep_cmd.py`
- `tests/test_sweep.py`

Required behavior:
- `--json` outputs a stable top-level object with summary counts and per-target results
- Include ranking order in JSON, not just raw result list
- Include counts for total, succeeded, failed, and analyzed_with_scores
- Keep JSON deterministic and free of Rich console noise

Checklist:
- [ ] `--json` supported
- [ ] Stable schema with counts + ranked results
- [ ] JSON deterministic / console-noise-free
- [ ] Tests for D3

### D4. Docs, reports, and release readiness

Update docs so the new command is discoverable and leave the repo ready for a release decision next cycle.

Required files:
- `README.md`
- `CHANGELOG.md`
- `BUILD-REPORT.md`
- `progress-log.md`
- `agentkit_cli/__init__.py`
- `pyproject.toml`

Checklist:
- [ ] README section with examples for positional targets and `--targets-file`
- [ ] CHANGELOG entry for v0.18.0
- [ ] Version bumped to 0.18.0
- [ ] BUILD-REPORT updated
- [ ] progress-log updated after each deliverable
- [ ] Full suite release-ready

## 4. Test Requirements

- [ ] Unit tests for target parsing / dedupe / sorting / JSON schema
- [ ] CLI tests for terminal and JSON modes
- [ ] Integration-style test covering multiple targets with mixed success/failure
- [ ] `python3 -m pytest -q tests/test_sweep.py`
- [ ] `python3 -m pytest -q tests/test_analyze.py`
- [ ] `python3 -m pytest -q`

## 5. Reports

Write progress to `progress-log.md` after each deliverable.
Include:
- what was built
- what tests pass
- what remains
- blockers if any

Update `BUILD-REPORT.md` with a short v0.18.0 section once the feature is complete.

## 6. Stop Conditions

- All deliverables checked and all tests passing -> DONE
- 3 consecutive failed attempts on same issue -> STOP, write blocker report
- Scope creep detected (for example: parallel execution, caching, remote auth, HTML dashboards) -> STOP and report the extra scope instead of implementing it
- Any regression in `agentkit analyze` -> STOP and document it
- All tests passing but docs/report/versioning incomplete -> continue until D4 is done

## 7. Important Context

- Repo: `/Users/mordecai/repos/agentkit-cli`
- Current repo state already contains unreleased v0.17.0 `analyze` work and the watch debounce unblock
- Full suite is currently green from orchestrator verification
- This contract should leave the repo in a releasable state, but do not publish or push
- Keep the implementation focused: sequential batch runner only, no async worker system, no new external dependencies unless absolutely required
