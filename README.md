# agentkit-cli

**One install to rule them all.**

```bash
pip install agentkit-cli
```

Get the full Agent Quality Toolkit pipeline in a single command — no more juggling four separate `pip install` steps.

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

## Links

- [agentmd](https://pypi.org/project/agentmd/)
- [agentlint](https://pypi.org/project/agentlint/)
- [coderace](https://pypi.org/project/coderace/)
- [agentreflect](https://pypi.org/project/agentreflect/)

---

## License

MIT
