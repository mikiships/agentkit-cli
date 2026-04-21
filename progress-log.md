# Progress Log — agentkit-cli v1.26.0 spec shipped truth sync

Status: RELEASE-READY (LOCAL-ONLY)
Date: 2026-04-21

## Why this lane exists

The freshly shipped flagship repo still let `agentkit spec . --json` recommend the just-shipped `adjacent-grounding` increment from v1.25.0. That meant the planner could see stale self-hosting objective text, but not that the adjacent grounding follow-up had already been completed locally.

## Root cause

`agentkit_cli/spec_engine.py` could suppress stale self-hosting work in favor of `adjacent-grounding`, but it had no follow-on rule for the next run after that increment itself was already present in shipped or local-release-ready workflow artifacts.

## What changed

- Added shipped-adjacent detection in `agentkit_cli/spec_engine.py` so the planner notices `adjacent-grounding` / `spec grounding` evidence in shipped or local-release-ready artifacts.
- Introduced a `shipped-truth-sync` recommendation that points the flagship repo at refreshing stale canonical source truth and local closeout surfaces instead of repeating the shipped v1.25.0 step.
- Added command and workflow regressions for the shipped-adjacent case.
- Refreshed `.agentkit/source.md`, version surfaces, changelog, build reports, and summary artifacts for truthful `v1.26.0` local closeout.

## Validation

- `uv run python -m pytest -q tests/test_spec_cmd.py tests/test_spec_workflow.py tests/test_main.py` -> `20 passed in 4.03s`
- `uv run python -m agentkit_cli.main spec . --json` from the refreshed tree -> primary recommendation kind `subsystem-next-step`
- `uv run python -m pytest -q` -> `5008 passed, 1 warning in 768.47s (0:12:48)`

## Local closeout truth

The current tree is truthfully `RELEASE-READY (LOCAL-ONLY)`: focused validation passed, the repo now self-specs to `subsystem-next-step`, and the full pytest suite passed from this tree.
