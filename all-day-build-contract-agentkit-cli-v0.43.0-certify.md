# Build Contract: agentkit-cli v0.43.0 — `agentkit certify`

**Repo:** ~/repos/agentkit-cli  
**Target version:** 0.43.0  
**Baseline:** 1725 tests passing (v0.42.0)  
**Time budget:** 2–6h  
**Model:** claude-sonnet (or whatever is available)

## Objective

Add `agentkit certify` — a dated, shareable certification report proving a repo passed all agentkit quality checks. The cert is a JSON document with SHA256 content hash + UTC timestamp, plus a dark-theme HTML report suitable for sharing (--share support). A --badge flag injects/updates the README badge with the cert status.

## Deliverables

### D1: CertEngine core + cert schema
- `agentkit_cli/certify.py` — CertEngine class
- Runs 4 checks: composite score (agentkit score), redteam resistance (agentkit redteam), context freshness (agentlint check-context), test count (from agentkit doctor)
- Produces CertResult dataclass with: timestamp (UTC ISO), score, redteam_score, freshness_score, tests_found, verdict (PASS/FAIL/WARN), sha256 (SHA256 of JSON content), cert_id (8-char hex from sha256 prefix)
- PASS: score>=80, redteam>=70, freshness>=70
- WARN: score>=60 OR redteam>=50 OR freshness>=50 (but not all three passing)
- FAIL: any score below the WARN thresholds
- At least 12 unit tests for CertEngine (mocked subprocess)

### D2: `agentkit certify` CLI command
- `agentkit_cli/commands/certify_cmd.py`
- Wire into main.py: `app.add_typer(certify_app, name="certify")`
- Options: `--path PATH` (default "."), `--output FILE`, `--json` (print JSON cert to stdout), `--min-score N` (fail exit if composite score < N, default 0 = no gate), `--share` (upload HTML to here.now if HERENOW_API_KEY set)
- Rich console output: show cert_id, timestamp, verdict badge (green PASS / yellow WARN / red FAIL), 4 sub-scores in a table, final summary line
- At least 10 tests

### D3: Dark-theme HTML cert report
- `agentkit_cli/templates/certify.html.j2` (or inline in certify.py)
- Cert card: cert_id, project name, timestamp, verdict badge, 4 sub-score rows, SHA256 fingerprint
- Matches the dark aesthetic of existing reports (bg #0d1117, accent #238636)
- `--output report.html` writes it; `--share` uploads it
- At least 8 tests for HTML generation

### D4: `--badge` flag + README inject
- `agentkit certify --badge` — generate shields.io badge URL for the cert verdict and inject into README.md (same idempotent pattern as `agentkit badge`)
- Badge format: `![agentkit certified](https://img.shields.io/badge/agentkit-PASS-brightgreen)` (color from verdict)
- Idempotent: update existing badge line if already present
- `--badge --dry-run` prints what would change
- At least 10 tests

### D5: Docs, CHANGELOG, version bump, BUILD-REPORT
- `README.md`: add `agentkit certify` section with usage examples
- `CHANGELOG.md`: v0.43.0 entry
- `pyproject.toml` + `agentkit_cli/__init__.py`: bump 0.42.0 → 0.43.0
- `BUILD-REPORT.md`: deliverables checklist + test count
- At least 5 tests (version assertion, help output)

## Test Targets
- Baseline: 1725 (v0.42.0)
- New tests: ≥45
- Total target: ≥1770

## Stop Conditions
- DO NOT publish to PyPI — build-loop handles publish
- DO NOT push to GitHub — build-loop handles push/tag
- DO run `python3 -m pytest -q --tb=short 2>&1 | tail -20` after each deliverable to verify
- If any deliverable adds a regression, stop and report — do not mask it

## Success Criteria
- All 5 deliverables complete
- ≥1770 tests passing
- `agentkit certify --help` works
- `agentkit certify .` runs end-to-end on the agentkit-cli repo itself (self-certification)
- `BUILD-REPORT.md` updated with all deliverables checked

## Report When Done
Write your completion summary to: ~/repos/agentkit-cli/BUILD-REPORT.md
Include: test count, any issues encountered, deliverables completed.
