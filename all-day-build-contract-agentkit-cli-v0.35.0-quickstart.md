# All-Day Build Contract: agentkit-cli v0.35.0 — `agentkit quickstart`

Status: In Progress
Date: 2026-03-16
Owner: Codex execution pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Build `agentkit quickstart` — a single command that gives a new user their most impressive agentkit output in under 60 seconds. This is the Show HN hook: someone reads the post, pip installs agentkit-cli, runs `agentkit quickstart`, and gets a beautiful score + shareable URL before they've read the next comment.

The command should:
1. Detect the current project (or accept a GitHub URL via `--repo`)
2. Run `agentkit doctor` to check toolchain readiness (skip tools not installed, degrade gracefully)
3. Run the fastest path to a composite score (use agentmd + agentlint only if coderace takes too long, or run with `--timeout 30`)
4. Print a beautiful Rich summary: score, grade, 3 top findings, a shareable URL (via `--share` if HERENOW_API_KEY or anonymous)
5. End with: "Run `agentkit run .` for the full analysis."

The whole thing must finish in under 60 seconds for a typical repo. Speed is the metric.

This contract is considered complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Full test suite must pass at the end (`python3 -m pytest -q`).
4. New features must ship with docs and report addendum updates in the same pass.
5. CLI outputs must be deterministic and schema-backed where specified.
6. Never modify files outside the project directory.
7. Commit after each completed deliverable (not at the end).
8. If stuck on same issue for 3 attempts, stop and write a blocker report.
9. Do NOT refactor, restyle, or "improve" code outside the deliverables.
10. Read existing tests and docs before writing new code.

## 3. Feature Deliverables

### D1. `agentkit_cli/commands/quickstart.py` — core command

- `agentkit quickstart [target]` (default: `.` for current dir; accepts `github:owner/repo`)
- Step 1: Print a beautiful "🚀 agentkit quickstart" Rich header
- Step 2: Run `agentkit doctor --no-fail-exit` internally, summarize readiness (one line: "N tools ready")
- Step 3: Run composite score analysis with timeout=30s per tool (fast path: skip coderace benchmark if over 20s, use cached result if available from DB history)
- Step 4: Print Rich panel with: Score/Grade, top 3 findings (from agentlint/agentmd), one-line description of next step
- Step 5: If HERENOW_API_KEY set or anonymous, call `agentkit publish` and print the share URL
- Step 6: Print "Next: run `agentkit run <target>` for the full 60-second analysis."
- Flag `--no-share`: skip publishing step
- Flag `--timeout N`: per-tool timeout (default 30)

Required tests (in `tests/test_quickstart.py`):
- test_quickstart_local_project: mock toolkit calls, verify Rich output, verify URL printed
- test_quickstart_github_repo: mock clone + toolkit, verify score displayed
- test_quickstart_no_share: --no-share skips publish step
- test_quickstart_timeout_respected: verify timeout flag is passed through
- test_quickstart_degraded: one tool missing, still runs remaining tools and shows partial score
- test_quickstart_cli_integration: `agentkit quickstart --help` exits 0

### D2. Wire into `agentkit/__main__.py` and update help text

- Register quickstart command
- Add `quickstart` to the help text near the top (it should be the first command new users see)
- Update `agentkit --help` listing to show quickstart prominently

Required test: test that `agentkit --help` includes "quickstart"

### D3. README update

- Add `agentkit quickstart` as the very first example in the README Quick Start section
- Replace current "agentkit analyze github:owner/repo --share" with "agentkit quickstart" as the onboarding entry point
- Keep analyze and other commands, just elevate quickstart

### D4. Show HN draft update (`memory/drafts/show-hn-quartet.md` in the workspace, not in the repo)

- Update the Show HN body to use `agentkit quickstart` as the first command shown
- Update test count to 1330+ (current after v0.34.0)
- Update composite score section to mention the fast path
- Add: "The quickest way to see it: `pip install agentkit-cli && agentkit quickstart`"

NOTE: This file is at `/Users/mordecai/.openclaw/workspace/memory/drafts/show-hn-quartet.md` — it is outside the repo. The agent can write this file directly.

### D5. Docs, CHANGELOG, version bump to v0.35.0, BUILD-REPORT

- Add `quickstart` to README commands table
- CHANGELOG.md: add v0.35.0 entry
- pyproject.toml: bump to 0.35.0
- CREATE `BUILD-REPORT.md` addendum entry for v0.35.0 (append to existing BUILD-REPORT.md)
- Write progress to `memory/contracts/agentkit-cli-v0.35.0-progress.md` in the workspace

## 4. Validation Gates

All of these must be true before declaring done:

- [ ] `python3 -m pytest -q` passes (all tests, not just new ones)
- [ ] `agentkit quickstart --help` runs without error
- [ ] `agentkit quickstart .` runs on the agentkit-cli repo itself and produces output
- [ ] New tests: at least 15 (targeting 20+)
- [ ] No regressions from existing suite
- [ ] Version in pyproject.toml = "0.35.0"
- [ ] CHANGELOG has v0.35.0 entry
- [ ] BUILD-REPORT.md has v0.35.0 addendum
- [ ] Show HN draft updated with `agentkit quickstart` as primary onboarding command

## 5. Stop Conditions

- Stop immediately if: test suite breaks and fix is not obvious after 2 attempts
- Stop immediately if: the quickstart command takes >90s on agentkit-cli repo itself
- Stop immediately if: any tool outside the project directory is modified
- On blocker: write `all-day-build-contract-agentkit-cli-v0.35.0-quickstart-BLOCKER.md` in the repo

## 6. Deliverable Checklist

- [ ] D1: quickstart.py core command + 6 tests
- [ ] D2: __main__.py wiring + help prominence
- [ ] D3: README update
- [ ] D4: Show HN draft updated (workspace path)
- [ ] D5: CHANGELOG + version bump + BUILD-REPORT

## 7. Repo Context

- Repo: ~/repos/agentkit-cli
- Current version: 0.34.0 (1330 tests passing)
- Python: python3
- Test runner: `python3 -m pytest -q`
- Key files: agentkit_cli/commands/, agentkit_cli/__main__.py, tests/
- Pattern: look at agentkit_cli/commands/doctor.py for a similar "meta-command that orchestrates other tools" reference implementation
- ToolAdapter is in agentkit_cli/tools.py — use it for all quartet tool invocations

## 8. Definition of Done

This contract is COMPLETE when all 5 deliverables are checked and all validation gates pass. Write final status to BUILD-REPORT.md addendum.
