# All-Day Build Contract: agentkit track (v0.40.0)

Status: In Progress
Date: 2026-03-17
Owner: Codex execution pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Build `agentkit track` — a PR status tracker that monitors campaign-submitted PRs and shows which ones got merged, closed, or are still open. This closes the campaign flywheel: users submit PRs via `agentkit campaign`, then use `agentkit track` to see outcomes.

The track command:
1. Reads PR records from the history DB (campaign submissions recorded by `agentkit pr` and `agentkit campaign`)
2. Queries GitHub API to check current PR status (open/merged/closed)
3. Shows a rich table with current status, days open, and review activity
4. Supports `--campaign-id` to filter to a specific campaign
5. Supports `--json` for CI/automation integration
6. Optional `--share` to upload a status report to here.now

This contract is considered complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Full test suite must pass at the end (currently 1537 tests; must not regress).
4. New features must ship with docs and report addendum updates in the same pass.
5. CLI outputs must be deterministic and schema-backed where specified.
6. Never modify files outside the project directory (~/repos/agentkit-cli/).
7. Commit after each completed deliverable (not at the end).
8. If stuck on same issue for 3 attempts, stop and write a blocker report to BUILD-REPORT.md.
9. Do NOT refactor, restyle, or "improve" code outside the deliverables.
10. Read existing tests and docs before writing new code.
11. GitHub API calls must be mocked in tests — no real network calls in the test suite.
12. Rate-limit GitHub API calls: respect X-RateLimit-Remaining headers, back off if < 10 remaining.

## 3. Feature Deliverables

### D1. PR Tracking Engine (`agentkit_cli/pr_tracker.py`)

Build a `PRTracker` class that:
- `get_tracked_prs(db_path, campaign_id=None, limit=50)` → List[TrackedPR]
  - Reads PR records from SQLite history DB
  - Returns PRs recorded by `agentkit pr` and `agentkit campaign` commands
  - Filters by campaign_id if provided
- `fetch_pr_status(owner, repo, pr_number, token=None)` → PRStatus
  - Queries GitHub REST API: GET /repos/{owner}/{repo}/pulls/{pull_number}
  - Returns: state (open/closed), merged (bool), mergeable_state, created_at, updated_at, review_comments, commits
  - Handles 404 (PR deleted), 403 (rate limit), network errors gracefully
- `refresh_statuses(prs, token=None)` → List[TrackedPRStatus]
  - Bulk-fetch statuses for all tracked PRs
  - Rate-limit: sleep 0.5s between API calls to stay within GitHub rate limits

TrackedPRStatus has:
- `repo: str` (owner/repo)
- `pr_number: int`
- `pr_url: str`
- `campaign_id: Optional[str]`
- `submitted_at: str` (ISO timestamp)
- `status: str` (open/merged/closed/unknown)
- `days_open: int`
- `review_comments: int`
- `is_merged: bool`
- JSON-serializable

Required files:
- `agentkit_cli/pr_tracker.py`
- `tests/test_pr_tracker.py` (mock GitHub API, no real network)

### D2. `agentkit track` CLI command

Wire the tracker into the CLI:

```
agentkit track [--campaign-id CAMPAIGN_ID] [--limit N] [--all] [--json] [--share]
```

- Default: show last 20 tracked PRs across all campaigns, sorted by submitted_at desc
- `--campaign-id`: filter to specific campaign
- `--limit N`: max PRs to show (default 20)
- `--all`: show all tracked PRs (no limit)
- `--json`: output structured JSON payload
- `--share`: upload dark-theme HTML report to here.now

Rich table output columns:
- Repo (owner/repo)
- PR # (link if terminal supports)
- Status (colored: green=merged, yellow=open, red=closed)
- Days Open
- Reviews
- Submitted

Summary line below table: "N merged, N open, N closed"

Required files:
- `agentkit_cli/commands/track_cmd.py`
- Tests in `tests/test_track_cmd.py`
- Wire into `agentkit_cli/main.py` (add `from agentkit_cli.commands.track_cmd import track_command` and `@app.command("track")`)

### D3. Track report HTML (`agentkit_cli/track_report.py`)

Dark-theme HTML report for `agentkit track --share`:
- Header: "PR Campaign Tracker — {timestamp}"
- Summary stats: merged count, open count, closed count, merge rate %
- Table: same columns as CLI output
- Color-coded status badges (green/yellow/red)
- Campaign grouping if multiple campaigns present
- Footer with agentkit-cli version + here.now upload timestamp

Required files:
- `agentkit_cli/track_report.py`
- Tests in `tests/test_track_report.py`

### D4. DB schema update for PR tracking

The existing history DB (in agentkit_cli/history.py) needs a `tracked_prs` table:

```sql
CREATE TABLE IF NOT EXISTS tracked_prs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repo TEXT NOT NULL,           -- "owner/repo"
    pr_number INTEGER,            -- NULL if PR submission failed
    pr_url TEXT,
    campaign_id TEXT,             -- NULL if submitted via single `agentkit pr`
    submitted_at TEXT NOT NULL,   -- ISO timestamp
    last_status TEXT DEFAULT 'unknown',  -- open/merged/closed/unknown
    last_checked_at TEXT          -- ISO timestamp of last GitHub API check
);
```

Check if the table already exists in `agentkit_cli/history.py`. If not, add migration in `ensure_db()`. Add helper functions:
- `record_pr(db_path, repo, pr_number, pr_url, campaign_id=None)` → int (row id)
- `get_tracked_prs(db_path, campaign_id=None, limit=50)` → list of dicts
- `update_pr_status(db_path, pr_id, status, last_checked_at)` → None

Wire `record_pr()` into:
- `agentkit_cli/commands/pr_cmd.py` — call after successful PR open
- `agentkit_cli/campaign.py` — call after each PR in campaign results

Required files:
- Update `agentkit_cli/history.py` (add table + helpers)
- Update `agentkit_cli/commands/pr_cmd.py` (record PR after success)
- Update `agentkit_cli/campaign.py` (record PR after each successful campaign PR)
- Tests in `tests/test_history.py` (add DB migration + helper tests)

### D5. Docs, CHANGELOG, version bump, BUILD-REPORT

- Update README.md: add `agentkit track` section after `agentkit campaign`
- Update CHANGELOG.md: v0.40.0 entry with all deliverables
- Bump version: `agentkit_cli/__init__.py` and `pyproject.toml` to `0.40.0`
- Write `BUILD-REPORT.md` addendum (append to existing file): what was built, test count, final status
- All existing tests must still pass (target: 1537 + new tests)

## 4. Test Requirements

- [ ] `tests/test_pr_tracker.py`: PRTracker unit tests with mocked GitHub API (10+ tests)
- [ ] `tests/test_track_cmd.py`: CLI command tests (8+ tests)
- [ ] `tests/test_track_report.py`: HTML report generation (5+ tests)
- [ ] `tests/test_history.py`: DB schema + helper function tests (8+ tests)
- [ ] All 1537 existing tests must still pass
- [ ] Edge cases: 404 on deleted PR, rate limit response, empty campaign, mixed merged/open/closed states

## 5. Reports

- Write progress to `progress-log.md` after each deliverable
- Include: what was built, what tests pass, what's next, any blockers
- Final summary when all deliverables done or stopped

## 6. Stop Conditions

- All deliverables checked and all tests passing → DONE
- 3 consecutive failed attempts on same issue → STOP, write blocker report
- Scope creep detected (new requirements discovered) → STOP, report what's new
- All tests passing but deliverables remain → continue to next deliverable
