# Progress Log — agentkit-cli v1.24.0 clean JSON stdout

Status: IN PROGRESS
Date: 2026-04-21

## Why this lane exists

Heartbeat found a concrete CLI contract bug in the shipped repo: `agentkit spec --json` prepends `Wrote spec directory: ...` to stdout before the JSON object, which breaks direct machine parsing.

## Goal

Ship a local fix so JSON mode is actually machine-readable, then close the repo truthfully as `RELEASE-READY (LOCAL-ONLY)`.
