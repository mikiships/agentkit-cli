# Build Contract: agentkit-cli v0.73.0 — `agentkit gist`

**Repo:** ~/repos/agentkit-cli
**Baseline:** v0.72.0, 3625 tests passing
**Target version:** 0.73.0
**Goal:** `agentkit gist` — publish analysis output as a GitHub Gist for permanent shareable links. Solves the here.now 24h expiry problem.

## Problem
`--share` uploads to here.now which expires in 24 hours. Users can't share a permanent link to their scorecard or send it to their team later. GitHub Gist gives permanent, indexable, shareable links with no account barrier beyond a GitHub token.

## Deliverables

### D1: GistPublisher core (≥12 tests)
- `agentkit_cli/gist_publisher.py`
- `GistPublisher` class with `publish(content, filename, description, public=False) -> GistResult`
- GistResult: `url`, `gist_id`, `raw_url`, `created_at`
- Auth: GITHUB_TOKEN env var OR gh CLI auth (`gh auth token`)
- Falls back gracefully if no token: prints instructions, does not crash
- Public gists: no token required (unauthenticated GitHub API allows public gist creation)
- Private gists: requires GITHUB_TOKEN

### D2: `agentkit gist` command (≥10 tests)
- `agentkit_cli/commands/gist_cmd.py`
- Usage: `agentkit gist [--from <file>]` — publish a report or analysis output
- If no `--from`: runs quickstart analysis on cwd and publishes that
- `--public` flag (default: private)
- `--description TEXT` — custom gist description
- `--format markdown|html` (default: markdown)
- Prints permanent gist URL on success
- Registered in `agentkit_cli/main.py`

### D3: `--gist` flag on existing commands (≥8 tests)
- `agentkit run --gist` — auto-publishes report as gist after run
- `agentkit report --gist` — publishes HTML report as gist  
- `agentkit analyze github:owner/repo --gist` — publishes analyze output
- Each returns gist URL alongside normal output
- Tests: verify flag passes through and GistPublisher.publish is called

### D4: GitHub Actions integration (≥5 tests)
- Add optional `gist-token` input to `action.yml`
- If provided, auto-publish run results as gist and set `gist-url` output
- Update `.github/workflows/examples/` with gist example
- Tests: mock GitHub API call and verify output

### D5: Docs, version, BUILD-REPORT (≥5 tests)
- README: add `agentkit gist` to command table + usage example
- CHANGELOG: v0.73.0 entry
- Version bump: 0.72.0 → 0.73.0 in pyproject.toml
- BUILD-REPORT-v0.73.0.md
- Version assertion tests updated

## Test Targets
- Baseline: 3625
- New: ≥40
- Total target: ≥3665 passing

## Stop Conditions
- Do NOT publish to PyPI (build-loop handles this)
- Do NOT create GitHub Gists using real API calls during tests (mock all HTTP)
- Do NOT push to git (build-loop handles commits and pushes)
- Full test suite must pass: `python3 -m pytest -q`

## Acceptance Criteria
1. `agentkit gist` command exists and is reachable
2. GistPublisher supports both authenticated (private) and unauthenticated (public) paths
3. `--gist` flag on run/report/analyze
4. All new tests pass
5. Full suite ≥3665 passing
6. Version is 0.73.0 in pyproject.toml
7. BUILD-REPORT-v0.73.0.md written

## Context
- GitHub Gist API: POST https://api.github.com/gists
- Unauthenticated public gist: works, just set `"public": true` in payload
- For authenticated: `Authorization: Bearer <token>` header
- `gh auth token` command gets token from gh CLI if configured
- The `GistPublisher` should be modeled after `HereNowPublisher` in `agentkit_cli/publisher.py`
