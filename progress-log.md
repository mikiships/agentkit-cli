# Progress Log — agentkit-cli release chronology

## v1.8.0 release completion D5: final chronology reconciliation — COMPLETE

**Reconciled:**
- Updated `BUILD-REPORT.md`, `BUILD-REPORT-v1.8.0.md`, and `progress-log.md` to one shipped chronology.
- Preserved the exact release truth that annotated tag `v1.8.0` and PyPI `1.8.0` both resolve to the tested release commit `3ed7f140394711e5822616dbe7006a9146d92465`, while later branch commits exist only for chronology reconciliation.
- Restored the repo to a clean working tree after publishing from the tagged release state.

**Final checks:**
- `bash /Users/mordecai/.openclaw/workspace/scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.8.0-clarify-loop` -> no contradictory success/blocker narratives found
- `bash /Users/mordecai/.openclaw/workspace/scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.8.0-clarify-loop` -> `Total findings: 0`
- origin branch head, origin tag, and live PyPI state re-verified after final reconciliation

**Next:** done.

## v1.8.0 release completion D4: PyPI publish and registry verification — COMPLETE

**Built and published:**
- Built fresh `1.8.0` wheel and sdist from the clean tagged release state at `3ed7f140394711e5822616dbe7006a9146d92465`.
- Published both artifacts to PyPI through the authenticated `uv run --with twine twine upload ...` path.
- Verified both the version-specific and top-level PyPI JSON endpoints directly after upload.

**Build + registry proof:**
- `uv build` -> built `dist/agentkit_cli-1.8.0.tar.gz` and `dist/agentkit_cli-1.8.0-py3-none-any.whl`
- `uv run --with twine twine upload dist/agentkit_cli-1.8.0.tar.gz dist/agentkit_cli-1.8.0-py3-none-any.whl` -> success, with PyPI project page link returned for `1.8.0`
- `https://pypi.org/pypi/agentkit-cli/1.8.0/json` -> live with:
  - `agentkit_cli-1.8.0-py3-none-any.whl` (`bdist_wheel`, `613519` bytes)
  - `agentkit_cli-1.8.0.tar.gz` (`sdist`, `1100491` bytes)
- `https://pypi.org/pypi/agentkit-cli/json` -> top-level project JSON now reports `1.8.0`

**Next:** D5 final chronology reconciliation.

## v1.8.0 release completion D3: git release surfaces — COMPLETE

**Published refs:**
- Pushed `feat/v1.8.0-clarify-loop` to `origin` at the tested release commit `3ed7f140394711e5822616dbe7006a9146d92465`.
- Created annotated tag `v1.8.0` at that same commit.
- Verified the remote branch head and peeled tag ref directly from `origin` after push.

**Ref proof:**
- `git push -u origin feat/v1.8.0-clarify-loop` -> success
- `git tag -a v1.8.0 -m "agentkit-cli v1.8.0" HEAD` -> success
- `git push origin refs/tags/v1.8.0` -> success
- `git ls-remote --heads origin feat/v1.8.0-clarify-loop` -> `3ed7f140394711e5822616dbe7006a9146d92465 refs/heads/feat/v1.8.0-clarify-loop`
- `git ls-remote --tags origin refs/tags/v1.8.0 refs/tags/v1.8.0^{}` -> annotated object `4b7c9a34daefb9566be24f487a3f0accb4703263`, peeled commit `3ed7f140394711e5822616dbe7006a9146d92465`

**Next:** D4 PyPI publish and registry verification.

## v1.8.0 release completion D2: validation baseline — COMPLETE

**Validated:**
- Re-ran the focused `agentkit clarify` release slice from the current `feat/v1.8.0-clarify-loop` branch state.
- Re-ran the full supported pytest suite from the same state under Python 3.11 with the required extras.
- Confirmed the release candidate remains green after the D1 audit and cleanup pass.

**Tests:**
- `python3 -m pytest -q tests/test_clarify.py tests/test_clarify_cmd.py tests/test_clarify_workflow.py tests/test_bundle.py tests/test_taskpack.py tests/test_source_audit_workflow.py tests/test_contract_d2.py tests/test_main.py` -> `32 passed in 1.72s`
- `uv run --python 3.11 --with pytest --with fastapi --with uvicorn --with httpx pytest -q` -> `4863 passed, 1 warning in 141.80s (0:02:21)`

**Next:** D3 git release surfaces.

## v1.8.0 release completion D1: release-state audit and repo cleanup — COMPLETE

**Audited source-of-truth first:**
- Ran the required release recall and status-conflict scan from the shared workspace script path before trusting the local v1.8.0 prose.
- Confirmed branch `feat/v1.8.0-clarify-loop` at `415cc57`, remote `origin https://github.com/mikiships/agentkit-cli.git`, version metadata `1.8.0` in both `pyproject.toml` and `agentkit_cli/__init__.py`, and no existing local `v1.8.0` tag.
- Confirmed `CHANGELOG.md`, `BUILD-REPORT.md`, `BUILD-REPORT-v1.8.0.md`, and `progress-log.md` are aligned on the v1.8.0 clarify release line before external release steps.

**Reconciled local drift:**
- Promoted the release-completion contract file into tracked repo history so the pass is documented inside the repo instead of left as untracked noise.
- Updated the v1.8.0 build-report surfaces from `RELEASE-READY, LOCAL-ONLY` to active release-completion truth after the audit and before external mutation.

**Checks:**
- `bash /Users/mordecai/.openclaw/workspace/scripts/pre-action-recall.sh release agentkit-cli /Users/mordecai/repos/agentkit-cli-v1.8.0-clarify-loop` -> recall confirmed `v1.7.0` as the last shipped line and `v1.8.0` as the active local build
- `bash /Users/mordecai/.openclaw/workspace/scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.8.0-clarify-loop` -> no contradictory success/blocker narratives found
- `git status --short --branch` reviewed before cleanup, showing the untracked release-completion contract file

**Next:** D2 validation baseline.

## v1.8.0 D4: release-readiness pass — COMPLETE

**Reconciled:**
- Bumped `pyproject.toml`, `agentkit_cli/__init__.py`, and `uv.lock` to `1.8.0`, and updated the CLI version assertion in `tests/test_main.py`.
- Rewrote `BUILD-REPORT.md`, added `BUILD-REPORT-v1.8.0.md`, and refreshed `FINAL-SUMMARY.md` so all local report surfaces describe the same release-ready clarify state.
- Re-ran release recall, contradiction scan, focused workflow tests, full suite, and hygiene checks before calling the repo local release-ready.

