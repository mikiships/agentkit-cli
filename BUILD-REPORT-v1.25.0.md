# BUILD-REPORT.md — agentkit-cli v1.25.0 spec grounding

Status: RELEASE-READY (LOCAL-ONLY)
Date: 2026-04-21
Contract: all-day-build-contract-agentkit-cli-v1.25.0-spec-grounding.md

## Outcome

Completed the spec-grounding pass that fixes the flagship repo's stale next-build recommendation. `agentkit spec` now reasons from current canonical-source readiness and recent shipped/local-ready workflow artifacts before ranking objectives, so it recommends the next honest adjacent increment instead of repeating already-satisfied self-hosting work.

## Deliverable summary

- D1: Added stale-self-hosting regression coverage in the spec command and workflow tests.
- D2: Added planner evidence gathering and ranking for already-satisfied prerequisite detection.
- D3: Emitted a concrete `adjacent-grounding` recommendation with tighter why-now, scope, validation, evidence, and contract-seed fields.
- D4: Updated local version and report surfaces for truthful `v1.25.0` closeout.

## Validation

- `uv run python -m pytest -q tests/test_source_audit.py tests/test_source_audit_workflow.py tests/test_spec_cmd.py tests/test_spec_workflow.py tests/test_main.py` -> `24 passed in 4.08s`
- `uv run python -m pytest -q` -> `5006 passed, 1 warning in 542.29s (0:09:02)`
- Full-suite closeout also preserved the existing daily build-report guard by keeping a verified test-count number in `BUILD-REPORT.md`.
- Local repo truth now reproduces the fixed result: `agentkit spec . --json` returns `adjacent-grounding` as the primary recommendation.

## Status

`RELEASE-READY (LOCAL-ONLY)`
