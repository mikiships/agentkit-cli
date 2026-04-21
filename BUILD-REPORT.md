# BUILD-REPORT.md — agentkit-cli v1.25.0 spec grounding

Status: SHIPPED
Date: 2026-04-21
Contract: all-day-build-contract-agentkit-cli-v1.25.0-spec-grounding.md

## Deliverables

| Deliverable | Status | Notes |
| --- | --- | --- |
| D1 | ✅ Complete | Added deterministic stale-self-hosting regressions that pin the flagship failure where `agentkit spec` re-proposes already-satisfied self-hosting work. |
| D2 | ✅ Complete | Grounded recommendation ranking in canonical-source readiness plus recent shipped/local-ready workflow evidence so stale prerequisites no longer outrank the next adjacent build. |
| D3 | ✅ Complete | Tightened the primary recommendation and contract seed so markdown and JSON output explain the concrete adjacent spec-grounding increment. |
| D4 | ✅ Complete | Pushed `feat/v1.25.0-spec-grounding`, tagged tested release commit `ecf1f46` as annotated `v1.25.0`, published `agentkit-cli==1.25.0`, and verified PyPI plus chronology surfaces. |

## Validation

- `uv run python -m pytest -q tests/test_spec_cmd.py tests/test_spec_workflow.py tests/test_main.py` -> `18 passed in 1.10s`
- `uv run python -m pytest -q tests/test_source_audit.py tests/test_source_audit_workflow.py tests/test_spec_cmd.py tests/test_spec_workflow.py tests/test_main.py` -> `24 passed in 9.80s`
- `uv run python -m agentkit_cli.main spec . --json` returns `primary_recommendation.kind=adjacent-grounding`.
- `uv run python -m pytest -q` -> `5006 passed, 1 warning in 863.10s (0:14:23)`
- `bash /Users/mordecai/.openclaw/workspace/scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.25.0-spec-grounding` -> `No contradictory success/blocker narratives found.`
- `bash /Users/mordecai/.openclaw/workspace/scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.25.0-spec-grounding` -> `Total findings: 0`
- `git push -u origin feat/v1.25.0-spec-grounding` -> remote branch now exists at docs-only chronology head `853a648`
- `git tag -a v1.25.0 -m "agentkit-cli v1.25.0" ecf1f46 && git push origin v1.25.0` -> remote annotated tag `v1.25.0` peels to tested release commit `ecf1f46`
- `uvx twine upload --skip-existing dist/agentkit_cli-1.25.0.tar.gz dist/agentkit_cli-1.25.0-py3-none-any.whl` completed successfully from detached release commit `ecf1f46`
- `https://pypi.org/pypi/agentkit-cli/1.25.0/json` and `https://pypi.org/pypi/agentkit-cli/json` both report `info.version=1.25.0` with wheel plus sdist live, and `https://pypi.org/project/agentkit-cli/1.25.0/` returns HTTP `200`

## Current truth

- `agentkit-cli v1.25.0` is shipped.
- Tested shipped release commit: `ecf1f46` (`chore: close out v1.25.0 local release state`).
- Later branch head `853a648` remains docs-only chronology after the shipped tag.
- The flagship repo now self-specs the honest next adjacent build instead of recycling the already-satisfied self-hosting/source-readiness objective.
