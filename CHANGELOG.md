# Changelog

## v0.18.0 (2026-03-14)

### Added
- `agentkit sweep` command: multi-target batch analysis with ranked output
  - **D1 Core engine**: `agentkit sweep github:psf/requests github:pallets/flask .` — batch runner reusing existing `analyze` pipeline; `--targets-file` for file-based target lists; deduplication; failure isolation (one bad target doesn't crash the batch)
  - **D2 Ranked output**: Rich table with columns (target | score | grade | status | error); `--sort-by` flag (score, name, grade); `--limit N` for top-N display
  - **D3 JSON output**: `--json` flag with stable schema `{ targets, results: [{rank, target, score, grade, status, error}], summary_counts }`; deterministic, console-noise-free; ranking order preserved in JSON
  - **D4 Docs**: README sweep section with usage examples; CHANGELOG entry; version bump to 0.18.0
- `sort_results()` in `agentkit_cli/sweep.py`: sort sweep results by score (descending), name, or grade
- 20 new tests covering sort, limit, Rich table, JSON schema, and determinism

## v0.17.0 (2026-03-14)

### Added
- `agentkit analyze <target>` command: zero-friction agent quality analysis for any GitHub repo or local path
  - **Target formats**: `github:owner/repo`, `https://github.com/owner/repo`, `owner/repo` (bare shorthand), `./local-path`
  - **Pipeline**: clones repo into temp dir (depth=1), runs `agentmd generate` (if no context), `agentmd score`, `agentlint check-context --format json`, `agentreflect generate`, computes composite score
  - **Output**: Rich table showing Tool / Status / Score / Key Finding + headline `Agent Quality Score: X/100 (Grade)  repo: owner/repo`
  - **Flags**: `--json` (machine-readable output), `--keep` (keep temp clone dir), `--publish` (publish HTML report to here.now), `--timeout N` (default 120s), `--no-generate` (skip agentmd generate)
  - **Error handling**: git not installed → clear error; clone failure → helpful message + temp dir cleanup; individual tool failure isolation; timeout → partial results; 1 retry with 5s backoff on clone
  - **JSON schema**: `target`, `repo_name`, `composite_score`, `grade`, `tools`, `generated_context`, `temp_dir` (if --keep), `report_url` (if --publish succeeded)
- 25 new tests covering URL parsing, mock clone, pipeline execution, JSON schema, and all error paths

## v0.16.2 (2026-03-14)

### Fixed
- `agentkit score`: was passing `--json` to `agentlint check-context` (invalid flag). Corrected to `--format json`.
- `agentkit suggest`: same flag issue in two places (`check-context --json` → `--format json`; bare `agentlint --json` → `agentlint check --format json`).
- `agentkit report`: `coderace benchmark history` now called with `--format json` instead of no format flag.
- Version check test made forward-compatible (checks `"0.16"` prefix, not exact string).

## v0.16.1 (2026-03-14)

### Fixed
- `agentkit doctor` context freshness check: was passing `--json` to `agentlint check-context` (invalid flag). Corrected to `--format json`. Regression test added.

## v0.16.0 (2026-03-14)

### Added
- `agentkit score` command: composite 0-100 agent quality score synthesizing all four toolkit tools
- `CompositeScoreEngine` in `agentkit/composite.py`: weighted scoring with automatic weight renormalization for missing tools
- Grade assignments (A/B/C/D/F) based on composite score thresholds
- `--breakdown` flag for per-component Rich table output
- `--json` output for machine-readable composite score
- `--ci` / `--min-score` flags for CI gate integration
- `agentkit run` now displays composite score line at pipeline completion
- Composite score recorded to history DB as `composite` tool
- `agentkit badge` now defaults to composite score; use `--tool <name>` for single-tool badge
- 50 new tests covering all composite score functionality

## v0.15.0 (2026-03-14)

### Added
- `agentkit leaderboard` command: ranked comparison of agent runs grouped by label
  - **D1 Run labeling**: `--label <str>` flag on `agentkit run`; label stored in history DB via backward-compatible `ALTER TABLE` migration
  - **D2 Leaderboard engine**: `agentkit/leaderboard_cmd.py` with `get_leaderboard_data()` — groups runs by label, computes avg/best/worst/trend (last-3 minus first-3 avg); handles NULL labels as "default"
  - **D3 CLI command**: Rich ranked table with Rank, Label, Runs, Avg Score, Trend (↑/↓/→), Best, Worst; `--json`, `--by`, `--since`, `--project`, `--last` flags
  - **D4 GitHub Actions**: `leaderboard-json` output when `save-history: true`; README example snippet
- 47 new tests; full suite 575 tests passing

## v0.14.0 (2026-03-14)

### Added
- `agentkit history` command: persistent quality score tracking with SQLite backend
  - **D1 HistoryDB**: SQLite store at `~/.config/agentkit/history.db`; `record_run()`, `get_history()`, `clear_history()` with idempotent schema
  - **D2 Auto-record**: `agentkit run` automatically records per-tool and overall scores after each run; `--no-history` flag to skip; DB failures never abort the run
  - **D3 history command**: Rich table with trend arrows and block bars; `--limit`, `--tool`, `--project`, `--graph` (sparkline), `--json`, `--clear` (with confirmation), `--all-projects` flags
  - **D4 GitHub Actions**: `save-history` optional input; `history-json` output; `examples/agentkit-ci.yml` example workflow
- 52 new tests; full suite 528 tests passing

## v0.13.0 (2026-03-14)

### Added
- `agentkit summary` command: maintainer-facing summary for CI, PR, and release workflows
  - **D1 Core command**: `--path` (local analysis) and `--json-input` (file mode); deterministic markdown rendering
  - **D2 Maintainer sections**: verdict logic (`PASSING`, `WARNINGS_PRESENT`, `ACTION_REQUIRED`, `REGRESSION_DETECTED`); per-tool status with concise notes; top-fixes section (up to 5 prioritized findings from agentlint/agentreflect); optional compare/regression section
  - **D3 GitHub-friendly outputs**: `--output <path>` writes markdown to file; `--job-summary` appends to `GITHUB_STEP_SUMMARY`; clear error when job-summary env var is absent
  - **D4 JSON mode**: `--json` emits structured payload (project, verdict, score, tool_status, top_fixes, compare, markdown)
- README `agentkit summary` section with full usage examples and GitHub Actions integration
- 7 new summary tests; full suite 476 tests passing

## v0.12.0 (2026-03-13)

### Added
- `agentkit doctor` expanded to a full preflight command (D2–D4):
  - **D2 Toolchain probes**: checks agentmd, agentlint, coderace, agentreflect (missing = fail); git, python3 (missing = warn); captures version text with noisy-output tolerance
  - **D3 Actionability checks**: source-file presence, context freshness via `agentlint check-context --json` (graceful degradation when unavailable), output-dir write access, HERENOW_API_KEY readiness
  - **D4 CLI ergonomics**: `--category repo|toolchain|context|publish` filter; `--fail-on warn|fail` threshold; `--no-fail-exit` for hooks
- README `agentkit doctor` section rewritten with full check table, troubleshooting checklist, and CI usage example
- 45 new doctor tests (21 → 66); full suite 469 tests passing

## v0.11.0 (2026-03-13)

### Added
- `agentkit suggest` command: prioritized action list from agentlint findings
- `suggest_engine.py`: `Finding` dataclass, `parse_agentlint_check_context`, `parse_agentlint_diff`, `prioritize`, `prioritize_findings`
- `--fix` flag: auto-applies safe fixes (year-rot, trailing-whitespace, duplicate-blank-lines) to context files only
- `--dry-run` flag: shows unified diff without writing changes
- `--all` flag: shows all findings instead of top 5
- `--json` flag: structured JSON output with score + findings array
- 59 new tests (357 → 416 total)

## v0.10.0 (2026-03-13)

### Added

- **`agentkit compare`** — new command to compare agent quality scores between two git refs.
  - `agentkit compare <ref1> <ref2>` (defaults: `HEAD~1`, `HEAD`)
  - Per-tool score deltas shown in a colored Rich table (green = improved, red = degraded)
  - Net delta + verdict: `IMPROVED` (>+5), `NEUTRAL` (-5..+5), `DEGRADED` (<-5)
  - `--json` flag: structured JSON output with all deltas
  - `--quiet` flag: only prints the verdict (IMPROVED/NEUTRAL/DEGRADED) — ideal for shell scripts
  - `--ci` flag: exits with code 1 if verdict is DEGRADED
  - `--min-delta N` flag: exits 1 if net delta is below N (for stricter CI gates)
  - `--tools` flag: limit which quartet tools are compared
  - `--files` flag: show which files changed between refs
  - Graceful handling of tool failures (marks as N/A, does not crash)
  - Uses `git worktree` for safe, isolated checkout of each ref
- **`agentkit_cli/utils/git_utils.py`** — new git helpers (resolve_ref, changed_files, Worktree context manager)
- **GitHub Action `mode: compare`** — new compare mode for action.yml with `compare-base`, `compare-head`, and `min-delta` inputs
- **Example workflow** — `.github/workflows/examples/agentkit-compare.yml`

### Changed

- Version bumped to 0.10.0

## v0.9.0 (2026-03-13)

### Added

- **`agentkit readme`** — new command to inject or update the agent quality badge in README.md.
  - Finds README.md in the current directory (or `--readme path/to/README.md`)
  - Idempotent: if the badge section already exists, updates the score; otherwise appends to end of file
  - `--dry-run`: show what would change without modifying the file
  - `--remove`: remove the injected section cleanly
  - `--section-header`: customize the injected section header (default: `## Agent Quality`)
  - `--score N`: override computed score
  - Prints summary: `Updated README.md — agent quality: 87/100 (green)`
- **`agentkit run --readme`** — runs the full pipeline then injects/updates the README badge
- **`agentkit report --readme`** — generates the HTML report then injects the badge

### Changed

- Version bumped to 0.9.0

## v0.8.0 (2026-03-13)

### Added

- **`agentkit badge`** — new command to generate a shields.io-compatible README badge showing the project's agent quality score. No server required; just a static badge URL.
  - Computes score from agentlint, agentmd, and coderace results (average of available components)
  - Color-coded: green ≥80, yellow 60-79, orange 40-59, red <40
  - Outputs badge URL, Markdown snippet, and HTML snippet
  - `--json` mode for CI integration: `{"score":87,"color":"green","badge_url":"...","markdown":"...","html":"..."}`
  - `--score N` to override computed score (useful for testing or CI gates)
- **Badge in HTML report** — `agentkit report` now embeds the badge at the top of the generated HTML report
- **Badge on publish** — `agentkit report --publish` now also prints the badge Markdown snippet

### Changed

- Version bumped to 0.8.0

## v0.7.0 (2026-03-13)

### Added

- **GitHub Actions composite action** (`action.yml`) — Run the full Agent Quality Toolkit pipeline on every PR. Checks agentlint context score, agentmd drift, and coderace review, then posts an aggregated quality comment to the PR.
  - Inputs: `github-token` (required), `min-lint-score` (default: 70), `post-comment` (default: true), `python-version` (default: 3.11)
  - Outputs: `lint-score`, `drift-status`, `review-summary`
  - Fails the action if lint score < `min-lint-score`
- **`scripts/run-agentkit-action.py`** — orchestrates agentlint, agentmd, and coderace; aggregates results to JSON; sets GitHub Actions outputs.
- **`scripts/post-pr-comment.py`** — posts/updates a formatted markdown quality report comment on the PR via GitHub API (idempotent).
- **`examples/agentkit-quality.yml`** — ready-to-use workflow file for adopters.
- **README GitHub Action section** — explains what the action checks, how to add it in 3 lines, PR comment format, and input/output reference.

## v0.6.0 (2026-03-13)

### Added

- **`agentkit publish`** — new command to upload an HTML report to [here.now](https://here.now) and return a shareable URL. Supports anonymous (24h expiry) and authenticated (persistent) publishes via `HERENOW_API_KEY` env var. Options: `--json`, `--quiet`.
- **`agentkit report --publish`** — generate a report and publish it in one command. Publish failure is non-fatal (prints a warning, does not exit 1).
- **`agentkit run --publish`** — run the full pipeline and publish the resulting report. Publish failure is also non-fatal.

## v0.5.1 (2026-03-13)

### Fixed
- **agentlint runner**: corrected CLI flag from `--json` (nonexistent) to `--format json`
- **coderace runner**: removed `benchmark --json` (no such flag); now uses `benchmark history`
  to check for cached results. Returns `{"status": "no_results", ...}` gracefully if no
  history found — no crash, no live agent run required
- **agentreflect runner**: `--format json` not supported; now uses `--from-git --format markdown`
  and returns `{"suggestions_md": text, "count": N}` instead of trying to parse JSON
- **agentmd summary card**: `_agentmd_summary_card` crashed when agentmd returned a list of
  per-file scored dicts instead of a single dict; now averages scores across the list and
  shows "N files analyzed" subtitle
- Updated `_agentreflect_section` to render `suggestions_md` key (markdown text in `<pre>`)
  with fallback to legacy `summary`/`reflection`/`output` keys

## v0.5.0 (2026-03-13)

### Added
- `agentkit report` — run all toolkit checks and generate a shareable HTML quality report
  - Detects which quartet tools are installed; runs available checks with 60s timeouts
  - `--json` emits structured JSON with coverage score, per-tool status, and tool output
  - `--output PATH` saves HTML report to specified path (default: `./agentkit-report.html`)
  - `--open` auto-opens the report in the default browser after saving
  - `--path PATH` override project directory
  - Self-contained HTML: no CDN, no external fonts, no JS libraries — inline CSS only
  - Dark theme with color-coded scores (green ≥80, yellow 50-79, red <50)
  - Sections: toolkit coverage, context quality (agentlint), context docs (agentmd), agent benchmark (coderace), reflection (agentreflect), pipeline status table
  - Gracefully handles any mix of installed/missing/failing tools (never crashes)
- `agentkit_cli/report_runner.py` — internal module with per-tool runner functions
  - `run_agentlint_check(path)`, `run_agentmd_score(path)`, `run_coderace_bench(path)`, `run_agentreflect_analyze(path)`
  - Each returns parsed JSON dict or `None` (tool missing / non-zero exit / unparseable output)
  - Robust JSON extraction: handles tools that prefix output with non-JSON lines

### Tests
- 201 tests (up from 170). Added 31 tests in `tests/test_report.py`.

## v0.4.0 (2026-03-13)

### Added
- `agentkit demo` — zero-config first-run experience
  - Detects project type (python/typescript/javascript/generic) from directory contents
  - Auto-selects best coderace task for detected project type
  - Auto-detects available AI agents (claude, codex) via PATH
  - Runs generate → lint → reflect pipeline steps without any config file
  - Optional benchmark step when agents are available
  - `--task TEXT` override, `--agents TEXT` override, `--skip-benchmark`, `--json` flags
  - Rich output with step table, benchmark results table, and footer hint
  - Highlights best-scoring agent in green

### Tests
- 157+ tests (up from 142). Added 20 tests in `test_demo.py`.

## v0.3.0 (2026-03-12)

### Added
- `agentkit ci` — generate a ready-to-use `.github/workflows/agentkit.yml` in one command
  - `--python-version`, `--benchmark`, `--min-score`, `--output-dir`, `--dry-run` flags
  - Generated YAML is validated via `yaml.safe_load` before writing
  - Installs all quartet tools and runs `agentkit run --ci` on every PR
- `agentkit watch` — watch the project for file changes and re-run the pipeline automatically
  - Powered by `watchdog` library
  - `--extensions`, `--debounce`, `--ci` flags
  - 2-second debounce by default; graceful Ctrl+C handling
- `agentkit run --ci` flag — CI-friendly non-interactive mode
  - Plain text output (no Rich markup/spinners for clean CI logs)
  - Exits 1 on any step failure
  - `--json` output now includes `success: bool` and `steps[{name, status, duration_ms, output_file}]` per contract spec

### Changed
- `agentkit run --json` output: added `success` top-level key; `steps` now uses contract format `{name, status, duration_ms, output_file}`; legacy `summary.steps` fields preserved for backwards compat
- `pyproject.toml`: added `watchdog>=3.0.0` and `pyyaml>=6.0.0` as runtime dependencies

### Tests
- 142 tests (up from 82). Added 30+ tests across `test_ci.py`, `test_watch.py`, `test_run_ci.py`.

## v0.2.1 (2026-03-12)

### Fixed
- `agentkit run` lint-diff step: was passing project path as command to agentlint (causing "No such command" error). Now correctly calls `agentlint check HEAD~1`.
- `agentkit run` reflect step: was using `--notes` flag (doesn't exist in agentreflect). Now correctly uses `--from-notes`.
- Added `pyyaml` dev dependency for GitHub Action tests.

### Tests
- 82 tests (up from 47). Added regression tests for both bug fixes.

## v0.2.0 (2026-03-12)

### Added
- `agentkit doctor` — diagnose quartet tool installation with Rich table output, `--json` flag, exits 1 on missing tools
- GitHub Action (`action.yml`) — composite action to run agentkit pipeline in CI with configurable inputs
- Example workflow (`.github/workflows/examples/agentkit-pipeline.yml`)
- Improved `agentkit run` summary table with ✓/✗/⊘ status symbols and `X/Y steps passed` line
- `summary` key in `agentkit run --json` output with structured step results

## v0.1.0 (2026-03-12)

Initial release.

### Added
- `agentkit init` — initialize project, detect tools, create `.agentkit.yaml`
- `agentkit run` — sequential pipeline runner (generate → lint → benchmark → reflect)
- `agentkit status` — health check with tool versions and last run summary
- `--json` flag on `run` and `status` for machine-readable output
- `--skip` flag on `run` to skip individual steps
- `--benchmark` flag to opt-in to the coderace benchmark step
- Rich terminal output throughout
- 25+ tests with typer CliRunner
