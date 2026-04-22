# BUILD-TASKS.md — agentkit-cli v1.28.0 flagship post-closeout advance

- [x] Reproduce the current flagship replay where `agentkit spec . --json` still recommends `flagship-concrete-next-step` after that lane is already closed out in local repo truth
- [x] Identify the exact shipped or local-release-ready evidence pattern that should suppress replay of the finished v1.27.0 lane
- [x] Implement deterministic planner logic in `agentkit_cli/spec_engine.py` for the post-closeout flagship case
- [x] Promote a fresh bounded flagship recommendation and contract seed instead of replaying the just-finished lane
- [x] Add focused regressions in `tests/test_spec_engine.py`, `tests/test_spec_cmd.py`, `tests/test_spec_workflow.py`, and `tests/test_main.py`
- [x] Refresh `.agentkit/source.md` and local closeout surfaces so the active objective matches the new v1.28.0 lane truthfully
- [ ] Run focused validation, then `uv run python -m pytest -q`
- [ ] Leave the tree in truthful local-only state
