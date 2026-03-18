# Build Contract: agentkit-cli v0.45.0 — `agentkit explain`

**Version:** 0.45.0
**Feature:** `agentkit explain` — LLM-powered coaching report explaining WHY scores are what they are
**Baseline tests:** 1857 (verify with `python3 -m pytest -q --tb=no` before starting)
**Target:** ≥1857 + 40 new = ≥1897 passing, zero failures
**Repo:** ~/repos/agentkit-cli/
**PyPI package:** agentkit-cli

---

## Objective

`agentkit suggest` gives rule-based quick wins. What's missing is a human-readable coaching report that explains the *reasoning* behind scores — why is context freshness low? what does a lint finding actually mean for agent behavior? why does this refactor task fail?

`agentkit explain` calls an LLM (Claude via Anthropic API, with graceful fallback to a template-based explanation) and returns a markdown coaching report. It reads from a report JSON file (from `agentkit run --json`) or runs inline.

**Distribution angle:** "Your AI agent's AI quality score, explained by AI." The meta-recursion is the hook.

---

## Deliverables

### D1: ExplainEngine — `agentkit_cli/explain.py` (≥12 tests)

```python
class ExplainEngine:
    def __init__(self, model="claude-3-5-haiku-20241022", timeout=30):
        ...
    
    def load_report(self, path: str) -> dict:
        """Load a report JSON file (from agentkit run --json --output report.json)"""
    
    def build_prompt(self, report: dict) -> str:
        """Build the LLM prompt from report data.
        
        Include:
        - Composite score and tier (A/B/C/D/F)
        - Per-tool scores (lint, coderace, agentmd, agentreflect)
        - Top findings from each tool
        - Project name + file count
        
        Prompt instructs the LLM to:
        1. In 2-3 sentences, explain what this score means for AI coding agents working on this repo
        2. Explain the top 2-3 findings in plain language (what does "path-rot" actually hurt?)
        3. Give 3 concrete next steps ordered by impact
        4. Give one "if you do nothing else" recommendation
        """
    
    def call_llm(self, prompt: str) -> str:
        """Call Anthropic API. If ANTHROPIC_API_KEY not set or call fails, fall back to template_explain()."""
    
    def template_explain(self, report: dict) -> str:
        """Template-based fallback. No API key needed.
        
        Generates a markdown coaching report based on score ranges and top findings,
        using rule-based logic (like agentkit suggest but as prose paragraphs).
        """
    
    def explain(self, report: dict) -> str:
        """Full pipeline: build_prompt → call_llm (or template fallback) → return markdown."""
```

Tests: load_report(), build_prompt structure, template_explain() coverage, explain() integration.

### D2: `agentkit explain` CLI command — `agentkit_cli/commands/explain_cmd.py` (≥10 tests)

```
agentkit explain [PATH] [--report REPORT_JSON] [--model MODEL] [--no-llm] [--json] [--output FILE]
```

Flags:
- `PATH` — project path (optional; runs `agentkit run` inline if no --report given)
- `--report REPORT_JSON` — load from existing report JSON file
- `--model MODEL` — LLM model to use (default: claude-3-5-haiku-20241022)
- `--no-llm` — force template-based explanation (no API call, offline mode)
- `--json` — output as JSON with fields: project, score, tier, explanation (str), recommendations (list), one_thing (str)
- `--output FILE` — write markdown to file

Rich console output: print a nicely formatted coaching report with Rich (not just raw markdown).

Integration into `agentkit run`:
- `agentkit run --explain` — run the full toolkit then call explain, append coaching section to report

Tests: CLI wiring, --report loading, --no-llm path, --json output structure, rich output, error handling.

### D3: Template-based explanation quality (≥8 tests)

The template fallback must produce useful output without an API key. Validate:
- Score ≥ 90: "Your repo is well-configured for AI agents. Here's what's already working..."
- Score 70-89: "Good foundation with room to improve. The biggest opportunities are..."
- Score 50-69: "Mixed results. AI agents can work here but will hit friction in..."
- Score < 50: "Significant gaps found. Agents working on this repo will likely..."

Each tier should correctly explain the top 2-3 findings from the report in plain language:
- path-rot → "File paths referenced in your context file don't exist, which confuses agents trying to navigate your codebase"
- year-rot → "References to past years make your context file appear stale, reducing agent trust in its accuracy"
- bloat → "Your context file is too long; agents perform better with focused, essential context"
- low coderace score → "Agents scored lower on benchmark tasks, suggesting your codebase structure makes it harder for them to navigate and complete changes"

Tests: one test per score tier, tests for each finding type in plain language output.

### D4: `agentkit run --explain` integration (≥6 tests)

Add `--explain` flag to `agentkit run`:
1. Run full toolkit (existing behavior)
2. Call ExplainEngine.explain() on the results
3. Append "## Coaching Report" section to console output and JSON report
4. If `--share`, include coaching section in the here.now HTML

Reuse existing RunResult structure. ExplainEngine should accept RunResult directly (not just JSON files) via an `explain_run_result(result: RunResult)` method.

Tests: --explain flag parsed, coaching section in output, JSON payload includes explanation field, --share doesn't break.

### D5: Docs, CHANGELOG, version bump, BUILD-REPORT (≥4 tests)

- README: new "AI-Powered Explanations" section with example output
- CHANGELOG: v0.45.0 entry
- pyproject.toml: bump 0.44.0 → 0.45.0
- BUILD-REPORT.md: deliverables checklist
- tests/test_explain.py: all D1-D4 tests organized here

---

## Implementation Notes

**API key:** Use `os.environ.get("ANTHROPIC_API_KEY")`. If not set, log a warning and fall back to template. Never hard-code keys. Never fail hard if API is unavailable.

**Model:** Default `claude-3-5-haiku-20241022`. Fast + cheap for explanation tasks (short prompt + short response). Don't use claude-3-opus or claude-sonnet by default (overkill + expensive).

**Response format:** Ask the LLM for markdown with specific headers:
```
## What This Score Means
## Key Findings Explained
## Top 3 Next Steps
## If You Do Nothing Else
```

Parse these sections for the `--json` output.

**Prompt length:** Keep the prompt under 2000 tokens. Include scores + top 5 findings max. Don't dump the entire raw tool output.

**Import the Anthropic SDK:** Use `import anthropic` (the official `anthropic` package). If not installed, the explain command should give a clear "install anthropic: pip install anthropic" error. Don't fail silently.

**Offline-first:** The `--no-llm` template path must work with zero external dependencies. This is important for CI environments.

---

## Stop Conditions

- Stop if tests drop below 1857 (baseline)
- Stop if any import errors appear in the test suite
- Stop if adding explain dependencies breaks existing commands
- Do NOT publish to PyPI — build-loop handles publish
- Do NOT run `agentkit explain` on live API in tests — mock the API call

---

## Verification Steps

Before marking done:
1. `python3 -m pytest -q --tb=no` — full suite green (≥1897)
2. `agentkit explain --no-llm .` — runs without API key, produces readable output
3. `agentkit explain --help` — all flags documented
4. `agentkit run --explain --no-llm .` (or with a test fixture) — coaching section appears
5. `git diff --stat HEAD~1` — only expected files changed
6. `grep -r "ANTHROPIC_API_KEY" agentkit_cli/explain.py` — present and used safely

After verification: commit all changes with message "D1-D5: agentkit explain — LLM coaching report, template fallback, --explain on run, v0.45.0"

Do NOT tag. Do NOT publish to PyPI. Build-loop handles those steps.
