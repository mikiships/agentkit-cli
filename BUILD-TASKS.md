# BUILD-TASKS.md — agentkit-cli v1.30.0 flagship adjacent next step

- [ ] Reproduce the current flagship adjacent-lane output from shipped repo truth: `agentkit spec . --json` now recommends `flagship-adjacent-next-step`
- [ ] Identify the exact shipped or truthful local-release-ready evidence pattern that should emit the concrete adjacent flagship lane instead of the generic subsystem fallback
- [ ] Implement deterministic planner logic in `agentkit_cli/spec_engine.py` and the nearest helpers so the flagship lane emits the concrete adjacent recommendation truthfully
- [ ] Promote one fresh bounded flagship recommendation and contract seed for `flagship-adjacent-next-step`
- [ ] Add focused regressions in `tests/test_spec_engine.py`, `tests/test_spec_cmd.py`, `tests/test_spec_workflow.py`, and `tests/test_main.py`
- [ ] Refresh `.agentkit/source.md` and local planning surfaces so the active objective matches the new v1.30.0 lane truthfully
- [ ] Run focused validation, then `uv run python -m pytest -q`
- [ ] Leave the tree in truthful local-only state
