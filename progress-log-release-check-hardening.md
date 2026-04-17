# Progress Log, release-check hardening

Date: 2026-04-11
Status: BLOCKED

## Blocker report

I hit an environment-level blocker before I could complete the contract safely:

- `exec` calls needed for `pytest`, `git status`, and `git commit` require interactive approval in this subagent session.
- As a subagent, I cannot complete `/approve ...` myself.
- The contract requires running relevant tests as I go, running the full suite at the end, and committing after each completed deliverable.
- Because those approval-gated actions are unavailable, I cannot truthfully mark any deliverable complete or produce the required commit hashes.

## What I changed before stopping

I made an implementation pass toward the contract in these files:

- `agentkit_cli/release_check.py`
- `agentkit_cli/commands/release_check_cmd.py`
- `agentkit_cli/main.py`
- `agentkit_cli/commands/run_cmd.py`
- `tests/test_release_check.py`
- `tests/test_run_command.py`
- `tests/test_main.py`

Intended coverage of that partial pass:

- stronger git branch/upstream/dirty-tree handling
- stricter local/remote tag checks against HEAD
- markdown summary export for release-check
- `agentkit run --release-check` wiring and JSON surface
- new tests for release-check and run integration

## What is still not done

- No focused tests executed
- No full test suite executed
- No deliverable-by-deliverable commits created
- No version bump/docs/changelog/build-report completion pass
- No validated final status

## Required next step

Resume with approval available for shell commands, then:

1. run focused tests for D1-D4
2. fix failures
3. commit each completed deliverable
4. finish D5 docs/version/build report
5. run full test suite
6. write final summary with commit hashes and test totals

## 2026-04-16 D1 recovery scan blocker note

I re-checked the partial D1 implementation in the touched files.

Current assessment before test execution:
- the release-check module, CLI command wiring, and new focused tests look internally consistent enough to continue from
- I did not find an obvious import-time break in the touched Python files by inspection alone
- one likely cosmetic regression is present in `agentkit_cli/commands/release_check_cmd.py`, where the header line now prints a comma before the path instead of a separator
- I did not mark D1 complete because I still cannot run the required focused tests or make the required D1 commit from this approval-gated subagent session

Immediate blocker:
- shell execution for `git status`, `pytest`, and `git commit` still requires `/approve ...`, which this subagent cannot self-grant
- after approval, the focused test run still failed immediately because this environment does not have `pytest` installed: `/Library/Developer/CommandLineTools/usr/bin/python3: No module named pytest`
- `pyproject.toml` currently does not list `pytest` in the dev dependency group, so the test runner is not available by default in this interpreter

Next recovery step once approvals and a test environment are available:
- install or activate an environment with `pytest`
- run focused tests for `tests/test_release_check.py`, `tests/test_run_command.py`, and `tests/test_main.py`
- fix any failures, including the `release_check_cmd.py` display regression if still present
- commit D1 only after the focused tests pass

## 2026-04-16 bookkeeping follow-up

Applied one low-risk direct fix while test execution is still blocked in this session:
- `agentkit_cli/commands/run_cmd.py` now refreshes summary counts after the optional `release-check` step instead of leaving JSON / saved last-run state frozen at the pre-release-check totals
- final terminal pass/fail messaging now uses the refreshed counts
- `save_last_run()` is re-run after release-check so `.agentkit-last-run.json` can include the release-check result
- `agentkit_cli/release_check.py` module docstring no longer says "4-surface" now that smoke-tests are part of the surfaced checks

What this does **not** prove yet:
- focused tests are still unverified from this session
- D1 remains open until `tests/test_release_check.py`, `tests/test_run_command.py`, and `tests/test_main.py` run green in an environment with `pytest`

## 2026-04-16 focused test failure follow-up

A later focused pytest run from the main environment did execute and surfaced 5 real failures.

Fixes applied after reviewing that run:
- restored missing `_escape_markdown_cell()` helper in `agentkit_cli/release_check.py`
- moved `load_config` to a module-level import in `agentkit_cli/commands/run_cmd.py` so the new tests can patch it correctly
- fixed the `release_check_cmd.py` header so it prints `agentkit release-check: <path>` instead of a stray comma before the path

