# Progress Log — agentkit-cli v0.99.0 context projections

## RC D1: mainline convergence provenance map — COMPLETE

**Branch:** `rc/v0.99.0-mainline`

**Provenance:**
- sync point with mainline history: `f2bc687` (`docs: record v0.98.0 sync validation`)
- source feature line: `feat/v0.99.0-context-projections`
- RC branch cut from feature HEAD `9140ced` to preserve the completed v0.99.0 context-projections deliverables while repairing release-trail drift locally
- intended convergence path for publish prep: replay the context-projections deliverables onto a current mainline publish pass with this branch as the local truth source for feature scope, chronology, and validation outcomes

**Built:**
- created local RC branch `rc/v0.99.0-mainline` for the release-candidate convergence pass
- added the RC contract file `all-day-build-contract-agentkit-cli-v0.99.0-mainline-rc.md` to keep the handoff self-contained inside the repo
- refreshed the versioned and canonical build reports with an explicit RC objective so the branch narrative is local release-ready, not already shipped

**Tests:** not run in D1, documentation/provenance pass only

**Next:** D2 release-trail reconciliation across build/report surfaces.

---

## RC D2: release-trail reconciliation — COMPLETE

**Built:**
- switched both report surfaces to the RC contract as the current governing document while keeping the original context-projections contract as prior provenance
- clarified that inherited v0.99.0 test counts are provisional until this branch reruns them in D3
- normalized the status narrative to one explicit state across surfaces: local RC convergence, not shipped or published

**Tests:** not run in D2, documentation reconciliation only

**Next:** D3 targeted validation for projection, init, and migrate surfaces, then full-suite verification.

---

## D1: projection engine core — COMPLETE

**Built:**
- `agentkit_cli/context_projections.py` with the canonical target schema, filename mapping, source auto-detection priority, projection generation, and hash-based drift logic.
- `agentkit_cli/migrate.py` compatibility layer so existing migrate surfaces keep working while reusing the new engine.
- `tests/test_context_projections.py` plus migrate-engine compatibility coverage for new targets and header normalization.

**Tests:** `uv run pytest -q tests/test_context_projections.py tests/test_migrate_engine.py` -> 28 passed

**Next:** D2 project command and reporting surface.

---

## D2: `agentkit project` CLI surface — COMPLETE

**Built:**
- `agentkit_cli/commands/project_cmd.py` with `--from`, `--targets`, `--output-dir`, `--check`, `--write`, and `--json`.
- `agentkit_cli/main.py` wiring for the new `agentkit project` command.
- `agentkit_cli/commands/migrate_cmd.py` now resolves the broader target alias set through the shared projection engine.
- `tests/test_project_cmd.py` covering write mode, `--check`, JSON summaries, custom output directories, and unknown targets.

**Tests:** `uv run pytest -q tests/test_project_cmd.py tests/test_migrate_cmd.py` -> 22 passed

**Next:** D3 sync and drift verification across the expanded target set.

---

## D3: drift and sync verification — COMPLETE

**Built:**
- `agentkit_cli/commands/sync_cmd.py` now understands the projection engine, reports the expanded target set, keeps legacy `--check` behavior stable for the classic trio, and repairs stale or missing projections in one pass.
- `tests/test_sync_projections.py` for new-target drift detection and repair coverage.
- Backward-compatibility behavior stayed green for existing migrate and sync tests while adding the new projection-aware checks.

**Tests:** `uv run pytest -q tests/test_sync_projections.py tests/test_migrate_cmd.py` -> 19 passed

**Next:** D4 workflow integration through an existing high-leverage command.

---

## D4: workflow integration — COMPLETE

**Built:**
- `agentkit_cli/commands/init_cmd.py` gained optional `--project-targets` and `--write-projections` so init can fan out from one canonical source immediately or report the next step safely.
- `tests/test_init_projections.py` proves the init integration path works in both write and report-first modes.
- Existing init tests still pass with the added projection-aware workflow.

**Tests:** `uv run pytest -q tests/test_init.py tests/test_init_projections.py` -> 11 passed

**Next:** D5 docs, release notes, version bump, and full-suite hygiene.

---

## D5: docs, release notes, and versioning — COMPLETE

**Built:**
- `README.md` usage guidance for canonical-source projection workflows, plus clear guidance on when to use `project` vs `migrate` vs `sync`.
- `CHANGELOG.md`, `BUILD-REPORT.md`, `pyproject.toml`, and `agentkit_cli/__init__.py` updated for `0.99.0`.
- Progress log now records the full deliverable path for the release pass.

**Tests:** focused command coverage already exercises the README-adjacent projection flows, and the release-ready verification pass completed with `84 passed` across the targeted projection suite plus `4775 passed, 1 warning` across the full suite.

**Next:** repo-local hygiene sweep and final release-ready handoff.
