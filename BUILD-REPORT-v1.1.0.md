# BUILD-REPORT.md — agentkit-cli v1.1.0 burn observability

Date: 2026-04-19
Builder: subagent burn observability pass
Contract: all-day-build-contract-agentkit-cli-v1.1.0-burn-observability.md
Status: LOCAL RC READY

## Summary

Completed a local-first `agentkit burn` workflow for transcript cost observability. The release adds transcript adapters, a normalized burn schema, an analysis engine for spend and waste patterns, a first-class CLI command, and a dark-theme HTML report.

## Deliverables

| # | Deliverable | Status | Notes |
|---|-------------|--------|-------|
| D1 | Transcript adapters + normalized burn schema | ✅ Complete | Codex, Claude Code, and OpenClaw-style local artifacts normalize into one session/turn schema with explicit cost states |
| D2 | Burn analysis engine | ✅ Complete | Aggregates spend by project/model/provider/task/source and detects waste patterns with stable evidence |
| D3 | `agentkit burn` CLI command | ✅ Complete | Supports `--path`, `--format json`, `--since`, `--limit`, `--project`, and `--output` |
| D4 | HTML report + narrative summary | ✅ Complete | Dark-theme HTML and markdown-ready summary highlight where spend goes and what to fix first |
| D5 | Docs, versioning, build report, and validation | ✅ Complete | README, changelog, progress log, version metadata, helper-script checks, and local validation updated for `1.1.0` |

## Validation

- focused burn slice: `uv run pytest -q tests/test_burn_adapters.py tests/test_burn_engine.py tests/test_burn_command.py tests/test_burn_report.py` -> `22 passed in 0.34s`
- final full suite: `uv run pytest -q` -> `4809 passed, 1 warning in 131.87s (0:02:11)`
- helper scripts: status-conflict scan `0 findings`, hygiene check `0 findings`
