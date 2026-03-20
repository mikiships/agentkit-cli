# Build Contract — agentkit-cli v0.67.0: `agentkit user-rank`

**Version:** 0.67.0  
**Date:** 2026-03-20  
**Baseline tests:** 3281  
**Target:** ≥3281 + 40 new = ≥3321 total  
**PyPI:** Will be published by build-loop after sub-agent completes

---

## Objective

Add `agentkit user-rank <topic>` — discover top GitHub contributors in a topic/language, score each for agent-readiness, produce a ranked "State of Agent Readiness in `<topic>`" report. Shareable dark-theme HTML + --share. Viral hook: "Which developers building in Python/Rust/Go are most AI-agent-ready?"

---

## Deliverables

### D1: `UserRankEngine` (`agentkit_cli/user_rank.py`)
- `search_topic_contributors(topic, limit=20)` — GitHub Search API: find repos matching topic, extract unique contributors
- `rank_contributors(contributors)` — score each via `UserScorecardEngine`, sort by composite score
- `UserRankResult` dataclass: topic, contributors (ranked list with score/grade), top_scorer, mean_score, grade_distribution, timestamp
- JSON serialization
- Graceful handling: rate limits, missing GITHUB_TOKEN, private repos
- ≥15 tests in `tests/test_user_rank_d1.py`

### D2: CLI command (`agentkit_cli/commands/user_rank_cmd.py`)
- `agentkit user-rank <topic>` — positional topic arg
- `--limit N` (default 20): max contributors to rank
- `--json`: structured `UserRankResult` JSON
- `--output FILE`: save HTML to file
- `--share`: publish to here.now via existing `share_report()` helper
- `--quiet`: suppress progress for CI
- Rich terminal table: rank, user, score, grade, top repo
- Wire into `agentkit_cli/main.py`
- ≥10 tests in `tests/test_user_rank_d2.py`

### D3: Dark-theme HTML report (`agentkit_cli/user_rank_html.py`)
- `UserRankHTMLRenderer` class with `.render(result: UserRankResult) -> str`
- Report sections: headline (topic + timestamp), ranked table with avatars, grade distribution bars, top-scorer spotlight
- Match existing dark-theme style (same CSS as user_team_html.py — reuse pattern)
- ≥8 tests in `tests/test_user_rank_d3.py`

### D4: Integration into `agentkit run` + `agentkit report`
- Add `user-rank` to `agentkit run` pipeline (optional, only when `--topic` flag present)
- Wire `--share` through existing `share_report()` pattern
- ≥7 tests in `tests/test_user_rank_d4.py`

### D5: Docs, CHANGELOG, version bump
- README: add `agentkit user-rank` section with example output
- CHANGELOG: add [0.67.0] entry
- `pyproject.toml`: bump version to 0.67.0
- `agentkit_cli/__init__.py`: bump `__version__` to "0.67.0"
- `BUILD-REPORT.md` + `BUILD-REPORT-v0.67.0.md`: full report
- `progress-log-v0.67.0.md`: status log
- ≥5 tests in `tests/test_user_rank_d5.py`

---

## Implementation Notes

### Reuse pattern from user_team.py
`UserRankEngine` should follow the same structure as `TeamScorecardEngine`:
- Constructor takes `github_token=None` (falls back to env var)
- `.run(topic, limit)` is the main entry point
- Uses `UserScorecardEngine` for per-user scoring (already exists)

### GitHub Search API
Use: `GET /search/repositories?q=topic:<topic>&sort=stars&per_page=50`
Then extract unique contributors from top repos' `/contributors` endpoint.
Cap at `limit` unique users after dedup.

### HTML reuse
Copy the CSS/structure from `user_team_html.py` and adapt for ranked list.
Don't reinvent — reuse the dark theme, card styles, grade badges.

### Test patterns
Look at `tests/test_user_team_d1.py` for the mock patterns to follow.
All GitHub API calls must be mocked in tests (no real API calls in test suite).

---

## Stop Conditions

- Stop after D5 is complete and all tests pass
- Do NOT publish to PyPI (build-loop handles that)
- Do NOT push to git (build-loop handles that)
- Do NOT modify any files outside ~/repos/agentkit-cli/
- Report completion with: test count, any failures, files changed

---

## Success Criteria

1. `agentkit user-rank python --limit 10` runs end-to-end (even with mocked/real GitHub API)
2. `--json` outputs valid `UserRankResult` JSON
3. `--share` produces a here.now URL (or fails gracefully if HERENOW_API_KEY missing)
4. Full test suite: ≥3321 passing, 0 failing
5. `BUILD-REPORT.md` updated, version bumped to 0.67.0
