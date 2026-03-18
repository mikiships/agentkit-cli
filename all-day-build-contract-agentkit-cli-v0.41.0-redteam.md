# All-Day Build Contract: agentkit redteam

Status: In Progress  
Date: 2026-03-17  
Owner: Codex execution pass  
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Build `agentkit redteam` — an adversarial eval command that generates malicious / edge-case inputs against a project's agent setup and scores how well its context files and instructions hold up. This directly targets the Promptfoo white-space: teams who were relying on Promptfoo (now OpenAI-owned) need a neutral, model-agnostic red-team tool.

The enterprise pain is now publicly quantified: 91% of orgs discover what an agent did *after execution*, only 7% have real-time governance. `agentkit redteam` gives developers a pre-execution adversarial check — run it in CI, fail the gate before anything ships.

This contract is considered complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Full test suite must pass at the end (`python3 -m pytest -q`).
4. New features must ship with docs and report addendum updates in the same pass.
5. CLI outputs must be deterministic and schema-backed where specified.
6. Never modify files outside the project directory.
7. Commit after each completed deliverable (not at the end).
8. If stuck on same issue for 3 attempts, stop and write a blocker report.
9. Do NOT refactor, restyle, or "improve" code outside the deliverables.
10. Read existing tests and docs before writing new code.

## 3. Feature Deliverables

### D1. Core RedTeamEngine + attack generation

Build `agentkit_cli/redteam_engine.py`:

- `AttackCategory` enum: `PROMPT_INJECTION`, `JAILBREAK`, `CONTEXT_CONFUSION`, `INSTRUCTION_OVERRIDE`, `DATA_EXTRACTION`, `ROLE_ESCALATION`
- `RedTeamEngine.generate_attacks(context_file_path, n_per_category=3)` → `List[Attack]`
  - Reads the CLAUDE.md / AGENTS.md at the given path
  - For each category, generates synthetic adversarial inputs using a simple template library (no LLM required for generation — deterministic templates + parameterization)
  - Templates use actual content from the context file to make attacks more targeted
- `Attack` dataclass: `{id, category, input_text, description, expected_behavior}`
- Write at least 6 templates per category (36 total minimum)
- No external API calls in the engine itself

Required files:
- `agentkit_cli/redteam_engine.py`
- `agentkit_cli/attack_templates/` directory with template definitions (JSON or Python constants)

- [ ] RedTeamEngine class + generate_attacks()
- [ ] AttackCategory enum, Attack dataclass
- [ ] ≥36 templates across 6 categories
- [ ] Templates are parameterizable from context file content
- [ ] Unit tests for template generation

### D2. RedTeamScorer — evaluate attack resistance

Build `agentkit_cli/redteam_scorer.py`:

- `RedTeamScorer.score_resistance(context_file_path)` → `RedTeamReport`
  - Uses agentlint check-context (already available) to detect known vulnerability patterns in the context file
  - Checks for: missing safety boundaries, overly permissive capability grants, unclear principal hierarchy, no refusal instructions, instructions that invite role escalation
  - Produces a resistance score 0-100 per category and an overall composite
- `RedTeamReport` dataclass: `{path, score_overall, score_by_category, findings, attack_samples, recommendations}`
- Scoring is **static analysis only** (no LLM calls for scoring) — this is the neutral/model-agnostic guarantee
- Recommendations are actionable strings: "Add an explicit refusal instruction for X"

Required files:
- `agentkit_cli/redteam_scorer.py`

- [ ] RedTeamScorer with static-analysis scoring
- [ ] RedTeamReport dataclass with all fields
- [ ] Score-by-category breakdown
- [ ] Recommendations engine (rule-based, not LLM)
- [ ] Unit tests for scorer

### D3. `agentkit redteam` CLI command

Wire up the CLI at `agentkit_cli/commands/redteam_cmd.py`:

Usage: `agentkit redteam [PATH] [OPTIONS]`

Options:
- `PATH`: project directory to analyze (default: `.`)
- `--categories`: comma-separated list of categories to test (default: all)
- `--attacks-per-category N`: how many attack samples to generate (default: 3)
- `--json`: JSON output
- `--share`: upload HTML report to here.now (reuse existing publish logic)
- `--min-score N`: exit 1 if overall score < N (CI gate integration)
- `--output FILE`: save report to file