**Validation:**
- `bash /Users/mordecai/.openclaw/workspace/scripts/pre-action-recall.sh release agentkit-cli /Users/mordecai/repos/agentkit-cli-v1.8.0-clarify-loop && bash /Users/mordecai/.openclaw/workspace/scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.8.0-clarify-loop` -> no contradictory success/blocker narratives found
- `python3 -m pytest -q tests/test_clarify.py tests/test_clarify_cmd.py tests/test_clarify_workflow.py tests/test_bundle.py tests/test_taskpack.py tests/test_source_audit_workflow.py tests/test_contract_d2.py tests/test_main.py` -> `32 passed in 1.68s`
- `uv run --python 3.11 --with pytest --with fastapi --with uvicorn --with httpx pytest -q` -> `4863 passed, 1 warning in 144.09s (0:02:24)`
- `bash /Users/mordecai/.openclaw/workspace/scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.8.0-clarify-loop` -> `Total findings: 0`

**Current truth:**
- D1-D4 are complete.
- Focused clarify workflow tests are green.
- Full suite is green.
- `BUILD-REPORT.md`, `BUILD-REPORT-v1.8.0.md`, and `progress-log.md` tell one truthful local release-ready story.
- No push, tag, or PyPI publish was attempted in this pass.

**Next:** done.

## v1.8.0 D3: end-to-end ambiguity loop validation — COMPLETE

**Built:**
- Added `tests/test_clarify_workflow.py` to validate the full `source -> source-audit -> map -> contract -> bundle -> taskpack -> clarify` lane.
- Added explicit gap-path coverage for missing canonical source and contradictory source guidance so clarify fails clearly with `pause` when upstream inputs are not ready.
- Updated README and CHANGELOG so the handoff story now ends with a deterministic clarify step before coding-agent execution.

**Validation:**
- `python3 -m pytest -q tests/test_clarify_workflow.py tests/test_bundle.py tests/test_taskpack.py tests/test_source_audit_workflow.py tests/test_contract_d2.py` -> `22 passed in 1.21s`

**Next:** D4 release-readiness pass.

## v1.8.0 D2: clarify CLI workflow + actionable rendering — COMPLETE

**Built:**
- Added `agentkit_cli/commands/clarify_cmd.py` and wired `agentkit clarify <path>` into `agentkit_cli/main.py`.
- Supported markdown, JSON, `--output`, and `--output-dir` flows so humans and orchestrators can save `clarify.md` plus `clarify.json` without glue code.
- Added focused CLI coverage in `tests/test_clarify_cmd.py` for JSON output, packet-directory writing, and required markdown sections.

**Validation:**
- `python3 -m pytest -q tests/test_clarify_cmd.py` -> `2 passed`

**Next:** D3 end-to-end ambiguity loop validation and docs/report updates.

## v1.8.0 D1: deterministic clarify engine + schema — COMPLETE

**Built:**
- Added `agentkit_cli/clarify.py` with a schema-backed clarify engine that composes bundle + taskpack surfaces into deterministic blocking questions, follow-up questions, assumptions, contradictions, and an execution recommendation.
- Kept ordering stable with explicit sort rules and stable JSON output under `agentkit.clarify.v1`.
- Added focused D1 coverage in `tests/test_clarify.py` for deterministic structure and recommendation behavior.

**Validation:**
- `python3 -m pytest -q tests/test_clarify.py` -> `1 passed`

**Next:** D2 CLI workflow + actionable rendering.

## v1.7.0 release completion D5: final chronology reconciliation — COMPLETE

**Reconciled:**
- Updated `BUILD-REPORT.md`, `BUILD-REPORT-v1.7.0.md`, and `progress-log.md` to one shipped chronology.
- Preserved the exact release truth that annotated tag `v1.7.0` and PyPI `1.7.0` both resolve to the tested release commit `a32b143422481591206511ec17ef810de29e0c4b`, while later branch commits exist only for chronology reconciliation.
- Left the repo clean except for intentional release artifacts in `dist/`.

**Final checks:**
- `bash /Users/mordecai/.openclaw/workspace/scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.7.0-taskpack-handoff` -> no contradictory success/blocker narratives found
- `bash /Users/mordecai/.openclaw/workspace/scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.7.0-taskpack-handoff` -> `Total findings: 0`
- `git ls-remote --heads origin feat/v1.7.0-taskpack-handoff` -> confirmed the branch exists on `origin` and now points at a later chronology-reconciliation commit than the shipped tag
- `git ls-remote --tags origin refs/tags/v1.7.0 refs/tags/v1.7.0^{}` -> annotated object `b1ea22d0cbea23e5548f41bc964eee344be4fca1`, peeled commit `a32b143422481591206511ec17ef810de29e0c4b`

**Next:** done.

## v1.7.0 release completion D4: PyPI publish and registry verification — COMPLETE

**Built and published:**
- Built fresh `1.7.0` wheel and sdist from the clean tagged release state at `a32b143422481591206511ec17ef810de29e0c4b`.
- Published both artifacts to PyPI through the authenticated `uv run --with twine twine upload ...` path.
- Verified the version-specific and top-level PyPI JSON endpoints directly after upload.

**Build + registry proof:**
- `uv build` -> built `dist/agentkit_cli-1.7.0.tar.gz` and `dist/agentkit_cli-1.7.0-py3-none-any.whl`
- `uv run --with twine twine upload dist/agentkit_cli-1.7.0.tar.gz dist/agentkit_cli-1.7.0-py3-none-any.whl` -> success, with PyPI project page link returned for `1.7.0`
- `https://pypi.org/pypi/agentkit-cli/1.7.0/json` -> live with:
  - `agentkit_cli-1.7.0-py3-none-any.whl` (`bdist_wheel`, `608441` bytes)
  - `agentkit_cli-1.7.0.tar.gz` (`sdist`, `1091373` bytes)
- `https://pypi.org/pypi/agentkit-cli/json` -> top-level project JSON now reports `1.7.0`

**Next:** D5 final chronology reconciliation.

## v1.7.0 release completion D3: git release surfaces — COMPLETE

**Published refs:**
- Pushed `feat/v1.7.0-taskpack-handoff` to `origin` at the tested release commit `a32b143422481591206511ec17ef810de29e0c4b`.
- Created annotated tag `v1.7.0` at that same commit.
- Verified the remote branch head and peeled tag ref directly from `origin` after push.

**Ref proof:**
- `git push -u origin feat/v1.7.0-taskpack-handoff` -> success
- `git tag -a v1.7.0 -m "agentkit-cli v1.7.0" a32b143` -> success
- `git push origin refs/tags/v1.7.0` -> success
- `git ls-remote --heads origin feat/v1.7.0-taskpack-handoff` -> `a32b143422481591206511ec17ef810de29e0c4b refs/heads/feat/v1.7.0-taskpack-handoff`
- `git ls-remote --tags origin refs/tags/v1.7.0 refs/tags/v1.7.0^{}` -> annotated object `b1ea22d0cbea23e5548f41bc964eee344be4fca1`, peeled commit `a32b143422481591206511ec17ef810de29e0c4b`

**Next:** D4 PyPI publish and registry verification.

## v1.7.0 release completion D2: validation baseline — COMPLETE

