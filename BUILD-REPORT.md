# BUILD-REPORT.md — agentkit-cli v1.5.0 source audit

Date: 2026-04-20
Builder: OpenClaw subagent execution pass
Contract: all-day-build-contract-agentkit-cli-v1.5.0-source-audit.md
Status: SHIPPED

## Summary

Added a deterministic `agentkit source-audit` lane that checks canonical or fallback source readiness before `map` and `contract`, then completed the full four-surface release checklist for `v1.5.0`.

## Deliverables

| # | Deliverable | Status | Notes |
|---|-------------|--------|-------|
| D1 | Deterministic source-audit engine + schema | ✅ Complete | Canonical-source preference, legacy fallback, required-section checks, ambiguity heuristics, contradiction hints, and stable JSON output |
| D2 | CLI workflow + actionable rendering | ✅ Complete | Added first-class `agentkit source-audit` with rich text, markdown/text output, `--json`, and contract-readiness summary |
| D3 | Docs + workflow handoff + validation | ✅ Complete | README, CHANGELOG, BUILD-REPORT, version metadata, progress log, and workflow coverage now match the new source-audit lane |
| D4 | Git + registry release surfaces | ✅ Complete | Branch pushed, annotated tag `v1.5.0` pushed, and PyPI `agentkit-cli==1.5.0` is live with wheel + sdist |
| D5 | Final chronology reconciliation | ✅ Complete | Repo reports now match the shipped branch/tag/registry truth |

## Validation

- focused source-audit slice: `uv run --python 3.11 --with pytest pytest -q tests/test_source_audit.py tests/test_source_cmd.py tests/test_contract_d2.py tests/test_map.py tests/test_main.py` -> `33 passed in 5.26s`
- workflow handoff slice: `uv run --python 3.11 --with pytest pytest -q tests/test_source_audit.py tests/test_source_audit_workflow.py tests/test_source_cmd.py tests/test_contract_d2.py tests/test_map.py tests/test_main.py` -> `34 passed in 1.26s`
- full suite baseline (pre-release fixup run): `uv run --python 3.11 --with pytest pytest -q` -> `2 failed, 4843 passed, 1 warning in 294.14s (0:04:54)`
- post-fix focused release-surface rerun: `uv run --python 3.11 --with pytest pytest -q tests/test_daily_d5.py tests/test_site_engine.py` -> `39 passed in 0.46s`
- final full suite: `uv run --python 3.11 --with pytest pytest -q` -> `4845 passed, 1 warning in 303.39s (0:05:03)`
- release contradiction scan: `bash /Users/mordecai/.openclaw/workspace/scripts/pre-action-recall.sh release agentkit-cli /Users/mordecai/repos/agentkit-cli-v1.5.0-source-audit && bash /Users/mordecai/.openclaw/workspace/scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.5.0-source-audit` -> no contradictory success/blocker narratives found
- hygiene check: `bash /Users/mordecai/.openclaw/workspace/scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.5.0-source-audit` -> `Total findings: 0`

## Release Truth

- tested release commit and current branch head: `5d340ac` (`test: reconcile v1.5.0 release validation baseline`)
- remote branch: `origin/feat/v1.5.0-source-audit` -> `5d340ac`
- annotated tag: `v1.5.0` object `60613af6dc5c8aca5a00aab51b724b173af80bee`, peeled commit `5d340ac`
- PyPI version JSON: `agentkit-cli/1.5.0` live with:
  - `agentkit_cli-1.5.0-py3-none-any.whl`
  - `agentkit_cli-1.5.0.tar.gz`
- top-level PyPI project JSON now reports `1.5.0`

## Notes

The release-completion sub-agent timed out after the irreversible release steps had already succeeded, so this final chronology reconciliation was completed afterward from source-of-truth surfaces. The package was shipped before this report was rewritten; this report now reflects that shipped truth.