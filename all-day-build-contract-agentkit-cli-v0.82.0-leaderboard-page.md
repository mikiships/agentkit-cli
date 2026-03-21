# Build Contract: agentkit-cli v0.82.0 — `agentkit leaderboard-page`

**Date:** 2026-03-21
**Owner:** builder sub-agent
**Baseline:** v0.81.1 — 4039 tests passing

## Objective

Add `agentkit leaderboard-page` command: generate a public, auto-updating HTML leaderboard page showing the top agent-ready GitHub repos by language ecosystem. The page is designed to be self-hosted on GitHub Pages and serves as an always-on organic discovery surface — indexed by search engines, linked from repo READMEs, and shareable.

This is a distribution play, not a feature play. The page exists to get agentkit-cli discovered by developers searching for "best AI-agent-ready Python repos" or similar queries.

## Deliverables

### D1: `agentkit leaderboard-page` command (≥20 tests)

- Fetch top repos for 5 default ecosystems: python, typescript, rust, go, javascript
- Score each via ExistingStateScorer (use `agentkit topic` internally for repo discovery)
- Generate a static HTML page with:
  - Headline: "Most AI-Agent-Ready Open Source Projects"
  - Ecosystem tabs (Python | TypeScript | Rust | Go | JavaScript)
  - Per-ecosystem top-10 ranked table: repo name, score, grade, stars, link
  - "Last updated" timestamp
  - Powered by agentkit-cli badge (links to PyPI)
- `--output <path>`: write HTML to file (default: `leaderboard.html`)
- `--ecosystems <csv>`: override default ecosystems
- `--limit N`: repos per ecosystem (default 10, max 25)
- `--share`: upload to here.now
- `--json`: structured output with all scores
- Must use ExistingStateScorer (same no-circular pattern as hot/daily-duel)

### D2: GitHub Pages auto-update workflow (≥10 tests)

- `.github/workflows/update-leaderboard.yml`: scheduled workflow (weekly) that runs `agentkit leaderboard-page --output docs/leaderboard.html` and commits the result
- The leaderboard page lives at `docs/leaderboard.html` in the repo
- Workflow uses: `actions/checkout@v4`, `actions/setup-python@v4`, `pip install agentkit-cli`, run command, `git commit --allow-empty`
- `--pages`: flag that writes directly to `docs/leaderboard.html` in cwd (for GitHub Pages path)

### D3: SEO optimizations in generated HTML (≥8 tests)

- `<title>`: "Most AI-Agent-Ready [Ecosystem] Repos — agentkit-cli Leaderboard"
- `<meta description>`: "Track which open source Python/TypeScript/etc repos have the best AI agent context, documentation, and test coverage."
- `<meta og:*>` tags for sharing
- Semantic HTML: `<table>` with `<caption>`, `<thead>`, `<tbody>`, proper `aria-label`
- JSON-LD structured data: `ItemList` schema for top repos
- Tests: verify title contains ecosystem, meta description exists, og tags present, JSON-LD is valid JSON

### D4: `agentkit leaderboard-page --embed` badge+widget (≥8 tests)

- `--embed github:owner/repo`: generate embeddable markdown for a specific repo's leaderboard position
- Output: markdown snippet with shields.io badge showing rank + score
- Example: `![Agent Rank](https://img.shields.io/badge/agent--rank-%231%20Python-green) Score: 94/100 · [View Leaderboard](https://mikiships.github.io/agentkit-cli/leaderboard.html)`
- `--embed-only`: just output the markdown, no full page generation

### D5: Docs, CHANGELOG, version bump, BUILD-REPORT (≥5 tests)

- README: new "Leaderboard" section with GitHub Pages link and cron usage example
- CHANGELOG: v0.82.0 entry
- `__version__` = "0.82.0" in `agentkit_cli/__init__.py`
- BUILD-REPORT.md + BUILD-REPORT-v0.82.0.md in repo root
- pyproject.toml version = "0.82.0"

## Target test count

4039 baseline + ≥51 new = ≥4090 total

## Stop conditions

- STOP if ExistingStateScorer or topic engine is not importable — check the actual import path
- STOP if GitHub API calls are needed (should use existing topic/ecosystem infrastructure, not new auth)
- DO NOT run agentmd generate before scoring (circular scoring issue)
- DO NOT publish to PyPI — build-loop handles publish
- DO NOT push to GitHub — build-loop handles push
- DO NOT create any new GitHub workflows in the actual repo that would auto-run on CI

## Technical notes

- ExistingStateScorer: `from agentkit_cli.existing_scorer import ExistingStateScorer`, use `score_all()['composite']`
- Ecosystem → GitHub topic mapping: python→python, typescript→typescript, rust→rust, go→go, javascript→javascript
- Reuse `agentkit_cli/topic.py` TopicEngine if it exists, otherwise use GitHub Search API (no auth needed for public repos)
- Keep HTTP calls mocked in tests — DO NOT make real GitHub API calls in tests
- HTML should be dark-theme (#0d1117) matching other agentkit HTML reports for brand consistency

## Definition of done

- `pytest -q` passes at or above target count
- `agentkit leaderboard-page --output /tmp/test-leaderboard.html` completes without error
- Generated HTML has correct title, meta tags, and at least one ecosystem tab
- `agentkit leaderboard-page --embed github:psf/requests` outputs a valid markdown badge snippet
- All files committed to git (do not push)
- BUILD-REPORT.md written
