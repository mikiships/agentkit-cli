# agentkit-cli

## Objective
Teach the flagship self-spec flow to detect when `flagship-concrete-next-step` is already closed out in the current repo, refuse to replay that same lane, and advance to one fresh adjacent recommendation plus updated flagship source truth.

## Commands
- `python3 -m agentkit_cli.main source-audit . --json`
- `python3 -m agentkit_cli.main spec . --output-dir <temp-dir> --json`
- `python3 -m pytest -q tests/test_source_audit.py tests/test_source_audit_workflow.py tests/test_spec_engine.py tests/test_spec_cmd.py tests/test_spec_workflow.py tests/test_main.py`
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
- Run `python3 -m agentkit_cli.main spec . --output-dir <temp-dir> --json` and confirm it emits the post-closeout flagship recommendation plus `spec.md` and `spec.json`.
- Run `python3 -m pytest -q tests/test_source_audit.py tests/test_source_audit_workflow.py tests/test_spec_engine.py tests/test_spec_cmd.py tests/test_spec_workflow.py tests/test_main.py`.
- Run `uv run python -m pytest -q` for the full-suite confidence pass.

## Deliverables
- Canonical `.agentkit/source.md` aligned with the repo's shipped local truth.
- Successful self-spec output for this repo with a deterministic post-closeout flagship recommendation after concrete-next-step closeout.
- Truthful local report surfaces in `BUILD-REPORT.md`, `FINAL-SUMMARY.md`, `progress-log.md`, `BUILD-TASKS.md`, and `CHANGELOG.md`.
- One local completion commit after validation passes.