**Validated:**
- Re-ran the focused `agentkit taskpack` release slice from the audited `feat/v1.7.0-taskpack-handoff` repo state.
- Re-ran the full supported pytest suite from the same repo state.
- Confirmed the tested release baseline moved forward to the audited D1 commit `d914d92` because the release-completion contract and chronology are now tracked in repo history.

**Tests:**
- `uv run --python 3.11 --with pytest pytest -q tests/test_daily_d5.py tests/test_taskpack.py tests/test_bundle.py tests/test_source_audit_workflow.py tests/test_contract_d2.py tests/test_map.py tests/test_main.py` -> `49 passed in 1.24s`
- `uv run --python 3.11 --with pytest pytest -q` -> `4857 passed, 1 warning in 136.18s (0:02:16)`

**Next:** D3 git release surfaces.

## v1.7.0 release completion D1: release-state audit and repo cleanup — COMPLETE

**Audited source-of-truth first:**
- Ran the required release recall and status-conflict scan from the shared workspace script path before trusting the local release prose.
- Confirmed branch `feat/v1.7.0-taskpack-handoff` at `45d41ef`, remote `origin https://github.com/mikiships/agentkit-cli.git`, release metadata `1.7.0` in both `pyproject.toml` and `agentkit_cli/__init__.py`, and no existing local `v1.7.0` tag.
- Re-ran the focused taskpack release slice and the full supported pytest suite from the audited repo state to confirm the tested baseline before any irreversible release actions.

**Reconciled local drift:**
- Reverted `.agentkit-last-run.json` so the release state is not tied to transient local runner output.
- Added the explicit release-completion contract file to the repo so the current pass is documented in tracked history instead of left as untracked noise.

**Checks:**
- `bash /Users/mordecai/.openclaw/workspace/scripts/pre-action-recall.sh release agentkit-cli /Users/mordecai/repos/agentkit-cli-v1.7.0-taskpack-handoff` -> completed with no temporal conflicts relevant to this release line
- `bash /Users/mordecai/.openclaw/workspace/scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.7.0-taskpack-handoff` -> no contradictory success/blocker narratives found
- `uv run --python 3.11 --with pytest pytest -q tests/test_daily_d5.py tests/test_taskpack.py tests/test_bundle.py tests/test_source_audit_workflow.py tests/test_contract_d2.py tests/test_map.py tests/test_main.py` -> `49 passed in 1.24s`
- `uv run --python 3.11 --with pytest pytest -q` -> `4857 passed, 1 warning in 136.18s (0:02:16)`

**Next:** D2 validation baseline is already re-established on the audited state, then proceed to D3 git release surfaces.

## v1.7.0 D4: release-readiness pass — COMPLETE

**Reconciled:**
- Bumped `pyproject.toml`, `agentkit_cli/__init__.py`, `uv.lock`, and the CLI version test to `1.7.0`.
- Ran the required release recall plus status-conflict scan from the shared workspace script path, then cleared the remaining report-surface failures by recording verified focused and full-suite counts in both build reports.
- Ran the final hygiene scan and left the repo with no merge markers, comment slop, or untracked-noise findings.

**Validation:**
- `bash /Users/mordecai/.openclaw/workspace/scripts/pre-action-recall.sh release agentkit-cli /Users/mordecai/repos/agentkit-cli-v1.7.0-taskpack-handoff && bash /Users/mordecai/.openclaw/workspace/scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.7.0-taskpack-handoff` -> no contradictory success/blocker narratives found
- `uv run --python 3.11 --with pytest pytest -q tests/test_daily_d5.py tests/test_taskpack.py tests/test_bundle.py tests/test_source_audit_workflow.py tests/test_contract_d2.py tests/test_map.py tests/test_main.py` -> `49 passed in 1.26s`
- `uv run --python 3.11 --with pytest pytest -q` -> `4857 passed, 1 warning in 139.57s (0:02:19)`
- `bash /Users/mordecai/.openclaw/workspace/scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.7.0-taskpack-handoff` -> `Total findings: 0`

**Current truth:**
- D1-D4 are complete.
- Focused workflow tests are green.
- Full suite is green.
- `BUILD-REPORT.md`, `BUILD-REPORT-v1.7.0.md`, and `progress-log.md` now tell one truthful local release-ready story.
- No push, tag, or PyPI publish was attempted in this pass.

**Next:** done.

## v1.7.0 D1-D3: taskpack engine, CLI workflow, and handoff validation — COMPLETE

**Built:**
- Added `agentkit_cli/taskpack.py` as a deterministic composition layer over the shipped bundle lane, separating durable context, task brief, execution checklist, target-aware instructions, and carried-forward gap reporting.
- Added `agentkit_cli/commands/taskpack_cmd.py` plus `agentkit taskpack <path>` wiring in `agentkit_cli/main.py` with `--target generic|codex|claude-code`, `--json`, `--output`, and `--output-dir` support.
- Added `tests/test_taskpack.py` to cover deterministic engine structure, target shaping, packet-directory writing, gap handling, CLI help, and the full `source -> contract -> bundle -> taskpack` lane.
- Updated README, CHANGELOG, and build-report surfaces so the supported handoff story is now `source -> source-audit -> map -> contract -> bundle -> taskpack`.

**Validation:**
- `python3 -m pytest -q tests/test_taskpack.py tests/test_bundle.py tests/test_source_audit_workflow.py tests/test_contract_d2.py tests/test_map.py tests/test_main.py` -> `36 passed in 1.79s`

**Current truth:**
- D1 deterministic taskpack engine + schema: complete.
- D2 CLI workflow + target modes: complete.
- D3 workflow validation and docs/report updates: complete.
- D4 release-readiness pass: pending final version bump, contradiction scan, hygiene check, and full-suite validation.

**Next:** bump release metadata to `1.7.0`, run the required recall/conflict/hygiene checks, then run the full suite and finalize the release-ready reports.

## v1.6.0 release completion D1: release-state audit and repo cleanup — COMPLETE

**Audited source-of-truth first:**
- Ran `bash /Users/mordecai/.openclaw/workspace/scripts/pre-action-recall.sh release agentkit-cli /Users/mordecai/repos/agentkit-cli-v1.6.0-handoff-bundle` before trusting local prose.
- Ran `bash /Users/mordecai/.openclaw/workspace/scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.6.0-handoff-bundle` and found no contradictory success/blocker narratives.
- Confirmed branch `feat/v1.6.0-handoff-bundle` at `b7fb900bc65a264262069533c483933d959cd72d`, local version metadata `1.6.0`, and no existing local `v1.6.0` tag.
- Reconciled local drift that had not been committed yet: `uv.lock` already reflected the intended `1.6.0` bump, while `BUILD-REPORT.md` and `BUILD-REPORT-v1.6.0.md` still described the branch as locally release-ready rather than active release completion.

