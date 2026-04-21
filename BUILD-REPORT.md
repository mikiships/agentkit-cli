# BUILD-REPORT.md — agentkit-cli v1.21.0 merge release completion

Status: SHIPPED
Date: 2026-04-21
Contract: all-day-build-contract-agentkit-cli-v1.21.0-release.md

## Deliverables

| Deliverable | Status | Notes |
| --- | --- | --- |
| D1 | ✅ Complete | Re-ran recall/conflict hygiene, re-verified local release-ready truth, and reran focused plus release-confidence validation from shipped candidate commit `1eb3e17` |
| D2 | ✅ Complete | Pushed `feat/v1.21.0-merge-lanes`, built `dist-release-v1.21.0/`, created and pushed annotated tag `v1.21.0`, and published `agentkit-cli==1.21.0` to PyPI |
| D3 | ✅ Complete | Reconciled report surfaces so the shipped tag commit `1eb3e17` stays distinct from the later docs-only chronology head on `origin/feat/v1.21.0-merge-lanes` |

## Validation

- Recall and contradiction hygiene: `/Users/mordecai/.openclaw/workspace/scripts/pre-action-recall.sh release agentkit-cli /Users/mordecai/repos/agentkit-cli-v1.21.0-merge-lanes` surfaced the expected stale temporal cue that `v1.20.0` was still the last shipped line before this release; `/Users/mordecai/.openclaw/workspace/scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.21.0-merge-lanes` reported no contradictory success or blocker narratives.
- Focused merge continuation slice from the shipped candidate: `python3 -m pytest -q tests/test_merge_cmd.py tests/test_merge_engine.py tests/test_merge_workflow.py tests/test_main.py` -> `15 passed in 4.48s`
- Release-confidence validation pass from the shipped candidate: `uv run python -m pytest -q` -> `4995 passed, 1 warning in 179.64s (0:02:59)`
- Build artifacts: `uv build --out-dir dist-release-v1.21.0 --sdist --wheel --clear` -> `agentkit_cli-1.21.0-py3-none-any.whl` and `agentkit_cli-1.21.0.tar.gz`
- Branch proof: `git ls-remote --heads origin feat/v1.21.0-merge-lanes` shows the branch on origin at a later docs-only chronology head after the shipped tag commit `1eb3e1700118b68292958c9fa8394f095cf03baf`
- Tag proof: `git ls-remote --tags origin v1.21.0` -> annotated tag object `72dbfad314869cb4f49e9cb78db7a5c5214e06dd`
- Peeled tag proof: `git ls-remote --tags origin v1.21.0^{}` -> shipped release commit `1eb3e1700118b68292958c9fa8394f095cf03baf`
- PyPI proof: `https://pypi.org/project/agentkit-cli/1.21.0/` and `https://pypi.org/pypi/agentkit-cli/1.21.0/json` live with `agentkit_cli-1.21.0-py3-none-any.whl` (`695609` bytes, uploaded `2026-04-21T07:15:33.040524Z`) and `agentkit_cli-1.21.0.tar.gz` (`1218832` bytes, uploaded `2026-04-21T07:15:34.749165Z`)
- Post-agent hygiene: `/Users/mordecai/.openclaw/workspace/scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.21.0-merge-lanes` -> `Total findings: 0`

## Release truth

- `agentkit-cli v1.21.0` is truthfully SHIPPED.
- The shipped release commit is `1eb3e1700118b68292958c9fa8394f095cf03baf` (`docs: finalize v1.21.0 merge release surfaces`).
- The current branch head is a later docs-only chronology commit on `origin/feat/v1.21.0-merge-lanes`.
- Annotated tag `v1.21.0` peels to the shipped release commit `1eb3e1700118b68292958c9fa8394f095cf03baf`.
- Supported continuation lane is now `launch -> observe -> supervise -> reconcile -> resume -> relaunch -> closeout -> land -> merge`.
- `agentkit merge` stays dry-run by default and only executes local merges when `--apply` is set explicitly.

## Notes

- Built and published release artifacts from `dist-release-v1.21.0/` with `twine upload dist-release-v1.21.0/*`.
- Local release artifact hashes: wheel `971830e3c3457a9b7a27eb4ac7ff4c11adc092c11427295a4e0742cc3225d7ae`, sdist `d0a10968d03848cf087c6b6df45a734a54bab397243a33a5d7ad7028d7862b54`.
- Intentional untracked contract artifacts remain in the worktree: `all-day-build-contract-agentkit-cli-v1.21.0-merge-finisher.md`, `all-day-build-contract-agentkit-cli-v1.21.0-merge-lanes.md`, and `all-day-build-contract-agentkit-cli-v1.21.0-release.md`.
