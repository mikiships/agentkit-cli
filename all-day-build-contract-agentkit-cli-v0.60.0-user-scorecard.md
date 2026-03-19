# All-Day Build Contract: agentkit-cli v0.60.0 — `agentkit user-scorecard`

Status: In Progress
Date: 2026-03-19
Owner: Codex execution pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Build `agentkit user-scorecard github:<user>` — automatically fetch all public repos for a GitHub user, analyze each one for agent readiness, and generate a beautiful dark-theme HTML profile card showing:
- Overall developer grade (A/B/C/D)
- Ranked repo table with per-repo score + grade badge
- Top 3 repos + 3 repos most needing improvement
- Total repos analyzed, avg score, context file coverage %
- Shareable URL (here.now) via `--share` flag
- Static HTML page publishable to GitHub Pages via `--pages github:<user>/<repo>`

This is the viral mechanic: every developer gets a `agentkit user-scorecard github:<user> --share` link they can post anywhere. The page footer credits agentkit-cli. It's not just utility — it's social proof at the developer identity level.

This contract is considered complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Full test suite must pass at the end (2886 baseline passing; do not break any).
4. New features must ship with docs and report addendum updates in the same pass.
5. CLI outputs must be deterministic and schema-backed where specified.
6. Never modify files outside the project directory (`~/repos/agentkit-cli/`).
7. Commit after each completed deliverable (not at the end).
8. If stuck on same issue for 3 attempts, stop and write a blocker report.
9. Do NOT refactor, restyle, or "improve" code outside the deliverables.
10. Read existing tests and docs before writing new code.
11. Do NOT run `pip install`, `twine upload`, `git push`, `git tag`, or PyPI publish — build-loop handles those.
12. Do NOT enable GitHub Pages or run `gh api` calls for external deployment.
13. Do NOT modify `pyproject.toml` to change the package version — build-loop sets the version.

## 3. Feature Deliverables

### D1. UserScorecardEngine (`agentkit_cli/user_scorecard.py`)

Core engine that:
- Accepts a GitHub username (from `github:<user>` target spec or bare `<user>`)
- Uses GitHub API (`/users/<user>/repos?type=public&per_page=100`) to list public repos (paginate if needed)
- Runs `AnalyzeEngine` or equivalent subprocess on each repo (with configurable timeout, default 60s per repo)
- Aggregates per-repo scores into a `UserScorecardResult` dataclass:
  - `username: str`
  - `total_repos: int`
  - `analyzed_repos: int` (repos that scored successfully)
  - `skipped_repos: int` (timeout, fork, empty, etc.)
  - `avg_score: float`
  - `grade: str` (A ≥80, B ≥65, C ≥50, D <50)
  - `context_coverage_pct: float` (% repos with CLAUDE.md, AGENTS.md, or AGENTS/ dir)
  - `top_repos: list[RepoResult]` (top 3 by score)
  - `bottom_repos: list[RepoResult]` (bottom 3 by score, only if ≥5 analyzed)
  - `all_repos: list[RepoResult]` (sorted by score desc)
- `RepoResult` dataclass: `name, full_name, score, grade, has_context, error`
- Configuration: `--limit N` (cap repos analyzed, default: 20), `--min-stars N` (skip below threshold, default: 0), `--skip-forks` (default: True, skip forked repos)
- Writes progress to console during analysis (Rich progress bar showing `[user/repo] score X/100`)

Required files:
- `agentkit_cli/user_scorecard.py`

- [ ] UserScorecardEngine class with list_public_repos(), run_analysis(), aggregate()
- [ ] UserScorecardResult + RepoResult dataclasses
- [ ] GitHub pagination support (handle >30 repos)
- [ ] Skip-forks filter, min-stars filter, per-repo timeout
- [ ] Grade calculation (A/B/C/D thresholds)
- [ ] context_coverage_pct calculation (check for CLAUDE.md/AGENTS.md/AGENTS/ in repo via GitHub Contents API or local clone)
- [ ] Tests for D1 (≥18 tests: happy path, pagination, skip-forks, timeout handling, grade calc, coverage %)

### D2. `agentkit user-scorecard` CLI command

Add command to `agentkit_cli/main.py`:
```
agentkit user-scorecard github:<user>
agentkit user-scorecard <user>  # bare username also accepted
```

Flags:
- `--limit N` (default: 20) — max repos to analyze
- `--min-stars N` (default: 0) — skip repos below star count
- `--skip-forks / --no-skip-forks` (default: True) — exclude forked repos
- `--json` — machine-readable JSON output
- `--share` — upload HTML report to here.now and print URL
- `--pages github:<owner>/<repo>` — publish HTML to GitHub Pages (uses existing PagesEngine pattern from org_pages.py)
- `--quiet` — print only final URL (for cron/scripting)
- `--timeout N` (default: 60) — per-repo timeout in seconds

Rich terminal output (when not `--json`):
- Header: `🧑‍💻 Agent Quality Profile: @<user>` with overall grade badge
- Stats row: N repos analyzed · avg score X.X · context coverage Y%
- Top repos table: rank, repo name, score bar, grade badge, context ✓/✗
- "Needs work" section (if ≥5 repos): bottom 3 with score + "run `agentkit analyze github:<user>/<repo>` to improve"
- Footer: "Powered by agentkit-cli" with GitHub Pages URL if applicable

