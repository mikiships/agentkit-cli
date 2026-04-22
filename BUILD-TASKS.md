# BUILD-TASKS.md — agentkit-cli v1.29.0 flagship self-advance

- [ ] Reproduce the current flagship replay where `agentkit spec . --json` still recommends `flagship-post-closeout-advance` after that lane is already shipped in repo truth
- [ ] Identify the exact shipped or local-release-ready evidence pattern that should suppress replay of the finished v1.28.0 lane
- [ ] Implement deterministic planner logic in `agentkit_cli/spec_engine.py` so the flagship lane advances past closed post-closeout work
- [ ] Promote one fresh bounded flagship recommendation and contract seed instead of replaying the just-finished lane
- [ ] Add focused regressions in `tests/test_spec_engine.py`, `tests/test_spec_cmd.py`, `tests/test_spec_workflow.py`, and `tests/test_main.py`
- [ ] Refresh `.agentkit/source.md` and local planning surfaces so the active objective matches the new v1.29.0 lane truthfully
- [ ] Run focused validation, then `uv run python -m pytest -q`
- [ ] Leave the tree in truthful local-only state
