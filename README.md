# agentkit-cli

**One install to rule them all.**

```bash
pip install agentkit-cli
```

Get the full Agent Quality Toolkit pipeline in a single command — no more juggling four separate `pip install` steps.

---

## Analyze Any Repo (Zero Setup)

The viral mechanic: analyze any public GitHub repo for agent quality without touching it first.

```bash
# GitHub shorthand
agentkit analyze tiangolo/fastapi

# github: prefix
agentkit analyze github:tiangolo/fastapi

# Full URL
agentkit analyze https://github.com/tiangolo/fastapi

# Local path
agentkit analyze ./my-project
```

Example output:

```
agentkit analyze — cloning https://github.com/tiangolo/fastapi.git …

             Analysis: fastapi
┌──────────────┬──────────┬───────┬───────────────────────────┐
│ Tool         │ Status   │ Score │ Key Finding               │
├──────────────┼──────────┼───────┼───────────────────────────┤
│ agentmd      │ ✓ pass   │ 82    │ context file found        │
│ agentlint    │ ✓ pass   │ 78    │ 2 suggestions             │
│ agentreflect │ ✓ pass   │ 85    │ reflection generated      │
└──────────────┴──────────┴───────┴───────────────────────────┘

────────────────────────────────────────────────────────────
Agent Quality Score: 82/100 (B)  repo: fastapi
────────────────────────────────────────────────────────────
```

**Options:**
- `--json` — machine-readable JSON output with full schema
- `--keep` — don't delete the temp clone (prints path for follow-up)
- `--publish` — publish HTML report to here.now after analysis
- `--timeout N` — clone + analysis timeout in seconds (default: 120)
- `--no-generate` — skip `agentmd generate`; score only what's already there

**JSON schema** (`--json`):
```json
{
  "target": "github:tiangolo/fastapi",
  "repo_name": "fastapi",
  "composite_score": 82.0,
  "grade": "B",
  "tools": {
    "agentmd": {"tool": "agentmd", "status": "pass", "score": 82.0, "finding": "context file found"},
    "agentlint": {"tool": "agentlint", "status": "pass", "score": 78.0, "finding": "2 suggestions"},
    "agentreflect": {"tool": "agentreflect", "status": "pass", "score": 85.0, "finding": "reflection generated"}
  },
  "generated_context": false
}
```

---

## Sweep: Batch Analysis

Compare multiple repos side-by-side in a single command:

```bash
# Positional targets
agentkit sweep github:psf/requests github:pallets/flask ./my-project

# Targets from a file (one per line)
agentkit sweep --targets-file repos.txt

# Mix positional + file targets (duplicates removed)
agentkit sweep github:psf/requests --targets-file repos.txt
```

Example output:

```
agentkit sweep — analyzed 3 target(s)

 target                  score  grade  status        error
 github:pallets/flask       88  B      ✓ succeeded
 github:psf/requests        82  B      ✓ succeeded
 ./my-project               64  D      ✓ succeeded

Total: 3 | Succeeded: 3 | Failed: 0
```

**Options:**
- `--sort-by score|name|grade` — sort order (default: score descending)
- `--limit N` — show only top N results in table output
- `--json` — machine-readable JSON output with ranked results and summary counts
- `--keep` — keep temp clone dirs
- `--publish` — publish HTML report after each analysis
- `--timeout N` — per-target timeout in seconds (default: 120)
- `--no-generate` — skip `agentmd generate`; score only what's there
- `--targets-file PATH` — file with one target per line (blank lines and `#` comments ignored)

**JSON schema** (`--json`):
```json
{
  "targets": ["github:psf/requests", "github:pallets/flask"],
  "results": [
    {"rank": 1, "target": "github:pallets/flask", "score": 88.0, "grade": "B", "status": "succeeded"},
    {"rank": 2, "target": "github:psf/requests", "score": 82.0, "grade": "B", "status": "succeeded"}
  ],
  "summary_counts": {"total": 2, "succeeded": 2, "failed": 0, "analyzed_with_scores": 2}
}
```

---

## Agent Quality Score

Get a single **0-100 composite score** for your AI agent project in one command:

```bash
agentkit score
# → Agent Quality Score: 87/100 (B)

agentkit score --breakdown
# Shows per-component table: coderace, agentlint, agentmd, agentreflect

agentkit score --json
# {"score": 87, "grade": "B", "components": {...}, "missing_tools": [...]}

agentkit score --ci --min-score 70
# Exits 1 if score < 70 (great for PR gates)
```

The composite score synthesizes all four toolkit tools into one headline metric using weighted averaging (coderace 30%, agentlint 25%, agentmd 25%, agentreflect 20%). Missing tools are automatically excluded and weights renormalized.

Use it in your README badge too:

```bash
agentkit badge           # composite score badge (default)
agentkit badge --tool coderace  # single-tool badge
```

---

## What is it?

`agentkit-cli` is a unified meta-CLI that wraps the **Agent Quality Toolkit quartet**:

| Tool | Purpose |
|------|---------|
| [agentmd](https://pypi.org/project/agentmd/) | Generate CLAUDE.md context files |
| [agentlint](https://pypi.org/project/agentlint/) | Lint AI context files and git diffs |
| [coderace](https://pypi.org/project/coderace/) | Benchmark AI coding performance |
| [agentreflect](https://pypi.org/project/agentreflect/) | Generate reflection reports from failures |

## Pipeline Overview

```
agentkit run
    │
    ├── 1. agentmd generate        → produces CLAUDE.md
    ├── 2. agentlint check-context → lints CLAUDE.md
    ├── 3. agentlint (diff)        → lints recent changes
    ├── 4. coderace benchmark      → (opt-in via --benchmark)
    └── 5. agentreflect generate   → reflection on failures
```

Zero to full pipeline in 30 seconds.

---

## Installation

```bash
pip install agentkit-cli
```

Install the quartet tools too:

```bash
pip install agentmd agentlint coderace agentreflect
```

---

## Usage

### `agentkit report`

Generate a shareable HTML quality report for the current project in one command.

```bash
agentkit report                          # saves agentkit-report.html in current dir
agentkit report --output myreport.html   # custom output path
agentkit report --open                   # save and auto-open in browser
agentkit report --json                   # emit structured JSON to stdout
agentkit report --path /my/project       # specify project directory
```

Runs all installed toolkit tools (agentlint, agentmd, coderace, agentreflect) with 60-second timeouts, collects results, and assembles a **self-contained HTML report** — no CDN, no external fonts, suitable for sharing as a screenshot or file. Tools that aren't installed are shown as skipped; the command never crashes regardless of toolkit state.

**Report sections:**
- Toolkit coverage score (% of tools ran successfully)
- Context quality score from agentlint (freshness, top issues)
- Context docs score from agentmd (file sizes, tier structure)
- Agent benchmark results from coderace (scores per agent, winner highlighted)
- Reflection summary from agentreflect
- Pipeline status table (installed / success / failed / not installed)

**JSON output format:**
```json
{
  "project": "my-project",
  "version": "0.5.0",
  "coverage": 75,
  "tools": [
    {"tool": "agentlint", "installed": true, "status": "success"},
    {"tool": "agentmd", "installed": true, "status": "success"},
    {"tool": "coderace", "installed": false, "status": "not_installed"},
    {"tool": "agentreflect", "installed": true, "status": "success"}
  ],
  "agentlint": { ... },
  "agentmd": { ... },
  "coderace": null,
  "agentreflect": { ... }
}
```

### Sharing Results

Publish a report to [here.now](https://here.now) and get a shareable link in seconds.

```bash
# Publish the most recently generated report
agentkit publish

# Publish a specific report file
agentkit publish path/to/report.html

# Generate and publish in one command
agentkit report --publish

# Run the full pipeline and publish at the end
agentkit run --publish

# Get just the URL (useful in scripts)
agentkit publish --quiet

# Get JSON output with URL and expiry info
agentkit publish --json
```

**Authentication:** Anonymous publishes expire after 24 hours. For persistent links, set the `HERENOW_API_KEY` environment variable:

```bash
export HERENOW_API_KEY=your-key-here
agentkit publish   # link never expires
```

### GitHub Action

Add automated agent quality checks to every pull request with the `mikiships/agentkit-cli` GitHub Action.

[![Agent Quality](https://github.com/mikiships/agentkit-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/mikiships/agentkit-cli/actions/workflows/ci.yml)

**What it checks:**
- **Context Lint Score** — runs `agentlint check-context` and scores your `AGENTS.md` / `CLAUDE.md` (0–100). Fails the action if the score falls below `min-lint-score`.
- **Context Drift** — runs `agentmd drift` to detect whether your context file has drifted from the codebase.
- **Code Review** — runs `coderace review` on the PR diff with parallel review lanes.

**Add it in 3 lines:**

```yaml
# .github/workflows/agent-quality.yml
name: Agent Quality
on: [pull_request]
jobs:
  quality:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
      - uses: mikiships/agentkit-cli@v0.7.0
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          min-lint-score: '70'
```

**PR comment format:**

```
## 🔬 Agent Quality Report

| Check | Result |
|-------|--------|
| Context Lint Score | 85/100 |
| Context Drift | ✅ Fresh |
| Code Review | Review complete |

[Details in workflow logs]
```

**Inputs:**

| Input | Default | Description |
|-------|---------|-------------|
| `github-token` | — | Required. Token for posting PR comments. |
| `min-lint-score` | `70` | Minimum lint score. Action fails if below this. |
| `post-comment` | `true` | Whether to post a PR comment. |
| `python-version` | `3.11` | Python version to use. |

**Outputs:** `lint-score`, `drift-status`, `review-summary`

See [`examples/agentkit-quality.yml`](examples/agentkit-quality.yml) for a complete ready-to-use workflow.

### `agentkit demo`

Zero-config first-run experience. Works in any directory — no `.agentkit.yaml` needed.

```bash
agentkit demo                        # auto-detect project type and agents
agentkit demo --skip-benchmark       # just run generate + lint + reflect
agentkit demo --task refactor        # pick a specific coderace task
agentkit demo --agents claude,codex  # specify agents manually
agentkit demo --json                 # emit results as JSON
```

Detects your project type (python/typescript/javascript/generic), picks the best benchmark task, finds installed agents (claude, codex), and runs the full pipeline without any setup. Footer shows how to continue with `agentkit init && agentkit run`.

---

### `agentkit init`

Initialize agentkit in a project. Checks which tools are installed and creates `.agentkit.yaml`.

```bash
agentkit init
agentkit init --path /my/project
```

Creates `.agentkit.yaml`:

```yaml
tools:
  coderace: true
  agentmd: true
  agentlint: true
  agentreflect: true
defaults:
  min_score: 80
  context_file: CLAUDE.md
```

---

### `agentkit run`

Run the full quality pipeline sequentially.

```bash
agentkit run
agentkit run --path /my/project
agentkit run --skip generate
agentkit run --skip lint
agentkit run --skip benchmark
agentkit run --skip reflect
agentkit run --benchmark        # include benchmark step
agentkit run --json             # emit summary as JSON
agentkit run --notes "regression after refactor"
```

Missing tools are skipped automatically with a warning — you don't need all four installed.

---

### `agentkit status`

Quick health check: tool versions, config presence, last run summary.

```bash
agentkit status
agentkit status --path /my/project
agentkit status --json
```

---

### `agentkit doctor`

Full preflight check: repo health, toolchain availability, context freshness, and publish readiness — all in one command.

```bash
agentkit doctor                          # human-readable Rich table
agentkit doctor --json                   # structured JSON output
agentkit doctor --category repo          # filter: repo | toolchain | context | publish
agentkit doctor --fail-on warn           # exit 1 on any warn or fail (default: fail only)
agentkit doctor --no-fail-exit           # always exit 0 (useful in informational hooks)
```

**What it checks:**

| Category | Check | Severity |
|----------|-------|----------|
| `repo` | Git repository present | fail |
| `repo` | At least one commit | warn |
| `repo` | Working tree clean | warn |
| `repo` | README.md present | warn |
| `repo` | pyproject.toml present | warn |
| `repo` | Context files (CLAUDE.md / AGENTS.md / .agents/) | warn |
| `toolchain` | agentmd on PATH + version | fail |
| `toolchain` | agentlint on PATH + version | fail |
| `toolchain` | coderace on PATH + version | fail |
| `toolchain` | agentreflect on PATH + version | fail |
| `toolchain` | git on PATH (optional) | warn |
| `toolchain` | python3 on PATH (optional) | warn |
| `context` | Source files present (.py/.ts/.js/.tsx/.jsx) | warn |
| `context` | Context freshness via `agentlint check-context` | warn |
| `context` | agentkit-report/ output dir writable | fail |
| `publish` | HERENOW_API_KEY set | warn |

Exit codes: `0` = all checks passed (or only warns at default threshold); `1` = one or more checks at the fail level. Use `--fail-on warn` to treat warns as failures (good for CI preflight).

**Troubleshooting / preflight checklist:**

1. **Missing quartet tools** — `pip install agentmd agentlint coderace agentreflect`
2. **No git repo** — `git init && git add . && git commit -m "Initial commit"`
3. **No context files** — `agentmd generate .`
4. **Stale context** — `agentmd generate .` to refresh CLAUDE.md / AGENTS.md
5. **No HERENOW_API_KEY** — set `export HERENOW_API_KEY=your-key` in your shell profile for persistent publish URLs
6. **Unwritable output dir** — `chmod u+w agentkit-report/` or use `--output` flag on `agentkit report`

**Use in CI:**

```yaml
- name: Preflight check
  run: agentkit doctor --fail-on warn --category toolchain
```

---

### `agentkit ci`

Generate a ready-to-use GitHub Actions workflow that runs the full quartet pipeline on every PR.

```bash
# Write .github/workflows/agentkit.yml
agentkit ci

# Preview without writing (dry run)
agentkit ci --dry-run

# With coderace benchmark step
agentkit ci --benchmark

# Gate PR on minimum lint score
agentkit ci --min-score 80

# Custom Python version
agentkit ci --python-version 3.11

# Custom output path
agentkit ci --output-dir .github/workflows
```

**Generated workflow example:**

```yaml
name: Agent Quality Toolkit

on:
  pull_request:
  push:
    branches: [main, master]

jobs:
  agentkit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install quartet tools
        run: pip install agentmd-gen ai-agentlint coderace ai-agentreflect agentkit-cli
      - name: Run agentkit pipeline
        run: agentkit run --ci
      - name: Upload lint report
        uses: actions/upload-artifact@v4
        with:
          name: agentkit-lint-report
          path: .agentlint_report.json
```

| Flag | Default | Description |
|------|---------|-------------|
| `--python-version` | `3.12` | Python version for the workflow |
| `--benchmark` | off | Include coderace benchmark step |
| `--min-score` | none | Gate PR on maintainer rubric score |
| `--output-dir` | `.github/workflows` | Where to write the workflow file |
| `--dry-run` | off | Print to stdout instead of writing |

---

### `agentkit compare`

Compare agent quality scores between two git refs. Useful for "did my PR improve or degrade agent quality?"

```bash
# Quick check: compare last commit to HEAD
agentkit compare

# Explicit refs
agentkit compare HEAD~1 HEAD

# Only show verdict (for shell scripts)
agentkit compare --quiet HEAD~1 HEAD

# Structured JSON output
agentkit compare --json HEAD~1 HEAD

# CI mode: exit 1 if verdict is DEGRADED
agentkit compare --ci HEAD~1 HEAD

# Require at least +5 net delta improvement
agentkit compare --ci --min-delta 5 HEAD~1 HEAD

# Limit to specific tools
agentkit compare --tools agentlint,agentreflect HEAD~1 HEAD

# Show which files changed between refs
agentkit compare --files HEAD~1 HEAD
```

**Verdicts:**
- `IMPROVED` — net delta > +5
- `NEUTRAL` — net delta between -5 and +5
- `DEGRADED` — net delta < -5

### `agentkit suggest`

Get a prioritized action list from agentlint findings. Answers: "What should I fix to improve my agent quality score?"

```bash
# Show top 5 prioritized findings
agentkit suggest

# Show all findings
agentkit suggest --all

# Output as JSON
agentkit suggest --json

# Auto-apply safe fixes (year-rot, trailing whitespace, duplicate blank lines)
agentkit suggest --fix

# Preview fixes without applying
agentkit suggest --fix --dry-run

# Run against a specific project directory
agentkit suggest --path /my/project
```

Shows:
```
Current score: 72/100 — 3 critical issues found

 agentkit suggest — top findings
 #  Severity   Category              Description       Fix Hint        Auto-fix?
 1  critical   year-rot              Stale year 2021   Update year     yes
 2  critical   path-rot              Broken file ref   Fix or remove   no
 3  high       stale-todo            Unresolved TODO   Resolve TODO    no
```

**Safe auto-fixes** (`--fix`): Only modifies CLAUDE.md, AGENTS.md, and `.agents/*.md`. Never touches source code files.

- **year-rot**: Updates stale year references (>2 years old) to current year
- **trailing-whitespace**: Strips trailing whitespace
- **duplicate-blank-lines**: Collapses 3+ consecutive blank lines to 2

---

### `agentkit summary`

Generate a maintainer-facing summary from agentkit analysis results. Designed for CI job summaries, PR comments, and release notes.

```bash
# Summarise the current project (runs the full toolkit)
agentkit summary

# Write markdown to a file
agentkit summary --output summary.md

# Append to GitHub Actions job summary
agentkit summary --job-summary

# Read from a JSON report (e.g. output of agentkit report --json)
agentkit summary --json-input report.json

# Emit structured JSON instead of markdown
agentkit summary --json
```

Output includes:

- **Overview**: project name, verdict (`Passing`, `Warnings Present`, `Action Required`, `Regression Detected`), overall score, tools passing
- **Tool status table**: per-tool status, score, and concise notes
- **Top fixes**: up to 5 prioritized findings derived from agentlint and agentreflect
- **Compare section** (when compare data is present): base/head refs, net delta, per-tool deltas

**GitHub Actions integration:**

```yaml
- name: Generate agent quality summary
  run: agentkit summary --job-summary
  env:
    GITHUB_STEP_SUMMARY: ${{ runner.temp }}/summary.md
```

---

### `agentkit watch`

Watch the project for file changes and automatically re-run the pipeline.

```bash
# Watch current directory
agentkit watch

# Watch specific directory
agentkit watch --path /my/project

# Custom extensions
agentkit watch --extensions .py --extensions .md

# Custom debounce (seconds)
agentkit watch --debounce 3.0

# Run in CI mode on changes
agentkit watch --ci
```

Shows:
```
Watching /my/project for changes... (Ctrl+C to stop)
Extensions: .py, .md, .yaml, .yml
Debounce: 2.0s
```

On any matching file change, clears the screen and re-runs `agentkit run`. Press Ctrl+C to stop.

**Requirements:** `pip install watchdog`

---

## agentkit setup-ci

One command to wire agentkit into GitHub Actions. Run it once in your repo and you're done.

```bash
# Default: write workflow, generate baseline, inject README badge
agentkit setup-ci

# Custom min-score threshold
agentkit setup-ci --min-score 80

# Preview without writing anything
agentkit setup-ci --dry-run

# Overwrite an existing workflow
agentkit setup-ci --force

# Skip baseline generation (useful if tools aren't installed locally)
agentkit setup-ci --skip-baseline

# Skip README badge injection
agentkit setup-ci --no-badge

# Custom workflow output path
agentkit setup-ci --workflow-path .github/workflows/quality.yml
```

**What it does:**

1. Writes `.github/workflows/agentkit-quality.yml` — a complete, working GitHub Actions
   workflow that runs `agentkit gate` on every push and PR, posts a verdict as a PR comment,
   and conditionally uses `--baseline-report` if `.agentkit-baseline.json` is present.
2. Runs `agentkit report --json --output .agentkit-baseline.json` to generate the initial
   baseline so CI can detect regressions immediately.
3. Injects the agent quality badge into `README.md` (if it exists).

**Full example flow:**

```bash
# In your Python project root:
agentkit setup-ci --min-score 75

# Commit everything in one go:
git add .github/workflows/agentkit-quality.yml .agentkit-baseline.json README.md
git commit -m "ci: add agentkit quality workflow"
git push

# CI now runs on every push and PR. You'll see:
# ✓ agentkit gate PASS — 82.0/100 (B)
```

**Flags:**

| Flag | Default | Description |
|---|---|---|
| `--min-score N` | 70 | Score threshold embedded in generated gate command |
| `--workflow-path PATH` | `.github/workflows/agentkit-quality.yml` | Override workflow output path |
| `--force` | false | Overwrite existing workflow file |
| `--dry-run` | false | Print workflow to stdout without writing |
| `--skip-baseline` | false | Skip baseline generation |
| `--no-badge` | false | Skip README badge injection |
| `--path PATH` | git root | Project root |

---

## agentkit gate

Block merges when agent quality drops. Gate on an absolute score, a regression threshold, or both.

```bash
# Fail if composite score < 75
agentkit gate --min-score 75

# Fail if score dropped more than 5 points from last release
agentkit gate --baseline-report baseline.json --max-drop 5

# Both rules together
agentkit gate --min-score 70 --baseline-report baseline.json --max-drop 5

# Machine-readable JSON (CI-safe, no Rich color codes)
agentkit gate --min-score 75 --json

# Write JSON to disk
agentkit gate --min-score 75 --output gate-result.json

# Write markdown verdict to GitHub Actions step summary
agentkit gate --min-score 75 --job-summary
```

**GitHub Actions example:**

```yaml
- name: Save baseline
  run: agentkit report --json > baseline.json

# ... your code changes ...

- name: Quality gate
  run: |
    agentkit gate \
      --min-score 70 \
      --baseline-report baseline.json \
      --max-drop 5 \
      --job-summary \
      --output gate-result.json
```

Exit code 0 = PASS, 1 = FAIL, 2 = configuration error.

---

## CI Integration

Use the agentkit GitHub Action to run the full pipeline in CI:

```yaml
- name: Run agentkit pipeline
  uses: mikiships/agentkit-cli@v0.2.0
  with:
    python-version: '3.12'
    skip: ''
    benchmark: 'false'
    fail-on-lint: 'true'
```

Or use `agentkit ci` to generate the workflow automatically (recommended for v0.3.0+).

**Inputs:**

| Input | Default | Description |
|-------|---------|-------------|
| `skip` | `''` | Comma-separated steps to skip (`generate`, `lint`, `benchmark`, `reflect`) |
| `benchmark` | `false` | Enable coderace benchmark step |
| `python-version` | `3.12` | Python version to use |
| `fail-on-lint` | `true` | Exit 1 on agentlint failures |

---

## Auto-Inject Badge

The fastest way to add an agent quality badge to your README:

```bash
agentkit readme
```

This computes the score, injects a badge section into `README.md`, and prints a summary:

```
Updated README.md — agent quality: 87/100 (green)
```

The injected section looks like:

```markdown
## Agent Quality

[![agent quality](https://img.shields.io/badge/agent%20quality-87%2F100-green)](https://pypi.org/project/agentkit-cli/)

Generated by [agentkit-cli](https://pypi.org/project/agentkit-cli/).
```

The command is **idempotent** — run it again and it just updates the score. Remove the section with `--remove`:

```bash
agentkit readme --remove
```

Other options:

```bash
agentkit readme --dry-run              # preview without modifying
agentkit readme --readme docs/README.md  # custom path
agentkit readme --section-header "## Quality"  # custom header
agentkit readme --score 87             # override score
```

Combine with the pipeline:

```bash
agentkit run --readme     # run full pipeline then inject badge
agentkit report --readme  # generate HTML report then inject badge
```

---

## Add a Badge (Manual)

Show your project's agent quality score in your README:

```bash
agentkit badge
```

This outputs a [shields.io](https://shields.io) badge URL plus ready-to-paste Markdown and HTML snippets. Add it to your README:

```markdown
[![agent quality](https://img.shields.io/badge/agent%20quality-87%2F100-green)](https://github.com/mikiships/agentkit-cli)
```

For CI or scripting, use `--json`:

```bash
agentkit badge --json
# {"score": 87, "color": "green", "badge_url": "...", "markdown": "...", "html": "..."}
```

To use a fixed score (e.g. from a gating check):

```bash
agentkit badge --score 87
```

**Color thresholds:** green ≥80 · yellow 60-79 · orange 40-59 · red <40

---

## Quality Trend Tracking

Every `agentkit run` automatically records scores to a local SQLite database (`~/.config/agentkit/history.db`). Use `agentkit history` to view your quality trend over time.

```bash
# Show last 10 runs for current project (Rich table with trend arrows)
agentkit history

# Filter to one tool
agentkit history --tool agentlint

# Show ASCII sparkline of last 10 overall scores
agentkit history --graph

# Machine-readable output
agentkit history --json

# Cross-project summary
agentkit history --all-projects

# Clear history for current project
agentkit history --clear

# Skip recording during a run
agentkit run --no-history
```

**GitHub Actions**: set `save-history: true` in the action to emit a `history.json` artifact:

```yaml
- uses: mikiships/agentkit-cli@main
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    save-history: 'true'

- uses: actions/upload-artifact@v4
  with:
    name: agentkit-history
    path: history.json
```

## Agent Leaderboard

Tag runs with `--label` to compare models, configs, or agents head-to-head over time. The leaderboard groups all runs by label and ranks them by average score.

```bash
# Tag runs with a label
agentkit run --label gpt-4
agentkit run --label claude-sonnet
agentkit run --label codex

# Show ranked leaderboard (Rich table)
agentkit leaderboard

# Rank by a specific tool dimension
agentkit leaderboard --by agentlint

# Filter to a specific project
agentkit leaderboard --project myproject

# Only use last N runs per label (recency bias)
agentkit leaderboard --last 5

# Filter by recency
agentkit leaderboard --since 7d
agentkit leaderboard --since 2026-01-01

# Machine-readable output
agentkit leaderboard --json
```

Example output:
```
Agent Quality Leaderboard ─────────────────────────────────
 Rank  Label          Runs  Avg Score  Trend   Best   Worst
  1    gpt-4          12    87.3       ↑+3.1   92.0   79.0
  2    claude-sonnet  8     83.1       →       89.0   75.0
  3    codex          5     71.4       ↓-2.0   78.0   61.0
─────────────────────────────────────────────────────────────
```

**GitHub Actions**: set `save-history: true` to also emit a `leaderboard-json` output:

```yaml
- uses: mikiships/agentkit-cli@main
  id: agentkit
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    save-history: 'true'

- name: Print leaderboard
  run: echo '${{ steps.agentkit.outputs.leaderboard-json }}'
```

## Notifications

Send gate results to Slack, Discord, or any webhook — no extra dependencies required.

### Slack

```bash
agentkit gate --min-score 80 --notify-slack https://hooks.slack.com/services/T.../B.../...
```

Posts a color-coded Slack attachment (green on pass, red on fail) with score, verdict, and top findings.

### Discord

```bash
agentkit gate --min-score 80 --notify-discord https://discord.com/api/webhooks/.../.../
```

Posts a color-coded Discord embed.

### Generic Webhook

```bash
agentkit gate --notify-webhook https://your-service.com/hook
```

Posts a JSON payload: `{project, score, verdict, top_findings, timestamp, delta}`.

### Control When Notifications Fire

```bash
# Only notify on failure (default)
agentkit gate --notify-slack $SLACK_URL --notify-on fail

# Notify on every run
agentkit gate --notify-slack $SLACK_URL --notify-on always
```

### Environment Variables

```bash
export AGENTKIT_NOTIFY_SLACK=https://hooks.slack.com/services/...
export AGENTKIT_NOTIFY_DISCORD=https://discord.com/api/webhooks/...
export AGENTKIT_NOTIFY_WEBHOOK=https://your-service.com/hook
export AGENTKIT_NOTIFY_ON=fail  # or always

agentkit gate --min-score 80  # picks up env vars automatically
```

### Test Connectivity

```bash
agentkit notify test --slack https://hooks.slack.com/services/...
# ✓ Notification delivered

agentkit notify test --discord https://discord.com/api/webhooks/...
agentkit notify test --webhook https://your-service.com/hook
```

### Show Current Config

```bash
agentkit notify config
```

### GitHub Actions

```yaml
- uses: mikiships/agentkit-cli@v0.21.0
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    min-lint-score: 80
    notify-slack: ${{ secrets.SLACK_WEBHOOK }}
    notify-on: fail
```

> **Note:** Notification failures never affect the gate exit code. If the webhook is unreachable, agentkit logs a warning and continues normally.

## Links

- [agentmd](https://pypi.org/project/agentmd/)
- [agentlint](https://pypi.org/project/agentlint/)
- [coderace](https://pypi.org/project/coderace/)
- [agentreflect](https://pypi.org/project/agentreflect/)

---

## License

MIT
