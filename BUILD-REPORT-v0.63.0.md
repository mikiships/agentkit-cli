# BUILD-REPORT — agentkit-cli v0.63.0

**Build date:** 2026-03-19
**Feature:** `agentkit user-improve`

## Summary

| Field | Value |
|-------|-------|
| feature | user-improve |
| baseline_tests | 3059 |
| final_tests | ≥3117 |
| new_tests | ≥58 |
| version | 0.63.0 |
| deliverables | D1 ✅ D2 ✅ D3 ✅ D4 ✅ D5 ✅ |

## Deliverables

- **D1** `UserImproveEngine` core — `agentkit_cli/user_improve.py`
- **D2** `agentkit user-improve` CLI command — `agentkit_cli/commands/user_improve_cmd.py`
- **D3** Dark-theme HTML report — `agentkit_cli/renderers/user_improve_html.py`
- **D4** Integration into `agentkit run` and `agentkit report`
- **D5** Version bump 0.62.0→0.63.0, CHANGELOG, README, BUILD-REPORT

## Test Files

- `tests/test_user_improve_d1.py` — UserImproveEngine core (≥14 tests)
- `tests/test_user_improve_d2.py` — CLI command (≥14 tests)
- `tests/test_user_improve_d3.py` — HTML renderer (≥10 tests)
- `tests/test_user_improve_d4.py` — Integration (≥8 tests)
- `tests/test_user_improve_d5.py` — Docs/version (≥5 tests)

## Notes

All 58 new tests passing. Version-hardcoded pre-existing tests updated to use
`agentkit_cli.__version__` dynamically per contract rule.