Current state:
- the first obvious regressions from the focused test run are now patched
- the remaining focused failure was traced to the new test expecting `SystemExit` while `run_command()` raises `typer.Exit`/Click `Exit`; `tests/test_run_command.py` now expects `click.exceptions.Exit` and asserts `exit_code`
- D1 still remains open until the focused test set is re-run green and the deliverable is committed

## 2026-04-16 async follow-up: shipped verdict path now passes

A later approved async test completed successfully against the recovered `run_release_check()` verdict logic.

Observed passing assertions from that run:
- `result.verdict == "SHIPPED"` when git push, git tag, registry, tests, and smoke-tests all pass
- `"smoke_tests" in [c.name for c in result.checks]`

What this confirms:
- `run_release_check()` now includes the smoke-test surface in the result set
- the SHIPPED verdict correctly requires the smoke-test surface in addition to tests, git push, git tag, and registry checks

What is still not confirmed from this async result alone:
- the rest of `tests/test_release_check.py`
- `tests/test_run_command.py`
- `tests/test_main.py`
- full-suite totals for the repo

Current blocker remains environment-level test execution: the system `python3` in this session still reports `No module named pytest`, so broader validation needs an environment with pytest available before D1 can be closed honestly.

## 2026-04-16 D1 scoped recovery pass

Validated by direct file inspection only, within the D1 file set:
- `agentkit_cli/release_check.py` now implements smoke-tests, tests, git push, git tag, registry checks, plus deterministic markdown export via `ReleaseCheckResult.to_markdown()` / `write_step_summary()`.
- `agentkit_cli/commands/release_check_cmd.py` is wired to render the richer result, emit JSON with markdown included, and optionally attach a changelog preview.
- `agentkit_cli/main.py` wires both `agentkit release-check` and `agentkit run --release-check`; I also corrected the stale help text so it no longer says "4-part" now that smoke-tests are part of the surfaced checks.
- `agentkit_cli/commands/run_cmd.py` includes the optional post-pipeline release-check integration and refreshes saved/JSON summary counts after that extra step.
- `tests/test_release_check.py`, `tests/test_run_command.py`, and `tests/test_main.py` are coherent with that intended behavior by inspection, including coverage for git edge cases, JSON/markdown export, and `run --release-check` forwarding.

What changed in this recovery pass:
- low-risk consistency fix in `agentkit_cli/main.py` help/doc text
- removed one stale unused import from `tests/test_release_check.py` to keep the touched test file clean
- appended this D1 status note

Focused tests for this pass:
- not run from this subagent, blocked by approval-gated shell execution here and the currently available system interpreter missing `pytest`

What is next:
- run `tests/test_release_check.py`, `tests/test_run_command.py`, and `tests/test_main.py` in a pytest-capable environment
- fix any remaining focused failures if they surface
- commit D1 only after those focused tests pass

Current D1 status:
- focused tests not run from this subagent because shell execution remains approval-gated here and the available system interpreter still lacks `pytest`
- no local D1 commit created
- D1 is still not complete until the focused tests pass in a pytest-capable environment

## 2026-04-16 heartbeat follow-up

Main-session review confirmed the same blocker from the heartbeat path: focused pytest execution still cannot run here because heartbeat exec approvals are unavailable in-chat.

Low-risk unblocker applied:
- added `pytest>=8.0.0` to the `dev` dependency group in `pyproject.toml` so the next validation-capable pass can provision a test environment without rediscovering the missing-runner issue

What still remains before D1 can close:
- run `tests/test_release_check.py`, `tests/test_run_command.py`, and `tests/test_main.py` in an approval-capable session
- fix any focused failures that surface
- commit D1 only after that focused test set passes

## 2026-04-16 D1 subagent recovery stop note

I did a fresh D1-only inspection of the currently touched files in this repo.

