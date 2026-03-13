# Changelog

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
