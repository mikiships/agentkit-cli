# Build Contract: agentkit-cli v0.74.0 — `agentkit repo-duel`

**Version:** 0.74.0
**Baseline:** 3689 tests passing (v0.73.0)
**Target:** 3689 + 45 new tests = 3734+ total
**Repo:** ~/repos/agentkit-cli/
**Time estimate:** 3–5 hours of Codex work

---

## Objective

Add `agentkit repo-duel github:owner/repo1 github:owner/repo2` — a head-to-head agent-readiness comparison of two specific GitHub repos. Declare a winner per dimension, produce an overall winner, and generate a shareable dark-theme HTML report.

**Why:** Completes the "duel family" (user-duel + topic-duel → repo-duel). Viral mechanic: people duel famous OSS repos (fastapi vs flask, react vs vue, etc.) and share the link. One command → shareable URL = organic distribution.

---

## Deliverables

### D1: RepoDuelEngine core (≥12 tests)
File: `agentkit_cli/commands/repo_duel.py`

- `RepoDuelEngine` class:
  - `run_duel(repo1: str, repo2: str, deep: bool = False)` → `RepoDuelResult`
  - Calls `agentkit analyze` (via ToolAdapter or direct) for each repo, collects `AnalysisResult`
  - Computes per-dimension winner: context_coverage, test_coverage, lint_score, redteam_resistance (if --deep), composite_score
  - Determines overall winner (most dimension wins, tie = draw)
  - `RepoDuelResult` dataclass: repo1, repo2, repo1_score, repo2_score, repo1_grade, repo2_grade, dimension_results (list of DimensionResult), winner ("repo1"|"repo2"|"draw"), run_date, share_url (optional)
  - `DimensionResult` dataclass: name, repo1_value, repo2_value, winner, delta

### D2: `agentkit repo-duel` CLI command (≥10 tests)
- `agentkit repo-duel github:owner/repo1 github:owner/repo2`
- Flags: `--deep` (add redteam dimension), `--share` (upload to here.now), `--json`, `--output <file>`, `--quiet`
- Rich terminal output:
  - Two-column header (repo1 vs repo2) with grade badges
  - Dimension-by-dimension comparison table (name | repo1 value | winner | repo2 value)
  - Overall winner banner
  - Share URL if `--share`
- Saves to history DB with label `repo_duel`

### D3: RepoDuelHTMLRenderer — dark-theme duel report (≥10 tests)
File: `agentkit_cli/renderers/repo_duel_renderer.py`

- Matches existing dark-theme style (deep-gray bg, colored highlights)
- Layout:
  - Header: "Repo Duel" title, repo1 vs repo2 names with github.com links
  - Score row: grade badges + numeric scores side by side (color-coded by grade)
  - Dimension table: striped rows, winner highlighted, delta shown
  - Winner banner: "🏆 {winner} wins" (or "🤝 Draw") in color
  - Footer: "Analyzed by agentkit-cli v{version}" + link to github.com/mikiships/agentkit-cli
- Standalone HTML (no external CSS/JS deps except Chart.js CDN optional for radar chart)

### D4: Integration hooks (≥8 tests)
- `agentkit run --repo-duel github:competitor/repo`: run a duel against a competitor inside existing pipeline
- `agentkit history --duels`: filter history to show only repo_duel runs
- `agentkit report` mentions recent repo-duel runs if present in history DB

### D5: Docs, CHANGELOG, version bump, BUILD-REPORT (≥5 tests)
- README: add `agentkit repo-duel` section with example (fastapi vs flask), example output, share mechanic
- CHANGELOG: v0.74.0 entry
- pyproject.toml: bump version 0.73.0 → 0.74.0
- `agentkit/_version.py` (or `__version__` wherever it lives): bump
- BUILD-REPORT.md in repo root: deliverables checklist, test count, known issues
- `agentkit doctor` check: confirm repo-duel can reach GitHub API

---

## Quality Bar

- All 5 deliverables must have tests
- Full test suite must pass: `python3 -m pytest -q` with 0 failures
- `agentkit repo-duel --help` shows all flags
- `agentkit repo-duel github:tiangolo/fastapi github:pallets/flask --share --json` runs end-to-end without error (mock in tests if GitHub API is slow)
- HTML renderer produces valid standalone HTML (no broken template vars)
- `agentkit doctor` still passes after changes

---

## Stop Conditions

- **STOP** if you cannot get the full test suite to pass after 3 fix attempts — report what's broken
- **STOP** before pushing to GitHub or publishing to PyPI (build-loop handles release)
- **STOP** before modifying any existing command's behavior in a breaking way
- **DO NOT** run `openclaw` CLI commands
- **DO NOT** deploy or publish anywhere

---

## Release Verification (build-loop does this, not the sub-agent)

1. Tests green: `python3 -m pytest -q`
2. Git push: `git push origin main`
3. Tag: `git tag v0.74.0 && git push --tags`
4. PyPI: `python3 -m build && twine upload dist/*0.74.0*`

---

## Context

- Repo: `~/repos/agentkit-cli/`
- Language: Python 3.11+
- Existing patterns to follow:
  - `agentkit_cli/commands/user_duel.py` — closest parallel (two-entity head-to-head pattern)
  - `agentkit_cli/commands/topic_duel.py` — second closest parallel
  - `agentkit_cli/commands/analyze.py` — for per-repo analysis pattern
  - `agentkit_cli/renderers/user_duel_renderer.py` — for dark-theme duel HTML style
  - `agentkit_cli/commands/history.py` — for DB interaction
  - Test files `tests/test_user_duel*.py` and `tests/test_topic_duel*.py` for test patterns
- GITHUB_TOKEN env var: available in environment for API calls
- here.now upload: see `agentkit_cli/share.py` for existing upload logic
- ToolAdapter at `agentkit_cli/tool_adapter.py` for invoking quartet tools
