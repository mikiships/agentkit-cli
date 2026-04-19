# Progress Log — agentkit-cli v0.99.0 context projections

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
