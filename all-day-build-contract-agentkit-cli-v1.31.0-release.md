# All-Day Build Contract: agentkit-cli v1.31.0 release completion

Status: In Progress
Date: 2026-04-22
Owner: OpenClaw build-loop pass
Scope type: Release completion

## 1. Objective

Take the already-built `agentkit-cli v1.31.0 bounded agentkit next step` branch from truthful local-only completion to fully shipped truth. This pass succeeds only if the package version surfaces are reconciled to `1.31.0`, validation stays green, the branch and annotated tag are pushed, PyPI `agentkit-cli==1.31.0` is live, and the repo-local report chronology tells one coherent story.

## 2. Non-Negotiable Release Rules

1. Do not claim `SHIPPED` unless tests are green, the branch push is proven, the annotated tag push is proven, and PyPI is live.
2. Verify package metadata surfaces directly before any release mutation: `pyproject.toml`, `agentkit_cli/__init__.py`, `uv.lock`, and the nearest release assertion test.
3. Work only inside `/Users/mordecai/repos/agentkit-cli-v1.31.0-subsystem-next-step`.
4. Publish only fresh `1.31.0` artifacts built from this repo.
5. Reconcile chronology so the shipped tag target and any later docs-only branch head are described truthfully.
6. If a real blocker appears, stop and write `blocker-report-v1.31.0-release.md` with concrete evidence.

## 3. Deliverables

### D1. Reconcile release surfaces
- [ ] Create this release contract.
- [ ] Update version surfaces to `1.31.0` in `pyproject.toml`, `agentkit_cli/__init__.py`, `uv.lock`, and nearest release assertion tests.
- [ ] Update changelog and repo-local report surfaces for the `v1.31.0` line.

### D2. Validate local release truth
- [ ] Run the focused validation slice.
- [ ] Run the full suite.
- [ ] Leave the tree in truthful local release-ready state before remote mutation.

### D3. Complete remote release surfaces
- [ ] Push branch `feat/v1.31.0-subsystem-next-step`.
- [ ] Create annotated tag `v1.31.0` on the intended release commit.
- [ ] Push tag `v1.31.0` and verify the remote peeled tag target.

### D4. Publish and reconcile shipped chronology
- [ ] Build fresh `1.31.0` wheel and sdist.
- [ ] Publish `agentkit-cli==1.31.0` to PyPI.
- [ ] Verify project JSON and version JSON both show `1.31.0` live.
- [ ] Update `BUILD-REPORT.md`, `BUILD-REPORT-v1.31.0.md`, and `FINAL-SUMMARY.md` so shipped chronology is explicit.
- [ ] Leave the repo clean.

## 4. Validation Requirements

- [ ] `python3 -m agentkit_cli.main source-audit . --json`
- [ ] `python3 -m agentkit_cli.main spec . --json`
- [ ] `uv run python -m pytest -q tests/test_spec_engine.py tests/test_spec_cmd.py tests/test_spec_workflow.py tests/test_main.py`
- [ ] `uv run python -m pytest -q`
- [ ] `uv build --out-dir .release-dist-v1.31.0`

## 5. Final Summary Requirements

Report only one of two outcomes:
1. `SHIPPED` with HEAD, branch, version surfaces, focused tests, full suite, push proof, tag proof, PyPI proof, and clean tree status, or
2. `BLOCKED` with the exact failing surface and evidence.
