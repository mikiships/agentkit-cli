# All-Day Build Contract: GitHub Checks API Integration

Status: In Progress
Date: 2026-03-18
Owner: Codex execution pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Add GitHub Checks API integration to agentkit-cli so CI runs post a native GitHub Check Run with
agent quality score, grade, and per-tool breakdown directly visible in the PR UI. When `agentkit run`
or `agentkit gate` runs in a GitHub Actions environment, it should automatically post a Check Run with:
- Summary: composite score + grade
- Per-tool scores as an annotation table
- Pass/fail status based on gate thresholds
- Link to shareable scorecard if `--share` is active

This makes agentkit a first-class GitHub CI citizen with visual PR indicators, not just log output.

This contract is considered complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Full test suite must pass at the end (all 2120+ existing tests must still pass, plus new ones).
4. New features must ship with docs and CHANGELOG updates in the same pass.
5. CLI outputs must be deterministic and schema-backed where specified.
6. Never modify files outside the project directory.
7. Commit after each completed deliverable (not at the end).
8. If stuck on same issue for 3 attempts, stop and write a blocker report.
9. Do NOT refactor, restyle, or "improve" code outside the deliverables.
10. Read existing tests and docs before writing new code.

## 3. Feature Deliverables

### D1. GitHubChecksClient — core API client (`agentkit_cli/checks_client.py`)

Build a thin GitHub Checks REST API client that:
- Creates a Check Run (POST /repos/{owner}/{repo}/check-runs)
- Updates a Check Run with status + output (PATCH /repos/{owner}/{repo}/check-runs/{id})
- Handles auth via GITHUB_TOKEN env var
- Detects GitHub Actions environment: reads GITHUB_REPOSITORY, GITHUB_SHA, GITHUB_HEAD_REF
- Returns check_run_id for subsequent updates

Required files:
- `agentkit_cli/checks_client.py`: GitHubChecksClient class

- [ ] GitHubChecksClient with create_check_run() and update_check_run()
- [ ] Reads GITHUB_REPOSITORY, GITHUB_SHA env vars
- [ ] GITHUB_TOKEN auth header
- [ ] Graceful no-op when not in GitHub Actions env (GITHUB_ACTIONS != 'true')
- [ ] Tests: create/update mock, missing env var, auth, graceful no-op (min 8 tests)

### D2. CheckRun output formatter (`agentkit_cli/checks_formatter.py`)

Build a formatter that converts RunResult/GateResult to GitHub Check Run markdown output:
- Title: "Agent Quality: 87/100 (B)"
- Summary: one-line score + pass/fail
- Text body: markdown table of per-tool scores (tool | score | status | finding)
- Annotations: one annotation per failing tool (level=warning/failure based on score)
- Linked scorecard URL if available

Required files:
- `agentkit_cli/checks_formatter.py`: format_check_output(result, gate_result=None, share_url=None) -> dict

- [ ] format_check_output() returns {"title", "summary", "text", "annotations"}
- [ ] Per-tool table in markdown
- [ ] Annotations array (max 50, annotate failing tools as warnings)
- [ ] Tests: formatting with all tools present, missing tools, gate pass/fail, share URL (min 8 tests)

### D3. Integration with `agentkit run` and `agentkit gate` commands

Wire the checks client into the existing run and gate commands:
- Both commands: add `--checks / --no-checks` flag (default: auto, posts check when GITHUB_ACTIONS=true)
- On start: create a "queued" check run, store check_run_id
- On complete: update with "completed" status, conclusion (success/failure), formatted output
- Error handling: if checks API fails, log warning but don't fail the main command

Required changes:
- `agentkit_cli/commands/run_cmd.py`: add check run lifecycle
- `agentkit_cli/commands/gate_cmd.py`: add check run lifecycle

- [ ] `agentkit run --checks` flag (default auto-detect)
- [ ] Check run created at start, updated at end
- [ ] Gate pass/fail maps to conclusion: success/failure
- [ ] Checks API failure is non-fatal (warns but continues)
- [ ] Tests: mock GitHub env, successful check run, failure handling (min 12 tests)

### D4. `agentkit checks` command for manual use and verification

New CLI command: `agentkit checks`
- `agentkit checks verify`: test that checks API is configured (token present, repo accessible)
- `agentkit checks post [--score 87] [--grade B] [--conclusion success]`: manually post a check run (useful for scripting)
- `agentkit checks status`: show last check run posted in this repo

Required files:
- `agentkit_cli/commands/checks_cmd.py`

- [ ] `agentkit checks verify` command
- [ ] `agentkit checks post` command with score/grade/conclusion flags
- [ ] `agentkit checks status` command (reads from local .agentkit-checks.json)
- [ ] Tests: verify flow, post flow, missing token error (min 10 tests)

### D5. CI workflow update, docs, CHANGELOG, version bump to 0.49.0

- Update GitHub Actions workflow template (`agentkit ci` output) to include GITHUB_TOKEN permission
- Add `checks_integration.md` to docs/ (or update existing CI docs) explaining the feature
- Update README with Checks API section (after badge section)
- CHANGELOG entry for 0.49.0
- Version bump in pyproject.toml and __init__.py
- BUILD-REPORT.md

- [ ] GitHub Actions template includes `checks: write` permission
- [ ] README has Checks API section
- [ ] CHANGELOG entry
- [ ] Version at 0.49.0
- [ ] BUILD-REPORT.md written

## 4. Test Requirements

- [ ] All 2120 existing tests still pass after changes
- [ ] Each deliverable has its own test file (tests/test_checks_client.py, tests/test_checks_formatter.py, tests/test_checks_cmd.py)
- [ ] Integration test: mock GitHub env vars → simulate full run → verify check run created + updated
- [ ] Edge case: non-GitHub env (no GITHUB_ACTIONS) → graceful no-op
- [ ] Edge case: invalid/missing GITHUB_TOKEN → error in verify, warning in run
- [ ] Edge case: checks API rate limit / 422 → non-fatal warning

## 5. Reports

- Write progress to `progress-log.md` in the repo root after each deliverable
- Include: what was built, what tests pass, what's next, any blockers
- Final summary when all deliverables done or stopped

## 6. Stop Conditions

- All deliverables checked and all tests passing → DONE
- 3 consecutive failed attempts on same issue → STOP, write blocker report
- Scope creep detected (new requirements discovered) → STOP, report what's new
- All tests passing but deliverables remain → continue to next deliverable
