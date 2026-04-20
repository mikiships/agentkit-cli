# BUILD-REPORT.md — agentkit-cli v1.3.0 repo map

Date: 2026-04-20
Builder: subagent release completion pass
Contract: all-day-build-contract-agentkit-cli-v1.3.0-release.md
Status: SHIPPED, VERIFIED, AND CHRONOLOGY-RECONCILED

## Summary

Shipped `agentkit map`, a deterministic repo explorer that turns a local checkout into an agent-ready architecture map with entrypoints, scripts, tests, subsystem candidates, work-surface hints, risk flags, and a contract handoff block.

## Deliverables

| # | Deliverable | Status | Notes |
|---|-------------|--------|-------|
| D1 | Release-state audit and repo cleanup | ✅ Complete | Reconciled dirty release state, lockfile drift, and contract/report noise before any release claims |
| D2 | Validation baseline | ✅ Complete | Re-ran the focused map slice and the full supported pytest suite on the reconciled repo state |
| D3 | Git release surfaces | ✅ Complete | Pushed `feat/v1.3.0-map` to origin and created the annotated `v1.3.0` tag at the tested release commit |
| D4 | PyPI publish and registry verification | ✅ Complete | Built wheel and sdist, published `agentkit-cli==1.3.0`, and verified the live registry state directly |
| D5 | Final chronology reconciliation | ✅ Complete | Reconciled repo reports to the shipped truth, reran contradiction/hygiene checks, and left a clean release handoff |

## Validation

- focused map release slice: `uv run pytest -q tests/test_map.py tests/test_main.py tests/test_landing_d5.py tests/test_user_scorecard_d5.py` -> `28 passed in 0.95s`
- final full suite: `uv run pytest -q` -> `4833 passed, 1 warning in 134.24s (0:02:14)`
- release recall: `bash /Users/mordecai/.openclaw/workspace/scripts/pre-action-recall.sh release agentkit-cli /Users/mordecai/repos/agentkit-cli-v1.3.0-map` -> completed
- contradiction scan: `bash /Users/mordecai/.openclaw/workspace/scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.3.0-map` -> no contradictory success/blocker narratives found
- hygiene check: `bash /Users/mordecai/.openclaw/workspace/scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.3.0-map` -> clean

## Release Verification

- tested release commit: `c4d4489cbf2342e2ad8bf691466428c3291607dc`
- origin branch ref for the release line: `origin/feat/v1.3.0-map` at the tested release commit before final chronology commits, then advanced only for report reconciliation
- shipped annotated tag: `v1.3.0` -> tag object `07346849f99e638981250faa6350d6ceaf1ce061`, peeled commit `c4d4489cbf2342e2ad8bf691466428c3291607dc`
- local build artifacts: `dist/agentkit_cli-1.3.0.tar.gz` and `dist/agentkit_cli-1.3.0-py3-none-any.whl`
- PyPI live: `https://pypi.org/pypi/agentkit-cli/1.3.0/json` lists both `agentkit_cli-1.3.0.tar.gz` and `agentkit_cli-1.3.0-py3-none-any.whl`
- PyPI page: `https://pypi.org/project/agentkit-cli/1.3.0/` returned `HTTP/2 200`
