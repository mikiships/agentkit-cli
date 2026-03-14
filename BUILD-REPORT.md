# BUILD-REPORT.md — agentkit-cli v0.12.0

**Status:** SHIPPED  
**Date:** 2026-03-13  
**Contract:** all-day-build-contract-agentkit-cli-v0.12.0-doctor-continuation.md

---

## Deliverables Completed

| Deliverable | Status | Commit |
|-------------|--------|--------|
| D1: Core doctor result model + repo checks | ✅ Done (prior pass) | `db30c34` |
| D2: Toolchain probes (agentmd/agentlint/coderace/agentreflect/git/python3) | ✅ Done | `0156f2c` |
| D3: Actionability checks (source files, context freshness, output dir, API key) | ✅ Done | `0156f2c` |
| D4: `--json`, `--category`, `--fail-on`, `--no-fail-exit` flags | ✅ Done | `0156f2c` |
| D5: README, CHANGELOG, version bump | ✅ Done | (this commit) |

---

## Test Command

```bash
python3 -m pytest -q
```

## Final Test Counts

- **469 total tests passing, 0 failing**
- Doctor-specific tests: **66** (21 from D1 + 45 new)
- Breakdown of new tests:
  - D2 toolchain: 10 tests
  - D3 actionability: 21 tests
  - D4 CLI flags: 14 tests

## New Features Shipped

### `agentkit doctor` (v0.12.0)

Full preflight command with 16 structured checks across 4 categories:

**repo**: git repo, initial commit, working tree clean, README.md, pyproject.toml, context files  
**toolchain**: agentmd, agentlint, coderace, agentreflect (fail if missing), git + python3 (warn if missing) — all with version capture  
**context**: source file presence, agentlint context freshness (graceful fallback), output dir write access  
**publish**: HERENOW_API_KEY readiness

CLI flags added:
- `--json` — structured JSON output (same model as human output)
- `--category repo|toolchain|context|publish` — filter to one category
- `--fail-on warn|fail` — exit threshold (default: `fail`)
- `--no-fail-exit` — always exit 0

### Key design decisions
- Missing core toolkit binary = `fail`; missing optional binary = `warn`
- Context freshness check degrades gracefully when agentlint unavailable, errors, or returns non-JSON
- Human and JSON output use the same `DoctorReport` model
- `--category` filters both displayed checks and summary counts

## Known Limitations

- Context freshness check relies on `agentlint check-context --json` — if agentlint doesn't support this subcommand in a given version, it degrades to `warn`
- Output-dir not-writable test skipped under environments where `chmod` doesn't affect root; test correctly guards behavior for non-root users
- `check_context_freshness` in tests is patched to avoid requiring agentlint installed in the test environment

## Repo State

- Branch: `main`
- Working tree: clean after final commit
- No PyPI publish performed (out of scope)
- All prior tests passing: ✅
