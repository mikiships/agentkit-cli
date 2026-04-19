# Progress Log — agentkit-cli v0.99.0 context projections

## D1: projection engine core — COMPLETE

**Built:**
- `agentkit_cli/context_projections.py` with the canonical target schema, filename mapping, source auto-detection priority, projection generation, and hash-based drift logic.
- `agentkit_cli/migrate.py` compatibility layer so existing migrate surfaces keep working while reusing the new engine.
- `tests/test_context_projections.py` plus migrate-engine compatibility coverage for new targets and header normalization.

**Tests:** `uv run pytest -q tests/test_context_projections.py tests/test_migrate_engine.py` -> 28 passed

**Next:** D2 project command and reporting surface.
