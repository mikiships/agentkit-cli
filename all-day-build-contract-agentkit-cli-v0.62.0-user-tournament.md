# Build Contract: agentkit-cli v0.62.0 — `agentkit user-tournament`

**Date:** 2026-03-19  
**Orchestrator:** Mordecai (build-loop)  
**Repo:** ~/repos/agentkit-cli/  
**Baseline:** v0.61.0 — 3009 tests passing, all green

---

## Objective

Add `agentkit user-tournament` command — a bracket-style developer agent-readiness tournament for N GitHub users. Extends `user-duel` into a multi-player experience. Round-robin comparison across all users, ranks by average duel score, declares an overall champion.

**Viral mechanic:** "Who's the most AI-agent-ready developer in your org?" — shareable HTML bracket page.

---

## Deliverables

### D1: UserTournamentEngine core (≥15 tests)
- `agentkit_cli/engines/user_tournament.py`
- `UserTournamentEngine`: accepts list of GitHub handles, runs UserDuelEngine for each pair (or selected matchups)
- Round-robin OR top-N bracket mode (auto-selects bracket if >6 users, else round-robin)
- `TournamentResult` dataclass: participants, standings, match_results, champion, rounds, timestamp
- `Standings` dataclass: rank, handle, wins, losses, avg_score, total_duel_score
- Champion selection: highest total duel wins; tiebreak = avg dimension score
- `--limit` to cap max comparisons if N is large (default: full round-robin for ≤8, bracket for >8)
- Graceful handling: skip inaccessible GitHub users (score = 0), warn but don't crash
- Parallel fetching via asyncio or ThreadPoolExecutor (reuse UserScorecardEngine logic)

### D2: `agentkit user-tournament` CLI command (≥10 tests)
- `agentkit_cli/commands/user_tournament_cmd.py`
- Wired into `agentkit_cli/main.py`
- Usage: `agentkit user-tournament github:<u1> github:<u2> [github:<uN>...] [options]`
- Required: ≥2 participants
- Flags:
  - `--share` — publish HTML report to here.now
  - `--json` — structured JSON output (stdout)
  - `--quiet` — suppress progress, print winner only
  - `--output PATH` — save HTML to local path
  - `--limit N` — max duel comparisons (default: all)
  - `--timeout N` — per-user scorecard timeout seconds (default: 60)
- Rich progress display: participant list, match progress bar, standings table
- Final output: Rich table with rank, handle, record (W-L), avg score, grade; champion banner
- Exit 0 on success, exit 1 on <2 valid participants

### D3: Dark-theme HTML tournament report (≥8 tests)
- `agentkit_cli/renderers/user_tournament_report.py`
- `UserTournamentReportRenderer.render(result) -> str` (pure HTML string, no file I/O)
- Dark background (#0d1117), accent (#4493f8), green/red for wins/losses
- Sections:
  1. Header: "Developer Agent-Readiness Tournament" + date
  2. Champion card: avatar (via GitHub), handle, grade badge, win record
  3. Standings table: rank, avatar, handle, W-L, avg score, grade
  4. Match results (collapsible or scrollable): each duel outcome with per-dimension breakdown
- `publish_user_tournament(result) -> str` — uploads HTML to here.now, returns URL
- Tests mock publish; renderer tests are standalone (no network)

### D4: Integration into `agentkit run` and `agentkit report` (≥6 tests)
- `agentkit run --user-tournament <u1>:<u2>:...` — run tournament, include in report/publish
- `agentkit report --user-tournament <u1>:<u2>:...` — render tournament section in combined report
- Colon-separated handle list (consistent with existing --user-duel syntax)
- Tests: unit tests for flag parsing + engine wiring; no live GitHub calls

### D5: Docs, CHANGELOG, version bump, BUILD-REPORT (≥6 tests)
- `CHANGELOG.md`: new `[0.62.0]` section at top with feature description
- `README.md`: add `agentkit user-tournament` to commands table and usage section
- `pyproject.toml` and `agentkit_cli/__init__.py`: bump version from 0.61.0 → 0.62.0
- `BUILD-REPORT.md`: header says v0.62.0, feature says `agentkit user-tournament`
- `BUILD-REPORT-v0.62.0.md`: versioned copy
- Tests: check version string, CHANGELOG presence, README mention, BUILD-REPORT header

---

## Test Requirements

- Baseline: 3009 passing
- Target: ≥3049 total (≥40 new tests)
- Zero failures, zero regressions
- All new tests in `tests/test_user_tournament_*.py` (5 files: d1–d5)
- Mock all GitHub API calls and UserDuelEngine calls in tests
- No live network calls in test suite

---

## Stop Conditions (HARD STOPS — do not proceed past these)

1. **Do NOT publish to PyPI.** Build-loop handles publish after verification.
2. **Do NOT push to GitHub.** Build-loop handles push + tag after verification.
3. **Do NOT run `agentkit user-tournament` against real GitHub users** during testing — use mocks.
4. Stop if test suite falls below 3009 (baseline) — fix before continuing.
5. Stop and write partial report if you can't complete all deliverables — partial is better than broken.

---

## Completion Criteria (ALL must be true before declaring done)

- [ ] `python3 -m pytest -q --tb=no` shows ≥3049 passed, 0 failed
- [ ] `agentkit user-tournament --help` shows all flags
- [ ] `from agentkit_cli import __version__; assert __version__ == "0.62.0"`
- [ ] `CHANGELOG.md` has `[0.62.0]` section
- [ ] `BUILD-REPORT.md` header says v0.62.0
- [ ] All changes committed (git commit, not just staged)

## Report Format

End your session with a plain-text BUILD-REPORT to stdout:
```
DONE | agentkit-cli v0.62.0 user-tournament
Tests: <N> passing, 0 failed
Deliverables: D1 ✅ D2 ✅ D3 ✅ D4 ✅ D5 ✅
Commits: <list of commit hashes>
Notes: <anything build-loop should know>
```
