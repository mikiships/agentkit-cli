# Progress Log — agentkit-cli v0.64.0

**Date:** 2026-03-19
**Feature:** `agentkit user-card`
**Build contract:** `all-day-build-contract-agentkit-cli-v0.64.0-user-card.md`

## Summary

All 5 deliverables implemented and committed in a single pass.

## Deliverables

### D1: UserCardEngine core ✅
- `agentkit_cli/user_card.py`
- `UserCardResult` dataclass with full `to_dict()` schema
- `UserCardEngine` wraps `UserScorecardEngine` and distils into compact card
- Handles empty username, engine exceptions (returns error card, not exception)
- Agent-ready count computed from repos with score ≥ 80
- Avatar URL computed as `https://github.com/{username}.png`

### D2: `agentkit user-card` CLI command ✅
- `agentkit_cli/commands/user_card_cmd.py`
- All flags: `--limit`, `--min-stars`, `--skip-forks/--no-skip-forks`, `--share`, `--json`, `--quiet`, `--timeout`
- History DB integration via `record_run(tool="user-card")`
- Rich terminal output: grade badge, stats line, top repo, embed snippet when --share used

### D3: Dark-theme HTML card ✅
- `agentkit_cli/renderers/user_card_html.py`
- 400px compact card, `#0d1117` background
- Avatar (48px), grade badge (color-coded A/B/C/D), stats row, top-repo chip
- Markdown embed snippet as HTML comment when `share_url` provided
- `upload_user_card()` delegates to `upload_scorecard()` from `agentkit_cli/share.py`

### D4: Integration into run and report ✅
- `agentkit run --user-card github:<user>`: triggers UserCardEngine, adds `user_card` to summary JSON
- `agentkit report --user-card github:<user>`: includes `user_card` section in report output
- Both `run_cmd.py` and `report_cmd.py` updated with user_card parameter
- `main.py` Typer commands updated with `--user-card` options

### D5: Docs, CHANGELOG, version bump ✅
- `agentkit_cli/__init__.py`: `__version__ = "0.64.0"`
- `pyproject.toml`: version 0.63.0 → 0.64.0
- `CHANGELOG.md`: v0.64.0 entry with full feature list
- `README.md`: `agentkit user-card` section added after `user-improve`
- `BUILD-REPORT.md` + `BUILD-REPORT-v0.64.0.md`: updated

## Test Results

| File | Tests | Status |
|------|-------|--------|
| test_user_card_d1.py | 14 | ✅ all pass |
| test_user_card_d2.py | 13 | ✅ all pass |
| test_user_card_d3.py | 12 | ✅ all pass |
| test_user_card_d4.py | 7 | ✅ all pass |
| test_user_card_d5.py | 5 | ✅ all pass |
| **Total new** | **52** | |
| **Full suite** | **3169** | ✅ 0 failed |

Baseline was 3117. Added 52 tests (contract target: ≥50). Full suite: 3169 passing, 0 failed.

## Commit

```
beb45e4 feat: agentkit user-card v0.64.0
```
