# Progress Log — agentkit-cli v1.24.0 clean JSON stdout

Status: RELEASE-READY (LOCAL-ONLY)
Date: 2026-04-21

## Why this lane exists

Heartbeat found a concrete CLI contract bug in the shipped repo: `agentkit spec --json` prepends `Wrote spec directory: ...` to stdout before the JSON object, which breaks direct machine parsing.

## Root cause

`agentkit_cli/commands/spec_cmd.py` always echoed the spec-directory write notice to stdout, even in JSON mode.

## What changed

- Routed the `Wrote spec directory: ...` notice to stderr when the effective format is JSON.
- Kept the notice on stdout for non-JSON runs.
- Added regression coverage for `spec --output-dir --json` so stdout must remain parseable JSON while stderr still carries the human notice.

## Validation

- `uv run python -m pytest -q tests/test_spec_cmd.py tests/test_spec_workflow.py` -> `8 passed in 9.20s`
- Direct command-path parse proof succeeded:
  - `uv run python -m agentkit_cli.main spec . --output-dir "$tmpdir/specdir" --json > "$tmpdir/spec.json" 2> "$tmpdir/spec.stderr"`
  - `json.loads(Path("$tmpdir/spec.json").read_text())` succeeded
  - stderr contained `Wrote spec directory: ...`
- `uv run python -m pytest -q` -> `5004 passed, 1 warning in 565.34s (0:09:25)`

## Local closeout truth

This lane is `RELEASE-READY (LOCAL-ONLY)`.

## Release-completion rerun

- Re-grounded the dirty partial-release tree instead of trusting the abandoned finisher state.
- Re-ran `bash /Users/mordecai/.openclaw/workspace/scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.24.0-json-clean-stdout` -> no contradictory success/blocker narratives found.
- Re-ran `uv run python -m pytest -q tests/test_spec_cmd.py tests/test_spec_workflow.py` -> `8 passed in 0.94s`.
- Re-proved the direct stdout/stderr contract from the current tree: JSON parsed cleanly from stdout, and stderr carried `Wrote spec directory: ...`.
- Re-ran `uv run python -m pytest -q` -> `5004 passed, 1 warning in 196.61s (0:03:16)`.
- Re-ran `bash /Users/mordecai/.openclaw/workspace/scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.24.0-json-clean-stdout` -> `Total findings: 0`.
- Current truth before any irreversible step: `v1.24.0` is release-ready from this tree, but not shipped until push, tag, and PyPI are directly proven.
