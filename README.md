# agentkit-cli

Unified CLI for the Agent Quality Toolkit (agentmd, coderace, agentlint, agentreflect).

## Installation

```bash
pip install agentkit-cli
```

## Quick Start

```bash
agentkit run           # run the full pipeline
agentkit score         # compute composite score
agentkit gate          # fail if score < threshold
```

## Configuration

agentkit uses `.agentkit.toml` for project-level configuration.

```bash
agentkit config init       # create .agentkit.toml with defaults
agentkit config show       # show effective config with sources
agentkit config set gate.min_score 80
agentkit config get gate.min_score
```

### Config Precedence

`CLI flags > env vars > project .agentkit.toml > user config > defaults`

## Profiles

Profiles are named presets for gate thresholds, notify config, and sweep targets.
Switch your entire quality policy in one command.

### Built-in Presets

| Profile | Min Score | Max Drop | Notify On | Gate |
|---------|-----------|----------|-----------|------|
| `strict` | 85 | 3 | fail | enabled |
| `balanced` | 70 | 10 | never | enabled |
| `minimal` | 50 | 20 | never | disabled |

### Usage

```bash
# Switch to strict quality standards
agentkit profile use strict

# List all profiles (built-in + user-defined)
agentkit profile list

# Show profile details
agentkit profile show strict

# Run gate with a specific profile
agentkit gate --profile strict

# Create a custom profile based on strict
agentkit profile create myprofile --from strict --min-score 90

# Export a profile as JSON or TOML
agentkit profile export strict --format json
```

### Using Profiles with Commands

All major commands support `--profile`:

```bash
agentkit gate --profile strict
agentkit run --profile balanced
agentkit sweep --profile minimal owner/repo1 owner/repo2
agentkit score --profile balanced
agentkit analyze --profile strict github:owner/repo
```

Explicit CLI flags always override profile values:
```bash
# Uses strict profile but overrides min-score to 99
agentkit gate --profile strict --min-score 99
```

## Commands

- `agentkit run` — run the full pipeline
- `agentkit score` — compute composite score
- `agentkit gate` — fail if score < threshold
- `agentkit analyze <target>` — analyze any GitHub repo
- `agentkit sweep <targets>` — batch analyze multiple repos
- `agentkit duel <repo1> <repo2>` — head-to-head agent-readiness comparison
- `agentkit tournament <repo1> ... <repoN>` — round-robin bracket across 4-16 repos
- `agentkit profile <sub>` — manage quality profiles
- `agentkit config <sub>` — manage configuration
- `agentkit history` — show score history
- `agentkit leaderboard` — compare runs by label
- `agentkit insights` — cross-repo pattern synthesis
- `agentkit trending` — fetch and rank trending GitHub repos by agent quality

## Trending Analysis

`agentkit trending` answers: "Which repos blowing up on GitHub are most AI-agent-ready today?"

```bash
# Rank this week's trending AI repos (default)
agentkit trending

# Fast mode: list repos without scoring
agentkit trending --no-analyze

# Filter by topic, publish a shareable report
agentkit trending --topic ai-agent --share

# Weekly trending, top 15, min 500 stars, JSON output
agentkit trending --period week --limit 15 --min-stars 500 --json

# Use a GitHub token for higher rate limits
agentkit trending --token ghp_xxx
```

Output: a ranked Rich table (Rank | Repo | Stars | Score | Grade | URL) and optionally a dark-theme HTML report published to here.now.

## Tournament

`agentkit tournament` runs a round-robin bracket across 4-16 repos and ranks them by win/loss record with avg score tiebreak.

```bash
# Run a 4-repo tournament
agentkit tournament github:fastapi/fastapi github:tiangolo/starlette github:django/django github:pallets/flask

# Publish a shareable HTML bracket report
agentkit tournament github:fastapi/fastapi github:tiangolo/starlette github:django/django github:pallets/flask --share

# JSON output for CI/scripting
agentkit tournament github:fastapi/fastapi github:tiangolo/starlette github:django/django github:pallets/flask --json

# Sequential (no parallel), quiet mode, save HTML
agentkit tournament github:fastapi/fastapi github:tiangolo/starlette github:django/django github:pallets/flask \
  --no-parallel --quiet --output bracket.html
```

Output: standings table (Rank | Repo | W-L | Avg Score | Grade), match results matrix, and winner banner. Use `--share` to publish a dark-theme HTML bracket to here.now.

