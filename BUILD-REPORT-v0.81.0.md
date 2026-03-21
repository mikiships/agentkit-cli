# BUILD-REPORT: agentkit-cli v0.81.0

**Date:** 2026-03-21
**Feature:** `agentkit hot` — GitHub Trending Repos Agent-Readiness Scorer

## What Shipped

### D1: `agentkit hot` command
- `agentkit_cli/hot.py` — `HotEngine`, `HotResult`, `HotRepoResult` dataclasses, `fetch_github_trending`, `_parse_trending_html`, `_find_most_surprising`, `_build_tweet_text`
- `agentkit_cli/commands/hot_cmd.py` — Typer command wrapper with Rich table output
- Registered in `agentkit_cli/main.py` as `@app.command("hot")`
- Flags: `--language`, `--limit` (max 25), `--tweet-only`, `--share`, `--json`, `--timeout`, `--token`
- Uses `ExistingStateScorer` (no agentmd generation — same circular-scoring fix as daily-duel)
- Fallback repo list when GitHub trending is unavailable

### D2: HTML Report
- `render_hot_html()` in `agentkit_cli/hot.py`
- Dark-theme (#0d1117) table with all scored repos
- Most surprising finding highlighted with ⭐ at top
- `--share` flag uploads to here.now

### D3: `post-hot.sh`
- `scripts/post-hot.sh` — posts via frigatebird, logs to `~/.local/share/agentkit/hot-post-log.jsonl`
- Flags: `--share`, `--dry-run`
- Pattern matches `post-daily-duel.sh` and `post-spotlight.sh`

### D4: Doctor integration
- `check_hot_trending_access()` in `agentkit_cli/doctor.py`
- Check ID: `hot.trending_access`, category: `hot`
- Warns (not fails) when trending is unreachable — hot uses fallback list
- Registered in `run_doctor()`

### D5: Docs, CHANGELOG, version bump
- `__version__` = "0.81.0" in `agentkit_cli/__init__.py`
- `pyproject.toml` version = "0.81.0"
- `CHANGELOG.md` v0.81.0 entry
- `README.md` — new "Trending Repos" section + command list entry
- `BUILD-REPORT.md` (this file)

## Test Count

- `test_hot_d1.py` — 34 tests (engine, fetch, score, tweet generation)
- `test_hot_d2.py` — 12 tests (HTML rendering)
- `test_hot_d3.py` — 11 tests (post-hot.sh)
- `test_hot_d4.py` — 7 tests (doctor integration)
- `test_hot_d5.py` — 12 tests (docs/version/files)

**Total new tests: 76**
**Target: ≥45**

## Deliverable Status

| Deliverable | Status | Tests |
|-------------|--------|-------|
| D1: `agentkit hot` command | ✅ DONE | 34 |
| D2: HTML report | ✅ DONE | 12 |
| D3: `post-hot.sh` | ✅ DONE | 11 |
| D4: Doctor integration | ✅ DONE | 7 |
| D5: Docs/CHANGELOG/version | ✅ DONE | 12 |

## Stop Conditions Check

- GitHub trending fetch: graceful fallback implemented ✅
- ExistingStateScorer importable at `agentkit_cli.existing_scorer.ExistingStateScorer` ✅
- No circular scoring (no agentmd generate called) ✅
- No PyPI publish ✅
- No GitHub push ✅

## Verified Test Count

**4041 tests collected, 4040 passed** (1 pre-existing version-pin test fixed this cycle).
