# Build Contract: agentkit-cli v0.31.0 — `agentkit tournament`

**Date:** 2026-03-16
**Builder:** Codex sub-agent
**Repo:** ~/repos/agentkit-cli/
**Target:** PyPI agentkit-cli 0.31.0

---

## Context

agentkit-cli is a Python CLI that runs quality analysis on GitHub repos using the agent quality
toolkit (agentmd, agentlint, coderace, agentreflect). We recently shipped `agentkit duel` (v0.30.0)
which does side-by-side comparison of two repos. The natural extension is a tournament bracket.

Current version: 0.30.0 (1155 tests passing, all green).

## Objective

Build `agentkit tournament <repo1> <repo2> ... <repoN>` — run a round-robin tournament across
N repos (4-16), score every pairing via the duel engine, rank by win/loss record, publish a
shareable HTML bracket report.

---

## Deliverables

### D1: Tournament engine (agentkit_cli/tournament.py)

```python
# Key classes/functions:
class TournamentResult:
    repos: list[str]
    rounds: list[list[DuelResult]]   # round-robin pairings
    standings: list[StandingEntry]   # ranked by wins desc, score tiebreak
    winner: str
    total_duels: int

class StandingEntry:
    repo: str
    wins: int
    losses: int
    avg_score: float
    rank: int

def run_tournament(repos: list[str], parallel: bool = True) -> TournamentResult:
    """Run all round-robin pairings. Reuse duel engine. Return full results."""
```

Requirements:
- Import and reuse `agentkit_cli/duel.py` run_duel() for each pairing
- Round-robin: every repo faces every other repo exactly once
- Parallel execution of independent pairings (use concurrent.futures.ThreadPoolExecutor)
- Clear progress display (Rich progress bar or spinner showing "repo1 vs repo2...")
- Handle partial failures: if one pairing fails, log it but continue tournament
- Tiebreak by avg composite score when win counts are equal

### D2: CLI command (agentkit_cli/commands/tournament_cmd.py)

```bash
agentkit tournament github:fastapi/fastapi github:tiangolo/starlette github:django/django github:pallets/flask
```

Flags:
- `--share` — publish HTML report to here.now (same as duel/analyze)
- `--json` — print full results as JSON to stdout
- `--quiet` — suppress Rich output, only final standings table
- `--parallel/--no-parallel` — control concurrent pairings (default: parallel)
- `--min-repos 4` / `--max-repos 16` — validation bounds
- `--output <file>` — write HTML report to file instead of temp

Register in agentkit_cli/main.py under tournament command.

### D3: HTML report (agentkit_cli/tournament_report.py)

Dark-theme HTML with:
- Header: "Agent-Readiness Tournament: [N] repos, [K] duels"
- Standings table: rank, repo name, W-L, avg score, grade (A/B/C/D/F)
- Match results grid: matrix table showing each pairings's winner highlighted
- Winner banner at top: "🏆 Winner: [repo] — [score]/100"
- Optional here.now publish via `--share` (reuse duel_report.py publish logic)
- Responsive, shares same dark-theme CSS as duel/analyze reports

### D4: Tests (tests/test_tournament.py)

Minimum 50 tests covering:
- round-robin pairing logic (3 repos → 3 pairs, 4 repos → 6 pairs, 5 repos → 10 pairs)
- parallel vs sequential execution paths
- partial failure handling (one pairing raises, rest continue)
- standings ranking: wins > score tiebreak
- HTML report generation (spot-check key strings: winner, standings headers)
- CLI integration (mock duel engine, test argument parsing, --json output)
- --share path (mock here.now publish, verify payload)
- validation: <4 repos raises error with clear message, >16 raises error

### D5: Docs + version bump

- README.md: Add "Tournament" section under Commands with example invocation
- CHANGELOG.md: Add v0.31.0 entry
- BUILD-REPORT.md: Create at repo root with deliverables checklist + test count
- Bump version in agentkit_cli/__init__.py from 0.30.0 to 0.31.0
- pyproject.toml version bump if present

---

## Stop Conditions

**STOP and commit what you have if:**
- All 5 deliverables are complete AND full test suite is green
- OR 5 hours of work elapsed regardless of completion

**DO NOT:**
- Publish to PyPI (build-loop handles publish after verifying tests)
- Push to GitHub (build-loop handles push)
- Modify any file outside ~/repos/agentkit-cli/

---

## Success Criteria

1. `agentkit tournament github:fastapi/fastapi github:tiangolo/starlette github:django/django github:pallets/flask` runs end-to-end (mocked in tests, real in manual)
2. Full pytest suite (all 1155 + new tests) passes green
3. `--share` generates and uploads an HTML report
4. BUILD-REPORT.md clearly states: PASS or FAIL for each deliverable + final test count
5. Version in __init__.py == "0.31.0"

---

## Implementation Notes

- The duel engine in duel.py is your building block — read it before writing tournament.py
- Round-robin formula for N repos: N*(N-1)/2 total pairings
- For 4 repos: (0v1), (0v2), (0v3), (1v2), (1v3), (2v3) = 6 pairings
- Keep tournament_report.py focused — HTML only. No business logic.
- Follow the same pattern as duel_cmd.py for CLI structure
- Look at how analyze.py calls duel internally for the parallel pattern
