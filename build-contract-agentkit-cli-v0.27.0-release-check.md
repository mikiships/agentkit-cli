# Build Contract: agentkit-cli v0.27.0 — `agentkit release-check`

**Version:** 0.27.0
**Date:** 2026-03-15
**Contract scope:** Add `agentkit release-check` command that verifies the 4-part release surface for a Python or npm package.

---

## Background

The recurring pattern (M35): packages get marked "shipped" when they are only locally complete. Tests pass, but the tag wasn't pushed, or PyPI doesn't have the new version yet. This command closes the verification loop.

---

## Deliverables

### D1: Core release-check engine (`agentkit_cli/release_check.py`)
Checks 4 surfaces for a given package name + version:
1. **Tests green** — run `pytest -q --tb=no` in the repo dir, check exit code
2. **Git push confirmed** — compare `git log --oneline -1` hash with `git ls-remote origin HEAD`; flag if local HEAD not in remote
3. **Tag confirmed** — check if `vX.Y.Z` tag exists in remote (`git ls-remote --tags origin vX.Y.Z`)
4. **Registry live** — for Python: query `https://pypi.org/pypi/{name}/{version}/json` and check 200. For npm: query `https://registry.npmjs.org/{name}/{version}` and check 200.

Output: structured dict with per-check status (pass/fail/skip), overall verdict (SHIPPED/RELEASE-READY/BUILT/UNKNOWN), and actionable next-step hints.

### D2: CLI command
```
agentkit release-check [--version VERSION] [--package NAME] [--registry pypi|npm|auto] [--skip-tests] [--json] [PATH]
```
- `PATH` defaults to current directory
- `--version` defaults to version in `pyproject.toml` or `package.json`
- `--package` defaults to name in `pyproject.toml` or `package.json`
- `--registry` auto-detects from project type if not specified
- `--skip-tests` skips the pytest/npm test step (for quick checks)
- `--json` outputs structured JSON for CI integration
- Rich table output by default with per-check colored status
- Exit code 0 = SHIPPED, 1 = not fully shipped (for CI use)

### D3: `--release-check` flag on `agentkit run` and `agentkit gate`
- `agentkit run --release-check` runs the full pipeline AND verifies release surfaces at the end
- `agentkit gate --release-check` adds release surface verification to the gate checks
- Prints release-check summary in the existing Rich output

### D4: Tests (minimum 30 new tests)
- Unit tests for each of the 4 checks (mock HTTP, mock git, mock pytest)
- Integration test against a fixture project
- CLI invocation tests (--json, --skip-tests, exit codes)
- Error handling: missing pyproject.toml, network failure, git not initialized

### D5: Docs and release
- README: add `agentkit release-check` section with example output
- CHANGELOG: v0.27.0 entry
- BUILD-REPORT.md: summary of what was built and test results
- Version bump: `0.26.1` → `0.27.0` in pyproject.toml

---

## Stop Conditions

**STOP and report if:**
- Full test suite drops below 960 passing
- Any existing command breaks (doctor, score, suggest, report, analyze, sweep, share all used in release-check integration)
- pyproject.toml version is not bumped to 0.27.0 before finishing
- Registry check logic makes assumptions about authentication (no API keys needed — only public registry lookups)

---

## Definition of Done

ALL of the following must be true:
- [ ] D1: `release_check.py` engine exists and all 4 checks work
- [ ] D2: `agentkit release-check` command works end-to-end
- [ ] D3: `--release-check` flag wired into `run` and `gate`
- [ ] D4: 30+ new tests, all passing, total suite >= 990
- [ ] D5: README + CHANGELOG + BUILD-REPORT + version 0.27.0

**DO NOT publish to PyPI. DO NOT push git tags. Build-loop handles publishing.**

---

## Repo
`~/repos/agentkit-cli/`

## Key files to understand first
- `agentkit_cli/commands/doctor.py` — pattern for toolchain verification commands
- `agentkit_cli/commands/gate_cmd.py` — pattern for gate commands with flags
- `agentkit_cli/commands/run_cmd.py` — pattern for adding flags to run
- `pyproject.toml` — version and project name