**Checks:**
- `git status --short --branch && git remote -v` -> branch is local `feat/v1.6.0-handoff-bundle`, remote `origin https://github.com/mikiships/agentkit-cli.git`
- `git log --oneline --decorate -n 8` -> release branch head `b7fb900`, prior shipped tag `v1.5.0` at `5d340ac`
- version metadata check -> `pyproject.toml` and `agentkit_cli/__init__.py` both report `1.6.0`

**Next:** D2 validation baseline.


## v1.6.0 release completion D2: validation baseline — COMPLETE

**Validated:**
- Re-ran the focused `agentkit bundle` release slice on the audited `feat/v1.6.0-handoff-bundle` repo state.
- Re-ran the full supported pytest suite from the same repo state.
- Cleared the one release-surface blocker by recording a verified 4-digit full-suite count in `BUILD-REPORT.md` and `BUILD-REPORT-v1.6.0.md`, then re-ran the gates until they were clean.

**Tests:**
- `uv run --python 3.11 --with pytest pytest -q tests/test_daily_d5.py tests/test_bundle.py tests/test_source_audit_workflow.py tests/test_contract_d2.py tests/test_map.py tests/test_main.py` -> `43 passed in 1.00s`
- `uv run --python 3.11 --with pytest pytest -q` -> `4851 passed, 1 warning in 135.62s (0:02:15)`
- `bash /Users/mordecai/.openclaw/workspace/scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.6.0-handoff-bundle` -> no contradictory success/blocker narratives found
- `bash /Users/mordecai/.openclaw/workspace/scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.6.0-handoff-bundle` -> `Total findings: 0`

**Release baseline commit:**
- Tested release commit is `28a8ab29c05aa0a7a5fe4bf184c33d94ec77c592`.

**Next:** D3 git release surfaces.

## v1.5.0 release completion D3-D5: shipped and reconciled — COMPLETE

**Published refs:**
- `origin/feat/v1.5.0-source-audit` -> `5d340ac`
- annotated tag `v1.5.0` object `60613af6dc5c8aca5a00aab51b724b173af80bee`, peeled commit `5d340ac`

**Registry proof:**
- `https://pypi.org/pypi/agentkit-cli/1.5.0/json` -> live with wheel + sdist
- `https://pypi.org/pypi/agentkit-cli/json` -> top-level project JSON reports `1.5.0`

**Important chronology note:**
- The release-completion sub-agent timed out after finishing the irreversible release steps, so the shipped truth had to be reconciled afterward from source-of-truth surfaces instead of trusting the stale local-only prose.
- Restored the repo to a clean working tree after the timed-out pass temporarily removed tracked historical `dist/` artifacts.

**Current truth:**
- `agentkit-cli v1.5.0` is shipped.
- Tests green at the shipped release commit: `4845 passed, 1 warning`.
- Branch, tag, and PyPI all resolve to `1.5.0`.
- Final repo/report chronology is now coherent again.

**Next:** done.

## v1.5.0 D3: docs, workflow handoff, and release-readiness surfaces — COMPLETE

**Built:**
- Updated README to document `agentkit source-audit` and the recommended `source -> source-audit -> map -> contract` lane.
- Added `tests/test_source_audit_workflow.py` to cover a realistic canonical-source handoff through `source-audit`, `map`, and `contract`.
- Bumped local release metadata to `1.5.0` in `pyproject.toml`, `agentkit_cli/__init__.py`, and `uv.lock`.
- Added the `1.5.0` changelog entry and rewrote `BUILD-REPORT.md` plus `BUILD-REPORT-v1.5.0.md` for truthful local release-readiness.

**Validation:**
- `uv run --python 3.11 --with pytest pytest -q tests/test_source_audit.py tests/test_source_cmd.py tests/test_contract_d2.py tests/test_map.py tests/test_main.py` -> `33 passed in 5.26s`
- `uv run --python 3.11 --with pytest pytest -q tests/test_source_audit.py tests/test_source_audit_workflow.py tests/test_source_cmd.py tests/test_contract_d2.py tests/test_map.py tests/test_main.py` -> `34 passed in 1.26s`
- `bash /Users/mordecai/.openclaw/workspace/scripts/pre-action-recall.sh release agentkit-cli /Users/mordecai/repos/agentkit-cli-v1.5.0-source-audit && bash /Users/mordecai/.openclaw/workspace/scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.5.0-source-audit` -> no contradictory success/blocker narratives found
- `bash /Users/mordecai/.openclaw/workspace/scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.5.0-source-audit` -> `Total findings: 0`

**Current truth:**
- D1 deterministic source-audit engine + schema: complete.
- D2 CLI workflow + actionable rendering: complete.
- D3 docs, workflow handoff, and release surfaces: complete.
- Branch is release-ready locally for `v1.5.0`; no push, tag, or publish was attempted.

**Later release-completion note:**
- Full-suite release validation on 2026-04-20 initially found 2 stale release-surface failures: `BUILD-REPORT.md` lacked a 4-digit verified full-suite count, and `tests/test_site_engine.py::test_generate_index_shows_current_frontdoor_story` still hardcoded the prior shipped frontdoor story instead of deriving it from the latest released tag.
- Fixed the drift by recording the full-suite counts in the build reports and making the frontdoor test derive release truth from the latest shipped tag.
- Verification reruns: `uv run --python 3.11 --with pytest pytest -q tests/test_daily_d5.py tests/test_site_engine.py` -> `39 passed in 0.46s`; `uv run --python 3.11 --with pytest pytest -q` -> `4845 passed, 1 warning in 303.39s (0:05:03)`.

**Next:** proceed to git release surfaces from this now-green repo state.

## v1.5.0 D1-D2: source audit engine + CLI workflow — COMPLETE

**Built:**
- Added deterministic `agentkit_cli/source_audit.py` with explicit canonical-source preference, legacy fallback detection, required-section checks, ambiguity heuristics, contradiction hints, and stable JSON output.
- Added first-class `agentkit source-audit` CLI wiring with rich text view, markdown rendering, `--json`, and output-file support.
- Added focused regression coverage for canonical-source preference, legacy fallback, missing sections, ambiguity detection, contradiction hints, markdown export, and CLI help.

**Validation:**
- `uv run --python 3.11 --with pytest pytest -q tests/test_source_audit.py tests/test_source_cmd.py tests/test_contract_d2.py tests/test_map.py tests/test_main.py` -> `33 passed in 5.90s`

**Current truth:**
- D1 deterministic source-audit engine + schema: complete.
- D2 CLI workflow + actionable rendering: complete enough for local use and tests.
- D3 docs/workflow handoff/release surfaces: still pending.

**Next:** update README/changelog/build-report surfaces for `source -> source-audit -> map -> contract`, add an end-to-end workflow fixture, and run the broader focused validation slice.


## Release completion D5: final chronology reconciliation — COMPLETE

