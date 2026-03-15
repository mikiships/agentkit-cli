# BUILD-REPORT: agentkit-cli v0.20.0

**Contract:** agentkit-cli-v0.20.0-setup-ci  
**Date:** 2026-03-14  
**Status:** COMPLETE

## Summary

Added `agentkit setup-ci` command — one-command CI onboarding for any Python repo.

## Deliverables

### D1: Core `agentkit setup-ci` command + GitHub Actions workflow writer ✅
- `agentkit_cli/commands/setup_ci_cmd.py` — full command implementation
- Wired into `agentkit_cli/main.py` as `agentkit setup-ci`
- Generates `.github/workflows/agentkit-quality.yml` with correct v0.19.0 gate flags
- Supports `--dry-run`, `--force`, `--workflow-path`, `--min-score`, `--path`
- Non-destructive by default: skips existing file unless `--force` is set
- Detects GitHub remote via `.git/config`

### D2: Baseline generation integration ✅
- Runs `agentkit report --json --output .agentkit-baseline.json` after workflow write
- Warns (doesn't abort) if baseline generation fails
- `--skip-baseline` bypasses report run
- Generated workflow uses `if [ -f ".agentkit-baseline.json" ]` guard before passing `--baseline-report`

### D3: README badge injection ✅
- Reuses existing `readme_cmd.readme_command()` — no duplication
- `--no-badge` skips injection
- Reports "Badge injected" or "skipped" clearly

### D4: Docs, CHANGELOG, version bump ✅
- `README.md`: full `## agentkit setup-ci` section with flags table, example flow, and usage
- `CHANGELOG.md`: v0.20.0 entry with all new flags documented
- `pyproject.toml`: version bumped `0.19.0` → `0.20.0`
- `agentkit_cli/__init__.py`: `__version__` bumped to `"0.20.0"`

## Tests

- `tests/test_setup_ci.py`: 16 new tests covering all contract requirements
- Full suite: **702 tests passing** (686 original + 16 new)
- `pytest -q` exits 0

### Test coverage:
- Workflow written to correct default path
- `--dry-run` prints to stdout without writing
- `--force` overwrites existing file
- Without `--force`, skips existing file
- `--min-score` value embedded in YAML
- `--skip-baseline` bypasses `_run_baseline`
- Baseline written on success; warning on failure (no abort)
- `--no-badge` skips `_inject_badge`
- Badge injected when README exists
- Custom `--workflow-path` respected
- `_is_github_repo` helper: true/false/no-git-dir cases

## No Regressions

All 686 pre-existing tests continue to pass unchanged.

## Files Modified

| File | Change |
|---|---|
| `agentkit_cli/commands/setup_ci_cmd.py` | Created (new command) |
| `agentkit_cli/main.py` | Wired setup-ci command |
| `tests/test_setup_ci.py` | Created (16 tests) |
| `pyproject.toml` | Version 0.19.0 → 0.20.0 |
| `agentkit_cli/__init__.py` | __version__ 0.19.0 → 0.20.0 |
| `CHANGELOG.md` | Added v0.20.0 entry |
| `README.md` | Added agentkit setup-ci section |
