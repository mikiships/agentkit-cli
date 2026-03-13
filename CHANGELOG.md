# Changelog

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
