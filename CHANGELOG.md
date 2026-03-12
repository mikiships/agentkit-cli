# Changelog

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
