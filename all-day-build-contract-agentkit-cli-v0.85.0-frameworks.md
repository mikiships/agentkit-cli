# All-Day Build Contract: agentkit-cli v0.85.0 — `agentkit frameworks`

Status: In Progress
Date: 2026-03-22
Owner: Codex execution pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Build `agentkit frameworks` — a command that detects which popular frameworks a project uses, then checks if framework-specific agent context rules are present and well-formed.

**Why now:** Next.js just published official AGENTS.md guidelines in their docs (March 20, 2026). Thousands of devs are setting up AGENTS.md for Next.js. This command tells them whether their agent context file follows best practices for their specific framework.

**User story:** `agentkit frameworks` runs on any project, auto-detects frameworks (Next.js, FastAPI, Django, Rails, etc.), checks if the CLAUDE.md/AGENTS.md contains framework-specific sections, and outputs a score + actionable missing items. With `--generate`, it adds the missing framework-specific blocks automatically.

This contract is considered complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Full test suite must pass at the end.
4. New features must ship with docs and report addendum updates in the same pass.
5. CLI outputs must be deterministic and schema-backed where specified.
6. Never modify files outside the project directory.
7. Commit after each completed deliverable (not at the end).
8. If stuck on same issue for 3 attempts, stop and write a blocker report.
9. Do NOT refactor, restyle, or "improve" code outside the deliverables.
10. Read existing tests and docs before writing new code.

## 3. Feature Deliverables

### D1. FrameworkDetector + FrameworkChecker (`agentkit_cli/frameworks.py`)

Detect frameworks from project files, then check if agent context files cover them.

**FrameworkDetector:** Detect frameworks by scanning project files:
- Next.js: presence of `next.config.js`, `next.config.ts`, `package.json` with `"next"` dependency
- FastAPI: `requirements.txt` / `pyproject.toml` with `fastapi`
- Django: `manage.py` or `settings.py` or `requirements.txt` with `django`
- Rails: `Gemfile` with `rails`
- Express/Node: `package.json` with `express`
- React: `package.json` with `react` (but not Next.js)
- Vue: `package.json` with `vue`
- Nuxt: `nuxt.config.ts` or `nuxt.config.js`
- Flask: `requirements.txt` / `pyproject.toml` with `flask`
- Laravel: `composer.json` with `laravel/framework`

Return: `List[DetectedFramework]` — each with `name`, `version_hint`, `confidence` (high/medium/low), `detection_files`.

**FrameworkChecker:** For each detected framework, check the agent context file (CLAUDE.md / AGENTS.md) for framework-specific coverage:
- Required sections: framework name mentioned, setup instructions, common patterns, known issues/gotchas
- Nice-to-have: testing patterns, deploy patterns
- Score: 0-100 per framework (required sections weighted 80%, nice-to-have 20%)
- Output: `FrameworkCoverage` — `framework`, `score`, `missing_required`, `missing_nice_to_have`, `suggestions`.

Required files:
- `agentkit_cli/frameworks.py` — FrameworkDetector, FrameworkChecker, DetectedFramework, FrameworkCoverage
- Tests: `tests/test_frameworks_d1.py` — min 15 tests (detection from fixture files + scoring logic)

- [ ] FrameworkDetector with 10+ framework rules
- [ ] FrameworkChecker scoring logic
- [ ] tests/test_frameworks_d1.py (15+ tests)
- [ ] Commit D1

### D2. `agentkit frameworks` CLI command (`agentkit_cli/commands/frameworks_cmd.py`)

**Command:** `agentkit frameworks [PATH] [OPTIONS]`

Arguments:
- `PATH`: local path to analyze (default: `.`)

Options:
- `--context-file PATH`: explicit path to CLAUDE.md/AGENTS.md (default: auto-detect)
- `--min-score N`: highlight frameworks scoring below N (default: 60)
- `--json`: structured JSON output
- `--quiet`: summary line only
- `--share`: upload report to here.now, print URL

**Default output (Rich table):**
```
Detected Frameworks in my-project
┌──────────────────┬──────────┬────────────────────────────────────────┐
│ Framework        │ Score    │ Missing                                │
├──────────────────┼──────────┼────────────────────────────────────────┤
│ Next.js (high)   │ 45/100   │ Setup instructions, Known gotchas      │
│ React (high)     │ 80/100   │ Testing patterns                       │
└──────────────────┴──────────┴────────────────────────────────────────┘

Overall: 2 frameworks detected, 1 below threshold (45 < 60)
Run `agentkit frameworks --generate` to add missing sections.
```

**JSON schema:**
```json
{
  "project_path": ".",
  "context_file": "CLAUDE.md",
  "detected_frameworks": [
    {
      "name": "Next.js",
      "confidence": "high",
      "score": 45,
      "missing_required": ["setup instructions", "known gotchas"],
      "missing_nice_to_have": []
    }
  ],
  "overall_score": 63,
  "below_threshold": ["Next.js"],
  "version": "0.85.0"
}
```

