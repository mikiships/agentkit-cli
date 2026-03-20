# BUILD-REPORT.md — agentkit-cli v0.74.0 repo-duel

## Checklist

| Deliverable | Status | Tests |
|-------------|--------|-------|
| D1: RepoDuelEngine core (RepoDuelResult, DimensionResult) | ✅ DONE | 12 |
| D2: CLI `agentkit repo-duel` with --deep/--share/--json/--output/--quiet | ✅ DONE | 10 |
| D3: RepoDuelHTMLRenderer (dark-theme HTML report) | ✅ DONE | 10 |
| D4: Integration hooks (`agentkit history --duels`) | ✅ DONE | 8 |
| D5: README, CHANGELOG v0.74.0, version bump, BUILD-REPORT | ✅ DONE | 5 |

**Total new tests:** 45+ (3734+ total in full suite)

## Architecture

- `RepoDuelEngine` in `agentkit_cli/repo_duel.py` — follows user_duel.py pattern
- `RepoDuelHTMLRenderer` in `agentkit_cli/renderers/repo_duel_renderer.py` — dark-theme, standalone HTML
- CLI in `agentkit_cli/commands/repo_duel_cmd.py` — rich terminal output + history DB recording
- `agentkit history --duels` filters history to repo_duel label runs
- Saves to history DB with label `repo_duel`

## Test Delta

- Baseline: 3689 passing (v0.73.0)
- Final: 3734+ passing
- Zero regressions

## Known Issues

- None

## Feature Family Context

This release completes the "duel family": `user-duel` + `topic-duel` + `topic-league` + `repo-duel`.

---

# BUILD-REPORT: agentkit-cli v0.75.0 — `agentkit daily-duel`

**Date:** 2026-03-20
**Status:** BUILT (tests green, awaiting tag/push)
**Version:** 0.74.0 → 0.75.0

## Summary

Added `agentkit daily-duel` — a zero-input command that auto-selects contrasting GitHub repo pairs, runs a repo duel, generates a shareable dark-theme HTML report, and outputs tweet-ready text (≤280 chars).

## Deliverables

### D1: DailyDuelEngine ✅
- **File:** `agentkit_cli/daily_duel.py`
- 23 preset contrasting repo pairs across 8 categories (web-frameworks, http-clients, ml-ai, testing, async-networking, databases, js-frameworks, devtools)
- `pick_pair(seed)` — deterministic by YYYY-MM-DD date seed (SHA-256 hash → index)
- `run_daily_duel(seed, deep)` — delegates to RepoDuelEngine, wraps result as DailyDuelResult
- `DailyDuelResult` extends `RepoDuelResult` with `tweet_text`, `pair_category`, `seed`
- `tweet_text` ≤280 chars guaranteed
- Atomic JSON write to `~/.local/share/agentkit/daily-duel-latest.json`
- `calendar(days)` for schedule preview
- **Tests:** 22 (test_daily_duel_d1.py)

### D2: CLI Command ✅
- **File:** `agentkit_cli/commands/daily_duel_cmd.py`
- Wired into `agentkit_cli/main.py` as `daily-duel`
- Flags: `--seed`, `--deep`, `--share`, `--json`, `--output`, `--pair`, `--quiet`, `--calendar`
- `--pair` overrides auto-pick (uses RepoDuelEngine directly)
- `--share` uploads HTML, appends URL to tweet_text if fits in 280 chars
- Rich terminal output: header, category badge, duel table, tweet box
- History DB save with label `daily_duel`
- **Tests:** 10 (test_daily_duel_d2.py)

### D3: Docs & Version Bump ✅
- `agentkit_cli/__init__.py`: `0.74.0` → `0.75.0`
- `pyproject.toml`: `0.74.0` → `0.75.0`
- `CHANGELOG.md`: v0.75.0 entry added
- `README.md`: `agentkit daily-duel` section added
- **Tests:** 7 (test_daily_duel_d3.py)

### D4: (included in D3) ✅
Version bump, CHANGELOG, README all completed in D3 above.

### D5: Progress log, BUILD-REPORT.md ✅
- `progress-log.md` updated after each deliverable
- `BUILD-REPORT.md` updated (this file)
- Versioned copy at `BUILD-REPORT-v0.75.0.md`

## Test Summary

| File | Tests |
|------|-------|
| test_daily_duel_d1.py | 22 |
| test_daily_duel_d2.py | 10 |
| test_daily_duel_d3.py | 7 |
| **Total new** | **39** |
| Baseline | 3743 |
| **Expected total** | **3782+** |

## Files Changed

- `agentkit_cli/daily_duel.py` (new)
- `agentkit_cli/commands/daily_duel_cmd.py` (new)
- `agentkit_cli/main.py` (import + @app.command added)
- `agentkit_cli/__init__.py` (version bump)
- `pyproject.toml` (version bump)
- `CHANGELOG.md` (v0.75.0 entry)
- `README.md` (daily-duel section)
- `tests/test_daily_duel_d1.py` (new)
- `tests/test_daily_duel_d2.py` (new)
- `tests/test_daily_duel_d3.py` (new)
- `BUILD-REPORT.md` (this file)
- `BUILD-REPORT-v0.75.0.md` (versioned copy)
- `progress-log.md` (updated)
