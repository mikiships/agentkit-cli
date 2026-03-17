# All-Day Build Contract: agentkit campaign (v0.39.0)

Status: In Progress
Date: 2026-03-17
Owner: Codex execution pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Build `agentkit campaign` — a batch PR submission system that finds repos missing CLAUDE.md and submits PRs across multiple repos in one command. This is the viral flywheel for `agentkit pr`: instead of submitting one PR manually, users can discover + contribute to 10 repos in seconds.

The campaign command:
1. Takes a target spec (GitHub org, language, topic, or a file of repos)
2. Filters for repos that lack CLAUDE.md / AGENTS.md
3. Submits PRs to each (reusing `agentkit pr` logic)
4. Tracks all submitted PRs in the history DB (with campaign_id grouping)
5. Shows a campaign summary: N repos targeted, N PRs opened, N skipped (already have context file)

This contract is considered complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Full test suite must pass at the end (currently 1471 tests; must not regress).
4. New features must ship with docs and report addendum updates in the same pass.
5. CLI outputs must be deterministic and schema-backed where specified.
6. Never modify files outside the project directory (~/repos/agentkit-cli/).
7. Commit after each completed deliverable (not at the end).
8. If stuck on same issue for 3 attempts, stop and write a blocker report to BUILD-REPORT.md.
9. Do NOT refactor, restyle, or "improve" code outside the deliverables.
10. Read existing tests and docs before writing new code.
11. `agentkit pr` is the atomic building block — reuse it, don't rewrite it.
12. Rate-limit GitHub API calls: max 5 PRs per campaign run unless --limit is specified.

## 3. Feature Deliverables

### D1. Campaign Discovery Engine (`agentkit_cli/campaign.py`)

Build a `CampaignEngine` class that:
- `find_repos(target_spec, limit=10, language=None, topic=None, min_stars=None)` → List[RepoSpec]
  - target_spec formats: `github:owner` (org), `topic:ai-agents`, `repos-file:path/to/list.txt`
  - For `github:owner`: call GitHub REST API `/orgs/{owner}/repos` (public only, sorted by stars)
  - For `topic:X`: call GitHub REST API `/search/repositories?q=topic:X+language:python` 
  - For `repos-file:path`: read one `owner/repo` per line from file
- `has_context_file(owner, repo, token=None)` → bool: check if CLAUDE.md or AGENTS.md exists at root of default branch
- `filter_missing_context(repos)` → List[RepoSpec]: keep only repos without context files
- `run_campaign(repos, dry_run=False, file="CLAUDE.md", force=False)` → CampaignResult

CampaignResult has:
- `campaign_id: str` (uuid4, short)
- `submitted: List[PRResult]`
- `skipped: List[RepoSpec]` (already had context file)
- `failed: List[tuple[RepoSpec, str]]`
- JSON-serializable

Required files:
- `agentkit_cli/campaign.py`
- `tests/test_campaign.py` (mock GitHub API calls, no real network)

- [ ] CampaignEngine class with find_repos, has_context_file, filter_missing_context, run_campaign
- [ ] GitHub API calls use GITHUB_TOKEN from env (no token = public rate limit only)
- [ ] Tests for D1 (at least 15 tests, all mocked)

### D2. `agentkit campaign` CLI Command

Wire into `agentkit_cli/main.py` as a new subcommand.

```
agentkit campaign [TARGET] [OPTIONS]

Arguments:
  TARGET  Target spec: github:owner, topic:TOPIC, or repos-file:PATH

Options:
  --limit INTEGER       Max repos to target [default: 5]
  --language TEXT       Filter by language (e.g. python, typescript)
  --min-stars INTEGER   Minimum stars threshold [default: 100]
  --file TEXT           Context file name to generate [default: CLAUDE.md]
  --force               Submit PR even if context file exists
  --dry-run             Show what would happen, no PRs opened
  --json                Output JSON instead of rich table
  --no-filter           Skip the "already has context file" check
  --skip-pr             Only discover repos, don't submit PRs
```

Output (rich table, non-dry-run):
```
Campaign ID: abc123
Target: github:pallets  Limit: 5  Language: python

┌──────────────┬────────────────────┬────────┬────────────────────────────────┐
│ Repo         │ Stars              │ Status │ PR URL                         │
├──────────────┼────────────────────┼────────┼────────────────────────────────┤
│ flask        │ ★ 68k              │ ✅ PR  │ https://github.com/.../pull/42 │
│ click        │ ★ 15k              │ ✅ PR  │ https://github.com/.../pull/7  │
│ jinja        │ ★ 10k              │ ⏭ skip│ Already has CLAUDE.md          │
│ werkzeug     │ ★ 7k               │ ✅ PR  │ https://github.com/.../pull/12 │
│ markupsafe   │ ★ 600              │ ❌ err │ Fork creation failed           │
└──────────────┴────────────────────┴────────┴────────────────────────────────┘
Campaign complete. 3 PRs opened, 1 skipped, 1 failed.
```

