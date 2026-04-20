# BUILD-REPORT.md — agentkit-cli Pages data refresh

Date: 2026-04-19
Builder: subagent pages-data-refresh pass
Contract: all-day-build-contract-agentkit-cli-v1.2.3-pages-data-refresh.md
Status: COMPLETE

## Summary

Fixed the GitHub Pages mixed-state bug by making the supported `agentkit pages-refresh` path regenerate `docs/data.json`, `docs/index.html`, and `docs/leaderboard.html` coherently, including the push-time `--from-existing-data` workflow path that previously only refreshed part of the site.

## Deliverables

| # | Deliverable | Status | Notes |
|---|-------------|--------|-------|
| D1 | Supported refresh path drives generated Pages data | ✅ Complete | `pages-refresh --from-existing-data` now rewrites `docs/data.json`, `docs/index.html`, and `docs/leaderboard.html` together |
| D2 | Regression coverage for mixed-state Pages drift | ✅ Complete | Added regression tests for refreshed timestamps, rebuilt leaderboard output, workflow staging, and coherent docs surfaces |
| D3 | Docs and handoff updates | ✅ Complete | Updated README, CHANGELOG, BUILD-REPORT, and progress log to describe the supported coherent refresh path |

## Root Cause

The push-time workflow was calling the supported command in a partial mode that rewrote `docs/index.html` from existing repo data but left `docs/leaderboard.html` untouched and preserved the stale `docs/data.json` generation timestamp. That allowed checked-in Pages surfaces to look partly current while still carrying stale payload state.

## What Changed

- Added `leaderboard_result_from_data_json()` so the supported refresh path can rebuild leaderboard HTML directly from `docs/data.json`.
- Made `agentkit pages-refresh --from-existing-data` stamp a fresh `generated_at` value every time it runs.
- Made that same path rewrite `docs/leaderboard.html` from the canonical payload before regenerating `docs/index.html`.
- Updated `.github/workflows/update-pages.yml` to stage `docs/leaderboard.html` alongside `docs/data.json` and `docs/index.html`.
- Regenerated the tracked docs artifacts from the supported command path.

## Validation

- Focused pages/site/workflow slice: pending final run
- Full suite: pending final run

## Final State

- Push-time and scoring-based Pages refreshes both flow through one coherent command path.
- `docs/data.json`, `docs/index.html`, and `docs/leaderboard.html` now refresh together.
- Repo is left ready for final validation and clean-state verification.