Observed state from direct inspection:
- `agentkit_cli/release_check.py` contains the intended smoke-tests, tests, git push, git tag, registry, metadata, and markdown summary paths.
- `agentkit_cli/commands/release_check_cmd.py` currently looks internally consistent with that result shape, including JSON output with markdown and optional changelog preview.
- `agentkit_cli/main.py` currently wires `agentkit release-check` and `agentkit run --release-check`, and the release-check help text now matches the expanded surface.
- `agentkit_cli/commands/run_cmd.py` includes the post-pipeline release-check integration and refreshes summary counts after the optional extra step.
- `tests/test_release_check.py`, `tests/test_run_command.py`, and `tests/test_main.py` look coherent with the intended D1 behavior by inspection.

Current hard blocker in this subagent:
- `exec` is denied in this session, so I cannot run the required focused pytest commands, inspect live git status/diff via shell, or create the required D1 commit hash.
- Because of that, I cannot honestly mark D1 green.

D1 status at stop:
- no additional code changes made in this pass beyond this blocker note
- focused tests not run from this subagent
- no D1 commit created from this subagent

## 2026-04-16 D1 closure from main session

Focused validation completed from the main session in a pytest-capable environment.

Focused tests run:
- `pytest tests/test_release_check.py tests/test_run_command.py tests/test_main.py -q`
- result: 27 passed, 1 warning

D1 completion state:
- recovered file set is now validated by focused tests
- D1 is ready to commit from the main session
- remaining deliverables stay open and out of scope for this checkpoint

## 2026-04-16 D2 inspection-driven patch (pending validation)

The approved async pytest attempt did not actually execute: the gateway rejected `uv run --group dev python -m pytest tests/test_release_check.py tests/test_run_command.py tests/test_main.py -q` with an allowlist-miss, so I am not counting D2 as validated.

Concrete progress made anyway:
- inspected D2 by code review and found the main remaining bug in `check_git_tag()`: annotated tags could be misread because the code compared the raw tag-object SHA instead of the peeled commit SHA
- patched `agentkit_cli/release_check.py` so local tags resolve with `git rev-parse vX.Y.Z^{}` and remote tags prefer the peeled `refs/tags/vX.Y.Z^{}` ref when present
- expanded `tests/test_release_check.py` to cover local tag mismatch, remote tag mismatch, and annotated-tag success behavior

Current D2 state:
- code and tests are tightened by inspection
- D2 still needs a real focused pytest run before it can be marked complete honestly

## 2026-04-17 heartbeat validation pass

Focused validation now runs cleanly in the repo's uv-managed dev environment.

Command run:
- `uv run --group dev python -m pytest tests/test_release_check.py tests/test_run_command.py tests/test_main.py -q`

Result:
- 34 passed, 1 warning (`PytestConfigWarning: Unknown config option: collect_ignore_glob`)

What this changes:
- the earlier blocker is no longer "pytest unavailable" when using the project environment
- the current focused release-check / run-command / main-command test target is green from the main session

What remains:
- D2/D3/D4 still need explicit deliverable review + commits, not just a green focused test target
- D5 docs/build-report/full-suite work is still open

## 2026-04-16 D2 subagent follow-up (tests/commit still blocked here)

Additional D2-focused test coverage added by inspection:
- `check_git_push()` dirty-worktree, detached-HEAD, and missing-upstream cases now assert the user-facing guidance text, not just the failure status
- added explicit coverage for an upstream ref that is configured but not available locally, to ensure the `git fetch --prune` guidance stays intact
- `check_git_tag()` remote-missing case now asserts the push hint, and there is now explicit coverage for an unusable remote `ls-remote` response that lacks the requested tag ref

What I could not complete in this subagent:
- `exec` remains denied here, so I could not run the focused D2 pytest target or create the required D2 commit

Recommended next validating command once approvals are available in a pytest-capable session:
- `pytest tests/test_release_check.py -q`

D2 status from this subagent at stop:
- implementation and focused tests appear aligned by inspection
- validation run and D2 commit are still blocked in this session

## 2026-04-16 heartbeat D3 consistency patch (inspection-driven)

Applied another low-risk `run --release-check` consistency pass by inspection:
- notification verdicts now use the post-release-check failure count instead of the pre-release-check pipeline count
- webhook payload `passed` / `failed` totals now reflect the final release-check-adjusted result
- GitHub Checks conclusion now follows the final release-check-adjusted failure count, so a release-check failure cannot be reported upstream as a success
- added a focused regression test in `tests/test_run_command.py` asserting JSON output marks a non-`SHIPPED` release-check as `success: false`, `failed: 1`, and includes the `release-check` step

