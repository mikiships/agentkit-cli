# BUILD-REPORT.md — agentkit-cli v0.57.0

**Date:** 2026-03-19
**Version:** 0.57.0
**Baseline tests:** 2675 (v0.56.0, 1 pre-existing failure in test_landing_d1)
**Final tests:** 2723 passing ✓ (+48 new tests vs baseline, 0 failures)

---

## Completion Criteria

- [x] `publish_to_pages()` implemented in `agentkit_cli/engines/daily_leaderboard.py`
- [x] `agentkit daily --pages` publishes to GitHub Pages
- [x] `agentkit daily --pages --pages-repo github:owner/repo` targets specific repo
- [x] `agentkit daily --pages --pages-path <path>` overrides output path
- [x] Falls back to `--share` when GitHub Pages publish fails
- [x] GitHub Actions workflow at `.github/workflows/examples/agentkit-daily-leaderboard-pages.yml`
- [x] `docs/index.html` nav link + leaderboard feature card added
- [x] All D1-D5 deliverables have tests (49 new tests across 5 test files)
- [x] `python3 -m pytest -q` passes with ≥2690 total (verified: 2723 passing, 0 failures)
- [x] `pyproject.toml` shows `0.57.0`
- [x] `agentkit_cli/__init__.py` shows `0.57.0`
- [x] CHANGELOG.md has `## [0.57.0]` entry
- [x] All stale `0.56.0` version assertions updated to `0.57.0`
- [x] BUILD-REPORT.md completed

---

## Deliverables

### D1: `publish_to_pages()` in DailyLeaderboardEngine

**Status:** DONE — 13 tests in `tests/test_daily_pages_d1.py`

- `publish_to_pages(html, leaderboard, repo_path, pages_path)` — commit and push HTML + JSON to GitHub Pages
- `_parse_github_pages_url(remote_url, pages_path)` — converts HTTPS and SSH remote URLs to Pages URL
- `_strip_dot_git(s)` — correctly strips `.git` suffix
- Writes `docs/leaderboard.html` and `docs/leaderboard-data.json` (structured top-10 JSON)
- Handles: git not found → graceful error, CalledProcessError → returns `committed: False`
- Returns `{"pages_url": "...", "committed": True/False}`

### D2: `--pages` flag on `agentkit daily`

**Status:** DONE — 11 tests in `tests/test_daily_pages_d2.py`

- `agentkit daily --pages` — publishes to GitHub Pages
- `agentkit daily --pages --pages-repo github:owner/repo` — targets specific repo
- `agentkit daily --pages --pages-path docs/leaderboard.html` — overrides output path
- `agentkit daily --pages --quiet` — prints URL only
- Falls back to `--share` automatically on failure

### D3: GitHub Actions workflow

**Status:** DONE — 10 tests in `tests/test_daily_pages_d3.py`

- `.github/workflows/examples/agentkit-daily-leaderboard-pages.yml`
- Cron: `0 8 * * *` (8 AM UTC daily) + `workflow_dispatch`
- Permissions: `contents: write`, `pages: write`
- Steps: checkout with GITHUB_TOKEN, setup-python, pip install agentkit-cli, git config, run daily --pages

### D4: Landing page nav update

**Status:** DONE — 6 tests in `tests/test_daily_pages_d4.py`

- Nav link: `<a href="leaderboard.html">Daily Leaderboard</a>`
- Feature card: "Daily Leaderboard" with `agentkit daily --pages` description
- Stats bar test count updated to 2690

### D5: Docs, version, CHANGELOG

**Status:** DONE — 9 tests in `tests/test_daily_pages_d5.py`

- `pyproject.toml`: `version = "0.57.0"`
- `agentkit_cli/__init__.py`: `__version__ = "0.57.0"`
- `CHANGELOG.md`: `## [0.57.0] - 2026-03-19` with full Added section
- `README.md`: `--pages`, `--pages-repo`, `--pages-path` documented with GitHub Actions cron example
- All stale `0.56.0` version assertions updated across test files

---

## Test Count Summary

| Deliverable | Test File | Tests |
|---|---|---|
| D1: publish_to_pages | `tests/test_daily_pages_d1.py` | 13 |
| D2: --pages CLI | `tests/test_daily_pages_d2.py` | 11 |
| D3: GH Actions workflow | `tests/test_daily_pages_d3.py` | 10 |
| D4: Landing page | `tests/test_daily_pages_d4.py` | 6 |
| D5: Docs/Version | `tests/test_daily_pages_d5.py` | 9 |
| **New total** | | **49** |

**Verified test count: 2723 passing** (target was ≥2690 ✓)

---

## Files Changed

- `agentkit_cli/engines/daily_leaderboard.py` — added `publish_to_pages()`, `_parse_github_pages_url()`, `_strip_dot_git()`
- `agentkit_cli/commands/daily_cmd.py` — added `--pages`, `--pages-repo`, `--pages-path` logic
- `agentkit_cli/main.py` — wired new flags to `daily` command
- `agentkit_cli/__init__.py` — version bump 0.56.0 → 0.57.0
- `pyproject.toml` — version bump 0.56.0 → 0.57.0
- `CHANGELOG.md` — v0.57.0 entry
- `README.md` — `--pages` documentation + GitHub Actions cron example
- `docs/index.html` — nav link, leaderboard feature card, updated stats
- `.github/workflows/examples/agentkit-daily-leaderboard-pages.yml` — NEW
- `tests/test_daily_pages_d1.py` — NEW (13 tests)
- `tests/test_daily_pages_d2.py` — NEW (11 tests)
- `tests/test_daily_pages_d3.py` — NEW (10 tests)
- `tests/test_daily_pages_d4.py` — NEW (6 tests)
- `tests/test_daily_pages_d5.py` — NEW (9 tests)
- `tests/test_landing_d1.py` — fixed pre-existing stale stat assertion
- All `tests/test_*_d5.py` files + `tests/test_improve.py` + `tests/test_explain.py` — updated `0.56.0` → `0.57.0`
- `BUILD-REPORT.md` — this file
