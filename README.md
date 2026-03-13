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

Diagnose whether all quartet tools are installed and functional.

```bash
agentkit doctor
agentkit doctor --json
```

Outputs a Rich table with ✓/✗ per tool, version, and install command. Exits 1 if any tool is missing.

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

## Links

- [agentmd](https://pypi.org/project/agentmd/)
- [agentlint](https://pypi.org/project/agentlint/)
- [coderace](https://pypi.org/project/coderace/)
- [agentreflect](https://pypi.org/project/agentreflect/)

---

## License

MIT
