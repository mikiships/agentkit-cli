# BUILD-REPORT.md — agentkit-cli v0.55.0

**Date:** 2026-03-19
**Version:** 0.55.0
**Baseline tests:** 2529 (v0.54.0)
**Final tests:** 2573 (44 new tests added) ✓

---

## Summary

v0.55.0 is a packaging and polish release focused on making the Show HN launch turnkey. No new major commands — all changes are landing site, UX polish, and launch infrastructure.

---

## Deliverables

### D1: GitHub Pages Landing Site (`docs/`)

**Status:** DONE

- `docs/index.html` — dark-theme single-page site with no CDN dependencies
  - Hero: "Benchmark AI Coding Agents on YOUR Repo"
  - Pipeline diagram: MEASURE → GENERATE → GUARD → LEARN → BENCHMARK
  - Feature grid: 6 tools (coderace, agentmd, agentlint, agentreflect, agentkit-mcp, agentkit-cli)
  - Live stats bar with `data-stat` attributes (2529 tests, 6 packages, 54 versions)
  - Quickstart code block: `pip install agentkit-cli && agentkit quickstart`
  - Full command reference table
  - Footer with GitHub + PyPI links
  - All CSS inline, zero external JS frameworks
- `docs/.nojekyll` — disables Jekyll processing for GitHub Pages
- **13 tests** in `tests/test_landing_d1.py`

### D2: GitHub Pages Config + CI

**Status:** DONE

- `.github/workflows/update-pages.yml` — on push to main, auto-updates `data-stat` values in `docs/index.html` using current pyproject.toml version + pytest count
- README: added Documentation badge linking to https://mikiships.github.io/agentkit-cli/
- README: added PyPI badge
- **7 tests** in `tests/test_landing_d2.py`

### D3: `agentkit quickstart` Improvements

**Status:** DONE

- Prints GitHub Pages URL: https://mikiships.github.io/agentkit-cli/
- "Next steps" section printed after score:
  ```
  Next steps:
    agentkit run .                  -- full analysis
    agentkit analyze github:owner/repo  -- analyze any public repo
    agentkit benchmark              -- compare Claude vs Codex on your tasks
  ```
- Graceful no-key fallback: when `HERENOW_API_KEY` is unset, prints skip message and completes without error
- Share step only runs when API key is present
- **10 tests** in `tests/test_landing_d3.py` + fixed 1 existing test in `test_quickstart.py`

### D4: `agentkit demo --record`

**Status:** DONE

- `agentkit demo --record` prints VHS/asciinema recording instructions and writes `demo.tape`
- `demo.tape` is valid VHS syntax: Output directive, Set, Type, Sleep commands
- `--record-output <path>` flag to control tape output path
- Tape records the quickstart → run → benchmark flow
- `demo_record_command()` extracted as standalone callable
- README: Demo section with VHS recording instructions and gif placeholder
- **8 tests** in `tests/test_landing_d4.py`

### D5: Docs, Version Bump, Show HN

**Status:** DONE

- `pyproject.toml`: version 0.54.0 → 0.55.0
- `agentkit_cli/__init__.py`: `__version__` 0.54.0 → 0.55.0
- `CHANGELOG.md`: v0.55.0 entry at top
- Show HN draft (`memory/drafts/show-hn-quartet.md`): updated test count (2529→2560+), added GitHub Pages link, noted benchmark feature
- **6 tests** in `tests/test_landing_d5.py`

---

## Test Results

```
python3 -m pytest -q
2573 passed, 2 warnings
```

---

## Verification Results

```
python3 -m pytest -q 2>&1 | tail -3
  → 2573 passed, 2 warnings in 70.95s   ✓

cat CHANGELOG.md | head -5
  → ## [0.55.0] - 2026-03-19            ✓

cat pyproject.toml | grep version
  → version = "0.55.0"                  ✓

agentkit --version
  → agentkit-cli v0.55.0               ✓

cat docs/index.html | grep -c 'data-stat'
  → 4                                   ✓
```

---

## GitHub Pages Setup (Manual Step Required)

**Josh needs to do this once:**

1. Go to https://github.com/mikiships/agentkit-cli/settings/pages
2. Under "Source", select: **Deploy from a branch**
3. Branch: **main**, folder: **/docs**
4. Click **Save**

The site will be live at: https://mikiships.github.io/agentkit-cli/

After enabling, the `update-pages.yml` workflow will auto-update stats on every push to main.

---

## Files Changed

- `docs/index.html` — NEW (GitHub Pages landing)
- `docs/.nojekyll` — NEW
- `.github/workflows/update-pages.yml` — NEW
- `agentkit_cli/commands/quickstart_cmd.py` — improved next steps + graceful share
- `agentkit_cli/commands/demo_cmd.py` — added `--record` flag + tape generation
- `agentkit_cli/main.py` — wired `--record` + `--record-output` to demo command
- `agentkit_cli/__init__.py` — version bump
- `pyproject.toml` — version bump
- `CHANGELOG.md` — v0.55.0 entry
- `README.md` — badges + Demo section
- `tests/test_landing_d1.py` — NEW (13 tests)
- `tests/test_landing_d2.py` — NEW (7 tests)
- `tests/test_landing_d3.py` — NEW (10 tests)
- `tests/test_landing_d4.py` — NEW (8 tests)
- `tests/test_landing_d5.py` — NEW (6 tests)
- `tests/test_quickstart.py` — fixed existing test for graceful no-key fallback
- Various `test_*_d5.py` — updated version assertions (0.54.0 → 0.55.0)
