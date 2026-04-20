# Progress Log — agentkit-cli release chronology

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
