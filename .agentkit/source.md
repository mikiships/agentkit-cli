# agentkit-cli

## Objective
Make this repo self-hosted for the repo-understanding lane so `agentkit source-audit`, `agentkit spec`, and the next contract step work cleanly from the repo's own canonical source.

## Commands
- `python3 -m agentkit_cli.main source-audit . --json`
- `python3 -m agentkit_cli.main spec . --output-dir <temp-dir> --json`
- `python3 -m pytest -q tests/test_source_audit.py tests/test_source_audit_workflow.py tests/test_spec_cmd.py tests/test_spec_workflow.py tests/test_main.py`
- `uv run python -m pytest -q`

## Scope
Work only inside this repository. Keep changes narrowly focused on deterministic source, audit, spec, validation, version, and local closeout surfaces for the current build. Leave unrelated features, release automation changes, and external system changes alone.

## Constraints
- Keep outputs deterministic and file-backed.
- Preserve the supported repo-understanding lane `source -> audit -> map -> spec -> contract`.
- Use repo-local commands and artifacts when validating the build.
- No remote push, tag, or publish from this repo state.
- Keep report surfaces truthful: this branch is local-only until all external release surfaces are intentionally completed.

## Validation
- Run `python3 -m agentkit_cli.main source-audit . --json` and confirm `ready_for_contract` is true with no findings.
- Run `python3 -m agentkit_cli.main spec . --output-dir <temp-dir> --json` and confirm it emits a primary recommendation plus `spec.md` and `spec.json`.
- Run `python3 -m pytest -q tests/test_source_audit.py tests/test_source_audit_workflow.py tests/test_spec_cmd.py tests/test_spec_workflow.py tests/test_main.py`.
- Run `uv run python -m pytest -q` for the full-suite confidence pass.

## Deliverables
- Canonical `.agentkit/source.md` ready for the contract lane.
- Successful self-spec output for this repo with a deterministic next-build recommendation.
- Truthful local report surfaces in `BUILD-REPORT.md`, `BUILD-REPORT-v1.24.0.md`, `FINAL-SUMMARY.md`, `progress-log.md`, and `BUILD-TASKS.md`.
- One local completion commit after validation passes.