**Reconciled:**
- Updated `BUILD-REPORT.md`, `BUILD-REPORT-v1.4.0.md`, and `progress-log.md` to one shipped chronology.
- Preserved the exact release truth that branch push, annotated tag `v1.4.0`, and PyPI `1.4.0` all point to the tested release commit `76c00581b283d9bb254def57f9c36dc09b8dfa92`.
- Kept the release chronology honest by leaving the tagged commit as the tested baseline and doing this report reconciliation afterward.

**Final checks:**
- `git ls-remote --heads origin feat/v1.4.0-contract-handoff` -> `76c00581b283d9bb254def57f9c36dc09b8dfa92 refs/heads/feat/v1.4.0-contract-handoff`
- `git ls-remote --tags origin refs/tags/v1.4.0 refs/tags/v1.4.0^{}` -> tag object `3c7d1a935b562d2f778302f5e054d68483ce58fe`, peeled commit `76c00581b283d9bb254def57f9c36dc09b8dfa92`
- `https://pypi.org/pypi/agentkit-cli/1.4.0/json` -> live with wheel + sdist
- `https://pypi.org/pypi/agentkit-cli/json` -> top-level project JSON now reports `1.4.0`

**Next:** done.

---

## Release completion D4: PyPI publish and registry verification — COMPLETE

**Built and published:**
- Built fresh `1.4.0` wheel and sdist from the clean tagged release state.
- Published both artifacts to PyPI through the authenticated `uv run --with twine twine upload ...` path after confirming global `twine` was absent in this shell.
- Verified both the version-specific and top-level PyPI JSON endpoints after upload.

**Build + registry proof:**
- `uv build` -> built `dist/agentkit_cli-1.4.0.tar.gz` and `dist/agentkit_cli-1.4.0-py3-none-any.whl`
- `uv run --with twine twine upload dist/agentkit_cli-1.4.0.tar.gz dist/agentkit_cli-1.4.0-py3-none-any.whl` -> success
- `https://pypi.org/pypi/agentkit-cli/1.4.0/json` -> `1.4.0` with:
  - `agentkit_cli-1.4.0-py3-none-any.whl` (`bdist_wheel`, `595071` bytes)
  - `agentkit_cli-1.4.0.tar.gz` (`sdist`, `1067335` bytes)
- `https://pypi.org/pypi/agentkit-cli/json` -> top-level project JSON reports `1.4.0`

**Next:** D5 final chronology reconciliation.

---

## Release completion D3: git release surfaces — COMPLETE

**Published refs:**
- Pushed `feat/v1.4.0-contract-handoff` to `origin` at the tested release commit `76c00581b283d9bb254def57f9c36dc09b8dfa92`.
- Created annotated tag `v1.4.0` at that same commit.
- Verified the remote branch head and peeled tag ref directly from `origin` after push.

**Ref proof:**
- `git push -u origin feat/v1.4.0-contract-handoff` -> success
- `git tag -a v1.4.0 -m "agentkit-cli v1.4.0" 76c0058` -> success
- `git push origin refs/tags/v1.4.0` -> success
- `git ls-remote --heads origin feat/v1.4.0-contract-handoff` -> `76c00581b283d9bb254def57f9c36dc09b8dfa92 refs/heads/feat/v1.4.0-contract-handoff`
- `git ls-remote --tags origin refs/tags/v1.4.0 refs/tags/v1.4.0^{}` -> annotated object `3c7d1a935b562d2f778302f5e054d68483ce58fe`, peeled commit `76c00581b283d9bb254def57f9c36dc09b8dfa92`

**Next:** D4 PyPI publish and registry verification.

---

## Release completion D2: validation baseline — COMPLETE

**Validated:**
- Re-ran the focused `contract/map/main/docs` release slice on the reconciled repo state.
- Fixed the stale release-surface blockers discovered during validation: one outdated version assertion in `tests/test_main.py`, one version-counter derivation bug in `agentkit_cli/site_engine.py`, one stale landing-page expectation in `tests/test_site_engine.py`, and a build report that omitted a verified full-suite count.
- Re-ran the full supported pytest suite from the same repo state and cut tested baseline commit `76c0058` only after it was clean.

**Tests:**
- `uv run --python 3.11 --with pytest pytest -q tests/test_contract_d2.py tests/test_map.py tests/test_main.py tests/test_landing_d5.py tests/test_user_scorecard_d5.py` -> `34 passed in 1.03s`
- `uv run --python 3.11 --with pytest pytest -q` -> `4839 passed, 1 warning in 348.07s (0:05:48)`

**Next:** D3 git release surfaces.

---

## v1.4.0 release-readiness pass: local chronology reconciliation — COMPLETE

**Reconciled:**
- Ran the next broader focused validation slice for the contract/map/help/docs surface on the current `feat/v1.4.0-contract-handoff` branch state.
- Bumped release metadata from `1.3.0` to `1.4.0` in `pyproject.toml`, `agentkit_cli/__init__.py`, and `uv.lock`.
- Updated `CHANGELOG.md`, rewrote `BUILD-REPORT.md`, and added `BUILD-REPORT-v1.4.0.md` so the repo tells one truthful local release-readiness story.

**Validation:**
- `uv run --python 3.11 --with pytest pytest -q tests/test_contract_d2.py tests/test_map.py tests/test_main.py tests/test_landing_d5.py tests/test_user_scorecard_d5.py` -> `34 passed in 1.09s`

**Truth after this pass:**
- Branch remains local-only on `feat/v1.4.0-contract-handoff`.
- No push, tag, or PyPI publish was attempted in this pass.
- State is `RELEASE-READY` locally, not shipped.

**Next:** release-completion pass when push/tag/publish are in scope.


## Release completion D5: final chronology reconciliation — COMPLETE

**Reconciled:**
- Updated `BUILD-REPORT.md`, `BUILD-REPORT-v1.3.0.md`, and `progress-log.md` to one shipped chronology.
- Preserved the exact release truth that `v1.3.0` and PyPI `1.3.0` point to the tested release commit `c4d4489cbf2342e2ad8bf691466428c3291607dc`, while later branch commits exist only for report reconciliation.
- Left the repo clean except for intentional release artifacts in `dist/`.

**Final checks:**
- `bash /Users/mordecai/.openclaw/workspace/scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.3.0-map`
- `bash /Users/mordecai/.openclaw/workspace/scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.3.0-map`

**Next:** done.

---

## Release completion D4: PyPI publish and registry verification — COMPLETE

**Built and published:**
- Built fresh `1.3.0` wheel and sdist from the clean tagged release state.
- Published both artifacts to PyPI through the authenticated local `twine upload` path.
- Verified the live version-specific PyPI JSON and project page after upload.

**Build + registry proof:**
- `uv build` -> built `dist/agentkit_cli-1.3.0.tar.gz` and `dist/agentkit_cli-1.3.0-py3-none-any.whl`
- `twine upload dist/agentkit_cli-1.3.0.tar.gz dist/agentkit_cli-1.3.0-py3-none-any.whl` -> success
- `https://pypi.org/pypi/agentkit-cli/1.3.0/json` -> `1.3.0` with:
  - `agentkit_cli-1.3.0-py3-none-any.whl` (`bdist_wheel`, `588754` bytes)
  - `agentkit_cli-1.3.0.tar.gz` (`sdist`, `1058379` bytes)