Required files:
- Update `agentkit_cli/main.py` (add campaign subcommand)
- `agentkit_cli/commands/campaign_cmd.py`
- `tests/test_campaign_cmd.py` (typer CliRunner tests, mock subprocess/network)

- [ ] CLI wiring and argument parsing
- [ ] Rich table campaign summary output
- [ ] --dry-run shows table with "[DRY RUN]" status, no real PRs
- [ ] --json outputs CampaignResult as JSON
- [ ] Tests for D2 (at least 15 tests)

### D3. Campaign History in History DB

Extend the SQLite history DB (agentkit_cli/history.py) to track campaigns:

- Add `campaigns` table: `campaign_id, target_spec, started_at, completed_at, total_repos, pr_count, skip_count, fail_count`
- Add `campaign_id` column to `runs` table (nullable, FK to campaigns)
- `history.record_campaign(result: CampaignResult)`
- `agentkit history --campaigns` shows campaign-grouped summary (campaign_id, when, PRs opened)
- `agentkit history --campaign-id <id>` shows all PRs from a specific campaign

Required files:
- Update `agentkit_cli/history.py`
- Update `agentkit_cli/commands/history_cmd.py`
- `tests/test_campaign_history.py`

- [ ] DB schema migration (campaigns table + campaign_id in runs)
- [ ] record_campaign method
- [ ] history --campaigns and --campaign-id CLI options
- [ ] Tests for D3 (at least 10 tests)

### D4. `agentkit campaign --share` Integration

After a campaign completes, generate a shareable dark-theme HTML report summarizing:
- Campaign header (target, timestamp, totals)
- Per-repo table with PR links, stars, generated context file score (agentlint score if available)
- "Contribute to Open Source" call-to-action footer linking to agentkit-cli PyPI page

Use `share.py` (existing here.now publisher) if HERENOW_API_KEY is set.

Required files:
- `agentkit_cli/campaign_report.py` (HTML generator)
- Update `campaign_cmd.py` to call share if `--share` flag set
- `tests/test_campaign_report.py`

- [ ] HTML report template (dark theme, matches existing agentkit aesthetics)
- [ ] `--share` flag on campaign command
- [ ] Tests for D4 (at least 8 tests)

### D5. Docs, CHANGELOG, Version Bump, BUILD-REPORT

- Update README.md: add `agentkit campaign` section with example usage, example output table
- Update CHANGELOG.md: v0.39.0 entry documenting all new features
- Bump version: `agentkit_cli/__init__.py` → `"0.39.0"`, `pyproject.toml` → `version = "0.39.0"`
- Write `BUILD-REPORT.md` with: all deliverables status, final test count, how to verify each feature
- Update `agentkit campaign --help` text to match the CLI docs

- [ ] README campaign section
- [ ] CHANGELOG v0.39.0 entry
- [ ] Version bumped in __init__.py and pyproject.toml
- [ ] BUILD-REPORT.md written

## 4. Test Requirements

- [ ] Unit tests for CampaignEngine (D1): mocked GitHub API, discovery logic, context-file check
- [ ] CLI tests for campaign command (D2): CliRunner, mock subprocess for `agentkit pr`
- [ ] DB tests for campaign history (D3): in-memory SQLite, migration, record_campaign
- [ ] HTML report tests (D4): output structure, --share conditional
- [ ] All 1471 existing tests must still pass (run full suite at the end)
- [ ] Total new tests: minimum 50

## 5. Reports

- Write progress to `progress-log-v0.39.0.md` after each deliverable
- Include: what was built, what tests pass, what's next, any blockers
- Final summary when all deliverables done or stopped

## 6. Stop Conditions

- All deliverables checked and all tests passing → DONE, write BUILT status to BUILD-REPORT.md
- 3 consecutive failed attempts on same issue → STOP, write blocker report
- Scope creep detected → STOP, report what's new
- All tests passing but deliverables remain → continue to next deliverable
- Do NOT publish to PyPI — build-loop handles publishing after verification

## 7. Verification Gate (for build-loop, not Codex)

Before build-loop marks SHIPPED:
1. `python3 -m pytest -q` → must show 1521+ tests passing (1471 + 50 new min), 0 failed
2. `agentkit campaign github:pallets --dry-run` → must show discovered repos table
3. `agentkit campaign --help` → must show all documented options
4. `git tag` → must include v0.39.0
5. PyPI: `curl -s https://pypi.org/pypi/agentkit-cli/0.39.0/json | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['info']['version'])"` → must print `0.39.0`
