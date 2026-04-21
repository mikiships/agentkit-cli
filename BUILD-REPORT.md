# BUILD-REPORT.md — agentkit-cli v1.24.0 clean JSON stdout

Status: RELEASE-READY (LOCAL-ONLY)
Date: 2026-04-21
Contract: all-day-build-contract-agentkit-cli-v1.24.0-json-clean-stdout.md

## Deliverables

| Deliverable | Status | Notes |
| --- | --- | --- |
| D1 | ✅ Complete | `agentkit spec --json` now keeps stdout machine-readable and routes the human write notice to stderr when `--output-dir` is used. |
| D2 | ✅ Complete | Added regression coverage for the broken JSON stdout contract and preserved human-facing reporting in non-JSON mode. |
| D3 | ✅ Complete | Local status surfaces now reflect the truthful lane state: `RELEASE-READY (LOCAL-ONLY)`. |

## Root cause

`agentkit_cli/commands/spec_cmd.py` always emitted `Wrote spec directory: ...` to stdout after writing `--output-dir`, even when `--json` selected machine-readable output. That unconditional human preamble contaminated stdout before the JSON payload.

## Validation

- `uv run python -m pytest -q tests/test_spec_cmd.py tests/test_spec_workflow.py` -> `8 passed in 9.20s`
- Direct command-path proof:
  - `uv run python -m agentkit_cli.main spec . --output-dir "$tmpdir/specdir" --json > "$tmpdir/spec.json" 2> "$tmpdir/spec.stderr"`
  - `uv run python - <<'PY' "$tmpdir/spec.json" ... json.loads(...) ... PY` -> `parsed schema_version=agentkit.spec.v1 primary_kind=subsystem-next-step`
  - `cat "$tmpdir/spec.stderr"` -> `Wrote spec directory: ...`
- `uv run python -m pytest -q` -> `5004 passed, 1 warning in 565.34s (0:09:25)`

## Files changed

- `agentkit_cli/commands/spec_cmd.py`
- `tests/test_spec_cmd.py`
- `BUILD-REPORT.md`
- `FINAL-SUMMARY.md`
- `BUILD-TASKS.md`
- `progress-log.md`

## Current truth

- This lane fixes a real stdout JSON contract bug locally.
- Validation is clean, including the full suite.
- The lane is `RELEASE-READY (LOCAL-ONLY)`.
