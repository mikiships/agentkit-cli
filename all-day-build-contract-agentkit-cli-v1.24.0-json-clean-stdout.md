# All-Day Build Contract: agentkit-cli v1.24.0 clean JSON stdout

Status: In Progress
Date: 2026-04-21
Owner: OpenClaw build-loop heartbeat
Scope type: Deliverable-gated

## 1. Objective

Fix the machine-readable contract for `agentkit spec --json` so it emits pure JSON on stdout with no human preamble, while preserving truthful local build surfaces and regression coverage.

## 2. Why this build

Fresh heartbeat evidence from the shipped `v1.23.0` repo:
- Running `.venv/bin/python -m agentkit_cli.main spec . --output-dir <tmp> --json > spec.json` produced a file whose first line was `Wrote spec directory: ...` before the JSON object.
- A direct `json.load()` on that output failed with `JSONDecodeError: Expecting value: line 1 column 1 (char 0)`.
- This is a real product bug, not a shell accident. `--json` must be machine-consumable.

## 3. Deliverables

### D1. JSON-mode behavior fix
- Make `agentkit spec --json` write only JSON to stdout.
- Route any human status text to stderr or suppress it in JSON mode.
- Preserve existing artifact generation behavior for the spec output directory.

### D2. Regression tests
- Add focused tests that fail on any non-JSON stdout contamination in `--json` mode.
- Cover the intended behavior for the spec output directory reporting path.

### D3. Truthful local closeout
- Reconcile `BUILD-REPORT.md`, `FINAL-SUMMARY.md`, and any version-local report surfaces to truthful `RELEASE-READY (LOCAL-ONLY)` state.
- Record the exact validation results and the bug fixed.

## 4. Test Requirements

- Focused tests for the spec command and any touched CLI output helpers
- One direct command-path check proving `agentkit spec --json` can be parsed as JSON from stdout
- `uv run python -m pytest -q`

## 5. Stop Conditions

- All deliverables complete and the command-path JSON parse succeeds -> DONE
- 3 consecutive failed attempts on the same blocker -> STOP and write the exact blocker
- No scope drift into unrelated repo-surface or launch work
