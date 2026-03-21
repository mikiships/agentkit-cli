# BUILD-REPORT: agentkit-cli v0.83.0

**Date:** 2026-03-21
**Feature:** `agentkit site` — Multi-page static site generator

## Deliverables

- [x] **D1: SiteEngine core** (`agentkit_cli/site_engine.py`) — `SiteEngine` class with `generate_site()`, `generate_index()`, `generate_topic_page()`, `generate_repo_page()`, `generate_sitemap()`. Data models: `SitePage`, `SiteConfig`, `PageMeta`, `RepoEntry`, `SiteResult`. 25 tests in `tests/test_site_engine.py`.
- [x] **D2: Dark-theme page templates** — Inline in `site_engine.py`. Index with hero/stats/topics-grid/recent-scores, topic pages with ranked table, repo pages with score breakdown/history chart/GitHub link, sitemap.xml. All pages: dark theme, canonical meta, JSON-LD structured data. 16 tests in `tests/test_site_templates.py`.
- [x] **D3: `agentkit site` CLI command** (`agentkit_cli/commands/site_cmd.py`) — `agentkit site <output-dir>` with `--topics`, `--limit`, `--live`, `--share`, `--deploy`, `--base-url`, `--json`, `--quiet`. Rich progress display. 14 tests in `tests/test_site_command.py`.
- [x] **D4: Integration into existing commands** — `agentkit run --site <dir>` regenerates index.html after run. `agentkit share` supports site directories via `--share` flag. 8 tests in `tests/test_site_integration.py`.
- [x] **D5: Release artifacts** — Version bumped to 0.83.0 in `__init__.py` and `pyproject.toml`. CHANGELOG.md updated with v0.83.0 entry. BUILD-REPORT.md updated.

## Verified Test Count

**4181 passed, 0 failed** (60 new tests added across 4 test files).
