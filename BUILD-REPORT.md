# BUILD-REPORT.md — agentkit-cli v1.4.0 contract handoff

Date: 2026-04-20
Builder: subagent release completion pass
Contract: all-day-build-contract-agentkit-cli-v1.4.0-contract-handoff.md
Status: SHIPPED

## Summary

Restored `agentkit contract` on top of the shipped `v1.3.0 map` branch, made the contract flow map-aware, validated the full release baseline, then completed push, tag, and PyPI publish for `v1.4.0`.

## Deliverables

| # | Deliverable | Status | Notes |
|---|-------------|--------|-------|
| D1 | Broader focused validation slice | ✅ Complete | Re-ran the contract, map, main CLI, and release-adjacent docs/help slice on the current branch state |
| D2 | Version metadata bump | ✅ Complete | Bumped package metadata to `1.4.0` in `pyproject.toml`, `agentkit_cli/__init__.py`, and `uv.lock` |
| D3 | Release-readiness docs and changelog | ✅ Complete | Added the `1.4.0` changelog entry and rewrote the active build report surfaces for the local contract-handoff state |
| D4 | Versioned build report | ✅ Complete | Added `BUILD-REPORT-v1.4.0.md` matching the active local release-readiness handoff |
| D5 | Final local truth check | ✅ Complete | Confirmed the branch remains ahead 1 before this pass, then left the repo in truthful local release-ready state with no publish/tag/push actions |

## Validation

- prior focused contract+map slice: `uv run --python 3.11 --with pytest pytest -q tests/test_contract_d2.py tests/test_map.py` -> `16 passed in 5.01s`
- direct contract recheck: `uv run --python 3.11 --with pytest pytest -q tests/test_contract_d2.py` -> `6 passed in 1.03s`
- broader focused release-readiness slice: `uv run --python 3.11 --with pytest pytest -q tests/test_contract_d2.py tests/test_map.py tests/test_main.py tests/test_landing_d5.py tests/test_user_scorecard_d5.py` -> `34 passed in 1.03s`
- full suite release baseline: `uv run --python 3.11 --with pytest pytest -q` -> `4839 passed, 1 warning`

## Release Truth

- branch: `feat/v1.4.0-contract-handoff`
- pushed branch commit: `76c0058 test: finalize v1.4.0 release baseline`
- remote branch: `origin/feat/v1.4.0-contract-handoff` -> `76c00581b283d9bb254def57f9c36dc09b8dfa92`
- annotated tag: `v1.4.0` -> tag object `3c7d1a935b562d2f778302f5e054d68483ce58fe`
- peeled release commit: `76c00581b283d9bb254def57f9c36dc09b8dfa92`
- PyPI: `agentkit-cli==1.4.0` live with wheel + sdist

## Notes

The tagged release commit is the tested baseline commit. Any later repo-surface reconciliation belongs on the branch after tag creation, not inside the shipped tag.
