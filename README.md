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

## Links

- [agentmd](https://pypi.org/project/agentmd/)
- [agentlint](https://pypi.org/project/agentlint/)
- [coderace](https://pypi.org/project/coderace/)
- [agentreflect](https://pypi.org/project/agentreflect/)

---

## License

MIT