- `https://pypi.org/project/agentkit-cli/1.3.0/` -> `HTTP/2 200`

**Next:** D5 final chronology reconciliation.

---

## Release completion D3: git release surfaces — COMPLETE

**Published refs:**
- Pushed `feat/v1.3.0-map` to `origin` at the tested release commit `c4d4489cbf2342e2ad8bf691466428c3291607dc`.
- Created annotated tag `v1.3.0` at that same commit.
- Verified the remote branch head and peeled tag ref directly from `origin` after push.

**Ref proof:**
- `git push -u origin feat/v1.3.0-map` -> success
- `git tag -a v1.3.0 -m "agentkit-cli v1.3.0" c4d4489cbf2342e2ad8bf691466428c3291607dc`
- `git push origin refs/tags/v1.3.0` -> success
- `git ls-remote --heads origin feat/v1.3.0-map` -> `c4d4489cbf2342e2ad8bf691466428c3291607dc refs/heads/feat/v1.3.0-map`
- `git ls-remote --tags origin refs/tags/v1.3.0 refs/tags/v1.3.0^{}` -> annotated object `07346849f99e638981250faa6350d6ceaf1ce061`, peeled commit `c4d4489cbf2342e2ad8bf691466428c3291607dc`

**Next:** D4 PyPI publish and registry verification.

---

## Release completion D2: validation baseline — COMPLETE

**Validated:**
- Re-ran the focused `agentkit map` release slice on the reconciled repo state.
- Re-ran the full supported pytest suite from the same repo state.
- Confirmed the release candidate commit stayed stable across both runs.

**Tests:**
- `uv run pytest -q tests/test_map.py tests/test_main.py tests/test_landing_d5.py tests/test_user_scorecard_d5.py` -> `28 passed in 0.95s`
- `uv run pytest -q` -> `4833 passed, 1 warning in 134.24s (0:02:14)`

**Next:** D3 git release surfaces.

---

## Release completion D1: release-state audit and repo cleanup — COMPLETE

**Audited:**
- Read the strict release contract plus the current release surfaces: `BUILD-REPORT.md`, `BUILD-REPORT-v1.3.0.md`, `progress-log.md`, `CHANGELOG.md`, git status, branch state, and tag state.
- Ran the required release recall and contradiction scan before trusting repo-local prose.
- Confirmed the intended release line is `1.3.0` in both `pyproject.toml` and `agentkit_cli/__init__.py`, with current release head `c7cf350` on `feat/v1.3.0-map` and no existing local `v1.3.0` tag.

**Reconciled:**
- Reverted `.agentkit-last-run.json` as generated noise, so release truth is not tied to a transient local run artifact.
- Staged the previously uncommitted `uv.lock` version drift so the lockfile matches the `1.3.0` package metadata.
- Promoted the v1.3.0 feature and release contract files into tracked repo history so the release handoff state is explicit instead of untracked noise.

**Checks:**
- `bash /Users/mordecai/.openclaw/workspace/scripts/pre-action-recall.sh release agentkit-cli /Users/mordecai/repos/agentkit-cli-v1.3.0-map` -> completed
- `bash /Users/mordecai/.openclaw/workspace/scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.3.0-map` -> `No contradictory success/blocker narratives found.`
- `git status --short --branch` reviewed before and after cleanup reconciliation

**Next:** D2 validation baseline.

---

## D1: transcript adapters + normalized burn schema — COMPLETE

**Built:**
- Added `agentkit_cli/burn_adapters.py` with normalized burn models for sessions, turns, tool usage, and cost states.
- Implemented deterministic fixture adapters for Codex, Claude Code, and OpenClaw-style local transcript files.
- Added burn fixtures plus parser coverage for missing fields, malformed JSON/JSONL, estimated costs, and stable ordering.

**Tests:** `uv run pytest -q tests/test_burn_adapters.py` -> `10 passed in 0.04s`

**Refinement:** tightened deterministic normalization by replacing process-randomized fallback turn IDs with stable SHA-256-derived IDs and sorting normalized turns by timestamp/id.

**Next:** D2 burn analysis engine.

---

## D2: burn analysis engine — COMPLETE

**Built:**
- Added `agentkit_cli/burn.py` with session filtering, aggregation by project/model/provider/task/source, top-session ranking, and stable JSON-ready report output.
- Implemented waste finding detection for expensive no-tool turns, retry-loop patterns, and low one-shot success sessions.
- Added engine tests for aggregation math, deterministic sorting, filters, and waste detection.

**Tests:** `uv run pytest -q tests/test_burn_adapters.py tests/test_burn_engine.py` -> `13 passed in 0.04s`

**Next:** D3 `agentkit burn` CLI command.

---

## D3: `agentkit burn` CLI command — COMPLETE

**Built:**
- Added `agentkit_cli/commands/burn.py` with `--path`, `--format`, `--since`, `--limit`, `--project`, and `--output` support.
- Added rich terminal output, stable JSON output, and clean empty-directory handling.
- Added CLI tests for happy path, filters, empty path, JSON shape, and HTML writing.

**Tests:** `uv run pytest -q tests/test_burn_adapters.py tests/test_burn_engine.py tests/test_burn_command.py tests/test_burn_report.py` -> `22 passed in 1.00s`

**Next:** D4 HTML report + narrative summary.

---

## D4: HTML burn report + narrative summary — COMPLETE

**Built:**
- Added `agentkit_cli/renderers/burn_report.py` with dark-theme HTML and markdown-ready burn summaries.
- Added renderer tests for report sections, styling markers, and markdown summary content.

**Tests:** `uv run pytest -q tests/test_burn_adapters.py tests/test_burn_engine.py tests/test_burn_command.py tests/test_burn_report.py` -> `22 passed in 1.00s`

**Next:** D5 docs, versioning, and final validation.

---

## D5: docs, build report, versioning, and final validation — COMPLETE

**Built and verified:**
- Confirmed the release metadata still reports `1.1.0` in `pyproject.toml` and `agentkit_cli/__init__.py`.
- Re-ran the contradiction scan and hygiene check from the workspace support scripts, both clean.
- Re-ran the focused burn validation slice plus `tests/test_main.py`, then re-ran the full suite on the current branch state.
- Verified the shipped registry state directly from the version-specific PyPI JSON for `agentkit-cli==1.1.0`.
- Reconciled `BUILD-REPORT.md` and `BUILD-REPORT-v1.1.0.md` to the actual chronology: branch head is now `0c47a5a`, while the shipped `v1.1.0` tag and PyPI release remain on `a704a06`.

