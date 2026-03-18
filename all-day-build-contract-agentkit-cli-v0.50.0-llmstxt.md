# All-Day Build Contract: agentkit-cli v0.50.0 — `agentkit llmstxt`

Status: In Progress
Date: 2026-03-18
Owner: Codex execution pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Add `agentkit llmstxt` — a command that generates `llms.txt` and `llms-full.txt` files for any repository, following the llms.txt specification (https://llmstxt.org/). These files tell LLMs how to consume a project's documentation and API surface, making repos accessible to AI-powered tools beyond just coding agents.

The feature complements `agentmd` (context for coding agents) with a parallel surface for "AI access to docs" — expanding agentkit's addressable market. Also adds `--llmstxt` flag to `agentkit run` and `agentkit report` to include llms.txt generation in the standard workflow.

This contract is considered complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Full test suite must pass at the end (`python3 -m pytest -q`). Baseline: 2183 tests.
4. New features must ship with docs and CHANGELOG updates in the same pass.
5. CLI outputs must be deterministic and schema-backed where specified.
6. Never modify files outside the project directory (`~/repos/agentkit-cli/`).
7. Commit after each completed deliverable (not at the end).
8. If stuck on same issue for 3 attempts, stop and write a blocker report.
9. Do NOT refactor, restyle, or "improve" code outside the deliverables.
10. Read existing tests and docs before writing new code.

## 3. Feature Deliverables

### D1. LlmsTxtGenerator core (agentkit_cli/llmstxt.py)

Generates llms.txt and llms-full.txt following the specification at https://llmstxt.org/:

- `llms.txt`: title, description, structured list of key docs with links
  - H1 title (project name)
  - Blockquote summary (one sentence description)
  - Sections: Docs, API, Examples — each with markdown links
- `llms-full.txt`: full inline content of all referenced files (not just links)
- LlmsTxtGenerator class with:
  - `scan_repo(path: str) -> RepoInfo` — detect README, CHANGELOG, docs/, examples/, API modules, CLAUDE.md/AGENTS.md
  - `generate_llms_txt(repo_info: RepoInfo) -> str` — standard llms.txt output
  - `generate_llms_full_txt(repo_info: RepoInfo) -> str` — expanded full-text version
  - Intelligent content extraction: find docstrings, README sections, CHANGELOG highlights
  - File size cap: skip files >100KB in llms-full.txt

Required files:
- `agentkit_cli/llmstxt.py` (LlmsTxtGenerator, RepoInfo dataclass)
- `tests/test_llmstxt.py` (≥20 tests covering scan, generate, edge cases)

- [ ] LlmsTxtGenerator core class
- [ ] scan_repo() function (README/docs/CHANGELOG/examples detection)
- [ ] generate_llms_txt() following spec format
- [ ] generate_llms_full_txt() with inline content
- [ ] Tests for D1 (≥20 tests)

### D2. `agentkit llmstxt` CLI command

New subcommand: `agentkit llmstxt [PATH] [--full] [--output DIR] [--json] [--share]`

- `PATH`: local path or `github:owner/repo` (clone + generate)
- `--full`: also generate llms-full.txt (default: only llms.txt)
- `--output DIR`: write files to directory (default: current dir)
- `--json`: structured JSON output with file paths, sizes, section counts
- `--share`: publish to here.now and return shareable URL
- Rich table output showing sections found, file sizes, links count
- Write `llms.txt` (and optionally `llms-full.txt`) to output dir

Required files:
- `agentkit_cli/commands/llmstxt_cmd.py`
- CLI wiring in `agentkit_cli/main.py`
- `tests/test_llmstxt_cmd.py` (≥15 tests)

- [ ] CLI command with all flags
- [ ] github:owner/repo support (clone, generate, cleanup)
- [ ] Rich table output
- [ ] --json structured output
- [ ] --share integration (upload llms.txt as here.now page)
- [ ] Tests for D2 (≥15 tests)

### D3. Integration into `agentkit run` and `agentkit report`

- `agentkit run --llmstxt`: include llms.txt generation step in the standard run workflow
  - Add "llmstxt" to the run pipeline after context generation
  - Include llms.txt section count and file size in run output
  - Store llmstxt_generated: bool and llmstxt_path in run record (history DB)
- `agentkit report --llmstxt`: include an llms.txt card in the HTML report
  - Card shows: files generated, section count, top-level structure preview
- `agentkit doctor`: add llmstxt readiness check (does README exist? any docs/ dir?)

Required files:
- Modifications to `agentkit_cli/commands/run_cmd.py`
- Modifications to `agentkit_cli/commands/report_cmd.py`
- Modifications to `agentkit_cli/commands/doctor_cmd.py`
- `tests/test_run_llmstxt.py` (≥10 tests)

- [ ] `agentkit run --llmstxt` integration
- [ ] Report card in HTML report
- [ ] Doctor readiness check
- [ ] Tests for D3 (≥10 tests)

### D4. `agentkit llmstxt --validate` and quality scoring

- `--validate`: check an existing llms.txt against the spec (correct H1, has blockquote summary, all links valid)
- Validation output: Rich table of pass/fail checks with suggestions
- `--score`: 0-100 quality score for the generated llms.txt:
  - Has title: 20pts
  - Has summary: 20pts
  - Has ≥2 sections: 20pts
  - Has ≥3 links: 20pts
  - No broken relative paths: 20pts
- `agentkit score` integration: include llmstxt_score as an optional dimension when `llms.txt` exists

Required files:
- Modifications to `agentkit_cli/llmstxt.py` (validator + scorer)
- `tests/test_llmstxt_validate.py` (≥12 tests)

- [ ] --validate flag with spec checking
- [ ] Scoring 0-100 function
- [ ] Rich output for validation results
- [ ] agentkit score integration (optional dimension)
- [ ] Tests for D4 (≥12 tests)

### D5. Docs, CHANGELOG, version bump, BUILD-REPORT

- README: new `agentkit llmstxt` section with examples
  - Include "What is llms.txt?" one-liner, command examples, sample output
- CHANGELOG: v0.50.0 entry (## [0.50.0] — YYYY-MM-DD)
- pyproject.toml: version 0.49.0 → 0.50.0
- BUILD-REPORT.md: deliverables checklist, test count, known limitations
- Progress log: write to `progress-log.md` after each deliverable

- [ ] README section added
- [ ] CHANGELOG entry
- [ ] Version bump to 0.50.0
- [ ] BUILD-REPORT.md written
- [ ] Progress log up to date

## 4. Test Requirements

- [ ] Unit tests for LlmsTxtGenerator (scan, generate, edge cases)
- [ ] CLI tests for `agentkit llmstxt` (all flags)
- [ ] Integration: run with --llmstxt flag
- [ ] Validation tests (valid/invalid llms.txt inputs)
- [ ] Edge cases: empty repo, no README, README-only repo, repo with full docs/
- [ ] All existing 2183 tests must still pass
- [ ] Final total: ≥2250 tests

## 5. Reports

- Write progress to `progress-log.md` after each deliverable
- Include: what was built, what tests pass, what's next, any blockers
- Final summary when all deliverables done or stopped

## 6. Stop Conditions

- All deliverables checked and all tests passing → DONE, write BUILD-REPORT
- 3 consecutive failed attempts on same issue → STOP, write blocker report
- Scope creep detected → STOP, report what's new
- All tests passing but deliverables remain → continue to next deliverable

## 7. Context

- Repo: ~/repos/agentkit-cli/
- Current version: 0.49.0 (just shipped GitHub Checks API)
- Test baseline: 2183 passing
- PyPI: agentkit-cli (pip install agentkit-cli)
- llms.txt spec reference: https://llmstxt.org/ — H1 title, blockquote summary, sections with markdown links
- Existing similar command to reference: `agentkit analyze` (github:owner/repo clone pattern), `agentkit share` (here.now upload pattern)
- All here.now uploads go through `agentkit_cli/commands/share.py` (HereNowUploader class)
- History DB: `agentkit_cli/history.py` (RunRecord dataclass + HistoryDB class)
- ToolAdapter: `agentkit_cli/tool_adapter.py` — use this for any quartet tool invocations
