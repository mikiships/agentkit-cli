# agentkit-cli Progress Log

## v0.12.0 — `agentkit doctor` continuation pass

### D1: Core doctor result model and repo checks — DONE (prior pass)
- `DoctorCheckResult`, `DoctorReport` dataclasses with `as_dict()` / `exit_code()`
- Checks: git repo, initial commit, working tree, README.md, pyproject.toml, context files
- 21 tests
- Commit: `db30c34`

### D2: Toolchain probes — DONE
- `check_tool_binary(binary, is_core)`: PATH probe + `--version` capture
- Version parsing handles noisy multi-line output (first line, 80-char cap)
- Subprocess failures degrade gracefully (binary still counts as found)
- Core tools (agentmd, agentlint, coderace, agentreflect): missing = `fail`
- Optional tools (git, python3): missing = `warn`
- `check_toolchain()` runs all 6 probes

### D3: Actionability checks — DONE
- `check_source_files()`: recursive scan for .py/.ts/.js/.tsx/.jsx
- `check_context_freshness()`: `agentlint check-context --json` with full graceful fallback (not found, non-zero exit, non-JSON output, subprocess error, timeout)
- `check_output_dir()`: agentkit-report/ existence + write permission; parent-dir fallback
- `check_herenow_api_key()`: warn (not fail) when unset

### D4: CLI ergonomics — DONE
- `--category repo|toolchain|context|publish`: filter checks and summary
- `--fail-on warn|fail`: threshold for exit 1
- `--no-fail-exit`: always exit 0
- Invalid values exit 2 with clear error
- Commit: `0156f2c` (D2+D3+D4 combined)

### D5: Docs, changelog, version — DONE
- README `agentkit doctor` section: full check table, troubleshooting checklist, CI usage
- CHANGELOG: v0.12.0 entry
- Version bumped: 0.11.0 → 0.12.0 in `__init__.py` and `pyproject.toml`
- Final commit: see BUILD-REPORT.md

### Test counts
- D1 baseline: 21 doctor tests, 403 total
- This pass: +45 doctor tests = 66 total
- Full suite: **469 passing**

## v0.13.0 — `agentkit summary` build pass

### D1: Core summary command — DONE
- Added `agentkit summary` wiring in `agentkit_cli/main.py`
- Added `agentkit_cli/commands/summary_cmd.py` with deterministic markdown rendering
- Supports `--path` local analysis mode and `--json-input` file mode
- Added baseline tests for command help, markdown rendering, JSON input, and path mode
- Tests passing: `python3 -m pytest tests/test_summary.py tests/test_main.py -q` -> `10 passed`
- Next: maintainer-focused sections for verdicts, prioritized fixes, and compare data
- Blockers: none
