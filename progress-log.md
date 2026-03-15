# Progress Log — agentkit-cli v0.23.0 profiles

## Session: 2026-03-15

### D1: Profile engine + bundled presets ✅

- Created `agentkit_cli/profiles.py`
- `ProfileDefinition` dataclass with all required fields
- `ProfileRegistry` with built-in presets: strict (85/3/fail), balanced (70/10/never), minimal (50/20/never)
- `apply_profile()` with CLI flag precedence (cli_min_score/cli_max_drop params)
- User profiles loaded from `~/.agentkit/profiles/*.toml`
- Case-insensitive lookup
- `tests/test_profiles.py` — 40 tests, all passing

### D2: `agentkit profile` command ✅

- Created `agentkit_cli/commands/profile_cmd.py`
- `profile list` — Rich table with all profiles
- `profile show <name>` — key-value table
- `profile create <name> [--from <base>]` — writes to `~/.agentkit/profiles/`
- `profile use <name>` — writes `profile.active` to `.agentkit.toml`
- `profile export <name> [--format toml|json]`
- Wired into `main.py` as `agentkit profile`
- `tests/test_profile_command.py` — 19 tests, all passing

### D3: `--profile` flag in 5 commands ✅

- Added `--profile` to gate, run, sweep, score, analyze in `main.py` and each command file
- Profile name shown in gate Rich output ("Profile: strict")
- Explicit CLI flags override profile values
- Invalid profile exits with code 2
- `tests/test_profile_integration.py` — 16 tests, all passing

### D4: Docs, CHANGELOG, version bump ✅

- `README.md` created with Profiles section (after Config section)
- `CHANGELOG.md` v0.23.0 entry added
- Version bumped: 0.22.0 → 0.23.0 in `pyproject.toml` + `__init__.py`
- `BUILD-REPORT.md` updated with v0.23.0 summary
- Fixed pre-existing test_action.py failure (README.md was missing)
- Fixed version assertions in test_main.py and test_leaderboard.py

## Final Test Results

```
892 passed in 14.49s
0 failed
```

## Commits

1. `feat(profiles): D1 - ProfileDefinition, ProfileRegistry, built-in presets, apply_profile`
2. `feat(profiles): D2 - agentkit profile list/show/create/use/export command`
3. `feat(profiles): D3 - --profile flag wired into gate, run, sweep, score, analyze`
4. `chore(release): v0.23.0 - docs, CHANGELOG, version bump`
5. `fix(tests): update version assertions to 0.23.0, add GitHub Action section to README`

## Notes

- All 4 deliverables complete
- 75 new tests across test_profiles.py (40), test_profile_command.py (19), test_profile_integration.py (16)
- Pre-existing test_action.py failure resolved (README.md now exists)
- Did NOT publish to PyPI
