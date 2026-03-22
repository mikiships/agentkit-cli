# agentkit weekly

Generate a 7-day quality digest across all tracked projects from your agentkit history database.

## Usage

```bash
agentkit weekly [OPTIONS]
```

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--days N` | `7` | Number of days to look back |
| `--project NAME` | all | Filter to specific project(s) (repeatable) |
| `--json` | false | Output structured JSON instead of rich table |
| `--output FILE` | — | Save HTML report to file |
| `--share` | false | Publish HTML to here.now and print URL |
| `--tweet-only` | false | Print tweet-ready summary and exit |
| `--quiet` | false | Suppress rich output (cron-friendly) |

## Examples

```bash
# Show weekly digest for all tracked projects
agentkit weekly

# JSON output for scripting
agentkit weekly --json

# Save HTML report
agentkit weekly --output weekly-report.html

# Print tweet-ready text only (useful for automation)
agentkit weekly --tweet-only

# Look back 14 days
agentkit weekly --days 14

# Filter to specific projects
agentkit weekly --project myrepo --project another-repo

# Share online
agentkit weekly --share
```

## Output

The weekly command produces:

- **Project Score Changes** — table of per-project score start/end/delta
- **Top Improvements** — projects that improved the most
- **Regressions** — projects that declined
- **Common Findings** — issues appearing across multiple repos
- **Top Recommended Actions** — most frequent actionable findings
- **Tweet-Ready Summary** — ≤280 char summary for social sharing

## Automation with post-weekly.sh

The `scripts/post-weekly.sh` script wraps the CLI for cron use:

```bash
# Basic: print tweet text + log
./scripts/post-weekly.sh

# Tweet only (no log)
./scripts/post-weekly.sh --tweet-only

# Upload HTML and log share URL
./scripts/post-weekly.sh --share

# Look back 14 days and save HTML
./scripts/post-weekly.sh --days 14 --output /tmp/weekly.html
```

The script **does not** call frigatebird or any tweet API. It logs to
`~/.local/share/agentkit/weekly-post-log.jsonl` and prints the tweet text
to stdout for you to pipe to your preferred posting tool.

## Data Source

`agentkit weekly` reads from the history DB (`~/.config/agentkit/history.db`),
the same SQLite database used by `agentkit history`, `agentkit insights`, and
`agentkit digest`. Run `agentkit run` or `agentkit analyze` to populate it.
