# BUILD-TASKS.md — agentkit-cli v1.27.0 spec concrete next step

- [x] Reproduce the current flagship post-v1.26.0 behavior where `agentkit spec . --json` falls through to the generic `subsystem-next-step` recommendation
- [x] Identify the exact shipped-truth evidence pattern that should unlock a concrete next recommendation for the flagship repo
- [x] Implement bounded planner logic in `agentkit_cli/spec_engine.py` for the post-shipped-truth flagship case
- [x] Add focused regressions in `tests/test_spec_cmd.py`, `tests/test_spec_workflow.py`, and nearby engine coverage as needed
- [x] Verify the new primary recommendation and contract seed are concrete enough to open the next lane without manual reinterpretation
- [x] Refresh `.agentkit/source.md` and local report surfaces only if the new planner behavior changes the truthful active objective
- [x] Run focused validation, then `uv run python -m pytest -q`
- [x] Leave the tree in truthful local-only state
