# BUILD-TASKS.md — agentkit-cli v1.29.0 flagship self-advance

- [x] Reproduce the current flagship replay gap from repo truth: shipped `v1.28.0` closes `flagship-post-closeout-advance`, while the live planner still fell through to the generic `subsystem-next-step` instead of a fresh flagship lane
- [x] Identify the deterministic suppression evidence pattern: shipped or truthful local-release-ready workflow artifacts that mention `flagship-post-closeout-advance` in CHANGELOG / BUILD-REPORT / FINAL-SUMMARY / progress surfaces
- [x] Implement deterministic planner logic in `agentkit_cli/spec_engine.py` so the flagship lane advances past closed post-closeout work
- [x] Promote one fresh bounded flagship recommendation and contract seed, `flagship-adjacent-next-step`, instead of replaying the just-finished lane or falling back to the generic subsystem recommendation
- [x] Add focused regressions in `tests/test_spec_engine.py`, `tests/test_spec_cmd.py`, `tests/test_spec_workflow.py`, and `tests/test_main.py`
- [x] Refresh `.agentkit/source.md` and local planning surfaces so the active objective matches the new v1.29.0 lane truthfully
- [x] Run focused validation, then `uv run python -m pytest -q`
- [x] Leave the tree in truthful local-only state
