# Progress Log — agentkit-cli v1.26.0 spec shipped truth sync

Status: RELEASE-READY (LOCAL-ONLY)
Date: 2026-04-21

## Why this lane exists

The freshly shipped flagship repo still let `agentkit spec . --json` recommend the just-shipped `adjacent-grounding` increment from v1.25.0. That meant the planner could see stale self-hosting objective text, but not that the adjacent grounding follow-up had already been completed locally.

## Root cause

`agentkit_cli/spec_engine.py` could suppress stale self-hosting work in favor of `adjacent-grounding`, but it had no follow-on rule for the next run after that increment itself was already present in shipped or local-release-ready workflow artifacts.

## What changed

- Added shipped-adjacent detection in `agentkit_cli/spec_engine.py` so the planner notices `adjacent-grounding` / `spec grounding` evidence in shipped or local-release-ready artifacts.
- Introduced a `shipped-truth-sync` recommendation that points the flagship repo at refreshing stale canonical source truth and local closeout surfaces instead of repeating the shipped v1.25.0 step.
- Added command and workflow regressions for the shipped-adjacent case.
- Refreshed `.agentkit/source.md`, version surfaces, changelog, build reports, and summary artifacts for truthful `v1.26.0` local closeout.

## Validation

- `uv run python -m pytest -q tests/test_spec_cmd.py tests/test_spec_workflow.py tests/test_main.py` -> `20 passed in 4.03s`
- `uv run python -m agentkit_cli.main spec . --json` from the refreshed tree -> primary recommendation kind `subsystem-next-step`
- `uv run python -m pytest -q` -> `5008 passed, 1 warning in 768.47s (0:12:48)`

## Local closeout truth

The current tree is truthfully `RELEASE-READY (LOCAL-ONLY)`: focused validation passed, the repo now self-specs to `subsystem-next-step`, and the full pytest suite passed from this tree.

## 2026-04-21 release completion pass

### D1. Re-grounded local release-ready state

- Re-read the release contract before any irreversible step.
- Re-ran `bash /Users/mordecai/.openclaw/workspace/scripts/pre-action-recall.sh release agentkit-cli /Users/mordecai/repos/agentkit-cli-v1.26.0-spec-shipped-truth`.
- Re-ran `bash /Users/mordecai/.openclaw/workspace/scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.26.0-spec-shipped-truth`.
- Reconfirmed local head `ba813b0836d8baa0cd6d1e5c27d42872c5fff555` on branch `feat/v1.26.0-spec-shipped-truth` with only the intentional contract file untracked.
- Result: still truthfully `RELEASE-READY (LOCAL-ONLY)` pending fresh validation and the four shipped surfaces.

### D2. Validation from the release tree

- `uv run python -m pytest -q tests/test_spec_cmd.py tests/test_spec_workflow.py tests/test_main.py` -> `20 passed in 13.05s`.
- Direct command-path proof: `uv run python -m agentkit_cli.main spec . --json` -> primary recommendation kind `subsystem-next-step`.
- `uv run python -m pytest -q` -> `5008 passed, 1 warning in 1401.37s (0:23:21)`.
- `bash /Users/mordecai/.openclaw/workspace/scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.26.0-spec-shipped-truth` -> `Total findings: 0`.
- Result: release tree re-proved as validation-clean and ready for release-surface completion.

### D3. Four-surface release completion

- Re-ran `bash /Users/mordecai/.openclaw/workspace/scripts/pre-action-recall.sh release agentkit-cli /Users/mordecai/repos/agentkit-cli-v1.26.0-spec-shipped-truth` and `bash /Users/mordecai/.openclaw/workspace/scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.26.0-spec-shipped-truth` immediately before irreversible steps.
- Pushed branch: `git push -u origin feat/v1.26.0-spec-shipped-truth`.
- Created and pushed annotated tag: `git tag -a v1.26.0 -m 'agentkit-cli v1.26.0'` and `git push origin v1.26.0`.
- Verified tag truth directly: origin tag object `37a948c4376cc0130afbed8042b3e4d72ed44b4c` peels to tested release commit `ba813b0836d8baa0cd6d1e5c27d42872c5fff555`.
- Published from this repo: `uvx --from build pyproject-build` then `uvx twine upload dist/*`.
- Verified PyPI JSON directly: `agentkit-cli==1.26.0` is live with wheel `agentkit_cli-1.26.0-py3-none-any.whl` (`706174` bytes) and sdist `agentkit_cli-1.26.0.tar.gz` (`1239070` bytes).
- Verified PyPI project page path directly: `https://pypi.org/project/agentkit-cli/1.26.0/` returned HTTP 200 during post-publish fetch, even though readability extraction hit a client-challenge shell instead of the human-visible body.
- Result: all four shipped surfaces are now directly proven for `v1.26.0`.

### D4. Post-release chronology reconciliation

- Reconciled `BUILD-REPORT.md`, `BUILD-REPORT-v1.26.0.md`, and `FINAL-SUMMARY.md` from local-only language to shipped truth while keeping the shipped tag commit distinct from the later docs-only chronology branch head.
- Recorded the docs-only chronology reconciliation on branch head `6ce56ecce14ae1fa60df0ef039286e2776154931` (`docs: reconcile v1.26.0 shipped chronology`) and pushed it to `origin/feat/v1.26.0-spec-shipped-truth`.
- Updated workspace chronology surfaces: `/Users/mordecai/.openclaw/workspace/memory/WORKING.md` and `/Users/mordecai/.openclaw/workspace/memory/temporal-facts.md` now both reflect shipped `v1.26.0` truth.
- Result: shipped tag truth, later docs-only branch chronology, and workspace memory surfaces now tell one coherent `v1.26.0` shipped story.
