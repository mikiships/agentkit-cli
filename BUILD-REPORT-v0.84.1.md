# BUILD-REPORT: agentkit-cli v0.84.1

**Date:** 2026-03-21
**Feature:** `agentkit populate` + `agentkit site --live` + `agentkit site --deploy`

## Deliverables

- [x] **D1: `agentkit populate`** (`agentkit_cli/populate_engine.py`, `agentkit_cli/commands/populate_cmd.py`) — `PopulateEngine` class with `populate()` method. Fetches top GitHub repos by topic, scores each via `agentkit analyze`, stores in history DB. Flags: `--topics`, `--limit`, `--force`, `--dry-run`, `--json`, `--quiet`. 14 tests in `tests/test_populate.py`.
- [x] **D2: `agentkit site --live`** — Implemented (was "not yet implemented"). Calls `PopulateEngine.populate()` before generating site. Help text updated. 6 tests added to `tests/test_site_command.py`.
- [x] **D3: `agentkit site --deploy`** — Improved implementation: copies site to `docs/` (or `--deploy-dir`), runs `git add + commit + push`. New flags: `--repo-path`, `--deploy-dir`, `--commit-message`, `--no-push`. 8 tests in `tests/test_site_deploy.py`.
- [x] **D4: Integration** — `agentkit run --populate` flag triggers populate after pipeline run. `agentkit doctor` warns when history DB has 0 entries. 6 integration tests in `tests/test_populate_integration.py`.
- [x] **D5: Release artifacts** — Version bumped to 0.84.0. CHANGELOG.md v0.84.0 entry. README "Populate & Deploy" section. BUILD-REPORT.md updated. 5 version/docs tests in `tests/test_v084_release.py`.

## Prior Builds

- v0.83.0: `agentkit site` — Multi-page static site generator
- v0.82.0: `agentkit leaderboard-page` — Public HTML leaderboard
- v0.81.1: `agentkit hot` — Trending repos scoring

## Verified Test Count

**4221+ passed, 0 failed** (39+ new tests added across 5 test files).
