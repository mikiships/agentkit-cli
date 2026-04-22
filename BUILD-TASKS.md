# BUILD-TASKS.md — agentkit-cli v1.30.0 flagship adjacent next step

- [x] Reproduce the current flagship adjacent-lane output from shipped repo truth: `agentkit spec . --json` now recommends `flagship-adjacent-next-step`
- [x] Identify the exact shipped or truthful local-release-ready evidence pattern that should advance past the closed `flagship-adjacent-next-step` lane
- [x] Implement deterministic planner logic in `agentkit_cli/spec_engine.py` and the nearest helpers so the flagship lane advances again from truthful repo evidence
- [x] Promote one fresh bounded flagship recommendation and contract seed for `flagship-adjacent-closeout-advance`
- [x] Add focused regressions in `tests/test_spec_engine.py`, `tests/test_spec_cmd.py`, `tests/test_spec_workflow.py`, and `tests/test_main.py`
- [x] Refresh `.agentkit/source.md` and local planning surfaces so the active objective matches the new v1.30.0 lane truthfully
- [x] Run focused validation, then `uv run python -m pytest -q`
- [x] Leave the tree in truthful local-only state
