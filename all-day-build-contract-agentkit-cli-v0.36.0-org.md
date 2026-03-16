# All-Day Build Contract: agentkit-cli v0.36.0 — `agentkit org`

Status: In Progress
Date: 2026-03-16
Owner: Codex execution pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Add `agentkit org github:<owner>` — score every public repo in a GitHub org or user account in a single command. Output a ranked leaderboard with score, grade, and per-tool highlights. Optionally share a dark-theme HTML report.

This is the "CTO audit" feature: someone can run `agentkit org github:vercel` and get an immediate ranked view of which repos are most AI-agent-ready. It's the natural step up from `agentkit duel` (2 repos) and `agentkit tournament` (N named repos) — fully automated, no need to know repo names up front.

This contract is considered complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Full test suite must pass at the end.
4. New features must ship with docs and report addendum updates in the same pass.
5. CLI outputs must be deterministic and schema-backed where specified.
6. Never modify files outside the project directory (`~/repos/agentkit-cli/`).
7. Commit after each completed deliverable (not at the end).
8. If stuck on same issue for 3 attempts, stop and write a blocker report.
9. Do NOT refactor, restyle, or "improve" code outside the deliverables.
10. Read existing tests and docs before writing new code.

## 3. Feature Deliverables

### D1. GitHub org/user repo listing + core org command

Build the `agentkit org` command that:
1. Accepts `github:<owner>` as the target (owner can be org or user)
2. Calls the GitHub API (unauthenticated first, `GITHUB_TOKEN` env var for auth) to list all public repos for the owner — paginate to get all repos
3. Filters out forks, archived repos, and empty repos by default
4. Provides `--include-forks`, `--include-archived`, `--limit N` flags
5. For each repo: clone to temp dir, run `agentkit analyze` (which already handles the full toolkit run), capture the composite score
6. Show a Rich live progress display: "Analyzing <N> repos... [3/12] flask ████████░░ 70%"
7. After all repos analyzed: print a Rich ranked table (rank, repo name, score, grade, top finding)

Required files:
- `agentkit_cli/commands/org.py` — core command
- `agentkit_cli/github_api.py` — GitHub REST API client (list repos, handle pagination, rate limit)
- Update `agentkit_cli/__main__.py` to register `org` command

- [ ] `github_api.py` with `list_repos(owner, include_forks, include_archived, token)` → list of repo dicts
- [ ] `OrgCommand` class with full arg parsing
- [ ] Live progress display during multi-repo analysis
- [ ] Ranked Rich table output on completion
- [ ] `--json` output: `{owner, repo_count, ranked: [{repo, score, grade, top_finding}]}`
- [ ] Tests for D1 (mock GitHub API, mock analyze calls)

### D2. HTML report generation + `--share`

1. Generate a dark-theme HTML report matching the visual style of existing reports (duel, tournament, trending)
2. Report includes: org name, analysis date, ranked table with scores/grades, summary stats (avg score, top repo, most common finding)
3. `--share` flag: upload to here.now and print the URL (reuse existing share infrastructure from `agentkit_cli/share.py`)
4. `--output <file>` flag: save HTML to disk

Required files:
- `agentkit_cli/org_report.py` — HTML report generator

- [ ] `OrgReport` class with `render()` method
- [ ] Dark-theme HTML with ranked table and summary stats
- [ ] `--share` via existing here.now upload
- [ ] `--output` saves to disk
- [ ] Tests for D2 (mock share, verify HTML structure)

### D3. Parallel analysis + rate limiting

By default, analyzing 20+ repos sequentially is slow. Add:
1. `--parallel N` flag (default: 3) — analyze up to N repos simultaneously using `concurrent.futures.ThreadPoolExecutor`
2. Respect GitHub API rate limits: check `X-RateLimit-Remaining` header, sleep if near 0
3. `--timeout N` per repo (default: 120s) — skip repos that take too long, mark as "timeout" in results
4. Summary at end: N analyzed, M skipped (timeout), K failed

- [ ] ThreadPoolExecutor-based parallel analysis
- [ ] Rate limit awareness in `github_api.py`
- [ ] Per-repo timeout with graceful skip
- [ ] Parallel tests (mock executor, verify result aggregation)

### D4. Docs, CHANGELOG, version bump, BUILD-REPORT

- [ ] README: add `agentkit org` to command reference and Quick Start section
- [ ] CHANGELOG: v0.36.0 entry
- [ ] `pyproject.toml` version: `0.35.0` → `0.36.0`
- [ ] `agentkit_cli/__init__.py` version: `0.35.0` → `0.36.0`
- [ ] Write/update `BUILD-REPORT.md` with deliverables summary and test count
- [ ] Progress log updated

## 4. Test Requirements

- [ ] Unit tests for `github_api.py` (mock HTTP responses, pagination, rate limiting)
- [ ] Unit tests for `OrgCommand` (mock analyze, test flag parsing, ranked output)
- [ ] Tests for HTML report generation
- [ ] Tests for parallel execution and timeout handling
- [ ] Integration test: mock full org run with 5 fake repos, verify ranked JSON output
- [ ] All existing 1349 tests must still pass

Target: 1349 + 50 new tests minimum = 1399+ total.

## 5. Reports

- Write progress to `progress-log.md` after each deliverable
- Include: what was built, what tests pass, what's next, any blockers
- Final summary when all deliverables done or stopped

## 6. Stop Conditions

- All deliverables checked and all tests passing → DONE
- 3 consecutive failed attempts on same issue → STOP, write blocker report
- Scope creep detected → STOP, report what's new
- All tests passing but deliverables remain → continue to next deliverable

## 7. Reuse guidance

- Look at `agentkit_cli/commands/sweep.py` for multi-target analysis pattern
- Look at `agentkit_cli/commands/tournament.py` for ranked HTML report pattern
- Look at `agentkit_cli/commands/trending.py` for GitHub API + live progress pattern
- Look at `agentkit_cli/share.py` for here.now upload pattern
- Use `agentkit_cli/commands/analyze.py` as the per-repo analysis engine (already handles clone + toolkit run)
