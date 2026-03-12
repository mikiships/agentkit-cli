# All-Day Build Contract: agentkit-cli v0.2.0 — doctor + GitHub Action

Status: In Progress
Date: 2026-03-12
Owner: Codex execution pass
Repo: ~/repos/agentkit-cli/
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Add three features to agentkit-cli that make it production-ready for CI/CD and easier to diagnose:

1. `agentkit doctor` — diagnose whether all quartet tools are installed, their versions, and whether they're runnable
2. GitHub Action (`action.yml`) — single action to run the full agentkit pipeline in CI
3. Improved `agentkit run` summary — emit a final Rich summary table showing all step results and pass/fail status

This contract is considered complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Full test suite must pass at the end (all existing 47 tests + new ones).
4. New features must ship with docs and CHANGELOG updates in the same pass.
5. CLI outputs must be deterministic and schema-backed where specified.
6. Never modify files outside the project directory.
7. Commit after each completed deliverable (not at the end).
8. If stuck on same issue for 3 attempts, stop and write a blocker report.
9. Do NOT refactor, restyle, or "improve" code outside the deliverables.
10. Read existing tests and docs before writing new code.

## 3. Feature Deliverables

### D1. `agentkit doctor` command

A diagnostic command that checks whether the quartet tools are installed and functional.

Required behavior:
- Check if `coderace`, `agentmd`, `agentlint`, `agentreflect` are on PATH (via `shutil.which` or subprocess `--version`)
- For each tool: show installed version or "NOT FOUND"
- Exit code 0 if all found, exit code 1 if any missing
- `--json` flag outputs `{"coderace": "1.9.0", "agentmd": "0.6.0", ...}` 
- Rich table output (name | status | version | install command)
- Check agentkit-cli's own version too

Required files:
- `agentkit_cli/commands/doctor_cmd.py` — implementation
- Updated `agentkit_cli/main.py` — register doctor command
- `tests/test_doctor.py` — unit tests (mock subprocess calls)

Checklist:
- [ ] doctor_cmd.py with check_tool() helper
- [ ] Rich table with ✓/✗ per tool
- [ ] --json flag
- [ ] exit 1 on missing tools
- [ ] tests/test_doctor.py with mocked subprocess (10+ tests)
- [ ] doctor registered in main.py

### D2. GitHub Action (action.yml)

A composite GitHub Action that runs `agentkit run` on a repo in CI.

Required files:
- `action.yml` — composite action
- `.github/workflows/examples/agentkit-pipeline.yml` — example workflow

action.yml inputs:
- `skip` (optional): comma-separated steps to skip (generate, lint, benchmark, reflect)
- `benchmark` (optional, default false): enable benchmark step
- `python-version` (optional, default 3.12): Python version
- `fail-on-lint` (optional, default true): exit 1 on agentlint failures

The action should:
1. Set up Python
2. Install agentkit-cli + quartet tools
3. Run `agentkit doctor` first (fast health check)
4. Run `agentkit run` with the given inputs
5. On failure: output clear error message with which step failed

Example workflow should show a realistic GitHub Action usage for a Python repo.

Checklist:
- [ ] action.yml with 4 inputs
- [ ] .github/workflows/examples/agentkit-pipeline.yml
- [ ] README updated with "CI Integration" section showing the action
- [ ] tests/test_action.py — verify action.yml is valid YAML with required keys (5+ tests)

### D3. Improved `agentkit run` summary table

After all pipeline steps complete, emit a final Rich summary table showing:
- Step name | Status (✓ PASS / ✗ FAIL / ⊘ SKIPPED) | Duration | Notes
- Overall line: "X/Y steps passed"
- If `--json`: include summary in JSON output as `summary` key

This replaces/augments the current per-step output with a clean completion view.

Required changes:
- `agentkit_cli/commands/run_cmd.py` — add summary table at end
- `tests/test_run.py` — add tests for summary table output (10+ new tests)

Checklist:
- [ ] Summary table with step/status/duration/notes columns
- [ ] --json summary key
- [ ] Tests for summary output

### D4. Version bump, docs, publish

- Bump version to 0.2.0 in pyproject.toml and __init__.py
- CHANGELOG.md entry for v0.2.0 with all three features
- README updated: add "doctor" to command list, add CI Integration section, update version badge
- Build and publish to PyPI: `python -m build && twine upload dist/*`
- Commit + push + tag v0.2.0 on GitHub

Checklist:
- [ ] version = "0.2.0" in pyproject.toml
- [ ] __version__ = "0.2.0" in __init__.py
- [ ] CHANGELOG.md updated
- [ ] README doctor + CI sections added
- [ ] PyPI published
- [ ] git tag v0.2.0 pushed

## 4. Test Requirements

- [ ] All existing 47 tests still pass
- [ ] New tests: 10+ for doctor, 5+ for action YAML, 10+ for run summary = 25+ new
- [ ] Total target: 70+ tests

## 5. Reports

- Write a BUILD-REPORT.md in ~/repos/agentkit-cli/ at the end
- Include: what was built, test counts, PyPI URL, any issues encountered

## 6. Stop Conditions

- All deliverables checked and all tests passing → DONE, write BUILD-REPORT.md
- 3 consecutive failed attempts on same issue → STOP, write blocker report to BUILD-REPORT.md
- Scope creep detected → STOP, report in BUILD-REPORT.md
