# BUILD-REPORT — agentkit-cli v0.27.0

**Date:** 2026-03-15
**Feature:** `agentkit release-check`

---

## Deliverable Status (D1–D5)

| # | Deliverable | Status |
|---|-------------|--------|
| D1 | `agentkit_cli/release_check.py` — 4-surface check engine | ✅ DONE |
| D2 | `agentkit release-check` CLI command with all flags | ✅ DONE |
| D3 | `--release-check` flag on `agentkit run` and `agentkit gate` | ✅ DONE |
| D4 | 52 new tests (min 30 required), full suite 1012 passing | ✅ DONE |
| D5 | README section, CHANGELOG entry, version 0.27.0, BUILD-REPORT | ✅ DONE |

---

## Test Results

```
1012 passed in 15.29s
```

- Previous count: ~960
- New tests added: 52 (file: `tests/test_release_check.py`)
- All existing tests: passing
- New tests: passing

---

## Files Changed

| File | Change |
|------|--------|
| `agentkit_cli/release_check.py` | New — 4-surface engine |
| `agentkit_cli/commands/release_check_cmd.py` | New — CLI command |
| `agentkit_cli/main.py` | Added `release-check` command + `--release-check` flags to `run` and `gate` |
| `tests/test_release_check.py` | New — 52 tests |
| `pyproject.toml` | Version bumped 0.26.1 → 0.27.0 |
| `agentkit_cli/__init__.py` | Version bumped 0.26.0 → 0.27.0 |
| `CHANGELOG.md` | v0.27.0 entry added |
| `README.md` | `agentkit release-check` section added |

---

## What Was Built

### D1: Engine (`release_check.py`)

Four independent check functions:
1. `check_tests(path)` — runs `python3 -m pytest -q --tb=no`, checks exit code
2. `check_git_push(path)` — compares `git log` hash vs `git ls-remote origin HEAD`
3. `check_git_tag(path, version)` — checks `git ls-remote --tags origin vX.Y.Z`
4. `check_registry_pypi/npm(pkg, ver)` — HTTP GET to PyPI or npm registry

Structured output: `ReleaseCheckResult` with per-check `CheckResult` (status, detail, hint) and overall verdict: `SHIPPED | RELEASE-READY | BUILT | UNKNOWN`.

Auto-detects package name, version, and registry from `pyproject.toml` or `package.json`.

### D2: CLI Command

```
agentkit release-check [PATH] [--version V] [--package N] [--registry pypi|npm|auto] [--skip-tests] [--json]
```

- Exit code 0 = SHIPPED
- Exit code 1 = not fully shipped (CI-safe)
- Exit code 2 = invalid args
- `--json` outputs structured JSON for CI integration
- Rich table output with colored per-check status

### D3: Integration Flags

- `agentkit run --release-check` — appends release check table after pipeline
- `agentkit gate --release-check` — prepends release check table before gate eval

### D4: Tests

52 tests in `tests/test_release_check.py` covering:
- All 4 check functions (pass/fail/error/timeout paths)
- `resolve_metadata` and `_detect_registry` helpers
- `run_release_check` integration (mocked subprocess + HTTP)
- CLI invocation: `--json`, `--skip-tests`, exit codes, `--help`, invalid args
- `CheckResult` and `ReleaseCheckResult` dataclass contracts

---

## Notes

- No PyPI publish performed (build-loop handles publishing)
- No git tags pushed (build-loop handles tagging)
- No GitHub push performed (build-loop handles pushing)
- Registry checks use only public HTTP, no auth required
