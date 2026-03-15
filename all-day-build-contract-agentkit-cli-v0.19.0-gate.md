# All-Day Build Contract: agentkit-cli v0.19.0 — `agentkit gate`

Status: In Progress
Date: 2026-03-14
Owner: Codex execution pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Build `agentkit gate`, a policy-enforcement command that turns the toolkit from reporting into an actual CI guardrail.

Why this matters: `agentkit score`, `summary`, `compare`, and now `sweep` tell you how a repo is doing, but they do not yet give teams a single command that can fail the build when agent quality drops below an agreed bar. The missing step is enforcement. `agentkit gate` should let someone say "this repo must stay above 80" or "do not let the score drop by more than 5 points from baseline" and get a deterministic pass/fail result plus machine-readable output.

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
9. Do NOT refactor unrelated commands or change existing CLI semantics outside the gate/run/report/summary path required for this feature.
10. Read the current implementations of `run`, `score`, `compare`, `summary`, the README, and the latest build contracts before changing code.

## 3. Feature Deliverables

### D1. Core gate engine + CLI wiring

Build a new command that evaluates a project and exits cleanly with PASS/FAIL semantics.

Required files:
- `agentkit_cli/gate.py`
- `agentkit_cli/commands/gate_cmd.py`
- `agentkit_cli/main.py`

Required behavior:
- New command: `agentkit gate`
- Run the existing toolkit pipeline needed to compute a composite score without re-implementing tool orchestration
- Support `--min-score N` as the base pass/fail threshold
- Exit 0 on pass, exit 1 on fail, exit >1 only for real execution errors
- Terminal output must make the verdict obvious and show the score/reason

Checklist:
- [ ] Gate engine created
- [ ] CLI command registered
- [ ] `--min-score` supported
- [ ] Deterministic pass/fail exit codes implemented
- [ ] Tests for D1

### D2. Baseline + regression-aware gating

Add the feature that makes this useful in real CI, not just as a wrapper around score.

Required files:
- `agentkit_cli/gate.py`
- `agentkit_cli/commands/gate_cmd.py`
- `tests/test_gate.py`

Required behavior:
- Support `--baseline-report PATH` to compare current results against a prior `agentkit report --json` artifact
- Support `--max-drop N` to fail if the composite score drops by more than N points from the baseline
- If both `--min-score` and `--max-drop` are provided, both rules must be enforced and the output must explain which one failed
- Baseline parsing must be deterministic and produce a clear user-facing error for invalid/missing files

Checklist:
- [ ] `--baseline-report` supported
- [ ] `--max-drop` supported
- [ ] Multiple rules enforced together
- [ ] Invalid baseline handling is clean
- [ ] Tests for D2

### D3. Machine-readable outputs + GitHub-friendly surfaces

Make the gate usable in workflows and status reporting.

Required files:
- `agentkit_cli/gate.py`
- `agentkit_cli/commands/gate_cmd.py`
- `README.md`
- `tests/test_gate.py`

Required behavior:
- Support `--json` with a stable object containing verdict, score, threshold inputs, failure reasons, and baseline delta when applicable
- Support `--output PATH` to write the JSON payload to disk
- Support `--job-summary` / `GITHUB_STEP_SUMMARY` to emit a concise markdown verdict block for Actions logs
- JSON mode must stay free of Rich console noise

Checklist:
- [ ] Stable `--json` payload supported
- [ ] `--output PATH` supported
- [ ] `--job-summary` supported
- [ ] GitHub-friendly markdown verdict exists
- [ ] Tests for D3

### D4. Docs, examples, and release readiness

Update docs so this is discoverable and leaves the repo ready for a release decision next cycle.

Required files:
- `README.md`
- `CHANGELOG.md`
- `BUILD-REPORT.md`
- `progress-log.md`
- `agentkit_cli/__init__.py`
- `pyproject.toml`

Checklist:
- [ ] README section with local + CI examples
- [ ] CHANGELOG entry for v0.19.0
- [ ] Version bumped to 0.19.0
- [ ] BUILD-REPORT updated with gate summary
- [ ] progress-log updated after each deliverable
- [ ] Full suite release-ready

## 4. Test Requirements

- [ ] Unit tests for threshold evaluation, baseline parsing, and verdict selection
- [ ] CLI tests for pass/fail exit codes in terminal mode
- [ ] CLI tests for JSON mode and `--output`
- [ ] Integration-style test covering current run vs baseline report regression
- [ ] `python3 -m pytest -q tests/test_gate.py`
- [ ] `python3 -m pytest -q tests/test_report.py`
- [ ] `python3 -m pytest -q`

## 5. Reports

Write progress to `progress-log.md` after each deliverable.
Include:
- what was built
- what tests pass
- what remains
- blockers if any

Update `BUILD-REPORT.md` with a short v0.19.0 section once the feature is complete.

## 6. Stop Conditions

- All deliverables checked and all tests passing -> DONE
- 3 consecutive failed attempts on same issue -> STOP, write blocker report
- Scope creep detected (for example: GitHub Checks API posting, comment bots, hosted baseline storage, branch-aware history DB migration) -> STOP and report the extra scope instead of implementing it
- Any regression in `agentkit run`, `score`, or `report` -> STOP and document it
- All tests passing but docs/report/versioning incomplete -> continue until D4 is done

## 7. Important Context

- Repo: `/Users/mordecai/repos/agentkit-cli`
- v0.18.0 `sweep` is now release-ready locally after full-suite verification (671 passed)
- This feature should build on existing report/summary/score machinery instead of inventing a second scoring path
- Keep the implementation focused: local/baseline file enforcement only, no network services, no hosted state, no new external dependencies unless absolutely required
- When completely finished, print a concise final summary covering verdict logic, tests, and remaining release actions