Required files:
- `agentkit_cli/commands/frameworks_cmd.py`
- Tests: `tests/test_frameworks_d2.py` — min 12 tests (CLI invocation + output formats)

- [ ] frameworks_cmd.py with all options
- [ ] tests/test_frameworks_d2.py (12+ tests)
- [ ] Commit D2

### D3. `--generate` flag: auto-add missing framework sections

**`agentkit frameworks --generate`** — for each framework below the min-score threshold, generate and append missing sections to the context file.

Templates per framework (inline in `agentkit_cli/framework_templates.py`):
- Each template is a markdown section with placeholder content:
  ```markdown
  ## [Framework Name] Notes
  
  ### Setup
  [Framework-specific setup for agents]
  
  ### Common Patterns
  [Idiomatic patterns for this framework]
  
  ### Known Gotchas
  [Common issues agents should avoid]
  ```
- Templates are minimal (10-20 lines each) — practical, not boilerplate-heavy
- All 10+ detected frameworks need a template

**Idempotent:** if a framework section already exists (detected by framework name in a `##` heading), skip it.

Required files:
- `agentkit_cli/framework_templates.py`
- Tests: `tests/test_frameworks_d3.py` — min 12 tests (template rendering + idempotency + append logic)

- [ ] framework_templates.py with 10+ templates
- [ ] --generate flag in frameworks_cmd.py
- [ ] tests/test_frameworks_d3.py (12+ tests)
- [ ] Commit D3

### D4. Integration: `agentkit run --frameworks`, `agentkit doctor` check

**`agentkit run --frameworks`:** After pipeline run, also run frameworks check. Add to run output.

**`agentkit doctor` check:** Add a "framework coverage" check:
- Detect frameworks in current project
- If any framework is detected and scores < 60, warn: "Framework detected but missing agent context: [name]. Run `agentkit frameworks --generate` to fix."
- If no context file exists at all, this is already caught elsewhere.

Required files:
- Modify `agentkit_cli/commands/run_cmd.py` (add `--frameworks` flag and logic)
- Modify `agentkit_cli/commands/doctor_cmd.py` (add FrameworkCoverageCheck)
- Tests: `tests/test_frameworks_d4.py` — min 10 tests

- [ ] run_cmd.py --frameworks flag
- [ ] doctor_cmd.py FrameworkCoverageCheck
- [ ] tests/test_frameworks_d4.py (10+ tests)
- [ ] Commit D4

### D5. Docs, CHANGELOG, version bump, BUILD-REPORT

- [ ] README.md: add `agentkit frameworks` to command reference table and quick-start examples
- [ ] CHANGELOG.md: `[0.85.0]` entry with all deliverables listed
- [ ] `agentkit_cli/__init__.py`: bump version `0.84.1` → `0.85.0`
- [ ] `pyproject.toml`: bump version `0.84.1` → `0.85.0`
- [ ] `BUILD-REPORT.md`: update header to `v0.85.0`, add D1-D4 summary
- [ ] `BUILD-REPORT-v0.85.0.md`: create versioned copy
- [ ] Tests: `tests/test_v085_release.py` — version assertion tests (use `startswith("0.85.")` pattern, not exact string)
- [ ] Full test suite passes: `python3 -m pytest -q --tb=short` — zero failures
- [ ] Commit D5

## 4. Validation Gates

Before marking complete:
1. `python3 -m pytest -q --tb=short` — zero failures
2. `agentkit frameworks --help` exits 0
3. `agentkit frameworks . --json` produces valid JSON with `detected_frameworks` key
4. `agentkit doctor` includes framework coverage check output

## 5. Test Baseline

Current passing: ~4221 tests (after test fix commits)
Target: 4221 + 49+ new tests = ~4270 total

## 6. What NOT to do

- Do NOT refactor existing commands
- Do NOT add new frameworks beyond the 10+ listed in D1
- Do NOT modify any file outside ~/repos/agentkit-cli/
- Do NOT deploy, publish to PyPI, or push to GitHub (build-loop handles this)
- Do NOT create a `--push` or `--publish` flag
- Stop and write a blocker if stuck for 3+ attempts on the same issue

## 7. Stop Conditions

Stop and write BLOCKER.md in the repo root if:
- Full test suite has >0 failures after 3 fix attempts
- Any deliverable requires changes to >5 existing files outside the deliverable scope
- Framework detection logic requires network access (must be 100% local file analysis)

## 8. Completion Report

When done, write `BUILD-REPORT.md` and `BUILD-REPORT-v0.85.0.md` with:
- Actual tests added per deliverable
- Final total test count
- Any scope deviations
- Git commits made
