# All-Day Build Contract: agentkit-cli v0.77.0 — Asymmetric Pair Selection

Status: In Progress
Date: 2026-03-21
Owner: Sub-agent execution pass
Scope type: Deliverable-gated

## 1. Objective

The `agentkit daily-duel` command currently produces boring "draw of champions" tweets because all 22 preset pairs are top-tier repos that score 100/100. This makes the daily tweet content meaningless as organic X distribution.

We need two things:
1. **Asymmetric pairs** — pairs where one repo is well-documented and one isn't, guaranteeing a clear winner and a useful score differential.
2. **Interesting narrative for clear wins** — the tweet copy for clear winners currently says "Winner: X on 3/4 dimensions" which is weak. It should say something like: "fastapi vs bottle: FastAPI scores 100, Bottle 61. FastAPI wins on all 4 agent-readiness dimensions — the doc gap is real."

This ships as v0.77.0.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion allowed only when all checklist items are checked.
3. Full test suite must pass at end.
4. New features must ship with docs and CHANGELOG in the same pass.
5. CLI outputs must be deterministic.
6. Never modify files outside ~/repos/agentkit-cli/.
7. Commit after each completed deliverable.
8. If stuck on same issue for 3 attempts, stop and write a blocker report.
9. Do NOT refactor code outside the deliverables.
10. Read existing tests before writing new code.

## 3. Feature Deliverables

### D1. Add asymmetric pairs to PRESET_PAIRS in agentkit_cli/daily_duel.py

Add at least 20 asymmetric pairs where one repo clearly has better agent-readiness documentation.
These should be: well-known popular repo vs. smaller/older alternative that likely lacks AGENTS.md or CLAUDE.md.

Good candidates for "low-score" repos (use these patterns):
- Older Python libs without modern context files (bottle, flask-restful, tornado, cherrypy, web2py)
- Less-maintained JS frameworks (backbone, ember, knockout)
- Older testing tools (nose, unittest runners)
- Legacy database adapters (psycopg2 vs asyncpg, MySQLdb vs aiomysql)
- Popular vs. old-school: click vs argparse, httpx vs urllib, ruff vs pylint
- New vs. old agent SDKs: anthropic-sdk-python vs openai-python (both might be close)

Target: PRESET_PAIRS grows from 22 to at least 42 entries. Categorize them properly.

Files: `agentkit_cli/daily_duel.py`

- [ ] Add 20+ asymmetric pairs across 6+ categories
- [ ] Ensure pairs use correct (owner/repo) format matching actual GitHub repos
- [ ] Add new categories if needed (e.g., "cli-tools", "legacy-vs-modern")
- [ ] Tests for asymmetric pair coverage

### D2. Improve clear-winner tweet copy in _build_tweet_text

Current (weak): "fastapi vs bottle agent-readiness: fastapi 100/100 (A), bottle 45/100 (C). Winner: fastapi on 3/4 dimensions."

Goal (strong): A tweet that tells a story. Example formats:
- Large diff (>30): "{winner_name} ({winner_score}/100) crushes {loser_name} ({loser_score}/100) in agent-readiness: wins {winner_wins}/{n_dims} dimensions. The doc gap between modern and legacy Python is real."
- Medium diff (15-30): "{winner_name} ({winner_score}/100) beats {loser_name} ({loser_score}/100) across {winner_wins}/{n_dims} agent-readiness dimensions. Which one would you hand to an AI agent?"
- Keep the near-draw (<15 pt) copy as-is (it's already good).

Add a `_diff_tier` helper: large (>30), medium (15-30), small (5-15).
Each tier gets its own set of rotating templates (at least 3 per tier) seeded by the pair seed.

Files: `agentkit_cli/daily_duel.py`

- [ ] _diff_tier helper
- [ ] Large-diff template set (3+ templates)
- [ ] Medium-diff template set (3+ templates)  
- [ ] Tweet length validated ≤ 280 chars for all templates
- [ ] Tests for each tier

### D3. Add --simulate flag to daily-duel command

`agentkit daily-duel --simulate` shows what pair would be selected for each of the next 7 days AND generates the tweet text from the pair scores stored in a lightweight "expected score" lookup.

Wait — we can't run full analysis for 7 days. Instead, `--simulate` should:
1. Show the 7-day pair schedule (already exists via `--calendar`)
2. For the *today* pair specifically, display the expected tweet text based on a mock "dry run" output where repo1 is assigned score_hint=100, repo2 assigned score_hint=75 (just for UI preview, not an actual run).

Actually keep it simpler: just make `--calendar` output also show "expected narrative type: asymmetric|balanced|draw" based on whether the pair is in an "asymmetric_pairs" vs "balanced_pairs" sublist.

Files: `agentkit_cli/commands/daily_duel_cmd.py`, `agentkit_cli/daily_duel.py`

- [ ] PRESET_PAIRS split into `ASYMMETRIC_PAIRS` and `BALANCED_PAIRS` lists, combined as `PRESET_PAIRS`
- [ ] Each pair tuple gains an optional 4th element: "asymmetric" | "balanced"
- [ ] `--calendar` shows narrative_type column
- [ ] Tests for calendar with narrative_type

### D4. Update docs and bump version

- README: update daily-duel section with asymmetric pairs explanation and example tweets
- CHANGELOG: v0.77.0 entry
- Version bump: 0.76.0 → 0.77.0
- BUILD-REPORT.md: document all deliverables

Files: README.md, CHANGELOG.md, agentkit_cli/__init__.py, BUILD-REPORT.md

- [ ] README updated
- [ ] CHANGELOG entry written
- [ ] Version bumped in __init__.py and pyproject.toml
- [ ] BUILD-REPORT.md written

### D5. Full test suite green

- [ ] Run `python3 -m pytest -q` — target: 3805 + ≥15 new tests = ≥3820 total
- [ ] All new tests pass
- [ ] No regressions (known flaky test in test_watch.py is acceptable)
- [ ] Report final test count in BUILD-REPORT.md

## 4. Test Requirements

- Unit tests for asymmetric pairs (at least 5 new pairs verified as real GitHub repos in comments)
- Tweet template tests for each diff tier with len ≤ 280
- Calendar narrative_type test
- All existing tests still pass

## 5. Reports

Write to `progress-log.md` (or append to existing) after each deliverable.
Final BUILD-REPORT.md when done.

## 6. Stop Conditions

- All deliverables checked, all tests passing → DONE, write BUILD-REPORT
- 3 consecutive failed attempts on same issue → STOP, write blocker report
- Any public posting action attempted → STOP immediately (not authorized)
- Scope creep detected → STOP, report
