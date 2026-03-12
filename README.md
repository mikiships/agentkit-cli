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

## Links

- [agentmd](https://pypi.org/project/agentmd/)
- [agentlint](https://pypi.org/project/agentlint/)
- [coderace](https://pypi.org/project/coderace/)
- [agentreflect](https://pypi.org/project/agentreflect/)

---

## License

MIT