**Tests and checks:**
- `uv run pytest -q tests/test_burn_adapters.py tests/test_burn_engine.py tests/test_burn_command.py tests/test_burn_report.py tests/test_main.py` -> `31 passed in 0.80s`
- `uv run pytest -q` -> `4811 passed, 1 warning in 128.98s (0:02:08)`
- `bash /Users/mordecai/.openclaw/workspace/scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.1.0-burn-observability` -> `0 findings`
- `bash /Users/mordecai/.openclaw/workspace/scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.1.0-burn-observability` -> `0 findings`
- PyPI verification -> live with `agentkit_cli-1.1.0.tar.gz` and `agentkit_cli-1.1.0-py3-none-any.whl`

**Audit notes:**
- The contract referenced repo-local helper scripts, but this repo does not contain them. The equivalent workspace support scripts were used for the required contradiction and hygiene checks.
- The branch and tag no longer point to the same commit. That is now documented explicitly instead of being reported as one commit.

**Final status:** shipped and reconciled. The release is live, validation is green, and the report surfaces now match the actual branch, tag, and PyPI state.

---

## D1: site freshness drift reproduced and locked down — COMPLETE

**Built:**
- Mapped the drift to two competing front-door writers: `site_engine.generate_index()` carried one set of hardcoded shell stats while `pages_refresh` and `update-pages.yml` mutated `docs/index.html` independently, so `docs/index.html` and `docs/data.json` could disagree.
- Added regression coverage for a canonical `frontdoor` payload shared by the landing shell and `data.json`.
- Added regression tests for full index rewrites, `--from-existing-data` refreshes, workflow wiring, and data payload coherence.

**Tests:** `python3 -m pytest -q tests/test_site_engine.py tests/test_pages_refresh.py` -> `84 passed in 0.50s`

**Next:** D2 deterministic front-door refresh path.

---

## D2: deterministic front-door refresh path — COMPLETE

**Built:**
- Replaced the regex-based `docs/index.html` mutation path with a canonical full-page rewrite from `SiteEngine.generate_index(site_data=...)`.
- Added shared `frontdoor` metadata to `docs/data.json` so the landing shell and data feed derive version/test/version-count/package-count stats from the same payload.
- Added `agentkit pages-refresh --from-existing-data` for the non-rescoring path, then regenerated `docs/index.html` and `docs/data.json` together from that supported command flow.

**Tests:** `python3 -m pytest -q tests/test_site_engine.py tests/test_pages_refresh.py` -> `84 passed in 0.50s`

**Next:** D3 workflow/docs durability updates.

---

## D3: Pages workflow wiring tightened — COMPLETE

**Built:**
- Updated `daily-pages-refresh.yml` to install the local checkout, compute front-door version/test stats, and pass them through `agentkit pages-refresh` instead of relying on a stale published CLI.
- Updated `update-pages.yml` to stop regex-editing `docs/index.html` and instead run `agentkit pages-refresh --from-existing-data` so push-time shell refreshes stay coherent with `docs/data.json`.
- Documented the supported refresh paths in `README.md`.

**Tests:** `python3 -m pytest -q tests/test_site_engine.py tests/test_pages_refresh.py` -> `84 passed in 0.50s`

**Next:** D4 reports, full validation, and final summary artifacts.

---

## D4: reports, validation, and final artifacts — COMPLETE

**Built:**
- Updated `BUILD-REPORT.md` with the drift root cause, the canonical refresh path, workflow changes, and final validation results.
- Added `FINAL-SUMMARY.md` with the concise repo-local handoff summary.
- Re-ran the contradiction scan and hygiene check, both clean.
- Ran the full pytest suite under Python 3.11 with API extras enabled, green.

**Tests and checks:**
- `python3 -m pytest -q tests/test_site_engine.py tests/test_pages_refresh.py` -> `84 passed in 0.50s`
- `uv run --python 3.11 --extra api --with pytest pytest -q tests/test_landing_d1.py tests/test_landing_d2.py tests/test_pages_sync_d4.py tests/test_site_engine.py tests/test_pages_refresh.py` -> `113 passed in 0.47s`
- `uv run --python 3.11 --extra api --with pytest pytest -q` -> `4821 passed, 1 warning in 127.85s (0:02:07)`
- `bash /Users/mordecai/.openclaw/workspace/scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.2.1-site-freshness` -> `0 findings`
- `bash /Users/mordecai/.openclaw/workspace/scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.2.1-site-freshness` -> `0 findings`

**Next:** done.


---

## D1: supported Pages refresh path regenerates the docs payload — COMPLETE

**Built:**
- Updated `agentkit pages-refresh --from-existing-data` to refresh `docs/data.json`, fully rewrite `docs/index.html`, and now regenerate `docs/leaderboard.html` from the same payload.
- Updated `.github/workflows/update-pages.yml` so the push-time Pages refresh stages and commits `docs/leaderboard.html` alongside `docs/data.json` and `docs/index.html`.
- Regenerated the checked-in docs artifacts from the supported command path so the repo starts from one coherent Pages state.

**Tests:** `python3 -m pytest -q tests/test_pages_refresh.py tests/test_landing_d2.py tests/test_site_engine.py` -> `93 passed in 1.92s`

**Next:** D2 regression coverage and D3 docs/report surfaces.

---

## D2: regression coverage for mixed-state Pages drift — COMPLETE

**Built:**
- Added regression coverage for rebuilding `docs/leaderboard.html` from `docs/data.json` during `agentkit pages-refresh --from-existing-data`.
- Added regression coverage for fresh `generated_at` timestamps on supported refresh runs that reuse existing repo payloads.
- Tightened workflow coverage so the push-time Pages job must stage `docs/leaderboard.html` together with the other generated docs surfaces.

**Tests:** `python3 -m pytest -q tests/test_pages_refresh.py tests/test_landing_d2.py tests/test_site_engine.py` -> `93 passed in 1.92s`

**Next:** D3 docs/build-report surfaces and final validation.

---

## D3: docs and handoff surfaces updated — COMPLETE

**Built:**
- Updated `README.md` so the supported `--from-existing-data` path explicitly documents the coherent regeneration of `docs/data.json`, `docs/leaderboard.html`, and `docs/index.html`.
- Added a changelog entry for the mixed-state Pages refresh fix.
- Rewrote `BUILD-REPORT.md` for this branch's Pages data-refresh pass.

**Tests:** awaiting final validation run.

**Next:** final focused tests, full `pytest -q`, and clean-state verification.


**Final validation:** `uv run --python 3.11 --extra api --with pytest pytest -q` -> `4823 passed, 1 warning in 130.20s (0:02:10)`

---

## D1: core map engine + schema — COMPLETE

**Built:**
- Added deterministic repo-map schema models for summary, important paths, entrypoints, scripts, tests, subsystems, hints, risks, and contract handoff.
- Added `agentkit_cli/map_engine.py` with offline-safe local repo walking, stable ordering, junk-directory ignores, language counting, entrypoint/script/test detection, subsystem inference, and explainable hints.
- Added targeted map fixtures covering a basic Python repo, a workspace-style monorepo, a script-heavy repo, and an empty repo.
- Added D1-focused tests for fixture mapping, ignored junk directories, empty repos, and local paths with spaces.

