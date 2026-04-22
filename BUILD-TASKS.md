# BUILD-TASKS.md — agentkit-cli v1.31.0 subsystem next step

- [ ] Reproduce the current generic subsystem output from repo truth: `agentkit spec . --json` now recommends `subsystem-next-step` for `agentkit_cli`
- [ ] Identify the exact repo evidence that should let the planner emit one concrete bounded next recommendation inside `agentkit_cli`
- [ ] Implement deterministic planner logic in `agentkit_cli/spec_engine.py` and the nearest helpers so the generic subsystem fallback advances to a concrete next step
- [ ] Promote one fresh bounded `agentkit_cli` recommendation with truthful why-now, scope, and validation fields
- [ ] Add focused regressions in `tests/test_spec_engine.py`, `tests/test_spec_cmd.py`, `tests/test_spec_workflow.py`, and `tests/test_main.py`
- [ ] Refresh `.agentkit/source.md` and local planning surfaces so the active objective matches the new v1.31.0 lane truthfully
- [ ] Run focused validation, then `uv run python -m pytest -q`
- [ ] Leave the tree in truthful local-only state
