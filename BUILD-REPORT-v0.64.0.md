# BUILD-REPORT — agentkit-cli v0.64.0

**Build date:** 2026-03-19
**Feature:** `agentkit user-card`

## Summary

| Field | Value |
|-------|-------|
| feature | user-card |
| baseline_tests | 3117 |
| final_tests | ≥3167 |
| new_tests | ≥50 |
| version | 0.64.0 |
| deliverables | D1 ✅ D2 ✅ D3 ✅ D4 ✅ D5 ✅ |

## Deliverables

- **D1** `UserCardEngine` core — `agentkit_cli/user_card.py`
- **D2** `agentkit user-card` CLI command — `agentkit_cli/commands/user_card_cmd.py`
- **D3** Dark-theme HTML card renderer — `agentkit_cli/renderers/user_card_html.py`
- **D4** Integration into `agentkit run` and `agentkit report`
- **D5** Version bump 0.63.0→0.64.0, CHANGELOG, README, BUILD-REPORT

## Test Files

- `tests/test_user_card_d1.py` — UserCardEngine core (≥14 tests)
- `tests/test_user_card_d2.py` — CLI command (≥14 tests)
- `tests/test_user_card_d3.py` — HTML renderer (≥10 tests)
- `tests/test_user_card_d4.py` — Integration (≥8 tests)
- `tests/test_user_card_d5.py` — Docs/version (≥5 tests)

## Notes

Lightweight wrapper over UserScorecardEngine. Compact 400px dark-theme HTML card suitable for embedding in READMEs and sharing. Includes Markdown embed snippet as HTML comment when --share is used.
