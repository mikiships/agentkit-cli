# All-Day Build Contract: agentkit-cli v0.86.0 — `agentkit hooks`

Status: In Progress
Date: 2026-03-22
Owner: Codex execution pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Add pre-commit hook integration to agentkit-cli so developers can install quality gates that run automatically on every commit. This makes agentkit sticky at the repo level and creates a daily-use touchpoint instead of a one-time analysis.

The feature has three surfaces:
1. **Git hooks** — native `.git/hooks/pre-commit` that runs `agentkit check`
2. **pre-commit framework** — `.pre-commit-config.yaml` hook entry for users of the pre-commit tool
3. **CLI commands** — `agentkit hooks install/status/uninstall`

This contract is considered complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Full test suite must pass at the end (`python3 -m pytest -q` from repo root).
4. New features must ship with docs and CHANGELOG entry in the same pass.
5. CLI outputs must be deterministic and schema-backed where specified.
6. Never modify files outside the project directory (~/repos/agentkit-cli/).
7. Commit after each completed deliverable (not at the end).
8. If stuck on same issue for 3 attempts, stop and write a blocker report to progress-log.md.
9. Do NOT refactor, restyle, or "improve" code outside the deliverables.
10. Read existing tests and docs before writing new code.
11. Target: 4299 baseline + ≥48 new tests = ≥4347 total passing.

## 3. Feature Deliverables

### D1. HookEngine core (`agentkit_cli/hooks.py`)

Core engine for managing git and pre-commit hooks.

Required files:
- `agentkit_cli/hooks.py`

Responsibilities:
- `HookEngine` class with methods: `install(path, mode, min_score, fail_on_drop)`, `uninstall(path)`, `status(path)`, `check(path)` 
- `mode` parameter: `"git"` (native .git/hooks) or `"precommit"` (pre-commit framework) or `"both"` (default)
- For git mode: write `{repo}/.git/hooks/pre-commit` shell script that runs `agentkit score --quiet --min-score {min_score}` and exits 1 on failure
- For precommit mode: add/update `.pre-commit-config.yaml` in repo root with agentkit repo + hook definition
- `status()` returns dict: `{git_installed: bool, precommit_installed: bool, min_score: int|None, last_check: str|None}`
- `check()` runs the quality check directly (same as what the hook would run) and returns pass/fail

The git hook script content should be:
```bash
#!/bin/sh
# agentkit quality gate (installed by agentkit hooks)
agentkit score --quiet || exit 1
```
With a configurable `--min-score N` in the shebang line via comment metadata.

- [ ] HookEngine class with install/uninstall/status/check methods
- [ ] Git hook script generation (executable, idempotent)
- [ ] Pre-commit config generation (idempotent, doesn't clobber existing repos)
- [ ] Tests for HookEngine (≥12 tests covering install/uninstall/status/idempotency/mock git)

### D2. `agentkit hooks` CLI command (`agentkit_cli/commands/hooks_cmd.py`)

The user-facing CLI surface.

Required files:
- `agentkit_cli/commands/hooks_cmd.py`
- Update `agentkit_cli/main.py` to register `hooks` command

Subcommands:
- `agentkit hooks install [--path .] [--min-score 60] [--mode git|precommit|both] [--dry-run]`
  - Installs hooks at the specified path (default: current directory)
  - `--dry-run` shows what would be installed without writing
  - Prints: "Installed git hook at .git/hooks/pre-commit" and/or "Updated .pre-commit-config.yaml"
- `agentkit hooks status [--path .] [--json]`
  - Shows whether hooks are installed, mode, min-score threshold
- `agentkit hooks uninstall [--path .] [--mode git|precommit|both]`
  - Removes installed hooks
- `agentkit hooks run [--path .] [--json]`
  - Manually runs the hook check (useful for CI or testing)

- [ ] hooks subcommand group registered in main.py
- [ ] install subcommand with --path, --min-score, --mode, --dry-run
- [ ] status subcommand with --json output
- [ ] uninstall subcommand
- [ ] run subcommand with --json output
- [ ] Tests for CLI (≥12 tests)

### D3. Integration with `agentkit doctor` and `agentkit setup-ci`

Hooks are a first-class quality signal that doctor should check.

Required changes:
- `agentkit_cli/commands/doctor_cmd.py`: Add a "hooks" category check
  - Check if `.git/hooks/pre-commit` exists and was installed by agentkit (check for agentkit comment in script)
  - Check if `.pre-commit-config.yaml` has agentkit hook defined
  - Print actionable fix: "Run `agentkit hooks install` to add quality gates"
- `agentkit_cli/commands/setup_ci_cmd.py`: Add optional hooks installation step to the CI setup wizard

- [ ] doctor hooks check added (category: "hooks")
- [ ] doctor `--category hooks` works
- [ ] setup-ci mentions hooks install step
- [ ] Tests for integration (≥8 tests)

### D4. `agentkit hooks` in `agentkit run` and `agentkit report`

Surface hooks status in the main agentkit workflows.

Required changes:
- `agentkit run`: When hooks are not installed, show a tip: "Tip: Run `agentkit hooks install` to enforce quality on every commit"
- `agentkit report` HTML: Add "Hooks" section showing installation status with install button (links to CLI command)

- [ ] agentkit run hooks tip (only shown when hooks not installed, once)
- [ ] agentkit report HTML hooks section
- [ ] Tests (≥8 tests)

### D5. Docs, CHANGELOG, version bump, BUILD-REPORT

Required:
- `CHANGELOG.md`: Add v0.86.0 entry documenting `agentkit hooks` feature
- `README.md`: Add `agentkit hooks` to the commands table
- `agentkit_cli/__init__.py`: bump `__version__` to `"0.86.0"`
- `pyproject.toml`: bump version to `"0.86.0"`
- `BUILD-REPORT.md`: Create `BUILD-REPORT-v0.86.0.md` with total test count, feature summary, release checklist
- progress-log.md: Final summary of what was built

- [ ] CHANGELOG.md updated
- [ ] README.md updated
- [ ] __version__ = "0.86.0"
- [ ] pyproject.toml version = "0.86.0"
- [ ] BUILD-REPORT-v0.86.0.md written
- [ ] Tests: ≥8 for version assertions and docs completeness

## 4. Test Requirements

- [ ] Unit tests for HookEngine (install/uninstall/status/idempotency)
- [ ] CLI tests for all 4 hooks subcommands
- [ ] Integration tests: install hook → run hook → check output → uninstall
- [ ] Doctor check test for hooks category
- [ ] All existing 4299 tests must still pass
- [ ] Target: ≥4347 total tests

## 5. Reports

- Write progress to `progress-log.md` in the repo after each deliverable
- Include: what was built, what tests pass, what's next, any blockers
- Final summary when all deliverables done or stopped

## 6. Stop Conditions

- All deliverables checked and all tests passing → DONE
- 3 consecutive failed attempts on same issue → STOP, write blocker report
- Scope creep detected → STOP, report what's new
- All tests passing but deliverables remain → continue to next deliverable

## 7. Release Steps (build-loop will execute these after completion)

The build-loop (not this agent) will:
1. Review git diff
2. Run full test suite
3. Bump version if not already bumped
4. `git push origin main`
5. `git tag v0.86.0 && git push --tags`
6. `pip install build && python -m build && twine upload dist/*`
