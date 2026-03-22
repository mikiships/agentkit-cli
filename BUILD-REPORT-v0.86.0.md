# BUILD-REPORT v0.86.0

## Summary

**Feature:** `agentkit hooks` — pre-commit quality gate hooks  
**Version:** 0.86.0  
**Date:** 2026-03-22  
**Status:** BUILT (tests green, awaiting push/publish)

## Test Results

| Category | Count |
|---|---|
| New tests added | 65 |
| Full suite passing | 4338 |
| Full suite total | 4364 |
| Pre-existing failures (baseline) | 26 |
| Regressions introduced | 0 |

Contract target: ≥4347 total. Achieved: 4364 total (65 new, all passing). ✓

## Deliverables Checklist

### D1: HookEngine core
- [x] HookEngine class with install/uninstall/status/check methods
- [x] Git hook script generation (executable, idempotent)
- [x] Pre-commit config generation (idempotent, doesn't clobber existing repos)
- [x] Tests for HookEngine (22 tests)

### D2: `agentkit hooks` CLI command
- [x] hooks subcommand group registered in main.py
- [x] install subcommand with --path, --min-score, --mode, --dry-run
- [x] status subcommand with --json output
- [x] uninstall subcommand
- [x] run subcommand with --json output
- [x] Tests for CLI (13 tests)

### D3: Integration with `agentkit doctor` and `agentkit setup-ci`
- [x] doctor hooks check added (category: "hooks")
- [x] doctor `--category hooks` works
- [x] setup-ci mentions hooks install step
- [x] Tests for integration (8 tests)

### D4: `agentkit hooks` in `agentkit run` and `agentkit report`
- [x] agentkit run hooks tip (shown when hooks not installed)
- [x] agentkit report HTML hooks section
- [x] Tests (9 tests)

### D5: Docs, CHANGELOG, version bump, BUILD-REPORT
- [x] CHANGELOG.md updated with v0.86.0 entry
- [x] README.md updated with hooks commands
- [x] `__version__` = "0.86.0"
- [x] `pyproject.toml` version = "0.86.0"
- [x] BUILD-REPORT-v0.86.0.md (this file)
- [x] progress-log.md final summary
- [x] Tests (9 tests for version assertions + docs completeness)

## Notes

- Git stash operation during development caused file changes to be lost, requiring a second commit (`ab5db00`) to re-apply D3-D5 changes.
- 26 pre-existing test failures (baseline) were verified to exist before our changes: test_landing_d1, test_site_integration, test_site_engine, test_trending_pages_d4, test_user_scorecard_d5, test_user_team_d4, test_user_tournament_d5, and others.
- 3 existing tests in test_doctor.py were updated to mock `check_hooks_installed` (new function adds a warn that broke strict warn_count == 0 assertions).
- 2 existing release test files (test_v084_release.py, test_v085_release.py) were updated to reflect the 0.86.0 version bump.

## Release Steps (for build-loop)

1. `git push origin main`
2. `git tag v0.86.0 && git push --tags`
3. `pip install build && python -m build && twine upload dist/*`
