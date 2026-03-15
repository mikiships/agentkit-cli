# All-Day Build Contract: agentkit profiles (v0.23.0)

Status: In Progress
Date: 2026-03-15
Owner: Codex execution pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Add a **quality profiles** system to agentkit-cli. Profiles are named presets for gate thresholds, notify config, and sweep targets. Three bundled presets (`strict`, `balanced`, `minimal`) let users configure agentkit in one command instead of manually tuning every threshold. Profiles are stored in `.agentkit.toml` and can be created, listed, switched, and exported.

This completes the config system shipped in v0.22.0 by adding the "profile" layer on top of raw key/value config.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Full test suite must pass at the end.
4. New features must ship with docs and report addendum updates in the same pass.
5. CLI outputs must be deterministic and schema-backed where specified.
6. Never modify files outside the project directory (`~/repos/agentkit-cli/`).
7. Commit after each completed deliverable (not at the end).
8. If stuck on same issue for 3 attempts, stop and write a blocker report.
9. Do NOT refactor, restyle, or "improve" code outside the deliverables.
10. Read existing tests and docs before writing new code.

## 3. Feature Deliverables

### D1. Profile engine + bundled presets (`agentkit_cli/profiles.py`)

Build the profile system:

- `ProfileDefinition` dataclass: name, description, config keys (gate thresholds, notify webhook, sweep targets, etc.)
- `ProfileRegistry`: stores built-in presets + user-defined profiles (read from `~/.agentkit/profiles/` TOML files)
- Three built-in presets:
  - `strict`: min-score 85, max-drop 3, notify on failure
  - `balanced` (default): min-score 70, max-drop 10, notify off
  - `minimal`: min-score 50, max-drop 20, gate disabled
- `apply_profile(name, config)` — merges profile values into AgentKitConfig (CLI flags > profile > project config > user config > defaults)
- Profile precedence: explicit CLI flags always win; profile fills gaps

Required files:
- `agentkit_cli/profiles.py`
- Tests in `tests/test_profiles.py` (unit tests, 20+ tests)

- [ ] ProfileDefinition dataclass
- [ ] ProfileRegistry with built-in presets
- [ ] apply_profile() merges into config correctly
- [ ] User-defined profile loading from ~/.agentkit/profiles/*.toml
- [ ] Profile lookup is case-insensitive
- [ ] Tests for D1

### D2. `agentkit profile` command (list/show/create/use/export)

New top-level command:

```
agentkit profile list                           # list all profiles (built-in + user)
agentkit profile show <name>                    # show profile config details
agentkit profile create <name> [--from <base>] # create new profile (optionally inheriting from base)
agentkit profile use <name>                     # set active profile in .agentkit.toml
agentkit profile export <name> [--format toml|json]  # print profile as TOML or JSON
```

Rich table output for `list`. Key-value table for `show`. `use` updates `[profile]` section in `.agentkit.toml` (calls existing `config.py` write logic).

Required files:
- `agentkit_cli/commands/profile.py`
- Wire into `agentkit_cli/cli.py` as `agentkit profile <sub>`
- Tests in `tests/test_profile_command.py` (15+ tests)

- [ ] `agentkit profile list` with Rich table
- [ ] `agentkit profile show <name>` with key-value table
- [ ] `agentkit profile create <name> [--from <base>]`
- [ ] `agentkit profile use <name>` writes to .agentkit.toml
- [ ] `agentkit profile export <name>` TOML/JSON output
- [ ] Help text for all subcommands
- [ ] Tests for D2

### D3. Wire `--profile` flag into gate, run, sweep, score, analyze

Add `--profile <name>` flag to the 5 main commands. When provided:
1. Load the named profile
2. Apply profile config values (fills gaps not covered by explicit CLI flags)
3. Show profile name in Rich output (e.g., "Profile: strict" in gate header)

Any explicit CLI flag (e.g., `--min-score 90`) overrides the profile value for that key.

Required files:
- Modify `agentkit_cli/commands/gate.py`, `run.py`, `sweep.py`, `score.py`, `analyze.py`
- Tests in `tests/test_profile_integration.py` (15+ tests)

- [ ] `--profile` flag added to gate
- [ ] `--profile` flag added to run
- [ ] `--profile` flag added to sweep
- [ ] `--profile` flag added to score
- [ ] `--profile` flag added to analyze
- [ ] Profile name shown in command output
- [ ] Explicit flags override profile values
- [ ] Tests for D3

### D4. Docs, CHANGELOG, version bump, BUILD-REPORT

- README: add "Profiles" section (after Config section). Show `agentkit profile use strict` one-liner, table of built-in presets.
- CHANGELOG.md: v0.23.0 entry with all new features
- pyproject.toml: bump version 0.22.0 → 0.23.0
- `agentkit_cli/__init__.py`: bump version
- `BUILD-REPORT.md`: update with v0.23.0 summary

- [ ] README Profiles section (after Config section)
- [ ] CHANGELOG v0.23.0 entry
- [ ] Version bumped to 0.23.0 in pyproject.toml + __init__.py
- [ ] BUILD-REPORT.md updated
- [ ] All tests pass (`python3 -m pytest -q`)

## 4. Test Requirements

- [ ] 40+ new tests across test_profiles.py, test_profile_command.py, test_profile_integration.py
- [ ] All existing 817 tests still pass
- [ ] Profile apply logic tested with partial overrides (CLI flag wins)
- [ ] `agentkit profile use` round-trips correctly (write then read back)
- [ ] Built-in preset values are stable (regression test: don't change preset values without updating tests)

## 5. Reports

- Write progress to `progress-log.md` after each deliverable
- Include: what was built, what tests pass, what's next, any blockers
- Final summary when all deliverables done or stopped

## 6. Stop Conditions

- All deliverables checked and all tests passing → DONE
- 3 consecutive failed attempts on same issue → STOP, write blocker report
- Scope creep detected → STOP, report what's new
- Do NOT publish to PyPI — build-loop handles release

## 7. Success Criteria

```
agentkit profile list                    # shows strict, balanced, minimal + any user profiles
agentkit profile use strict              # writes [profile] active = "strict" to .agentkit.toml
agentkit gate --profile strict           # gates with strict thresholds, shows "Profile: strict"
agentkit run --profile balanced          # runs with balanced defaults
python3 -m pytest -q                     # 850+ tests, 0 failures
```
