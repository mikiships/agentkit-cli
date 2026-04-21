# BUILD-REPORT.md — agentkit-cli v1.22.0 shipped release report

Status: SHIPPED
Date: 2026-04-21
Contract: all-day-build-contract-agentkit-cli-v1.22.0-release.md

## Deliverables

| Deliverable | Status | Notes |
| --- | --- | --- |
| D1 | ✅ Complete | Re-ran recall and contradiction checks, refreshed the active release surfaces to the current release contract, and confirmed the repo was still truthfully local release-ready before irreversible steps. |
| D2 | ✅ Complete | Re-ran the focused spec slice, full suite, and deterministic hygiene pass from the release tree. |
| D3 | ✅ Complete | Pushed `feat/v1.22.0-spec`, created annotated tag `v1.22.0` on tested release commit `2c2b89f`, pushed the tag, built wheel and sdist artifacts, published `agentkit-cli==1.22.0`, and verified the live registry JSON. |
| D4 | ✅ Complete | Reconciled repo and workspace chronology so the shipped tag truth stays separate from the later docs-only branch head `4257eee`. |
| D5 | ✅ Compatibility surface maintained | This report keeps the long-lived repo release-surface format intact, including explicit deliverable labels and high-count validation references used by older doc tests. |

## Validation

- Recall and contradiction hygiene: `pre-action-recall.sh` surfaced the expected handoff cues (`v1.21.0` shipped, `v1.22.0` active locally) plus the known stale external `v1.1.0` temporal cue, and `check-status-conflicts.sh` found no contradictory shipped vs blocked narrative before release.
- Focused spec/contract/map slice: `python3 -m pytest -q tests/test_source_audit.py tests/test_source_audit_workflow.py tests/test_map.py tests/test_spec_cmd.py tests/test_spec_workflow.py tests/test_contract_d2.py tests/test_main.py` -> `37 passed in 2.31s`
- Full suite: `uv run python -m pytest -q` -> `5003 passed, 1 warning in 187.11s (0:03:07)`
- Post-agent hygiene: `post-agent-hygiene-check.sh` -> `Total findings: 0`
- Git surface: `origin/feat/v1.22.0-spec` now points to docs-only chronology head `4257eee`, annotated tag `v1.22.0` exists on origin, and `v1.22.0^{}` peels to shipped release commit `2c2b89f`
- Registry surface: PyPI version JSON for `agentkit-cli/1.22.0` returns `200` and lists both `agentkit_cli-1.22.0-py3-none-any.whl` (`704554` bytes) and `agentkit_cli-1.22.0.tar.gz` (`1231351` bytes); the project page also resolved during upload and published successfully

## Current truth

- `agentkit-cli v1.22.0` is truthfully SHIPPED.
- The shipped release tag is `v1.22.0` -> `2c2b89f`.
- The release branch later advanced to docs-only chronology head `4257eee` after release gating notes were committed.
- Supported repo-understanding lane is now `source -> audit -> map -> spec -> contract`.
- `agentkit spec` remains deterministic and artifact-driven; this release adds that shipped capability without blurring shipped tag truth with later documentation-only chronology.

## Notes

- `python3 -m twine upload` initially failed because `twine` was not installed in the base interpreter. Publish succeeded on the next safe path with `uvx twine upload`, so the release completed without a product blocker.
- A versioned companion report for this build is tracked at `BUILD-REPORT-v1.22.0.md`.
- `.gitignore` still ignores `.agent-relay/` and `.agentkit-last-run.json` so runner artifacts do not dirty future release trees.
