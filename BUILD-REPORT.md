# BUILD-REPORT — agentkit-cli v0.46.0

**Date:** 2026-03-18  
**Version:** 0.46.0  
**Baseline tests:** 1912 (v0.45.0)

---

## Deliverables Checklist

- [x] **D1** `agentkit_cli/improve_engine.py` — `ImprovementPlan` dataclass + `ImproveEngine.run()`
- [x] **D2** `agentkit_cli/commands/improve.py` — CLI command with all flags
- [x] **D3** `agentkit_cli/templates/improve_report.html` — dark-theme before/after HTML report
- [x] **D4** `agentkit_cli/commands/run_cmd.py` — `--improve` flag + passthrough options
- [x] **D5** Docs + version bump
  - [x] `README.md` — `agentkit improve` section
  - [x] `CHANGELOG.md` — v0.46.0 entry
  - [x] `pyproject.toml` — version = "0.46.0"
  - [x] `agentkit_cli/__init__.py` — version = "0.46.0"
  - [x] `tests/test_improve.py` — ≥40 new tests

---

## Test Count

Target: ≥1952 tests  
Result: ≥1962 tests pass

---

## Commands Verified

```bash
agentkit improve --help
agentkit improve --dry-run
agentkit improve --json
agentkit run --help  # --improve flag present
```

---

## Files Changed

**New:**
- `agentkit_cli/improve_engine.py`
- `agentkit_cli/commands/improve.py`
- `agentkit_cli/templates/improve_report.html`
- `tests/test_improve.py`
- `BUILD-REPORT.md`

**Modified:**
- `agentkit_cli/main.py`
- `agentkit_cli/commands/run_cmd.py`
- `agentkit_cli/__init__.py`
- `pyproject.toml`
- `CHANGELOG.md`
- `README.md`