## Portfolio Insights

Once you've analyzed multiple repos with `agentkit analyze` or `agentkit run`, the
`agentkit insights` command synthesizes patterns across all historical runs:

```bash
# Portfolio health summary (avg score, best/worst repo, top issue)
agentkit insights

# Most common agentlint findings across all repos
agentkit insights --common-findings

# Repos scoring in the bottom quartile
agentkit insights --outliers

# Repos with significant score movement between runs
agentkit insights --trending

# All sections in one view
agentkit insights --all

# Machine-readable JSON (useful for scripts/dashboards)
agentkit insights --json

# Use a specific history DB
agentkit insights --db /path/to/history.db
```

Store agentlint findings alongside scores for richer cross-repo analysis:

```bash
agentkit run --record-findings
agentkit analyze github:owner/repo --record-findings
```

**JSON output schema:**

```json
{
  "portfolio_summary": {
    "avg_score": 74.5,
    "total_runs": 12,
    "unique_repos": 4,
    "top_issue": "missing-tools-section",
    "best_repo": "owner/repo-a",
    "worst_repo": "owner/repo-d"
  },
  "common_findings": [
    {"finding": "missing-tools-section", "repo_count": 3, "total_occurrences": 5}
  ],
  "outliers": [
    {"project": "owner/repo-d", "latest_score": 42.0, "avg_score": 48.5, "run_count": 2}
  ],
  "trending": [
    {"project": "owner/repo-b", "previous_score": 55.0, "latest_score": 80.0, "delta": 25.0, "direction": "up"}
  ]
}
```

## Sharing Results

Share your agent quality score card with a single command:

```bash
# Generate and upload a score card to here.now
agentkit share

# Share from a saved JSON report
agentkit share --report agentkit-report.json

# Hide raw numbers (show pass/fail only)
agentkit share --no-scores

# Output JSON with URL and score
agentkit share --json

# Auto-share after a run
agentkit run --share

# Auto-share after generating a report
agentkit report --share

# Analyze a GitHub repo and share the score card in one command
agentkit analyze github:owner/repo --share

# Batch analyze repos and share a combined scorecard
agentkit sweep github:owner/repo1 github:owner/repo2 --share
```

Score cards are standalone HTML pages (dark theme) showing: composite score, per-tool breakdown, project name, git ref, and timestamp. Anonymous cards expire in 24h; set `HERENOW_API_KEY` for persistent links.

## GitHub Actions

Use the agentkit GitHub Action to run quality checks on every PR:

```yaml
- uses: mikiships/agentkit-cli@v0.7.0
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    min-score: 70
```

Or install and run directly:

```yaml
- uses: actions/checkout@v4
- run: pip install agentkit-cli
- run: agentkit gate --profile strict
```

See `agentkit setup-ci` for automated workflow generation.

## Release Check

`agentkit release-check` verifies the 4-part release surface to confirm a package is truly shipped, not just locally complete:

```
agentkit release-check [PATH] [OPTIONS]

Options:
  --version VERSION   Version to verify (default: from pyproject.toml/package.json)
  --package NAME      Package name (default: from pyproject.toml/package.json)
  --registry          pypi|npm|auto (default: auto-detected)
  --skip-tests        Skip the pytest/npm test step for quick checks
  --json              Output structured JSON for CI integration
```

Example output:

```
agentkit release-check — /your/project

┌────────────┬────────┬─────────────────────────────────┐
│ Check      │ Status │ Detail                          │
├────────────┼────────┼─────────────────────────────────┤
│ tests      │ ✓ PASS │ 42 passed in 1.23s              │
│ git_push   │ ✓ PASS │ Local HEAD abc12345 matches rem │
│ git_tag    │ ✓ PASS │ Tag v1.0.0 found on remote.     │
│ registry   │ ✓ PASS │ PyPI: mypkg==1.0.0 is live.    │
└────────────┴────────┴─────────────────────────────────┘

Verdict: SHIPPED
```

Verdict levels:
- **SHIPPED** — all 4 surfaces confirmed (exit 0)
- **RELEASE-READY** — tests + git confirmed, registry not yet live (exit 1)
- **BUILT** — tests pass locally, not yet pushed (exit 1)
- **UNKNOWN** — tests failing (exit 1)

Integrate with `agentkit gate --release-check` or `agentkit run --release-check` to add release verification to your pipeline.

## License

MIT