Display:
- Rich table showing score per category with color coding (≥80 green, 50-79 yellow, <50 red)
- Sample attacks shown (one per category, truncated to 120 chars)
- Top 3 recommendations with fix suggestions
- Overall resistance grade (A/B/C/D/F)

Required files:
- `agentkit_cli/commands/redteam_cmd.py`
- Wire into `agentkit_cli/main.py` (add `redteam` command)

- [ ] CLI command wired and registered
- [ ] Rich output with color-coded table
- [ ] --json output (stable schema)
- [ ] --share uploads HTML report
- [ ] --min-score gate (exit 1)
- [ ] Unit tests for CLI invocation

### D4. Dark-theme HTML report

Build `agentkit_cli/redteam_report.py`:

Generates an HTML report (same dark-theme style as existing reports):
- Header: project name, overall score, grade badge
- Score breakdown: category cards with progress bars
- Attack samples section: collapsible cards showing 1-2 examples per category
- Recommendations: numbered list with copy-paste fix snippets
- Footer: "Generated by agentkit-cli v{version}" + timestamp

The report must be self-contained (no external CSS/JS dependencies).

Required files:
- `agentkit_cli/redteam_report.py`

- [ ] HTML report generator
- [ ] Dark theme consistent with existing reports
- [ ] Attack samples shown (collapsible or truncated)
- [ ] Recommendations section
- [ ] here.now upload via existing `publish.publish_html()`
- [ ] Unit tests for report generation

### D5. Docs, version bump, BUILD-REPORT

- Update `README.md`: add `agentkit redteam` to the commands table and add a "Red-Team Your Agent Setup" section
- Update `CHANGELOG.md` with v0.41.0 entry
- Bump version to `0.41.0` in `pyproject.toml` and `agentkit_cli/__init__.py`
- Write `BUILD-REPORT-v0.41.0.md` summarizing: deliverables completed, tests before/after, architecture decisions, sample output
- Integrate into `agentkit_cli/commands/run_cmd.py`: add optional redteam step with `--redteam` flag on `agentkit run`
- Update `agentkit_cli/commands/score_cmd.py`: if redteam score is available, include in composite

- [ ] README updated (table + section)
- [ ] CHANGELOG entry for v0.41.0
- [ ] Version bumped in both files
- [ ] BUILD-REPORT-v0.41.0.md written
- [ ] `agentkit run --redteam` flag added
- [ ] `agentkit score` uses redteam if available
- [ ] Full test suite passing (1584 baseline + ≥45 new tests)

## 4. Test Requirements

- [ ] Unit tests for RedTeamEngine (template generation, parameterization)
- [ ] Unit tests for RedTeamScorer (known-vulnerable and known-safe fixtures)
- [ ] Integration test: `agentkit redteam .` on the agentkit-cli repo itself
- [ ] CLI tests: all flags, --json schema, --min-score gate exit codes
- [ ] HTML report test: output is valid HTML, contains expected sections
- [ ] All existing 1584 tests must still pass

Minimum new tests: 45

## 5. Reports

- Write progress to `redteam-progress-log.md` after each deliverable
- Include: what was built, test counts, what's next, blockers
- Final summary in BUILD-REPORT-v0.41.0.md

## 6. Stop Conditions

- All deliverables checked and all tests passing → DONE
- 3 consecutive failed attempts on same issue → STOP, write blocker report
- Scope creep detected → STOP, report what's new
- If agentlint integration fails for any reason, fall back to pure template/pattern analysis (no agentlint dependency in scoring critical path)

## 7. Distribution Angle

This is the key narrative shift after the Promptfoo acquisition ($86M, OpenAI):
- Teams using non-OpenAI models now need a **neutral** red-team tool
- Static analysis = no model dependency = truly model-agnostic
- One command: `agentkit redteam github:owner/repo` — adversarial eval of any public repo's agent setup
- CI gate: `agentkit redteam --min-score 70` fails the build before unsafe agent configs ship

Show HN hook (update show-hn-quartet.md after this ships):
"After OpenAI acquired Promptfoo, I added a model-agnostic red-team command to agentkit-cli. No LLM required for scoring — just static analysis of your context files."

## 8. Architecture Constraints

- RedTeamEngine: no LLM calls, pure Python, deterministic output
- RedTeamScorer: static analysis only, builds on agentlint output where possible
- RedTeamReport: reuse existing `publish.publish_html()` — do not reinvent
- All new code follows existing patterns in `agentkit_cli/commands/` and uses existing `ToolAdapter` where applicable
