# BUILD-REPORT.md — agentkit-cli v1.28.0 flagship post-closeout advance

Status: SHIPPED
Date: 2026-04-21
Contract: all-day-build-contract-agentkit-cli-v1.28.0-flagship-post-closeout-advance.md

## Deliverables

| Deliverable | Status | Notes |
| --- | --- | --- |
| D1 | ✅ Complete | Re-verified current-tree source, spec, focused tests, full suite, and pre-release external truth directly from source-of-truth commands. |
| D2 | ✅ Complete | Pushed the release branch, created annotated tag `v1.28.0`, and proved the remote branch and peeled tag both matched the shipped commit at release time. |
| D3 | ✅ Complete | Built fresh `1.28.0` artifacts, published only the wheel and sdist to PyPI, and verified project plus version endpoints directly. |
| D4 | ✅ Complete | Reconciled shipped tag truth versus later docs-only branch chronology, reran hygiene/conflict checks, and closed with a clean repo. |

## Validation

- `python3 -m agentkit_cli.main source-audit . --json` -> `ready_for_contract=true`, `findings=[]`.
- `python3 -m agentkit_cli.main spec . --json` -> `kind=flagship-post-closeout-advance`; title `Advance the flagship planner past the closed concrete-next-step lane`; contract seed title `All-Day Build Contract: agentkit-cli-v1.28.0-flagship-post-closeout-advance flagship post-closeout advance`.
- `python3 -m agentkit_cli.main source-audit . --json` -> `ready_for_contract=true`, `findings=[]`.
- `python3 -m agentkit_cli.main spec . --json` -> `kind=flagship-post-closeout-advance`.
- `uv run python -m pytest -q tests/test_source_audit.py tests/test_source_audit_workflow.py tests/test_spec_engine.py tests/test_spec_cmd.py tests/test_spec_workflow.py tests/test_main.py` -> `32 passed in 1.71s`.
- `uv run python -m pytest -q` -> `5014 passed, 1 warning in 188.89s (0:03:08)`.
- `git ls-remote --heads origin feat/v1.28.0-flagship-post-closeout-advance` -> remote branch created; release-time head `1a6a8a366e43c28d1c227fd7acac7d1806efb6f9`.
- `git ls-remote --tags origin refs/tags/v1.28.0 refs/tags/v1.28.0^{}` -> annotated tag object `c5832f0d153b60d376546408e0dbda90bfd39e40`, peeled commit `1a6a8a366e43c28d1c227fd7acac7d1806efb6f9`.
- `uv build` -> fresh artifacts `dist/agentkit_cli-1.28.0.tar.gz` and `dist/agentkit_cli-1.28.0-py3-none-any.whl` after `python3 -m build` was unavailable in this shell.
- `uvx twine upload --repository pypi dist/agentkit_cli-1.28.0.tar.gz dist/agentkit_cli-1.28.0-py3-none-any.whl` -> publish succeeded using the existing `.pypirc` auth path.
- PyPI project JSON and version JSON now both report `1.28.0`, with files `agentkit_cli-1.28.0-py3-none-any.whl` and `agentkit_cli-1.28.0.tar.gz`.
- `bash /Users/mordecai/.openclaw/workspace/scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.28.0-flagship-post-closeout-advance` -> `No contradictory success/blocker narratives found.`
- `bash /Users/mordecai/.openclaw/workspace/scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.28.0-flagship-post-closeout-advance` -> `Total findings: 0`.

## Current truth

- `agentkit-cli v1.28.0` is shipped: tests are green, branch push is proven, annotated tag `v1.28.0` is live on origin, and PyPI `agentkit-cli==1.28.0` is live with both artifacts.
- The shipped release commit is the peeled tag target `1a6a8a366e43c28d1c227fd7acac7d1806efb6f9`.
- Later branch-head commits are docs-only release-surface reconciliation and do not change the shipped tag or the published PyPI payload.
- The flagship self-spec flow no longer replays the closed `flagship-concrete-next-step` lane from current repo truth.
