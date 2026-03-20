# Build Contract: agentkit-cli v0.64.0 — `agentkit user-card`

**Date:** 2026-03-19
**Baseline:** v0.63.0, 3117 tests passing
**Target:** v0.64.0, ≥3167 tests passing (≥50 new)

## Objective

Add `agentkit user-card github:<user>` — generate a compact, embeddable "developer agent-readiness card" that shows a user's grade, score, top repo, and context coverage in a shareable single-page HTML card format (like a GitHub stats card). Lightweight wrapper over UserScorecardEngine.

Closes the "profile card" use case — a quick, tweet/README-embeddable snapshot of a developer's agent-readiness.

## Deliverables

### D1: UserCardEngine core (≥14 tests)
File: `agentkit_cli/user_card.py`

```python
@dataclass
class UserCardResult:
    username: str
    avatar_url: str
    grade: str
    avg_score: float
    total_repos: int
    analyzed_repos: int
    context_coverage_pct: float
    top_repo_name: str
    top_repo_score: float
    agent_ready_count: int  # repos with score >= 80
    summary_line: str  # e.g. "3/10 repos agent-ready · Grade B"

class UserCardEngine:
    def __init__(self, github_token=None, limit=10, min_stars=0, skip_forks=True, timeout=60)
    def run(self, user: str) -> UserCardResult
```

`UserCardResult` must have `to_dict()` method.

### D2: `agentkit user-card` CLI command (≥14 tests)
File: `agentkit_cli/commands/user_card_cmd.py`

```
agentkit user-card github:<user>
  --limit N         (default 10, max 30) — repos to analyze
  --min-stars N     (default 0) — skip repos below star count
  --no-skip-forks   — include forks (default: skip forks)
  --share           — publish HTML card to here.now, print URL
  --json            — output machine-readable result
  --quiet           — print only the share URL (cron-friendly)
  --timeout N       (default 60) — per-repo timeout in seconds
```

Output (Rich): avatar/grade badge header + compact stats row + "Copy embed snippet" section

### D3: Dark-theme HTML card (≥10 tests)
File: `agentkit_cli/renderers/user_card_html.py`

- Compact card design: 400px wide, single-column, dark theme (#0d1117)
- Header: avatar (48px), @handle, grade badge
- Stats row: score ring/number, context %, repos analyzed, agent-ready count
- Top repo chip: "Top: <repo> · <score>/100"
- Footer: "Powered by agentkit-cli · agentkit.dev"
- Markdown embed snippet: `![Agent-Readiness Card](share_url)` (included as HTML comment)
- `--share` integration: same here.now publish flow via `agentkit_cli/share.py`

### D4: Integration into `agentkit run` and `agentkit report` (≥8 tests)
- `agentkit run --user-card github:<user>` flag (similar to --user-improve)
- `user_card` section in `agentkit report` JSON output when available
- History DB: record each user-card run as a row in `runs` table with `tool="user-card"`

### D5: Docs, CHANGELOG, version bump, BUILD-REPORT (≥5 tests for version assertions)
- README: new `agentkit user-card` section after `user-improve`
- CHANGELOG: v0.64.0 entry
- `pyproject.toml`: version 0.63.0 → 0.64.0
- `agentkit_cli/__init__.py`: `__version__ = "0.64.0"`
- `BUILD-REPORT.md`: update in repo root

## Constraints

- **Must pass full test suite**: `python3 -m pytest -q` ≥ 3167 passing, 0 failed before committing
- **No version-hardcoded tests**: use `agentkit_cli.__version__` or `importlib.metadata`, not string literals
- **Reuse UserScorecardEngine** — do not re-implement GitHub API calls
- **Reuse here.now publish** from `agentkit_cli/share.py`
- **Error resilience**: if scorecard engine fails, return a minimal error card
- **No deploy**: do not deploy or make anything public. Build and test only.
- **Commit everything**: all files committed before reporting done

## Verification
Before calling complete:
1. `python3 -m pytest -q` — must show ≥ 3167 passing, 0 failed
2. `agentkit user-card --help` — must show the command with all flags
3. `git log --oneline -5` — show last 5 commits
4. `grep __version__ agentkit_cli/__init__.py` — must show 0.64.0

## Report Format (BUILD-REPORT.md fields to populate)
- feature: user-card
- baseline_tests: 3117
- final_tests: <actual>
- new_tests: <actual>
- version: 0.64.0
- deliverables: D1 ✅ D2 ✅ D3 ✅ D4 ✅ D5 ✅
