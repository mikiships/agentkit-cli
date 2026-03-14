# All-Day Build Contract: agentkit-cli v0.17.0 — `agentkit analyze`

Status: In Progress
Date: 2026-03-14
Owner: Codex execution pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Add `agentkit analyze <target>` command that clones a GitHub repo (or uses a local path),
runs the static analysis tools (agentmd, agentlint, agentreflect), and returns a composite
agent quality score + summary.

This is the "viral mechanic" for the Show HN: zero-friction way to see what the toolkit does
on any public repo without installing anything in it first.

Target syntax:
- `agentkit analyze github:tiangolo/fastapi`
- `agentkit analyze https://github.com/tiangolo/fastapi`
- `agentkit analyze ./local-path`

This contract is considered complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Full test suite must pass at the end (all 626 existing + new tests).
4. New features must ship with docs and CHANGELOG updates in the same pass.
5. CLI outputs must be deterministic and schema-backed where specified.
6. Never modify files outside the project directory (~/repos/agentkit-cli/).
7. Commit after each completed deliverable (not at the end).
8. If stuck on same issue for 3 attempts, stop and write a blocker report.
9. Do NOT refactor, restyle, or "improve" code outside the deliverables.
10. Read existing tests and docs before writing new code.

## 3. Feature Deliverables

### D1. Core `agentkit analyze` command

**What:** New CLI command that:
1. Accepts a target: `github:owner/repo`, `https://github.com/owner/repo`, or local path
2. For GitHub targets: clones into a temp directory (`tempfile.mkdtemp(prefix='agentkit-analyze-')`)
3. Runs the static analysis pipeline:
   - `agentmd generate .` (if no CLAUDE.md/AGENTS.md exists, generate one)
   - `agentmd score .` (score existing or newly generated context)
   - `agentlint check-context --format json` (freshness + quality check)
   - `agentreflect generate .` (suggestions from git log + test output if any)
4. Computes composite score from available tool results
5. Prints Rich table summary with per-tool results + headline score
6. Cleans up temp dir after analysis (unless --keep)

**Required files:**
- `agentkit_cli/commands/analyze_cmd.py` (new)
- `agentkit_cli/analyze.py` (core analysis engine, new)
- Update `agentkit_cli/main.py` to register the command

**Options:**
- `--json` - machine-readable output
- `--keep` - don't delete temp clone dir (prints path for follow-up)
- `--publish` - publish HTML report to here.now after analysis
- `--timeout N` - clone + analysis timeout in seconds (default: 120)
- `--no-generate` - skip agentmd generate, only score what's already there

**Target parsing:**
- `github:owner/repo` → `https://github.com/owner/repo.git`
- `https://github.com/owner/repo` or `.git` URL → use as-is
- Bare `owner/repo` string (exactly one `/`, no spaces) → treat as GitHub shorthand
- Local path (starts with `.`, `/`, or `~`) → use directly, no clone

- [ ] `agentkit_cli/analyze.py` with `AnalyzeResult` dataclass + `analyze_target()` function
- [ ] `agentkit_cli/commands/analyze_cmd.py` with CLI wiring
- [ ] `main.py` registration
- [ ] Tests for D1 (target parsing, mock clone, pipeline execution)

### D2. Output formatting + JSON schema

**What:** 
- Rich table showing: Tool, Status, Score, Key Finding
- Headline: `Agent Quality Score: X/100 (Grade)  repo: owner/repo`
- `--json` flag outputs `AnalyzeResult` as JSON with fields:
  - `target`: str
  - `repo_name`: str  
  - `composite_score`: float
  - `grade`: str
  - `tools`: dict mapping tool name to `{score, status, finding}`
  - `generated_context`: bool
  - `temp_dir`: str (only if --keep)
  - `report_url`: str (only if --publish succeeded)

- [ ] Rich table output with color-coded grades
- [ ] `--json` structured output
- [ ] Tests for D2 (output format validation)

### D3. Error handling + graceful degradation

**What:**
- Git not installed → clear error message with install hint
- Clone fails (network, private repo, bad URL) → helpful error, clean temp dir
- Tool not installed (agentmd, agentlint, agentreflect) → skip tool, note in output, still score on available tools
- Empty repo / no Python files → note "no source files found" but still run context analysis
- Timeout → kill subprocess, clean temp dir, report partial results

- [ ] Network error handling with retry (1 retry, 5s backoff)
- [ ] Individual tool failure isolation (don't fail whole analysis if one tool errors)
- [ ] Temp dir cleanup in all error paths (use try/finally)
- [ ] Tests for D3 (mocked failures, timeout simulation)

### D4. README + docs update

**What:**
- Add `agentkit analyze` section to README.md under "Commands"
- Include example output (copy from actual test run)
- Add to CHANGELOG under v0.17.0

- [ ] README.md `agentkit analyze` section with examples
- [ ] CHANGELOG v0.17.0 entry
- [ ] Version bumped from 0.16.2 → 0.17.0 in pyproject.toml and __init__.py

### D5. Build report

**What:** Create `BUILD-REPORT.md` in ~/repos/agentkit-cli/ documenting:
- What was built (all deliverables)
- Test count (all existing + new tests passing)
- Any deviations from plan
- Any follow-up items

- [ ] BUILD-REPORT.md written
- [ ] All tests passing (run `python3 -m pytest -q`)

## 4. Test Requirements

- [ ] Unit tests for target URL parsing (github:, https://, local path, bare owner/repo)
- [ ] Mock clone test (patch subprocess.run for git clone)
- [ ] Mock pipeline test (patch run_tool calls, verify correct args)
- [ ] JSON output schema test
- [ ] Error handling tests (clone failure, tool failure, timeout)
- [ ] All 626 existing tests still passing

## 5. Reports

Write progress to `progress-log.md` after each deliverable:
- What was built
- What tests pass
- What's next
- Any blockers

## 6. Stop Conditions

- All deliverables checked and all tests passing → DONE, write BUILD-REPORT.md
- 3 consecutive failed attempts on same issue → STOP, write blocker report
- Scope creep detected → STOP, report what's new
- Any test that was passing before this build is now failing → STOP, fix before continuing

## 7. Important Context

- Project is at ~/repos/agentkit-cli/
- Current version: 0.16.2
- Target version: 0.17.0
- Use `python3 -m pytest -q` to run tests (NOT `python` or `pytest` alone)
- Existing tools available: agentmd, agentlint, agentreflect, coderace (all on PATH)
- Run tool calls use `agentkit_cli.tools.run_tool()` — see existing commands for patterns
- Don't publish to PyPI — build-loop handles that
- Don't commit to git — build-loop handles that
- Write BUILD-REPORT.md when done