Still not validated from this session:
- focused pytest execution remains blocked here, so this D3 patch is inspection-driven until the next approval-capable test pass

## 2026-04-17 D2 validation and completion

Focused D2 validation completed in a pytest-capable environment.

What D2 now covers:
- `check_git_push()` rejects dirty worktrees, detached HEAD, missing upstream, and missing local upstream refs with explicit recovery guidance
- `check_git_tag()` resolves local tags with `^{}` so annotated tags are compared by peeled commit, not tag-object SHA
- remote tag verification is separate from local tag verification and prefers the peeled remote ref when present, with a dedicated failure for unusable `ls-remote` output

Focused tests run:
- `uv run --group dev python -m pytest tests/test_release_check.py -q`
- result: 23 passed, 1 warning (`collect_ignore_glob` unknown config option)

D2 completion state:
- D2 implementation is now validated
- next required action is the scoped D2 commit touching only `agentkit_cli/release_check.py`, `tests/test_release_check.py`, and this progress log

## 2026-04-17 D3 validation and completion

Focused D3 validation completed in a pytest-capable environment.

What D3 now covers:
- `agentkit run --release-check` forwards the CLI flag into `run_command()`
- the post-pipeline release-check step is reflected in JSON output, including the embedded `release_check` payload and a `release-check` step entry
- release-check failures now propagate to the final failure surface consistently, including notifications, webhook payload counts, and GitHub Checks conclusion
- a non-`SHIPPED` release-check verdict causes `run_command()` to exit non-zero, matching release-surface failure behavior

Focused tests run:
- `uv run --group dev python -m pytest tests/test_run_command.py tests/test_main.py -q`
- result: 10 passed, 1 warning (`collect_ignore_glob` unknown config option)

D3 completion state:
- D3 scoped implementation is validated
- next required action is the scoped D3 commit touching `agentkit_cli/commands/run_cmd.py`, `tests/test_run_command.py`, and this progress log

## 2026-04-17 D4 validation and completion

Focused D4 validation completed in a pytest-capable environment.

What D4 now covers:
- deterministic markdown export remains the single release-check artifact for CI and GitHub step summaries via `ReleaseCheckResult.to_markdown()` and `write_step_summary()`
- the export includes the overall verdict plus one row per release surface
- markdown table cells are escaped deterministically for pipes and newlines, keeping snapshot assertions stable
- the summary writer preserves a newline-terminated artifact for file-based export

Focused tests run:
- `uv run --group dev python -m pytest tests/test_release_check.py -q`
- result: 24 passed, 1 warning (`collect_ignore_glob` unknown config option)

D4 completion state:
- D4 scoped implementation is validated
- next required action is the scoped D4 commit touching `tests/test_release_check.py` and this progress log

## 2026-04-17 D5 docs + full-suite handoff

D5 resumed from the main session after the earlier gateway interruption during the full-suite run.

Scoped D5 changes now in place:
- version aligned to `0.96.0` in `pyproject.toml` and `agentkit_cli/__init__.py`
- README and CHANGELOG updated for `release-check` hardening
- `BUILD-REPORT.md` refreshed for `v0.96.0`
- `BUILD-REPORT-v0.96.0.md` restored as the required versioned copy

Full-suite validation run:
- `uv run --group dev python -m pytest -q`
- result: 4706 passed, 11 failed, 2 warnings in 675.20s

Failure triage:
- 9 failures were stale BUILD-REPORT/versioned-copy expectations caused by D5 not being finished yet; those are now addressed by the refreshed report and versioned copy
- 2 failures remain outside this release-check scope:
  - `tests/test_pages_refresh.py::TestDataJson::test_has_8_plus_repos`
  - `tests/test_watch.py::TestChangeHandler::test_debounce_resets_on_rapid_changes`

D5 state from this pass:
- docs/version/build-report handoff is updated
- contract completion is still blocked by unrelated full-suite failures, so the build is `BUILT`, not `RELEASE-READY` or `SHIPPED`

