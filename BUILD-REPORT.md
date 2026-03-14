# BUILD-REPORT.md — agentkit-cli v0.15.0

**Date:** 2026-03-14  
**Feature:** `agentkit leaderboard` command  
**PyPI:** https://pypi.org/project/agentkit-cli/0.15.0/

---

## Test Results

- **Total tests:** 575
- **Passing:** 575
- **Failing:** 0
- **New tests added:** 47 (in `tests/test_leaderboard.py`)

```
575 passed in 6.86s
```

---

## What Was Built

### D1: Run Labeling
- Added `--label <str>` flag to `agentkit run`
- Label stored in history DB via backward-compatible `ALTER TABLE` migration
- Old rows without label column are readable (migrate to NULL → shown as "default")
- Module-level `record_run()` and `HistoryDB.record_run()` both accept `label=` kwarg

### D2: Leaderboard Engine
- `agentkit_cli/commands/leaderboard_cmd.py` — `leaderboard_command()` function
- `HistoryDB.get_leaderboard_data()` — groups by label, computes avg/best/worst/trend
- `_compute_trend()` — avg(last 3) - avg(first 3), handles short arrays cleanly
- Supports `tool`, `project`, `since` (ISO timestamp), `last_n` filters

### D3: CLI Command
- `agentkit leaderboard` registered in `main.py`
- Rich ranked table: Rank, Label, Runs, Avg Score, Trend (↑/↓/→), Best, Worst
- Color-coded scores (green ≥80, yellow ≥50, red <50)
- Flags: `--by`, `--project`, `--last`, `--since`, `--json`, `--db` (hidden, for testing)

### D4: GitHub Actions
- `action.yml` updated with `leaderboard-json` output
- Emitted alongside `history-json` when `save-history: true`

### D5: Docs, Tests, Version
- README: "Agent Leaderboard" section added with example output and GitHub Actions snippet
- CHANGELOG: v0.15.0 entry
- Version: 0.14.0 → 0.15.0 in `pyproject.toml` and `__init__.py`

---

## Demo Commands

```bash
# Install
pip install agentkit-cli==0.15.0

# Tag runs with labels
agentkit run --label gpt-4 --no-history  # (tools not installed, use --no-history for demo)
agentkit run --label claude-sonnet

# View leaderboard
agentkit leaderboard
agentkit leaderboard --json
agentkit leaderboard --by agentlint
agentkit leaderboard --last 5
agentkit leaderboard --since 7d

# Verify version
agentkit --version  # → agentkit-cli v0.15.0
```

---

## Known Issues

- `test_watch.py::TestChangeHandler::test_debounce_resets_on_rapid_changes` is a pre-existing flaky timing test; it passes on most runs but occasionally fails under load. Not related to this feature.
- The `--label` flag on `agentkit run` does not appear in the run summary JSON output (it's stored in the DB only). This could be a future enhancement.
