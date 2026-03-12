# Changelog

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
