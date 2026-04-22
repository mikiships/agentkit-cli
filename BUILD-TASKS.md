# BUILD-TASKS.md — agentkit-cli v1.31.0 bounded agentkit next step

- [x] Reproduce the current generic subsystem output from repo truth and confirm the old fallback target was `kind=subsystem-next-step`, title `Use agentkit_cli as the next scoped build surface`
- [x] Identify the exact repo evidence that should narrow `agentkit_cli` into one concrete bounded next recommendation, namely the shipped `v1.30.0` adjacent-closeout artifacts plus the current canonical source objective
- [x] Implement deterministic planner logic in `agentkit_cli/spec_engine.py` and the nearest helpers so the generic fallback advances to a concrete bounded `agentkit_cli` next step
- [x] Promote one fresh bounded `agentkit_cli` recommendation with truthful why-now, scope, validation, and contract-seed fields
- [x] Add focused regressions in `tests/test_spec_engine.py`, `tests/test_spec_cmd.py`, `tests/test_spec_workflow.py`, and `tests/test_main.py`
- [x] Refresh `.agentkit/source.md` and local planning surfaces so the active objective matches the bounded post-fallback truthfully
- [x] Run focused validation, then `uv run python -m pytest -q`
- [x] Leave the tree in truthful local-only state
