# BUILD-REPORT-v1.19.0.md — agentkit-cli v1.19.0 closeout lanes

Status: SHIPPED
Date: 2026-04-21
Contract: all-day-build-contract-agentkit-cli-v1.19.0-release.md

## Deliverables

| Deliverable | Status | Notes |
| --- | --- | --- |
| D1 | ✅ Complete | Re-ran recall and contradiction hygiene, revalidated the closeout slice, and confirmed the tracked tree was clean before release actions |
| D2 | ✅ Complete | Pushed `feat/v1.19.0-closeout-lanes`, created annotated tag `v1.19.0`, built `1.19.0` wheel and sdist, published them to PyPI, and re-verified all three release surfaces directly |
| D3 | ✅ Complete | Reconciled the shared report surfaces so the shipped release commit stays distinct from the later docs-only chronology head |

## Validation

- Recall and contradiction hygiene: `/Users/mordecai/.openclaw/workspace/scripts/pre-action-recall.sh release agentkit-cli /Users/mordecai/repos/agentkit-cli-v1.19.0-closeout-lanes` and `/Users/mordecai/.openclaw/workspace/scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.19.0-closeout-lanes`
- Focused closeout continuation slice from the candidate tree: `python3 -m pytest -q tests/test_closeout_engine.py tests/test_closeout_cmd.py tests/test_closeout_workflow.py tests/test_relaunch_engine.py tests/test_relaunch_cmd.py tests/test_relaunch_workflow.py tests/test_resume_engine.py tests/test_reconcile_engine.py tests/test_main.py` -> `36 passed in 9.08s`
- Release-confidence validation pass from the candidate tree: `uv run python -m pytest -q` -> `4978 passed, 1 warning in 169.53s (0:02:49)`
- Build command used: `uv build` (fallback because `python3 -m build` was unavailable in this environment)

## Source-of-truth release evidence

- Release commit: `6ca258f6bf4550fc2ae0fb86eed9cc2618695776` (`chore: prepare v1.19.0 closeout release surfaces`)
- Origin branch proof: `git ls-remote --heads origin feat/v1.19.0-closeout-lanes` -> `6ca258f6bf4550fc2ae0fb86eed9cc2618695776 refs/heads/feat/v1.19.0-closeout-lanes`
- Annotated tag proof: `git ls-remote --tags origin v1.19.0` -> `825d0e8ffc1ecdabe5b8de3ac64d240d468a4995 refs/tags/v1.19.0`
- Tag peel proof: `git ls-remote --tags origin v1.19.0^{}` -> `6ca258f6bf4550fc2ae0fb86eed9cc2618695776 refs/tags/v1.19.0^{}`
- PyPI proof: `https://pypi.org/project/agentkit-cli/1.19.0/` and `https://pypi.org/pypi/agentkit-cli/1.19.0/json` are live for `agentkit-cli==1.19.0`
- PyPI artifacts: `agentkit_cli-1.19.0-py3-none-any.whl` (`682342` bytes) and `agentkit_cli-1.19.0.tar.gz` (`1201482` bytes)

## Chronology truth

- The shipped public artifact is pinned to `v1.19.0` -> `6ca258f6bf4550fc2ae0fb86eed9cc2618695776`.
- Any later branch-head movement after that tag is docs-only chronology reconciliation and does not change the shipped release artifact.
- Supported handoff lane target remains `source -> source-audit -> map -> contract -> bundle -> taskpack -> clarify -> resolve -> dispatch -> stage -> materialize -> launch -> observe -> supervise -> reconcile -> resume -> relaunch -> closeout`.
