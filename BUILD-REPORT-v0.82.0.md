# BUILD REPORT — agentkit-cli v0.82.0

## Summary

Implemented `agentkit leaderboard-page` — a command that generates a public HTML leaderboard of top agent-ready GitHub repos by ecosystem.

## Deliverables

### D1: `agentkit leaderboard-page` command
- `agentkit_cli/leaderboard_page.py`: Engine, scoring, HTML rendering, embed badge
- `agentkit_cli/commands/leaderboard_page_cmd.py`: CLI command
- Registered in `agentkit_cli/main.py` as `leaderboard-page`
- Flags: `--output`, `--ecosystems`, `--limit`, `--share`, `--json`, `--pages`, `--embed`, `--embed-only`
- Scores via `ExistingStateScorer.score_all()['composite']` when cloning; heuristic fallback when not
- Dark-theme HTML (#0d1117) with ecosystem tabs, ranked table, timestamps, powered-by badge

### D2: GitHub Pages workflow
- `.github/workflows/update-leaderboard.yml`: Weekly schedule, runs `leaderboard-page --pages`, commits to `docs/leaderboard.html`

### D3: SEO
- Generated HTML includes: `<title>`, `<meta description>`, og: tags, twitter: tags, JSON-LD ItemList

### D4: Embed badge
- `render_embed_badge()` generates shields.io markdown badge snippet
- `--embed github:owner/repo` and `--embed-only` flags supported

### D5: Docs/CHANGELOG/version
- `__version__` bumped to `0.82.0`
- `pyproject.toml` version bumped to `0.82.0`
- CHANGELOG.md entry added for [0.82.0]
- README.md Leaderboard section added
- BUILD-REPORT.md and BUILD-REPORT-v0.82.0.md updated

## Test Coverage
- `tests/test_leaderboard_page_d1.py`: ≥20 tests (engine, scoring, rendering, command integration)
- `tests/test_leaderboard_page_d2.py`: ≥10 tests (workflow file, schedule, steps)
- `tests/test_leaderboard_page_d3.py`: ≥8 tests (SEO: title, meta, og tags, JSON-LD)
- `tests/test_leaderboard_page_d4.py`: ≥8 tests (embed badge)
- `tests/test_leaderboard_page_d5.py`: ≥5 tests (version, docs)
