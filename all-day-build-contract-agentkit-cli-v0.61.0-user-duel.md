# All-Day Build Contract: agentkit-cli v0.61.0 — `agentkit user-duel`

Status: In Progress
Date: 2026-03-19
Owner: Codex execution pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Build `agentkit user-duel github:<user1> github:<user2>` — a head-to-head agent-readiness comparison between two GitHub developers. Each user's public repos are scored via `UserScorecardEngine`, then compared side-by-side with winner declared per dimension (best grade, highest avg score, most agent-ready repos). Output: rich terminal table + shareable dark-theme HTML duel report (same aesthetic as existing agentkit reports). Extends the v0.60.0 `user-scorecard` feature naturally.

This is a viral social mechanic: "Who is more AI-agent-ready — @tiangolo or @kennethreitz?" One command, shareable URL.

This contract is considered complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Full test suite must pass at the end (2953 baseline → ≥2993 total, ≥40 new tests).
4. New features must ship with docs and report addendum updates in the same pass.
5. CLI outputs must be deterministic and schema-backed where specified.
6. Never modify files outside the project directory.
7. Commit after each completed deliverable (not at the end).
8. If stuck on same issue for 3 attempts, stop and write a blocker report.
9. Do NOT refactor, restyle, or "improve" code outside the deliverables.
10. Read existing tests and docs before writing new code.
11. DO NOT bump version in pyproject.toml or __init__.py — build-loop handles publish.
12. DO NOT run `git push` or `twine upload` — build-loop handles those.
13. DO NOT modify any file outside ~/repos/agentkit-cli/.

## 3. Feature Deliverables

### D1. UserDuelEngine core (`agentkit_cli/user_duel.py`)

Implement `UserDuelEngine` that:
- Takes two GitHub usernames
- Calls `UserScorecardEngine` for each (reuse existing engine from v0.60.0)
- Computes per-dimension winner: avg_score, grade, repo_count, top_repo_score
- Returns `UserDuelResult` dataclass with: user1, user2, scores for each, winner per dimension, overall winner (majority of dimensions), tied status

Required files:
- `agentkit_cli/user_duel.py` — UserDuelEngine, UserDuelResult, DuelDimension

- [ ] UserDuelResult dataclass with full schema
- [ ] UserDuelEngine.run(user1: str, user2: str) -> UserDuelResult
- [ ] Dimension comparison: avg_score, letter_grade, repo_count, agent_ready_repos
- [ ] Overall winner: majority of dimension wins (tie if equal)
- [ ] Tests for D1: ≥12 tests (mocked UserScorecardEngine)

### D2. `agentkit user-duel` CLI command

Wire up the duel command at `agentkit_cli/commands/user_duel.py`:

```
agentkit user-duel github:<user1> github:<user2> [--limit N] [--json] [--share] [--quiet]
```

- `--limit N`: max repos per user to score (default 10)
- `--json`: emit UserDuelResult as JSON
- `--share`: publish HTML report to here.now, print URL
- `--quiet`: suppress progress, just print winner

Rich terminal output:
- Header: "⚔️ Agent Readiness Duel" with both usernames
- Side-by-side comparison table (dimension | user1 value | user2 value | winner)
- Overall verdict banner: "🏆 @user1 wins!" or "🤝 Tied!"
- Progress display while fetching (reuse pattern from user-scorecard)

Required files:
- `agentkit_cli/commands/user_duel.py`
- Wire into `agentkit_cli/main.py` as `user-duel` command

- [ ] CLI wired into main.py
- [ ] user-duel command with all flags
- [ ] Rich table output (side-by-side)
- [ ] Verdict banner
- [ ] Tests for D2: ≥12 tests

### D3. Dark-theme HTML duel report

`UserDuelReportRenderer` in `agentkit_cli/user_duel.py` (or separate renderer file):

- Same dark-theme aesthetic as existing agentkit reports (#0d1117 bg)
- Header section: "⚔️ Agent Readiness Duel" with both user avatars side by side
- Dimension table: per-dimension results with winner highlighted
- Per-user repo cards: top 5 repos for each user with scores
- Overall winner banner at bottom
- `--share` uploads to here.now (reuse `publish_to_herenow` from existing codebase)

Required files:
- HTML renderer in `agentkit_cli/user_duel.py` or `agentkit_cli/user_duel_renderer.py`

- [ ] HTML renderer with dark theme
- [ ] Avatar integration (GitHub avatar URLs)
- [ ] Dimension table with winner highlights
- [ ] Per-user repo cards (top 5)
- [ ] here.now upload via --share
- [ ] Tests for D3: ≥8 tests

### D4. Integration with `agentkit run` and `agentkit report`

- `agentkit run --user-duel github:<u1> github:<u2>` should trigger the duel as part of the run pipeline
- `agentkit report --user-duel github:<u1> github:<u2>` should include duel section in HTML report

This is lightweight — just wire the flag to call UserDuelEngine and include results.

- [ ] `--user-duel` flag on `agentkit run`
- [ ] Duel result included in JSON output when --user-duel specified
- [ ] Tests for D4: ≥8 tests

### D5. Docs, CHANGELOG, BUILD-REPORT

- [ ] README.md: add `agentkit user-duel` to commands table and usage section
- [ ] CHANGELOG.md: new 0.61.0 entry at top (above 0.60.0)
- [ ] BUILD-REPORT-v0.61.0.md in repo root
- [ ] At least 5 doc-validation tests

## 4. Validation Gates

```
pytest -q                     # 0 failures required; ≥ 2993 total
agentkit user-duel github:tiangolo github:kennethreitz --quiet  # prints a winner or tie
agentkit user-duel github:mikiships github:tiangolo --json       # valid JSON output
agentkit user-duel github:mikiships github:tiangolo --limit 3   # completes without error
```

## 5. Stop Conditions

- STOP if the test suite has more than 5 failures at end of any deliverable
- STOP if you find yourself modifying files outside ~/repos/agentkit-cli/
- STOP if UserScorecardEngine import fails (file a blocker, don't rewrite it)
- STOP and write blocker report if the GitHub API rate-limits and you can't mock around it

## 6. Deliverable Checklist

- [ ] D1: UserDuelEngine core (≥12 tests)
- [ ] D2: user-duel CLI command (≥12 tests)
- [ ] D3: HTML report renderer (≥8 tests)
- [ ] D4: run/report integration (≥8 tests)
- [ ] D5: docs, CHANGELOG, BUILD-REPORT (≥5 tests)
- [ ] Full suite: ≥2993 passing, 0 failures
- [ ] CHANGELOG 0.61.0 entry at top
- [ ] BUILD-REPORT-v0.61.0.md written

## 7. Context

- Repo: ~/repos/agentkit-cli/
- Current version: 0.60.0 (do NOT bump — build-loop handles this)
- Existing user scorecard engine: `agentkit_cli/user_scorecard.py` (built in v0.60.0)
- Existing here.now publish util: look for `publish_to_herenow` or similar in existing codebase
- Existing HTML report pattern: look at `agentkit_cli/report.py` or `agentkit_cli/user_scorecard_renderer.py` for dark-theme pattern
- Existing duel pattern for repos: `agentkit_cli/commands/duel.py` (repo vs repo) — use as reference
- Test count baseline: 2953 passing
- Target: ≥2993 passing (40 new tests minimum)
