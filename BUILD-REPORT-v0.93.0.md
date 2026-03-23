# BUILD-REPORT: agentkit-cli v0.93.0

**Version:** 0.93.0
**Date:** 2026-03-23
**Owner:** Codex execution pass

## Deliverables

| # | Deliverable | Status | Tests |
|---|-------------|--------|-------|
| D1 | ChangelogEngine core | ✅ DONE | 20 tests |
| D2 | `agentkit changelog` CLI command | ✅ DONE | 11 tests |
| D3 | Integration with `agentkit release-check --changelog` | ✅ DONE | 5 tests |
| D4 | `GITHUB_STEP_SUMMARY` support + GitHub Release creation | ✅ DONE | 8 tests |
| D5 | Docs, CHANGELOG, version bump to v0.93.0 | ✅ DONE | 8 tests |

## Test Counts

- **Baseline (v0.92.0):** ~1814 passing
- **New tests added:** 52
- **Final:** 4635 passing, 0 regressions

## Files Added/Modified

### New Files
- `agentkit_cli/changelog_engine.py` — ChangelogEngine class
- `agentkit_cli/commands/changelog_cmd.py` — changelog CLI command
- `tests/test_changelog_engine_d1.py` — D1 tests (20)
- `tests/test_changelog_cmd_d2.py` — D2 tests (11)
- `tests/test_release_check_changelog_d3.py` — D3 tests (5)
- `tests/test_changelog_github_d4.py` — D4 tests (8)
- `tests/test_changelog_d5.py` — D5 tests (8)
- `tests/test_changelog_integration.py` — integration tests (3)
- `BUILD-REPORT.md` — this file
- `BUILD-REPORT-v0.93.0.md` — versioned copy

### Modified Files
- `agentkit_cli/__init__.py` — version bumped to 0.93.0
- `agentkit_cli/main.py` — `changelog` command registered
- `agentkit_cli/commands/release_check_cmd.py` — `--changelog` flag added
- `pyproject.toml` — version bumped to 0.93.0
- `CHANGELOG.md` — `## [0.93.0]` section added
- `README.md` — `## Changelog Generation` section added
- `tests/test_interactive_ui_d5.py` — version assertions updated

## Deviations

- None. All deliverables match the contract spec.

## Feature Summary

`agentkit changelog` generates a human-readable changelog from git commits and quality score deltas:

```bash
agentkit changelog --version v0.93.0
agentkit changelog --format release --version v0.93.0
agentkit release-check --changelog
```

Groups commits by conventional-commit prefix (feat/fix/docs/refactor/test/chore).
Includes score delta from history DB when available.
Supports GITHUB_STEP_SUMMARY for GitHub Actions CI output.