**Tests:** `uv run pytest -q tests/test_map.py tests/test_main.py` -> `17 passed in 1.29s`

**Next:** D2 command surface tightening, then D3/D4 docs and handoff polish.

---

## D2: `agentkit map` CLI command — COMPLETE

**Built:**
- Added `agentkit map <target>` wiring with `--json`, `--output`, and `--format text|markdown|json` support.
- Added Rich terminal rendering plus deterministic markdown and JSON outputs from one shared map engine.
- Tightened local-path handling so bare existing directories work first-class, including paths with spaces.

**Tests:** `uv run pytest -q tests/test_map.py tests/test_main.py` -> `17 passed in 0.67s`

**Next:** D3 explorer-grade hints and D4 contract handoff polish.

---

## D3: explorer-grade hints and task boundaries — COMPLETE

**Built:**
- Added deterministic subsystem inference from code-bearing directories plus workspace and pyproject tooling signals.
- Added grounded work-surface hints, next-step explorer suggestions, and risk flags for missing tests, missing context files, and unclear script surfaces.
- Kept heuristics explainable and fully local, with no hidden LLM dependency.

**Tests:** `uv run pytest -q tests/test_map.py tests/test_main.py` -> `17 passed in 0.67s`

**Next:** D4 contract workflow bridge and docs.

---

## D4: contract integration surface — COMPLETE

**Built:**
- Added a deterministic `contract_handoff` block to the repo-map schema plus rendered markdown/text sections for manual `map -> contract` handoff.
- Updated README with a supported `agentkit map` workflow that saves the explorer artifact before drafting a build contract.
- Added coverage that asserts the rendered map includes the contract-handoff section and prompt seed.

**Tests:** `uv run pytest -q tests/test_map.py tests/test_main.py tests/test_landing_d5.py tests/test_user_scorecard_d5.py` -> `28 passed in 0.86s`

**Next:** D5 versioning, reports, required validation scripts, and full-suite verification.

---

## D5: docs, reports, and release surfaces — COMPLETE

**Built:**
- Updated README with `agentkit map` purpose, usage, and explicit local plus GitHub examples.
- Bumped package metadata to `1.3.0` in `pyproject.toml` and `agentkit_cli/__init__.py`, and added a v1.3.0 changelog entry.
- Rewrote `BUILD-REPORT.md` and added `BUILD-REPORT-v1.3.0.md` for the repo-map release.
- Ran the required pre-action recall, contradiction scan, hygiene check, focused validation, and final full-suite pass.

**Tests and checks:**
- `uv run pytest -q tests/test_map.py tests/test_main.py tests/test_landing_d5.py tests/test_user_scorecard_d5.py` -> `28 passed in 0.86s`
- `uv run pytest -q tests/test_daily_d5.py` -> `13 passed in 0.03s`
- `uv run pytest -q` -> `4833 passed, 1 warning in 135.18s (0:02:15)`
- `bash /Users/mordecai/.openclaw/workspace/scripts/pre-action-recall.sh release agentkit-cli /Users/mordecai/repos/agentkit-cli-v1.3.0-map` -> completed
- `bash /Users/mordecai/.openclaw/workspace/scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.3.0-map` -> `0 findings`
- `bash /Users/mordecai/.openclaw/workspace/scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.3.0-map` -> `0 findings`

**Final status:** all deliverables complete, validations green, and the repo is ready for a later release-completion pass.

---

## D1: deterministic bundle engine + schema — COMPLETE

**Built:**
- Added `agentkit_cli/bundle.py` with a schema-backed `HandoffBundle` result that deterministically composes source context, source-audit output, repo map output, contract surface detection, and explicit gap reporting.
- Reused existing `ContractEngine`, `SourceAuditEngine`, and `RepoMapEngine` paths instead of inventing new repo-understanding semantics.
- Added focused bundle-engine coverage for assembled surfaces, explicit missing-contract gaps, and stable JSON output.

**Tests:** `python3 -m pytest -q tests/test_bundle.py tests/test_source_audit_workflow.py tests/test_contract_d2.py tests/test_map.py tests/test_main.py` -> `29 passed in 6.32s`

**Next:** D2 CLI wiring and portable markdown rendering.

---

## D2: `agentkit bundle` CLI workflow — COMPLETE

**Built:**
- Added `agentkit_cli/commands/bundle_cmd.py` plus `agentkit bundle <path>` wiring in `agentkit_cli/main.py`.
- Added portable markdown output with sections for source, source audit, architecture map, execution contract, and open gaps, plus `--json` for stable machine-readable output.
- Kept partial upstream availability explicit by surfacing a saved-contract gap while still including the deterministic map handoff prompt fallback.

**Tests:** `python3 -m pytest -q tests/test_bundle.py tests/test_source_audit_workflow.py tests/test_contract_d2.py tests/test_map.py tests/test_main.py` -> `29 passed in 6.32s`

**Next:** D3 docs, versioning, reports, and final validation.

---

## D3: docs, workflow narrative, and validation — COMPLETE

**Built:**
- Updated README so the repo-understanding story is now `source -> audit -> map -> contract -> bundle`, with a first-class `agentkit bundle` section and end-to-end handoff examples.
- Added the v1.6.0 changelog entry, bumped package metadata to `1.6.0`, and rewrote `BUILD-REPORT.md` plus `BUILD-REPORT-v1.6.0.md` for this branch state.
- Extended bundle coverage with a realistic `source -> contract -> bundle` workflow assertion and reconciled the version test to the new release line.
- Ran the required release contradiction scan and hygiene check from the shared workspace script path because the contract's repo-local script paths are absent in this worktree.

**Tests and checks:**
- `python3 -m pytest -q tests/test_bundle.py tests/test_source_audit_workflow.py tests/test_contract_d2.py tests/test_map.py tests/test_main.py` -> `30 passed in 1.38s`
- `python3 -m pytest -q tests/test_bundle.py tests/test_source_cmd.py tests/test_source_audit.py tests/test_source_audit_workflow.py tests/test_contract_d2.py tests/test_map.py tests/test_main.py` -> `40 passed in 1.66s`
- `bash /Users/mordecai/.openclaw/workspace/scripts/pre-action-recall.sh release agentkit-cli /Users/mordecai/repos/agentkit-cli-v1.6.0-handoff-bundle && bash /Users/mordecai/.openclaw/workspace/scripts/check-status-conflicts.sh /Users/mordecai/repos/agentkit-cli-v1.6.0-handoff-bundle` -> no contradictory success/blocker narratives found
- `bash /Users/mordecai/.openclaw/workspace/scripts/post-agent-hygiene-check.sh /Users/mordecai/repos/agentkit-cli-v1.6.0-handoff-bundle` -> `Total findings: 0`

**Next:** final commit and release-readiness check.
