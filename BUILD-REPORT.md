# Build Report — agentkit-cli v0.11.0

**Date:** 2026-03-13
**Contract:** memory/contracts/agentkit-cli-v0.11.0-suggest.md
**Status:** COMPLETE

## What Was Built

### `agentkit suggest` command

A new CLI command that turns agentlint findings into a prioritized action list answering "What should I fix to improve my agent quality score?"

**New files:**
- `agentkit_cli/suggest_engine.py` — prioritization engine
  - `Finding` dataclass (tool, severity, category, description, fix_hint, auto_fixable, file, line)
  - `parse_agentlint_check_context(json)` — extracts findings from check-context JSON
  - `parse_agentlint_diff(json)` — extracts findings from diff analysis JSON
  - `prioritize(findings, top_n)` — deduplicates (same category+file = one finding), sorts critical→high→medium→low
  - `prioritize_findings(output)` — high-level entry point
  - Severity mapping: year-rot/path-rot/mcp-security=critical, script-rot/stale-todo=high, bloat/multi-file-conflict=medium, cosmetic/whitespace=low

- `agentkit_cli/commands/suggest_cmd.py` — command implementation
  - `suggest_command(path, show_all, fix, dry_run, json_output)`
  - Auto-fixes: year-rot (updates years >2 years old), trailing-whitespace, duplicate-blank-lines
  - Only modifies context files: CLAUDE.md, AGENTS.md, .agents/*.md
  - `--dry-run` shows unified diff without writing
  - Rich table output with severity color-coding
  - Score summary line: "Current score: 72/100 — 3 critical issues found"

**Modified files:**
- `agentkit_cli/main.py` — wired `suggest` command with all flags
- `tests/test_suggest.py` — 59 new tests
- `tests/test_main.py` — updated version assertion
- `CHANGELOG.md` — v0.11.0 entry
- `README.md` — `agentkit suggest` section added
- `pyproject.toml` — version bumped to 0.11.0
- `agentkit_cli/__init__.py` — version bumped to 0.11.0

## Test Count

| Phase | Count |
|-------|-------|
| Baseline (v0.10.0) | 357 |
| New tests added | 59 |
| **Final (v0.11.0)** | **416** |

Contract required 392+ (35+ new). Delivered 416 (59 new). ✓

## Deviations from Contract

**None.** All D1–D5 deliverables implemented as specified.

Minor implementation notes:
- Fix helpers (`_fix_year_rot`, etc.) live in `suggest_cmd.py` rather than `suggest_engine.py` since they are command-level concerns and the engine stays importable without side effects.
- `run_fixes` is also exported from `suggest_cmd.py` (importable for tests).
- The `suggest_command` function runs auto-fixes even when no agentlint findings exist (a user may want to run `--fix` on a clean project for whitespace/year cleanup).

## Ready to Publish

**Yes.** All 416 tests pass, version bumped to 0.11.0, docs updated, CHANGELOG written.
