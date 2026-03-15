# BUILD-REPORT: agentkit-cli v0.28.0

Date: 2026-03-15
Build contract: memory/contracts/agentkit-cli-v0.28.0-insights.md
Status: COMPLETE

## Summary

Delivered `agentkit insights` — a cross-repo pattern synthesis command that answers
"I've analyzed 10 repos. What patterns should I fix?" by aggregating findings across
all historical runs stored in the history DB.

---

## D1: InsightsEngine (`agentkit_cli/insights.py`)

**Built:**
- `InsightsEngine` class with configurable DB path (defaults to `~/.config/agentkit/history.db`)
- `get_common_findings(min_repos=2)` — findings appearing in 2+ distinct repos, sorted by repo_count
- `get_outliers(percentile=25)` — repos in bottom quartile by latest score
- `get_trending(window=5)` — repos with score delta >10 between last two runs
- `get_portfolio_summary()` — avg_score, total_runs, unique_repos, top_issue, best_repo, worst_repo
- Graceful empty-DB handling: all methods return empty results without crashing
- Fallback parsing: findings can live in the `findings` column or embedded in the `details` JSON column
- Old DB support: reads tables without the `findings` column via try/except fallback

**Tests added:** `tests/test_insights.py` — 23 tests
- Empty DB coverage for all 4 methods
- Non-existent DB file (no crash)
- Portfolio summary with 1 / multiple repos
- Non-overall tool filtering
- Common findings across repos, min_repos=1, sorted order, details-column fallback
- Outliers: bottom quartile, sorted ascending, single-project edge case
- Trending: improvement, regression, small-delta ignored, single-run ignored, sorted by abs(delta)
- Old DB without findings column (migration handled gracefully)
- 10 runs same repo

**Commit:** D1+D2 combined (feat: D1+D2 agentkit insights engine and CLI command)

---

## D2: CLI Command (`agentkit insights`)

**Built:**
- `agentkit_cli/commands/insights_cmd.py` — Rich-formatted command module
- Wired as `@app.command("insights")` in `agentkit_cli/main.py`
- Default (no flags): Rich panel showing portfolio health
- `--common-findings`: table of findings with repo count and total occurrences
- `--outliers`: table of bottom-quartile repos with score coloring
- `--trending`: table of repos with significant score movement, colored by direction
- `--all`: all four sections in sequence
- `--json`: structured JSON output (`portfolio_summary`, `common_findings`, `outliers`, `trending`)
- `--db <path>`: override DB path
- Graceful empty DB output: "No history found. Run agentkit analyze…"

**JSON output schema documented:** in README.md and verifiable via `agentkit insights --json`

**Tests added:** `tests/test_insights_cmd.py` — 15 tests
- Empty/non-existent DB shows empty message
- Default output shows "Portfolio Health" panel
- Avg score appears correctly
- `--common-findings`, `--outliers`, `--trending` flags all tested
- `--all` shows multiple sections
- `--json` output structure and field validation
- `--db` path override works

**Commit:** D1+D2 combined

---

## D3: Findings Storage

**Built:**
- `ALTER TABLE runs ADD COLUMN findings TEXT` added to `_MIGRATIONS` in `history.py` (idempotent)
- `HistoryDB.record_run` accepts `findings: Optional[list]` parameter, stores as JSON
- Module-level `record_run` function forwards `findings` kwarg
- `agentkit run --record-findings`: captures agentlint output lines and stores them in DB for the overall run record
- `agentkit analyze --record-findings`: flag accepted (analyze doesn't call record_run directly; findings parsed from report files at insights time per contract fallback)
- `InsightsEngine._ensure_findings_column()` applies the same migration on open, ensuring old DBs work

**Scope decision:** The contract specified a "simpler fallback" option (parse report files at insights time) if schema migration was complex. We implemented both: findings stored via `--record-findings` AND fallback parsing from the `details` JSON column. No existing DB is broken.

**Tests added:** `tests/test_insights_d3.py` — 7 tests
- `record_run` stores findings as JSON
- `record_run` without findings stores NULL
- Module-level `record_run` forwards findings
- Old DB without findings column gets column added by InsightsEngine
- Migration is idempotent (double-init safe)
- `agentkit run --help` shows `--record-findings`
- `agentkit analyze --help` shows `--record-findings`

**Commit:** D3 (feat: D3 findings storage in history DB, --record-findings flag on run/analyze)

---

## D4: Documentation, Version, Tests

**Built:**
- `README.md`: Added `agentkit insights` to command list; added full "Portfolio Insights" section with usage examples and JSON schema
- `CHANGELOG.md`: Added v0.28.0 entry with full feature description
- `agentkit_cli/__init__.py`: Bumped to `0.28.0`
- `pyproject.toml`: Bumped to `0.28.0`
- `BUILD-REPORT-v0.28.0.md`: This file

---

## Test Summary

| File | Tests | Notes |
|------|-------|-------|
| `tests/test_insights.py` | 23 | InsightsEngine unit tests |
| `tests/test_insights_cmd.py` | 15 | CLI integration tests |
| `tests/test_insights_d3.py` | 7 | Findings storage + migration |
| **New total** | **45** | — |
| Baseline | 1012 | v0.27.0 |
| **Final total** | **1057** | All passing ✓ |

---

## Files Changed

| File | Change |
|------|--------|
| `agentkit_cli/insights.py` | New — InsightsEngine |
| `agentkit_cli/commands/insights_cmd.py` | New — CLI command module |
| `agentkit_cli/main.py` | +insights command, +record-findings on run/analyze |
| `agentkit_cli/history.py` | +findings column migration, +findings param on record_run |
| `agentkit_cli/commands/run_cmd.py` | +record_findings param, findings capture logic |
| `agentkit_cli/commands/analyze_cmd.py` | +record_findings param |
| `agentkit_cli/__init__.py` | Version → 0.28.0 |
| `pyproject.toml` | Version → 0.28.0 |
| `README.md` | +Portfolio Insights section |
| `CHANGELOG.md` | +v0.28.0 entry |
| `tests/test_insights.py` | New — 23 tests |
| `tests/test_insights_cmd.py` | New — 15 tests |
| `tests/test_insights_d3.py` | New — 7 tests |

---

## Validation Gates

- [x] InsightsEngine class with all 4 methods
- [x] Handles empty DB gracefully
- [x] Tests for InsightsEngine (23 tests, min 6 required)
- [x] `agentkit insights` shows portfolio summary
- [x] All flags work correctly
- [x] `--json` output is stable and schema-documented
- [x] Graceful output when history DB has 0 entries
- [x] Findings stored or parseable for insights
- [x] No schema migration errors on existing DBs
- [x] README section added
- [x] CHANGELOG entry for v0.28.0
- [x] Version bumped in pyproject.toml and __init__.py
- [x] 45 new tests (>20 required)
- [x] Full test suite passes: 1057 tests (baseline 1012 + 45 new)