Required files:
- New command in `agentkit_cli/main.py` (import from user_scorecard.py)

- [ ] user-scorecard command with all flags
- [ ] Rich progress display during analysis
- [ ] Rich summary output (header, stats, top/bottom tables)
- [ ] JSON output schema with username, grade, avg_score, context_coverage_pct, repos[]
- [ ] `--pages` integration using existing OrgPagesEngine pattern (or new UserPagesEngine)
- [ ] Tests for D2 (≥12 tests: CLI parsing, output format, --json schema, --quiet, --share, --pages)

### D3. Dark-theme HTML Report (`agentkit_cli/user_scorecard_report.py`)

Generate a self-contained dark-theme HTML profile card:
- Header: GitHub avatar (img from `https://github.com/<user>.png`), username, overall grade A/B/C/D with color (A=green, B=blue, C=yellow, D=red)
- Stats panel: repos analyzed, avg score, context coverage %, grade
- Ranked repo table: repo name (linked to GitHub), score bar (CSS), grade badge, context ✓/✗
- "Improve these" section: bottom 3 repos with copy-paste `agentkit analyze` command
- Footer: "Generated by agentkit-cli · https://github.com/mikiships/agentkit-cli"
- No external CSS/JS dependencies (fully self-contained HTML for here.now / GitHub Pages)
- CSS: same dark theme (#0d1117 background) as existing reports (org_pages.py / trending_pages.py)
- Shareable URL printed after `--share` upload

Required files:
- `agentkit_cli/user_scorecard_report.py`

- [ ] UserScorecardReportRenderer class with render(result) → HTML str
- [ ] Dark-theme CSS matching existing report style
- [ ] Grade color system (A=green, B=blue, C=yellow, D=red)
- [ ] Ranked repo table with score bars
- [ ] Improve-these section with copy-paste CLI commands
- [ ] Footer with agentkit-cli credit and GitHub link
- [ ] Tests for D3 (≥10 tests: HTML structure, grade colors, all sections present, score bar widths)

### D4. GitHub Pages integration + `--share` wiring

Wire `--share` to use `share.py` / `publish.py` pattern (matching existing `agentkit analyze --share`):
- Generate HTML report in temp dir
- POST to here.now API (reuse existing `HereNowPublisher` or equivalent in `share.py`)
- Print shareable URL
- If `--pages github:<owner>/<repo>`: push HTML as `docs/user-scorecard.html` to target repo using `OrgPagesEngine` pattern (clone/pull/commit/push)

- [ ] `--share` wiring: generate HTML → upload to here.now → print URL
- [ ] `--pages` wiring: generate HTML → push to GitHub Pages repo
- [ ] Tests for D4 (≥8 tests: share upload mock, pages push mock, error handling)

### D5. Docs, CHANGELOG, version bump, BUILD-REPORT

- Add `agentkit user-scorecard` to `docs/index.html` feature cards section (one new card: "Developer Profile Card")
- Add quickstart next-steps mention: `agentkit user-scorecard github:<user>`
- CHANGELOG: add `[0.60.0]` entry with full feature list
- Bump version in `pyproject.toml` from `0.59.0` to `0.60.0`
- Write `BUILD-REPORT-v0.60.0.md` in repo root: summary of deliverables, test delta, any notes

- [ ] docs/index.html updated with user-scorecard feature card
- [ ] CHANGELOG.md updated with [0.60.0] entry
- [ ] pyproject.toml version bumped to 0.60.0
- [ ] BUILD-REPORT-v0.60.0.md written
- [ ] `agentkit quickstart` next-steps includes user-scorecard mention

## 4. Test Requirements

- [ ] Unit tests for UserScorecardEngine (D1: ≥18)
- [ ] CLI tests for user-scorecard command (D2: ≥12)
- [ ] HTML report tests for UserScorecardReportRenderer (D3: ≥10)
- [ ] Integration/wiring tests for --share and --pages (D4: ≥8)
- [ ] Docs/changelog tests (D5: ≥5)
- [ ] All 2886 baseline tests must still pass
- [ ] Total target: 2886 + 53 new = ≥2939 passing

## 5. Reports

- Write progress to `progress-log-v0.60.0.md` after each deliverable
- Include: what was built, what tests pass, what's next, any blockers
- Final summary when all deliverables done or stopped

## 6. Stop Conditions

- All deliverables checked and all tests passing → DONE (write final summary, then STOP)
- 3 consecutive failed attempts on same issue → STOP, write blocker report
- Scope creep detected → STOP, report what's new
- Do NOT push, tag, publish, or deploy — build-loop handles that

## 7. Reference Files

Existing patterns to follow (read before writing new code):
- `agentkit_cli/engines/org_pages.py` — GitHub Pages push pattern
- `agentkit_cli/engines/trending_pages.py` — trending report HTML pattern
- `agentkit_cli/share.py` — here.now upload pattern
- `agentkit_cli/analyze.py` — GitHub repo analysis pattern
- `agentkit_cli/sweep.py` — multi-repo sweep pattern
- `agentkit_cli/github_api.py` — GitHub API helpers
- `tests/test_analyze.py` — analyze test patterns
- `tests/test_sweep.py` — sweep test patterns (if exists)
