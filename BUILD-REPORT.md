# BUILD-REPORT: agentkit-cli v0.5.1

**Date:** 2026-03-13  
**Build type:** Bug-fix release — `agentkit report` CLI invocation fixes

## Test Results

```
210 passed in 2.65s
```

All 210 tests pass (pytest tests/ -x). Includes new tests added in this release:
- `test_runner_agentlint_uses_format_json_flag` — verifies `--format json` not `--json`
- `test_runner_coderace_no_history` — graceful no_results dict when history is unparseable
- `test_runner_coderace_run_fails` — graceful no_results dict when command fails
- `test_runner_agentreflect_success` — returns `suggestions_md` dict
- `test_runner_agentreflect_uses_correct_flags` — verifies `--from-git --format markdown`
- `test_agentmd_summary_card_handles_list` — averages scores across list
- `test_agentmd_summary_card_handles_empty_list` — no crash on empty list
- `test_agentmd_summary_card_handles_dict` — existing dict behavior preserved
- `test_report_html_with_agentmd_list` — full HTML generation with agentmd list
- `test_agentreflect_section_renders_suggestions_md` — renders suggestions_md key

## End-to-End Result

```
agentkit report --path ~/repos/agentkit-cli
```

**Result: SUCCESS — HTML produced at agentkit-report.html (4367 bytes)**

Tool outcomes:
| Tool | Status | Notes |
|------|--------|-------|
| agentlint | failed | agentlint itself crashed (unrelated to our fix; non-zero exit) |
| agentmd | success | returned data, rendered in HTML |
| coderace | success | no cached history → returned no_results dict gracefully |
| agentreflect | success | returned suggestions_md markdown |

agentlint's own crash is a pre-existing issue in the agentlint tool itself (Python traceback from inside agentlint's code). Our runner handles it correctly — logs a warning and returns None instead of crashing the report.

## Bugs Fixed

1. **D1 agentlint**: `--json` → `--format json`
2. **D2 coderace**: `benchmark --json` → `benchmark history` + graceful `no_results` fallback
3. **D3 agentreflect**: `--format json` → `--from-git --format markdown`, returns `{"suggestions_md": text, "count": N}`
4. **D4 agentmd crash**: `_agentmd_summary_card` and `_agentmd_section` now handle list input by averaging scores

## Files Changed

- `agentkit_cli/report_runner.py` — D1, D2, D3 fixes
- `agentkit_cli/commands/report_cmd.py` — D4 fix + agentreflect section rendering
- `tests/test_report.py` — updated fixtures + 10 new tests
- `pyproject.toml` — bumped to 0.5.1
- `CHANGELOG.md` — documented all fixes
