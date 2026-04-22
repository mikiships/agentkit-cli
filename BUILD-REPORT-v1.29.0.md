# BUILD-REPORT.md — agentkit-cli v1.29.0 flagship self-advance

Status: SHIPPED
Date: 2026-04-21
Contract: all-day-build-contract-agentkit-cli-v1.29.0-release.md

## Deliverables

| Deliverable | Status | Notes |
| --- | --- | --- |
| D1 | ✅ Complete | Re-verified current-tree source, branch/head state, focused tests, full suite, and reconciled the stale local-ready mismatch by restoring package version surfaces to `1.29.0` and updating the version assertion test. |
| D2 | ✅ Complete | Proved remote branch `feat/v1.29.0-flagship-self-advance`, corrected annotated tag `v1.29.0` to the test-green shipped commit, and re-verified the remote peeled tag target directly. |
| D3 | ✅ Complete | Verified fresh `1.29.0` artifacts exist under `dist/`, PyPI serves `agentkit-cli==1.29.0`, and both project plus version endpoints report the release directly. |
| D4 | ✅ Complete | Reconciled shipped-versus-later chronology, reran contradiction plus hygiene checks, and closed with a clean tree. |

## Validation

- `bash /Users/mordecai/.openclaw/workspace/scripts/pre-action-recall.sh release agentkit-cli /Users/mordecai/repos/agentkit-cli-v1.29.0-flagship-self-advance` -> recall run completed and reminded that tests, branch, tag, and registry all had to be proven directly.
- `python -m agentkit_cli.main source-audit . --json` -> `ready_for_contract=true`, `findings=[]`.
- `python -m agentkit_cli.main spec . --json` -> `kind=flagship-adjacent-next-step`; the flagship planner advances past the closed `flagship-post-closeout-advance` lane.
- Release verification caught a real mismatch before ship: `pyproject.toml` and `agentkit_cli/__init__.py` still said `1.28.0`, and `tests/test_main.py` still expected `1.28.0`. Those surfaces were reconciled to `1.29.0` before final release proof.
- `uv run python -m pytest -q tests/test_spec_engine.py tests/test_spec_cmd.py tests/test_spec_workflow.py tests/test_main.py` -> `29 passed in 1.83s`.
- `uv run python -m pytest -q` -> `5017 passed, 1 warning in 190.83s (0:03:10)`.
- `git ls-remote --heads origin feat/v1.29.0-flagship-self-advance` -> remote branch head `f869a12f54501abe115a7369d75d51c0b1d19656`.
- `git ls-remote --tags origin refs/tags/v1.29.0 refs/tags/v1.29.0^{}` -> annotated tag object `1eb19058143ef3f6629e6f25da6041f0213efbeb`, peeled shipped commit `404ada0eb6cf8092659d567b10f3c28448aafc66`.
- Release reconciliation caught one more git-surface issue: the pre-existing `v1.29.0` tag initially peeled to `c80e636d41d6a38437792fd35131889ca44d0831`, which predates the version-assertion test fix. The annotated tag was corrected and force-pushed to the test-green shipped commit `404ada0eb6cf8092659d567b10f3c28448aafc66`.
- `ls dist/agentkit_cli-1.29.0*` -> `dist/agentkit_cli-1.29.0-py3-none-any.whl`, `dist/agentkit_cli-1.29.0.tar.gz`.
- PyPI project JSON reports `info.version=1.29.0` and includes release `1.29.0`.
- PyPI version JSON for `1.29.0` reports files `agentkit_cli-1.29.0-py3-none-any.whl` and `agentkit_cli-1.29.0.tar.gz`.
- `bash /Users/mordecai/.openclaw/workspace/scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.29.0-flagship-self-advance` -> `No contradictory success/blocker narratives found.`
- `bash /Users/mordecai/.openclaw/workspace/scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.29.0-flagship-self-advance` -> `Total findings: 0`.

## Current truth

- `agentkit-cli v1.29.0` is shipped.
- The shipped release commit is `404ada0eb6cf8092659d567b10f3c28448aafc66`.
- The current branch head is the later docs-only chronology commit `f869a12f54501abe115a7369d75d51c0b1d19656` on `origin/feat/v1.29.0-flagship-self-advance`.
- Annotated tag `v1.29.0` now peels to the shipped commit, while the branch remains ahead for release-surface closeout docs only.
- PyPI `agentkit-cli==1.29.0` is live with both the wheel and sdist artifacts.
- The shipped functional outcome for this lane is the flagship planner self-advance: `agentkit spec . --json` now emits `flagship-adjacent-next-step` instead of replaying the closed `flagship-post-closeout-advance` lane.
