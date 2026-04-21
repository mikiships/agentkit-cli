# Progress Log — agentkit-cli v1.21.0 merge lanes

## D4 complete: docs and local release-readiness surfaces landed

**What changed:**
- Updated `README.md`, `CHANGELOG.md`, `agentkit_cli/__init__.py`, `pyproject.toml`, `tests/test_main.py`, `BUILD-REPORT.md`, and `FINAL-SUMMARY.md` for `agentkit merge` and `v1.21.0` local release truth.
- Added the required versioned report copy `BUILD-REPORT-v1.21.0.md` after the full suite exposed missing release-surface coverage.
- Replaced stale shipped `v1.20.0` land-release language in the active status surfaces with truthful `v1.21.0 merge lanes` local-only wording, then recorded the actual validation outcomes.

**Validation:**
- `python3 -m pytest -q tests/test_merge_cmd.py tests/test_merge_engine.py tests/test_merge_workflow.py tests/test_main.py` -> `15 passed in 5.36s`
- Initial `uv run python -m pytest -q` exposed missing build-report release surfaces, specifically the absent `BUILD-REPORT-v1.21.0.md` and missing high test-count reference in `BUILD-REPORT.md`
- After fixing the release surfaces, `uv run python -m pytest -q` -> `4995 passed, 1 warning in 341.61s (0:05:41)`
- `bash /Users/mordecai/.openclaw/workspace/scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.21.0-merge-lanes` -> `Total findings: 0`

**Current truth:**
- D1 through D4 are complete.
- The repo is truthfully `RELEASE-READY (LOCAL-ONLY)` for `v1.21.0`.
- No push, tag, publish, or remote mutation happened.

## D3 complete: merge packets and local apply execution landed

**What changed:**
- Added `agentkit_cli/merge.py` with deterministic local merge-plan assembly from saved `land.json` plus upstream continuation evidence and local git/worktree checks.
- Added per-lane merge packets, stable summary buckets, target-branch selection, explicit preflight checks, and conflict-aware `--apply` execution that stops truthfully on blockers.
- Added focused merge engine, CLI, and workflow coverage for the full `launch -> observe -> supervise -> reconcile -> resume -> relaunch -> closeout -> land -> merge` continuation loop.

**Validation:**
- `python3 -m pytest tests/test_merge_cmd.py tests/test_merge_engine.py tests/test_merge_workflow.py tests/test_main.py` -> `15 passed in 7.51s`

**Current truth:**
- D1 through D3 are complete.
- D4 report and release-readiness surfaces were still pending after this step.
- Merge execution remains explicit opt-in behind `--apply`; dry-run is still the default.

---

# Historical log (pre-v1.21.0)

## D3 complete: four-surface release completion and chronology reconciliation finished, v1.20.0 shipped

**What changed:**
- Pushed `feat/v1.20.0-land-lanes` to origin at shipped commit `5baec07b5fb2f2be35559edbef2a10081b850910`, created annotated tag `v1.20.0`, pushed the tag, then advanced the branch with docs-only chronology commits to reconcile shared report surfaces.
- Built `agentkit_cli-1.20.0-py3-none-any.whl` and `agentkit_cli-1.20.0.tar.gz` in `dist-release-v1.20.0/`, then published both with `twine upload`.
- Reconciled `BUILD-REPORT.md`, `BUILD-REPORT-v1.20.0.md`, and `FINAL-SUMMARY.md` so they now record shipped truth, direct ref proofs, and the exact PyPI evidence without blurring the shipped tag line.

**Validation:**
- `git ls-remote --heads origin feat/v1.20.0-land-lanes` -> current docs-only chronology head on `origin/feat/v1.20.0-land-lanes`, later than the shipped tag commit `5baec07b5fb2f2be35559edbef2a10081b850910`
- `git ls-remote --tags origin v1.20.0` -> `1ac306c4426cd644bb537a8b75e5c9fec4ad0081 refs/tags/v1.20.0`
- `git ls-remote --tags origin v1.20.0^{}` -> `5baec07b5fb2f2be35559edbef2a10081b850910 refs/tags/v1.20.0^{}`
- PyPI proof: `https://pypi.org/project/agentkit-cli/1.20.0/` and `https://pypi.org/pypi/agentkit-cli/1.20.0/json` live with `agentkit_cli-1.20.0-py3-none-any.whl` (`689640` bytes) and `agentkit_cli-1.20.0.tar.gz` (`1211626` bytes)

**Current truth:**
- Deliverables D1 through D3 in the release contract are complete.
- `agentkit-cli v1.20.0` is truthfully SHIPPED.
- The shipped artifact is pinned to `v1.20.0` -> `5baec07b5fb2f2be35559edbef2a10081b850910`, while the branch head is now a later docs-only chronology commit.
