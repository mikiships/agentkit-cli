# BUILD-REPORT.md — agentkit-cli v1.25.0 spec grounding

Status: SHIPPED
Date: 2026-04-21
Contract: all-day-build-contract-agentkit-cli-v1.25.0-spec-grounding.md

## Outcome

Completed the spec-grounding pass that fixes the flagship repo's stale next-build recommendation. `agentkit spec` now reasons from current canonical-source readiness and recent shipped/local-ready workflow artifacts before ranking objectives, so it recommends the next honest adjacent increment instead of repeating already-satisfied self-hosting work.

## Deliverable summary

- D1: Added stale-self-hosting regression coverage in the spec command and workflow tests.
- D2: Added planner evidence gathering and ranking for already-satisfied prerequisite detection.
- D3: Emitted a concrete `adjacent-grounding` recommendation with tighter why-now, scope, validation, evidence, and contract-seed fields.
- D4: Pushed the branch, tagged tested release commit `ecf1f46` as `v1.25.0`, published `agentkit-cli==1.25.0`, and reconciled shipped chronology surfaces.

## Validation

- `uv run python -m pytest -q tests/test_source_audit.py tests/test_source_audit_workflow.py tests/test_spec_cmd.py tests/test_spec_workflow.py tests/test_main.py` -> `24 passed in 9.80s`
- `uv run python -m pytest -q` -> `5006 passed, 1 warning in 863.10s (0:14:23)`
- `bash /Users/mordecai/.openclaw/workspace/scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.25.0-spec-grounding` -> `No contradictory success/blocker narratives found.`
- `bash /Users/mordecai/.openclaw/workspace/scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.25.0-spec-grounding` -> `Total findings: 0`
- Local repo truth reproduces the fixed result: `agentkit spec . --json` returns `adjacent-grounding` as the primary recommendation.
- `git push -u origin feat/v1.25.0-spec-grounding` created the remote branch, and the later chronology reconciliation push advanced docs-only head `035ce8a` on origin.
- Annotated tag `v1.25.0` was created and pushed, peeling to tested release commit `ecf1f46`.
- `uvx twine upload --skip-existing dist/agentkit_cli-1.25.0.tar.gz dist/agentkit_cli-1.25.0-py3-none-any.whl` succeeded.
- PyPI verification after propagation: both `https://pypi.org/pypi/agentkit-cli/1.25.0/json` and `https://pypi.org/pypi/agentkit-cli/json` show `1.25.0` live with `agentkit_cli-1.25.0-py3-none-any.whl` and `agentkit_cli-1.25.0.tar.gz`, and the exact version page returns HTTP `200`.

## Status

`SHIPPED`
