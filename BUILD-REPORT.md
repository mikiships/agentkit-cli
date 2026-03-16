# BUILD-REPORT: agentkit-cli v0.29.0 — `agentkit trending`

Date: 2026-03-15
Contract: all-day-build-contract-agentkit-cli-v0.29.0-trending.md

## Deliverable Status

| # | Deliverable | Status |
|---|------------|--------|
| D1 | `agentkit_cli/trending.py` — GitHub trending/popular fetcher | ✅ DONE |
| D2 | `agentkit_cli/commands/trending_cmd.py` — CLI command, registered in main.py | ✅ DONE |
| D3 | `agentkit_cli/trending_report.py` — HTML report generation + here.now publish | ✅ DONE |
| D4 | Version bump, CHANGELOG, README, BUILD-REPORT, progress-log | ✅ DONE |

## Test Results

- **New tests:** 49 (across test_trending.py)
- **Total suite:** 1106 passed, 0 failed
- **Test categories covered:**
  - D1: fetch_trending() — period filtering, topic filtering, rate-limit handling, network errors, token auth, limit capping, empty results
  - D1: fetch_popular() — all categories, invalid category, limit, rate-limit
  - D2: CLI flags — --no-analyze, --json, schema validation, --min-stars, --limit, --period, --topic, --share, fallback on publish error, command registration
  - D3: generate_html() — structure, repo names, links, stars, version, pip install, dark theme colors, null score handling, empty results
  - Integration: --no-analyze end-to-end with mocked GitHub response (single repo, multiple repos, filter by min-stars)

## Files Created/Modified

### New
- `agentkit_cli/trending.py` — fetch_trending(), fetch_popular(), graceful rate-limit handling
- `agentkit_cli/trending_report.py` — generate_html(), publish_report() (3-step here.now API)
- `agentkit_cli/commands/trending_cmd.py` — trending_command() with all flags
- `tests/test_trending.py` — 49 tests

### Modified
- `agentkit_cli/main.py` — registered @app.command("trending")
- `agentkit_cli/__init__.py` — bumped to v0.29.0
- `pyproject.toml` — bumped to v0.29.0
- `CHANGELOG.md` — added [0.29.0] entry
- `README.md` — added trending to commands table + "Trending Analysis" section

## Feature Summary

`agentkit trending` fetches trending/popular GitHub repos via the GitHub Search API and optionally scores each with `agentkit analyze`. Key behaviors:

- **Fetching:** merges trending (by creation date) + popular (by topic/category) repos, deduplicating by full_name
- **Scoring:** calls analyze_target() for each repo unless --no-analyze is set
- **Ranking:** sorts by score desc (unscored repos last), renumbers ranks
- **Output:** Rich table in terminal; JSON with --json; dark-theme HTML report with --share
- **Publish:** 3-step here.now API; falls back to ./trending-report.html if publish fails
- **Rate limits:** graceful warning + empty list on 403 or network error; supports GITHUB_TOKEN
