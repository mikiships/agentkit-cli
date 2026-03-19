# Build Contract: agentkit-cli v0.63.0 — `agentkit user-improve`

**Date:** 2026-03-19
**Baseline:** v0.62.0, 3059 tests passing
**Target:** v0.63.0, ≥3105 tests passing (≥46 new)

## Objective

Add `agentkit user-improve github:<user>` — find a GitHub user's lowest-scoring public repos, auto-improve them (generate CLAUDE.md + harden), and display a before/after quality lift report.

Closes the "discover → benchmark → improve" flywheel for individual developers.

## Deliverables

### D1: UserImproveEngine core (≥14 tests)
File: `agentkit_cli/user_improve.py`

```python
class UserImproveEngine:
    def __init__(self, github_token=None, tempdir=None)
    def fetch_user_repos(self, user: str) -> list[dict]  # top public repos
    def score_repos(self, repos: list[dict]) -> list[UserRepoScore]  # run agentkit analyze on each
    def select_targets(self, scores: list[UserRepoScore], limit: int, below: int) -> list[UserRepoScore]
    def improve_repo(self, repo: UserRepoScore, tempdir: str) -> UserImproveResult  # generate + harden
    def run(self, user: str, limit: int = 5, below: int = 80) -> UserImproveReport
```

`UserImproveResult`: before_score, after_score, lift, repo_url, files_generated, files_hardened, errors
`UserImproveReport`: user, avatar_url, total_repos, improved, skipped, results, summary_stats (avg_before, avg_after, avg_lift)

### D2: `agentkit user-improve` CLI command (≥14 tests)
File: `agentkit_cli/commands/user_improve.py`

```
agentkit user-improve github:<user>
  --limit N         (default 5, max 20) — repos to target
  --below N         (default 80) — only target repos scoring below this
  --share           — publish HTML report to here.now, print URL
  --json            — output machine-readable result
  --dry-run         — show what would be improved, no changes
```

Output (Rich table): repo name | before score | after score | lift | status

### D3: Dark-theme HTML report (≥10 tests)
File: `agentkit_cli/renderers/user_improve_html.py`

- Dark theme consistent with user-scorecard/user-duel/user-tournament style
- User avatar + handle header
- Summary bar: repos improved, avg lift, total files generated
- Per-repo cards: before/after score bars, lift badge (green if positive), files generated, link to repo
- `--share` integration: same here.now publish flow as other user commands

### D4: Integration into `agentkit run` and `agentkit report` (≥8 tests)
- `agentkit run --user-improve github:<user>` (similar to how analyze is integrated)
- `user_improve` section in `agentkit report` JSON output when available
- History DB: record each user-improve run as a row in `runs` table with `command="user-improve"`

### D5: Docs, CHANGELOG, version bump, BUILD-REPORT (≥ 5 tests for version assertions)
- README: new `agentkit user-improve` section after `user-tournament`
- CHANGELOG: v0.63.0 entry
- `pyproject.toml`: version 0.62.0 → 0.63.0
- `agentkit_cli/__init__.py`: `__version__ = "0.63.0"`
- `BUILD-REPORT.md`: update in repo root

## Constraints

- **Must pass full test suite**: `python3 -m pytest -q` ≥ 3105 passing, 0 failed before committing
- **No version-hardcoded tests**: use `agentkit_cli.__version__` or `importlib.metadata`, not string literals
- **Reuse ToolAdapter** for all quartet tool invocations — do not shell out directly
- **Reuse here.now publish** from `agentkit_cli/share.py` (same as user-scorecard/user-duel)
- **Tempdir cleanup**: always clean up cloned repos in a finally block
- **Error resilience**: if one repo fails to improve, log and skip; don't abort the whole run
- **No deploy**: do not deploy or make anything public. Build and test only.
- **Commit everything**: all files committed before reporting done

## Stop Conditions
- If test count drops below 3059 (the baseline), stop and report what broke
- If ToolAdapter import fails, stop and report the dependency chain issue
- If GitHub API rate limits block scoring, implement exponential backoff (max 3 retries) rather than failing

## Verification
Before calling complete:
1. `python3 -m pytest -q` — must show ≥ 3105 passing, 0 failed
2. `agentkit user-improve --help` — must show the command with all flags
3. `git log --oneline -5` — show last 5 commits
4. `git diff --stat HEAD~5 HEAD` — summarize what was changed
5. `grep __version__ agentkit_cli/__init__.py` — must show 0.63.0

## Report Format (BUILD-REPORT.md fields to populate)
- feature: user-improve
- baseline_tests: 3059
- final_tests: <actual>
- new_tests: <actual>
- version: 0.63.0
- deliverables: D1 ✅ D2 ✅ D3 ✅ D4 ✅ D5 ✅
- notes: <any caveats>
