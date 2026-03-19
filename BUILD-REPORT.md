# BUILD-REPORT — agentkit-cli v0.60.0

**Build date:** 2026-03-19
**Feature:** `agentkit pages-trending`

## Summary

Added `agentkit pages-trending` command — fetch today's trending GitHub repos, score them for agent-readiness with agentkit heuristics, and publish a dark-theme daily leaderboard to GitHub Pages at `https://<owner>.github.io/<repo>/trending.html`.

## Deliverables

### D1: TrendingPagesEngine core ✅
- `agentkit_cli/engines/trending_pages.py`
- Fetches trending repos via existing `agentkit_cli.trending.fetch_trending` infrastructure
- Scores repos using `_score_repo()` heuristic (stars, language, description keywords)
- Generates dark-theme `trending.html` with date, ranked repos, score breakdown, subscribe CTA
- `leaderboard.json` alongside HTML with structured data
- GitHub Pages publish: clones/pulls target repo, writes to `docs/` path, commits+pushes
- Handles: rate limits (graceful skip via fallback), empty results, clone failures
- Tests: **35 new tests** in `tests/test_trending_pages_d1.py`

### D2: `agentkit pages-trending` CLI command ✅
- `agentkit_cli/commands/pages_trending_cmd.py`
- Wired in `agentkit_cli/main.py`
- Flags: `--pages-repo`, `--limit` (1-50, default 20), `--language`, `--period` (today/week/month), `--dry-run`, `--quiet`, `--share`, `--json`
- Rich progress display
- Auto-detects pages-repo from current git remote
- Tests: **25 new tests** in `tests/test_trending_pages_d2.py`

### D3: GitHub Actions workflow ✅
- `.github/workflows/examples/agentkit-trending-pages.yml`
- Cron: daily at 8 AM UTC
- Uses `GITHUB_TOKEN`
- Inputs: `limit`, `language`, `period`
- Updates `docs/index.html` nav after publish
- Tests: **14 new tests** in `tests/test_trending_pages_d3.py`

### D4: Docs and `docs/index.html` update ✅
- `docs/index.html`: "Daily Trending" feature card and nav link
- "Subscribe to daily AI-ready repos" CTA pointing to agentkit-trending repo
- `agentkit quickstart` next-steps updated to mention `agentkit pages-trending`
- SEO: og:title, og:description, structured JSON data
- Tests: **6 new tests** in `tests/test_trending_pages_d4.py`

### D5: README, CHANGELOG, version bump ✅
- `pyproject.toml`: bumped to `0.59.0`
- `CHANGELOG.md`: new section at top for 0.59.0
- `README.md`: `pages-trending` in commands table + full usage section
- Tests: **10 new tests** in `tests/test_trending_pages_d5.py`

## Test Count

| Suite | Tests |
|-------|-------|
| test_trending_pages_d1.py | 35 |
| test_trending_pages_d2.py | 25 |
| test_trending_pages_d3.py | 14 |
| test_trending_pages_d4.py | 6 |
| test_trending_pages_d5.py | 10 |
| **New total** | **90** |
| Baseline | 2804 |
| **Final total** | **≥2854** |

## Known Issues / Deferred

- `--share` integration with here.now: `upload_html` uses existing publish infrastructure; actual 24h URL only generated when `HERENOW_API_KEY` is set and publish succeeds
- ToolAdapter deep scoring (calling `analyze_target` per repo) is available but not default — the current heuristic is fast and works offline; pass `_prefetched_repos` with `composite_score` fields to use real scores
- Pages repo creation when repo doesn't exist: current behavior is graceful failure with clear error message; auto-create requires GitHub API calls beyond scope

## Files Added/Modified

**New files:**
- `agentkit_cli/engines/trending_pages.py`
- `agentkit_cli/commands/pages_trending_cmd.py`
- `.github/workflows/examples/agentkit-trending-pages.yml`
- `tests/test_trending_pages_d1.py`
- `tests/test_trending_pages_d2.py`
- `tests/test_trending_pages_d3.py`
- `tests/test_trending_pages_d4.py`
- `tests/test_trending_pages_d5.py`

**Modified files:**
- `agentkit_cli/main.py` (added import + `pages-trending` command)
- `agentkit_cli/commands/quickstart_cmd.py` (next-steps mention)
- `docs/index.html` (nav link + feature card)
- `pyproject.toml` (version bump)
- `CHANGELOG.md` (new 0.59.0 section)
- `README.md` (commands table + usage section)
