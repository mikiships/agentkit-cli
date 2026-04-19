# BUILD-REPORT.md — agentkit-cli site freshness

Date: 2026-04-19
Builder: subagent site-freshness pass
Contract: all-day-build-contract-agentkit-cli-v1.2.1-site-freshness.md
Status: COMPLETE

## Summary

Fixed the GitHub Pages front-door freshness drift by making `docs/index.html` and `docs/data.json` share one canonical `frontdoor` payload, routing both the daily refresh and push-time refresh workflows through `agentkit pages-refresh`, and regenerating the checked-in docs artifacts from that supported path.

## Deliverables

| # | Deliverable | Status | Notes |
|---|-------------|--------|-------|
| D1 | Reproduce drift and lock it down with tests | ✅ Complete | Added regression coverage for shared front-door payloads, full index rewrites, reuse-existing-data refreshes, and workflow wiring |
| D2 | Deterministic front-door freshness path | ✅ Complete | `pages_refresh` now rewrites `docs/index.html` from canonical site data instead of regex patching stale HTML |
| D3 | Durable Pages workflow wiring | ✅ Complete | Both workflows now call `agentkit pages-refresh`; push-time shell refresh uses `--from-existing-data` |
| D4 | Docs, reports, and generated artifacts | ✅ Complete | Updated `README.md`, `progress-log.md`, `BUILD-REPORT.md`, `docs/index.html`, and `docs/data.json` |

## Root Cause

Two independent paths were mutating the front door:
- `SiteEngine.generate_index()` carried one set of baked-in shell stats.
- `pages_refresh` and `update-pages.yml` regex-edited `docs/index.html` after the fact.

That let the checked-in landing page drift away from `docs/data.json` and from the actual supported refresh path.

## What Changed

- Added shared front-door stat construction in `agentkit_cli.site_engine.build_frontdoor_stats()`.
- Stored that payload under `frontdoor` in `docs/data.json`.
- Made `SiteEngine.generate_index(site_data=...)` render from the same canonical payload used for `data.json`.
- Replaced regex-based `docs/index.html` mutations with full deterministic rewrites.
- Added `agentkit pages-refresh --from-existing-data` for the non-rescoring path.
- Updated `daily-pages-refresh.yml` to install the local checkout and pass current front-door version/test counts into `agentkit pages-refresh`.
- Updated `update-pages.yml` to refresh the shell via `agentkit pages-refresh --from-existing-data` instead of editing HTML directly.
- Regenerated `docs/index.html` and `docs/data.json` from the supported command path.

## Validation

- Focused freshness slice: `python3 -m pytest -q tests/test_site_engine.py tests/test_pages_refresh.py` -> `84 passed in 0.50s`
- Extended freshness slice: `uv run --python 3.11 --extra api --with pytest pytest -q tests/test_landing_d1.py tests/test_landing_d2.py tests/test_pages_sync_d4.py tests/test_site_engine.py tests/test_pages_refresh.py` -> `113 passed in 0.47s`
- Full suite: `uv run --python 3.11 --extra api --with pytest pytest -q` -> `4821 passed, 1 warning in 127.85s (0:02:07)`
- Status-conflict scan: `0 findings`
- Post-agent hygiene check: `0 findings`

## Generated Artifacts

- `docs/data.json` now includes a canonical `frontdoor` object alongside repo stats.
- `docs/index.html` now renders the same front-door version/test/version-count/package-count payload found in `docs/data.json`.

## Final State

- Front-door shell and backing data are coherent.
- Daily refresh and push-time refresh both use the same supported command path.
- Local validation is green.
