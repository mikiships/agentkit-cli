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
- `agentkit profile <sub>` — manage quality profiles
- `agentkit config <sub>` — manage configuration
- `agentkit history` — show score history
- `agentkit leaderboard` — compare runs by label

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

## License

MIT
