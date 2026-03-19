# All-Day Build Contract: agentkit pages-org — Public GitHub Pages Org Leaderboard

Status: In Progress
Date: 2026-03-19
Owner: Codex execution pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Add `agentkit pages-org github:<owner>` — a command that scores all public repos in a GitHub organization using the existing `agentkit org` engine, generates a dark-theme HTML org-wide leaderboard, and publishes it to a dedicated GitHub Pages site (a new repo named `<owner>/agentkit-scores` or user-specified). The result is a permanent public URL like `https://<owner>.github.io/agentkit-scores/` that anyone can share.

This extends v0.57.0's GitHub Pages persistence to the org level. The viral mechanic: one command gives any GitHub org a live, shareable AI-readiness scorecard. The `agentkit daily --pages` infrastructure built in v0.57.0 is the model; reuse its git-publish helpers where appropriate.

This contract is considered complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Full test suite must pass at the end (baseline: 2725 passing — do not regress).
4. New features must ship with docs and report addendum updates in the same pass.
5. CLI outputs must be deterministic and schema-backed where specified.
6. Never modify files outside the project directory (~/ repos/agentkit-cli/).
7. Commit after each completed deliverable (not at the end).
8. If stuck on same issue for 3 attempts, stop and write a blocker report.
9. Do NOT refactor, restyle, or "improve" code outside the deliverables.
10. Read existing tests and docs before writing new code.
11. Do NOT publish to PyPI, GitHub, or any external service. Build and test only. The build-loop will publish.
12. Do NOT deploy to here.now or any external URL. Local testing only.

## 3. Feature Deliverables

### D1. OrgPagesEngine core (`agentkit_cli/engines/org_pages.py`)

Build the engine that:
- Accepts a GitHub org name + optional `pages_repo` (default: `<owner>/agentkit-scores`), `pages_path` (default: `docs/`), and `pages_branch` (default: `main`)
- Uses the existing OrgEngine (from `agentkit org`) to score all public repos
- Generates `index.html` (dark-theme, responsive) with:
  - Org name + scan date header
  - Ranked table: repo name, composite score, grade letter (A-F), top finding, last-analyzed date
  - Summary stats bar: repo count, average score, top scorer, most-improved (if history available)
  - Link to each repo's GitHub page
- Generates `leaderboard.json` with structured data (org, scan_date, repos array with name/score/grade/top_finding)
- Handles git clone/pull of `pages_repo`, writes files, commits, pushes (same pattern as `daily_leaderboard.py` v0.57.0)
- Returns `OrgPagesResult` dataclass with `pages_url`, `repos_scored`, `avg_score`, `top_repo`, `published`

Required: ≥ 15 tests in `tests/test_org_pages_d1.py`. Test the engine with mocked subprocess/git calls and mocked OrgEngine results.

### D2. `agentkit pages-org` CLI command (`agentkit_cli/commands/pages_org_cmd.py`)

Wire the engine into a new CLI subcommand:
```
agentkit pages-org github:<owner> [OPTIONS]

Options:
  --pages-repo TEXT     GitHub repo for Pages (default: <owner>/agentkit-scores)
  --pages-path TEXT     Subdirectory in repo for HTML (default: docs/)
  --pages-branch TEXT   Branch (default: main)
  --only-below INT      Only include repos scoring below this threshold (default: include all)
  --limit INT           Max repos to score (default: 50)
  --json                Output JSON result instead of rich table
  --quiet               Suppress progress, print only final URL
  --dry-run             Score repos but skip git push
```

Rich output:
- Progress bar while scoring repos
- Final rich table: org, repos scored, avg score, pages URL
- On `--quiet`: print only the pages URL

Required: ≥ 12 tests in `tests/test_org_pages_d2.py`. Test CLI parsing, option defaults, --dry-run behavior, and error cases (invalid target format, missing GITHUB_TOKEN).

### D3. `agentkit org --pages` flag integration

Add `--pages` and `--pages-repo` flags to the existing `agentkit org` command so users can do:
```
agentkit org github:<owner> --pages
agentkit org github:<owner> --pages --pages-repo myorg/agentkit-scores
```

When `--pages` is set, after scoring, invoke OrgPagesEngine to publish results. Add the Pages URL to the org command's rich output table footer and JSON result.

Required: ≥ 10 tests in `tests/test_org_pages_d3.py`. Verify flag wiring, that --pages triggers publish, and that --dry-run skips push.

### D4. Example GitHub Actions workflow

Create `.github/workflows/examples/agentkit-org-pages.yml`:
```yaml
name: Agentkit Org Leaderboard

on:
  schedule:
    - cron: '0 8 * * 1'   # Every Monday 8 AM UTC
  workflow_dispatch:

jobs:
  leaderboard:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install agentkit-cli
      - run: agentkit pages-org github:${{ github.repository_owner }} --quiet
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

Include a clear README section explaining: (1) how to enable GitHub Pages on the scores repo, (2) how to schedule weekly updates, (3) what the output URL will look like.

Required: ≥ 8 tests in `tests/test_org_pages_d4.py`. Validate workflow YAML structure (parse it, check required fields).

### D5. Docs, CHANGELOG, version bump, BUILD-REPORT

- Bump version from `0.57.0` → `0.58.0` in `pyproject.toml` and `agentkit_cli/__init__.py`
- Add CHANGELOG entry for v0.58.0 with feature description
- Add `agentkit pages-org` section to README under "Publishing & Sharing" heading
- Update `docs/index.html` (GitHub Pages landing): add "Org Leaderboard" nav entry and update test count stat
- Write `BUILD-REPORT.md` with: feature summary, test count before/after, all deliverable statuses checked
- Fix any stale version assertions in existing tests (grep for `"0.57.0"` and update to `"0.58.0"`)

Required: ≥ 5 tests in `tests/test_org_pages_d5.py`. Test version string, CHANGELOG entry presence, README section presence.

## 4. Validation Gate (run before declaring complete)

```bash
# From ~/repos/agentkit-cli/
python3 -m pytest -q --tb=short 2>&1 | tail -5
# Must show: X passed, 0 failed (X >= 2780)

agentkit pages-org --help  # Must print usage without error
agentkit org --help         # Must show --pages flag
```

All deliverable checklists must be checked.

## 5. Stop Conditions

- If OrgEngine import is broken or OrgPagesEngine can't be integrated cleanly: write blocker report, stop.
- If GitHub Pages git-push flow fails after 3 attempts: implement `--dry-run` as default and write blocker note.
- Do NOT attempt to push to any real GitHub repo. All git operations in tests must be mocked.
- Do NOT modify any file outside `~/repos/agentkit-cli/`.
- Do NOT run `pip install`, `twine upload`, `gh release create`, or any publish commands.

## 6. Baseline Reference

Current passing: 2725 tests (v0.57.0)
Target: ≥ 2780 tests (baseline + ≥55 new)
PyPI current: https://pypi.org/project/agentkit-cli/0.57.0/
GitHub current: tag v0.57.0

## 7. Key Files to Read First

- `agentkit_cli/engines/daily_leaderboard.py` — the v0.57.0 GitHub Pages publish pattern to follow
- `agentkit_cli/commands/daily_cmd.py` — how `--pages` flag is wired in daily command
- `agentkit_cli/commands/org_cmd.py` — existing org command to extend with `--pages`
- `agentkit_cli/engines/org_engine.py` — existing org engine to reuse
- `tests/test_daily_pages_d1.py` — example test pattern for Pages engine
