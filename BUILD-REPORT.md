# Build Report: agentkit-cli v0.8.0

**Date:** 2026-03-13  
**Contract:** `agentkit-cli-v0.8.0-badge.md`

## Test Results

```
290 passed in 3.33s
```

**Target:** ≥265 · **Actual:** 290 ✅  
**New tests added:** 40 (in `tests/test_badge.py`)

## Deliverables

| # | Deliverable | Status |
|---|-------------|--------|
| D1 | `agentkit badge` CLI command | ✅ |
| D2 | `compute_badge_score()` + color thresholds | ✅ |
| D3 | `--json` output mode | ✅ |
| D4 | Badge snippet in `agentkit report` HTML + `--publish` | ✅ |
| D5 | Tests (40 new), README "Add a Badge" section, CHANGELOG, version bump | ✅ |

## Version

- `__init__.py`: `0.8.0`
- `pyproject.toml`: `0.8.0`

## Implementation Notes

- `agentkit_cli/commands/badge_cmd.py` — new file with all badge logic
- `agentkit_cli/main.py` — `badge` command registered
- `agentkit_cli/commands/report_cmd.py` — badge snippet embedded in HTML report; badge markdown printed on `--publish`
- `tests/test_badge.py` — 40 tests covering color thresholds, URL generation, score extraction, compute_badge_score, CLI integration, JSON output, score override, and clamping
- Two existing tests updated: `test_version_flag` (0.7.0→0.8.0) and `test_report_html_is_self_contained` (badge URLs are intentional external links, not CDN deps)

## Hard Rules Compliance

- ❌ Did NOT publish to PyPI
- ❌ Did NOT make HTTP requests to external services (badge URLs are generated strings only)
- ❌ Did NOT modify any repo other than `~/repos/agentkit-cli`
