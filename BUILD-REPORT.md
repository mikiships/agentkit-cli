# BUILD-REPORT.md — agentkit-cli v1.29.0 flagship self-advance

Status: SHIPPED
Date: 2026-04-21
Contract: all-day-build-contract-agentkit-cli-v1.29.0-release.md

## Deliverables

| Deliverable | Status | Notes |
| --- | --- | --- |
| D1 | ✅ Complete | Re-verified current-tree source, current branch/head state, focused tests, full suite, and reconciled the stale local-ready mismatch by restoring the package version surfaces to `1.29.0`. |
| D2 | ✅ Complete | Pushed branch `feat/v1.29.0-flagship-self-advance`, created annotated tag `v1.29.0`, and verified the remote branch head plus peeled tag target match the shipped release commit. |
| D3 | ✅ Complete | Built fresh `1.29.0` artifacts, published only the wheel and sdist to PyPI, and verified both project and version endpoints directly. |
| D4 | ✅ Complete | Reconciled shipped status across local surfaces, reran contradiction plus hygiene checks, and closed with a clean tree. |

## Validation

- `bash /Users/mordecai/.openclaw/workspace/scripts/pre-action-recall.sh release agentkit-cli /Users/mordecai/repos/agentkit-cli-v1.29.0-flagship-self-advance` -> recall run completed; surfaced active release cues and reminded that all four release surfaces must be proven directly.
- `git status --short --branch` -> branch `feat/v1.29.0-flagship-self-advance`; current tree initially showed the release contract file untracked.
- `git rev-parse HEAD` -> current local release-candidate head started at `f96cd44941a0cbb96c7e212b0cebbc82009cd707` before release-completion edits.
- `python -m agentkit_cli.main source-audit . --json` -> `ready_for_contract=true`, `findings=[]`.
- `python -m agentkit_cli.main spec . --json` -> `kind=flagship-adjacent-next-step`; objective advanced past the closed `flagship-post-closeout-advance` lane.
- `uv run python -m pytest -q tests/test_spec_engine.py tests/test_spec_cmd.py tests/test_spec_workflow.py tests/test_main.py` -> `29 passed in 1.79s`.
- `uv run python -m pytest -q` -> `5017 passed, 1 warning in 190.05s (0:03:10)`.
- Source-of-truth mismatch found during release verification: `pyproject.toml` and `agentkit_cli/__init__.py` still reported `1.28.0` even though the repo was carrying the `v1.29.0` lane. Reconciled those version surfaces before proceeding with branch/tag/publish work.
- `git push -u origin feat/v1.29.0-flagship-self-advance` -> remote branch created and set to track origin.
- `git ls-remote --heads origin feat/v1.29.0-flagship-self-advance` -> remote branch head matches the shipped release commit.
- `git tag -a v1.29.0 -m "v1.29.0"` plus `git push origin v1.29.0` -> annotated tag created and pushed.
- `git ls-remote --tags origin refs/tags/v1.29.0 refs/tags/v1.29.0^{}` -> remote tag object present and peeled tag target matches the shipped release commit.
- `uv build` -> fresh artifacts `dist/agentkit_cli-1.29.0.tar.gz` and `dist/agentkit_cli-1.29.0-py3-none-any.whl`.
- `uvx twine upload --repository pypi dist/agentkit_cli-1.29.0.tar.gz dist/agentkit_cli-1.29.0-py3-none-any.whl` -> publish succeeded.
- PyPI project JSON now reports `1.29.0`, and version JSON lists `agentkit_cli-1.29.0-py3-none-any.whl` plus `agentkit_cli-1.29.0.tar.gz`.
- `bash /Users/mordecai/.openclaw/workspace/scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.29.0-flagship-self-advance` -> no contradictory success or blocker narratives found.
- `bash /Users/mordecai/.openclaw/workspace/scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.29.0-flagship-self-advance` -> no hygiene findings.

## Current truth

- `agentkit-cli v1.29.0` is shipped: tests are green, branch push is proven, annotated tag `v1.29.0` is live on origin, and PyPI `agentkit-cli==1.29.0` is live with both artifacts.
- The live planner result remains the shipped functional outcome for this lane: `flagship-adjacent-next-step` / `Emit the next flagship lane after post-closeout advance`.
- Release verification started by catching a real mismatch, package version surfaces still on `1.28.0`, and fixing it before any branch, tag, or registry claim.
