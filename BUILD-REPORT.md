# BUILD-REPORT.md — agentkit-cli v1.30.0 flagship adjacent next step

Status: SHIPPED
Date: 2026-04-22
Contract: all-day-build-contract-agentkit-cli-v1.30.0-release.md

## Deliverables

| Deliverable | Status | Notes |
| --- | --- | --- |
| D1 | ✅ Complete | Re-grounded the current tree from repo truth, reran source-audit, spec, focused tests, and the full suite, and reconciled stale `1.29.0` package/test surfaces to `1.30.0`. |
| D2 | ✅ Complete | Pushed branch `feat/v1.30.0-flagship-adjacent-next-step`, created annotated tag `v1.30.0`, and verified the remote branch head plus peeled tag target truthfully. |
| D3 | ✅ Complete | Built fresh `1.30.0` artifacts in `.release-dist-v1.30.0/`, published only the wheel and sdist, and verified both PyPI project and version endpoints directly. |
| D4 | ✅ Complete | Reconciled shipped chronology across repo surfaces, reran contradiction plus hygiene checks, and closed with a clean tree. |

## Validation

- `bash /Users/mordecai/.openclaw/workspace/scripts/pre-action-recall.sh release agentkit-cli /Users/mordecai/repos/agentkit-cli-v1.30.0-flagship-adjacent-next-step` -> recall run completed; surfaced active release cues and reminded that all four release surfaces must be proven directly.
- `git rev-parse --abbrev-ref HEAD` -> `feat/v1.30.0-flagship-adjacent-next-step`.
- `git rev-parse HEAD` at release-proof start -> `341ea50504a8734756a7bf144a2507e67d82fef7`.
- `python3 -m agentkit_cli.main source-audit . --json` -> `ready_for_contract=true`, `findings=[]`.
- `python3 -m agentkit_cli.main spec . --json` -> `kind=flagship-adjacent-closeout-advance`; objective advanced past the closed `flagship-adjacent-next-step` lane.
- `uv run python -m pytest -q tests/test_spec_engine.py tests/test_spec_cmd.py tests/test_spec_workflow.py tests/test_main.py` -> `32 passed in 2.13s`.
- Release verification caught a real mismatch first: `pyproject.toml`, `agentkit_cli/__init__.py`, and `tests/test_main.py` still reported `1.29.0`. Reconciled those version surfaces to `1.30.0` before any branch, tag, or registry mutation.
- `uv run python -m pytest -q` after the version-surface reconciliation -> `5020 passed, 1 warning in 205.87s (0:03:25)`.
- `git push -u origin feat/v1.30.0-flagship-adjacent-next-step` -> remote branch created and later advanced cleanly.
- `git ls-remote --heads origin feat/v1.30.0-flagship-adjacent-next-step` -> remote branch head matches the later docs-only closeout branch state, distinct from the shipped tag target.
- `git tag -a v1.30.0 -m "v1.30.0"` plus `git push origin v1.30.0` -> annotated tag created and pushed.
- `git ls-remote --tags origin refs/tags/v1.30.0 refs/tags/v1.30.0^{}` -> remote tag object is `cef4b48a63630c131927ce05e219abd60e3840c1`; peeled tag target is shipped release commit `e0554e08d69a0ab332555dbe01e17b5a7967c730`.
- `uv build --out-dir .release-dist-v1.30.0` -> fresh artifacts `agentkit_cli-1.30.0.tar.gz` and `agentkit_cli-1.30.0-py3-none-any.whl`.
- `uvx twine upload --repository pypi .release-dist-v1.30.0/agentkit_cli-1.30.0.tar.gz .release-dist-v1.30.0/agentkit_cli-1.30.0-py3-none-any.whl` -> publish succeeded; PyPI returned `https://pypi.org/project/agentkit-cli/1.30.0/`.
- Direct PyPI verification after publish:
  - project JSON `https://pypi.org/pypi/agentkit-cli/json` -> `info.version = 1.30.0`, release files `agentkit_cli-1.30.0-py3-none-any.whl`, `agentkit_cli-1.30.0.tar.gz`
  - version JSON `https://pypi.org/pypi/agentkit-cli/1.30.0/json` -> `info.version = 1.30.0`, same two files under `urls`
- `bash /Users/mordecai/.openclaw/workspace/scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.30.0-flagship-adjacent-next-step` -> no contradictory success or blocker narratives found.
- `bash /Users/mordecai/.openclaw/workspace/scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.30.0-flagship-adjacent-next-step` -> no hygiene findings.

## Current truth

- `agentkit-cli v1.30.0` is shipped: tests are green, branch push is proven, annotated tag `v1.30.0` is live on origin, and PyPI `agentkit-cli==1.30.0` is live with both artifacts.
- The shipped functional outcome is the flagship planner self-advance: `agentkit spec . --json` now emits `flagship-adjacent-closeout-advance` instead of replaying the already-closed `flagship-adjacent-next-step` lane.
- Chronology is intentionally split: shipped release commit is the peeled tag target `e0554e08d69a0ab332555dbe01e17b5a7967c730`, while later branch-head commits on `feat/v1.30.0-flagship-adjacent-next-step` are docs-only closeout reconciliation that records the shipped proof.