## 2026-04-17 D2 continuation verification

Started from the existing worktree and verified the D2 file set before changing anything.

What I found:
- `agentkit_cli/release_check.py` already contains the D2 hardening paths for branch detection, detached-HEAD failure, dirty-worktree failure, upstream lookup, local tag-at-HEAD verification, and separate remote tag verification.
- `tests/test_release_check.py` already covers the D2 cases, including detached HEAD, missing upstream, missing local upstream ref, local tag mismatch, remote tag missing, unusable remote tag output, and annotated remote tag peeling.
- `git log -- agentkit_cli/release_check.py tests/test_release_check.py` shows D2 was already committed earlier as `cdfa3cf` (`Finish D2 release-check git surface hardening`).

Focused tests run in this continuation pass:
- `uv run --group dev python -m pytest tests/test_release_check.py -q`
- result: 24 passed in 1.76s

D2 continuation state:
- no D2 code fix was needed in this pass
- D2 remains complete and validated
- existing D2 commit: `cdfa3cf`

## 2026-04-17 D3 continuation verification

Started from the existing worktree and verified the D3 file set before changing anything.

What I found:
- `agentkit_cli/main.py` already forwards `--release-check` into `run_command()`.
- `agentkit_cli/commands/run_cmd.py` already runs release-check after the normal pipeline, records the result in `summary["release_check"]`, adds a `release-check` step entry, refreshes saved/JSON counts, and exits non-zero when the release verdict is not `SHIPPED`.
- `tests/test_run_command.py` and `tests/test_main.py` already cover flag forwarding, JSON surface, and non-zero exit behavior.
- `git log -- agentkit_cli/main.py agentkit_cli/commands/run_cmd.py tests/test_run_command.py tests/test_main.py` shows D3 was already committed earlier as `49fced0` (`Finish D3 run release-check hardening`).

Focused tests run in this continuation pass:
- `uv run --group dev python -m pytest tests/test_run_command.py tests/test_main.py -q`
- result: 10 passed in 5.86s

D3 continuation state:
- no D3 code fix was needed in this pass
- D3 remains complete and validated
- existing D3 commit: `49fced0`

## 2026-04-17 D5 full-suite completion

Follow-up validation after the earlier two unrelated red tests:
- targeted rerun:
  - `uv run --group dev python -m pytest tests/test_pages_refresh.py::TestDataJson::test_has_8_plus_repos tests/test_watch.py::TestChangeHandler::test_debounce_resets_on_rapid_changes -q`
  - result: `2 passed`
- repo-wide validation:
  - `uv run --group dev python -m pytest -q`
  - result: `4717 passed, 1 warning` in `387.77s`

What this changes:
- the previously named unrelated blockers no longer reproduce in the current tree
- D5 is now complete from the local validation standpoint
- the release-check hardening contract is locally complete through D5

Release-state note:
- this is still a local build checkpoint only, not a shipped release
- this pass did not push, tag, or publish
- unrelated working-tree churn outside the scoped D5 files still exists in the repo

## 2026-04-17 D2 continuation reverification

Started from the existing worktree and re-checked the D2-only file set before touching code.

What I found:
- `agentkit_cli/release_check.py` still contains the D2 git-surface hardening for branch detection, dirty-worktree failure, detached-HEAD failure, upstream lookup, local tag-at-HEAD verification, and separate remote tag verification.
- `tests/test_release_check.py` still covers the D2 cases, including missing upstream, missing local upstream ref, detached HEAD, local tag mismatch, remote tag missing, unusable remote tag output, and annotated-tag peeling.
- `git log -- agentkit_cli/release_check.py tests/test_release_check.py` still shows the scoped D2 commit as `cdfa3cf` (`Finish D2 release-check git surface hardening`).

Focused tests run in this continuation pass:
- `uv run --group dev python -m pytest tests/test_release_check.py -q`
- result: 24 passed in 1.24s

D2 continuation state:
- no D2 code fix was needed in this pass
- D2 remains complete and validated
- existing D2 commit: `cdfa3cf`
