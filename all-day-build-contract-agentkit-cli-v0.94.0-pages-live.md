# All-Day Build Contract: agentkit-cli v0.94.0 — GitHub Pages Live Leaderboard

Status: In Progress
Date: 2026-03-23
Owner: Codex execution pass
Scope type: Deliverable-gated

## 1. Objective

Make `https://mikiships.github.io/agentkit-cli/` a permanently live, auto-updating leaderboard showing real agent-readiness scores for top GitHub repos. Currently the site shows "0 repos scored" because the leaderboard page is empty and the index.html has no live data.

This builds two things:
1. A daily GitHub Actions cron that runs `agentkit ecosystem --limit 5` for top ecosystems and commits updated HTML to docs/
2. Updates `docs/index.html` to display the most recently scored repos inline on the front page (no "0 repos scored" embarrassment)

This is specifically for Show HN distribution — visitors need to see real data the moment they land. No auth, no install required.

This contract is considered complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Full test suite must pass at the end.
4. New features must ship with docs and report addendum updates in the same pass.
5. CLI outputs must be deterministic and schema-backed where specified.
6. Never modify files outside the project directory.
7. Commit after each completed deliverable (not at the end).
8. If stuck on same issue for 3 attempts, stop and write a blocker report.
9. Do NOT refactor, restyle, or "improve" code outside the deliverables.
10. Read existing tests and docs before writing new code.

## 3. Feature Deliverables

### D1. `agentkit pages-refresh` command (core + CLI)

New command that generates fresh HTML content for GitHub Pages by pulling live scores.

Required behavior:
- `agentkit pages-refresh` — run ecosystem scoring for `python,typescript,rust,go` with limit 5 each
- Write results to `docs/leaderboard.html` (same as `agentkit leaderboard-page --pages`)
- Write a `docs/data.json` file with the top repos and scores (for JavaScript to consume)
- Update stats in `docs/index.html` from `docs/data.json` (repos scored count, top score, median score)
- Print a summary of what was updated

Required files:
- `agentkit_cli/commands/pages_refresh.py` — core logic
- Update `agentkit_cli/cli.py` to register the command
- `tests/test_pages_refresh.py` — at least 12 tests

- [ ] `pages_refresh` command registered and `agentkit pages-refresh --help` works
- [ ] `docs/data.json` generated with structure: `{generated_at, repos: [{name, url, score, grade, ecosystem}], stats: {total, median, top_score}}`
- [ ] `docs/index.html` stat counters updated: `repos scored` counter reflects actual scored repo count
- [ ] Tests for D1 (12+)

### D2. GitHub Actions daily cron workflow

A new workflow `.github/workflows/daily-pages-refresh.yml` that:
- Runs daily at 08:00 UTC (cron: `'0 8 * * *'`)
- Installs agentkit-cli from PyPI (latest)
- Runs `agentkit pages-refresh`
- Commits and pushes `docs/leaderboard.html` + `docs/data.json` + `docs/index.html`
- Workflow can be triggered manually via `workflow_dispatch`

Required files:
- `.github/workflows/daily-pages-refresh.yml`

- [ ] Workflow file exists with correct cron schedule and manual trigger
- [ ] Uses `GITHUB_TOKEN` for git push
- [ ] Commit message: `chore: daily pages refresh [skip ci]`
- [ ] Tests for D2 (5+): test workflow file exists, has required keys

### D3. `docs/index.html` live data display

Update `docs/index.html` to:
- Show a "Recently Scored Repos" section that reads from `docs/data.json` if present, or shows a placeholder if not
- The section should list top 5 repos with name, score, grade chip (A/B/C/D/F), and ecosystem badge
- Use JavaScript `fetch('/agentkit-cli/data.json')` to load and render the data
- The "0 repos scored" stat should now show actual count from data.json

The section should be positioned after the hero and before the commands table.

Required files:
- `docs/index.html` (update in place — the fetch/render script)
- `docs/data.json` (initial seed file)

- [ ] `docs/index.html` has JavaScript that loads `data.json` and renders repo list
- [ ] Initial `docs/data.json` seed file committed (use the 10 repos scored by leaderboard-page command)
- [ ] Repos-scored stat shows real count (not 0)
- [ ] Tests for D3 (8+): test that index.html has fetch script, data.json is valid JSON, required fields present

### D4. Seed initial `docs/data.json` with real data

Run `agentkit leaderboard-page --json` locally, transform to data.json format, commit as the initial seed.

Actually: the `pages-refresh` command from D1 should be run once locally to generate the initial seed. Commit both `docs/leaderboard.html` and `docs/data.json` and `docs/index.html` in this deliverable.

- [ ] `docs/data.json` has at least 8 repos with real scores
- [ ] `docs/leaderboard.html` has matching data
- [ ] Both files committed to git (NOT pushed — build-loop will push)

### D5. README update, CHANGELOG, version bump, BUILD-REPORT

- Update README with a "Live Leaderboard" section pointing to GitHub Pages URL
- Add CHANGELOG entry for v0.94.0
- Bump version to `0.94.0` in `pyproject.toml` and `agentkit_cli/__init__.py`
- Write `BUILD-REPORT.md` in the repo root

- [ ] README has Live Leaderboard section with https://mikiships.github.io/agentkit-cli/leaderboard.html
- [ ] CHANGELOG entry for v0.94.0
- [ ] Version is 0.94.0 in pyproject.toml and __init__.py
- [ ] BUILD-REPORT.md written

## 4. Test Requirements

- [ ] Unit tests for pages_refresh command (D1: 12+)
- [ ] Workflow file tests (D2: 5+)
- [ ] index.html fetch-script tests (D3: 8+)
- [ ] data.json structure tests (D3: 5+)
- [ ] All existing tests must still pass (baseline: 4648)
- [ ] Total target: baseline + 30+ new tests

## 5. Reports

- Write progress to `progress-log.md` after each deliverable
- Final summary in BUILD-REPORT.md when all deliverables done

## 6. Stop Conditions

- All deliverables checked and all tests passing → DONE
- 3 consecutive failed attempts on same issue → STOP, write blocker report
- Scope creep detected → STOP, report what's new
- Tests failing after 3 attempts → STOP, write blocker report

## 7. Context

- Repo: ~/repos/agentkit-cli
- Current version: 0.93.0
- Tests baseline: 4648 passing
- Python: 3.12
- GitHub Pages: https://mikiships.github.io/agentkit-cli/
- Leaderboard page: https://mikiships.github.io/agentkit-cli/leaderboard.html
- GitHub repo: mikiships/agentkit-cli
- The `agentkit leaderboard-page --pages --ecosystems python,typescript --limit 5` command already works and generates docs/leaderboard.html
- The `docs/index.html` stat for "repos scored" currently shows 0 - this is the main embarrassment to fix
- IMPORTANT: Do NOT run `agentkit leaderboard-page` during testing as it makes real network calls — mock all GitHub API calls in tests
