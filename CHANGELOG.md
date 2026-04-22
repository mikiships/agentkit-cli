# Changelog

## [1.29.0] - 2026-04-21

### Fixed
- Taught the flagship `agentkit spec` flow to recognize when `flagship-post-closeout-advance` is already closed out in current repo truth, suppress replay of that finished lane, and promote the fresh `flagship-adjacent-next-step` recommendation instead of the generic subsystem fallback.
- Added focused regression coverage across spec engine, command, workflow, and CLI entry paths for the post-closeout flagship replay case.

### Docs
- Advanced `.agentkit/source.md`, `BUILD-TASKS.md`, and `progress-log.md` to truthful `v1.29.0` release-ready status before release completion.
- Completed strict release proof for `v1.29.0`: current-tree validation, branch push, annotated tag push, and PyPI publish all verified directly.
- Recorded chronology truth that shipped `v1.29.0` is the peeled tag commit `404ada0eb6cf8092659d567b10f3c28448aafc66`, while later branch-head commit `f869a12f54501abe115a7369d75d51c0b1d19656` is docs-only release-surface reconciliation.

## [1.28.0] - 2026-04-21

### Fixed
- Taught the flagship `agentkit spec` flow to detect when `flagship-concrete-next-step` is already closed out in repo truth and suppress replay of that finished lane.
- Promoted a fresh `flagship-post-closeout-advance` recommendation and contract seed so the self-spec flow advances past the just-finished v1.27.0 lane.
- Added focused regression coverage across engine, command, workflow, and CLI entry paths for the post-closeout flagship replay case.

### Docs
- Advanced `.agentkit/source.md`, BUILD-TASKS, BUILD-REPORT, FINAL-SUMMARY, and progress surfaces to truthful `v1.28.0` local-only status.
- Completed strict release proof for `v1.28.0`: branch push, annotated tag push, and PyPI publish all verified directly.
- Recorded chronology truth that shipped `v1.28.0` is the peeled tag commit `1a6a8a366e43c28d1c227fd7acac7d1806efb6f9`, while later branch-head commits are docs-only release-surface reconciliation.

## [1.27.0] - 2026-04-21

### Fixed
- Taught the flagship `agentkit spec` flow to emit a concrete next lane after shipped-truth sync, so the primary recommendation now resolves to `flagship-concrete-next-step` for the repo's own flagship case.
- Added focused regression coverage across engine, command, workflow, and CLI entry paths for the concrete-next-step recommendation.

### Docs
- Reconciled local release surfaces for truthful `v1.27.0` status, including the changelog entry required by the release consistency checks.

## [1.26.0] - 2026-04-21

### Fixed
- Taught `agentkit spec` to recognize when the adjacent `spec grounding` increment is already shipped or local release-ready, so it no longer re-proposes the v1.25.0 work.
- Added shipped-adjacent regression coverage across command and workflow paths, and promoted a `shipped-truth-sync` recommendation when the next honest step is refreshing stale flagship source truth.

### Docs
- Refreshed `.agentkit/source.md`, BUILD-TASKS, BUILD-REPORT, FINAL-SUMMARY, and progress surfaces for truthful `v1.26.0` local closeout.

## [1.25.0] - 2026-04-21

### Fixed
- Grounded `agentkit spec` in current repo truth so the flagship repo no longer recommends the already-satisfied self-hosting/source-readiness objective.
- Added regression coverage for canonical-source-ready repos with shipped/local-ready workflow artifacts, and promoted an `adjacent-grounding` recommendation when the honest next increment is improving spec grounding itself.

### Docs
- Updated BUILD-REPORT, FINAL-SUMMARY, and progress surfaces for truthful `v1.25.0` local closeout.

## [1.24.0] - 2026-04-21

### Fixed
- Kept `agentkit spec --json` stdout machine-readable when `--output-dir` is used by routing the human `Wrote spec directory: ...` notice to stderr instead of stdout.
- Added regression coverage for deterministic JSON stdout in the spec command and preserved the full `source -> audit -> map -> spec -> contract` workflow validation.

### Docs
- Updated the active build, summary, and progress surfaces so this lane truthfully records `v1.24.0` as a local release candidate until the external release surfaces are proven.

## [1.23.0] - 2026-04-21

### Added
- Added a real repo-local `.agentkit/source.md` for the flagship `agentkit-cli` repo so source-audit and spec no longer fall back to legacy `AGENTS.md`.
- Added explicit self-hosting guidance for objective, scope, constraints, validation, and deliverables in the canonical source surface.

### Docs
- Updated the active build, summary, and progress surfaces so `v1.23.0` truthfully records local self-spec source readiness while `v1.22.0` remains the last shipped release.

## [1.22.0] - 2026-04-21

### Added
- Added `agentkit spec`, a deterministic next-build planning step that turns source context, source-audit readiness, repo-map context, and recent workflow artifacts into one primary adjacent-build recommendation plus bounded alternates.
- Added stable spec markdown and JSON rendering, `--output`, `--output-dir`, and direct contract seeding through `agentkit contract --spec`.
- Added focused coverage for happy-path, missing-upstream, contradictory-upstream, fallback, and `source -> audit -> map -> spec -> contract` workflow behavior.

### Docs
- README, BUILD-REPORT, FINAL-SUMMARY, and progress surfaces updated so the supported repo-understanding lane now becomes `source -> audit -> map -> spec -> contract`, with `v1.22.0` left in truthful local release-ready state only.

## [1.21.0] - 2026-04-21

- Added `agentkit merge`, a local-only merge workflow that consumes saved `land` artifacts plus local git and worktree evidence.
- Added deterministic merge markdown and JSON reports, per-lane merge packets, explicit `merge-now`, `blocked`, `waiting`, and `already-landed` visibility, and dry-run-by-default local apply support behind `--apply`.
- Added conflict-aware local merge execution that stops on dirty-state blockers or merge conflicts and writes truthful result status instead of continuing blindly.

## [1.20.0] - 2026-04-21

- Added `agentkit land`, a local-only landing workflow that consumes saved `closeout`, `relaunch`, `resume`, and `reconcile` artifacts plus local git/worktree evidence.
- Added deterministic landing markdown and JSON reports, per-lane `packet.md` landing packets, likely target-branch context, and explicit landing-order guidance for merge-ready lanes.
- Preserved review-required, waiting, and already-closed lanes explicitly so operators can turn closeout state into one truthful local landing plan without mutating git state.

## [1.19.0] - 2026-04-20

- Added `agentkit closeout`, a local-only closeout workflow that consumes saved `relaunch`, `resume`, and `reconcile` artifacts plus local worktree evidence.
- Added deterministic closeout markdown and JSON reports, plus per-lane `packet.md` closeout packets with merge-readiness reasons, human verification notes, and follow-on unblock notes.
- Preserved waiting, review-required, and already-closed lanes explicitly so operators can close out a relaunch lane set without manual restitching.

## [1.18.0] - 2026-04-20

### Added
- Added `agentkit relaunch` as a deterministic continuation step after `resume`, with stable markdown and JSON output plus per-lane relaunch packet directories.
- Added schema-backed relaunch plan structures that validate saved `resume`, `reconcile`, and `launch` evidence before surfacing fresh relaunch-ready packets.
- Added fresh per-lane `handoff.md` relaunch packets, helper command files, stale-worktree review notes, and preserved `waiting`, `review-only`, and `completed` visibility alongside eligible `relaunch-now` lanes.
- Added focused relaunch engine, CLI, and workflow tests covering `launch -> observe -> supervise -> reconcile -> resume -> relaunch`.

### Changed
- Extended the documented handoff lane so the supported local continuation flow now ends with `relaunch` after `resume`.
- Bumped local version surfaces from `1.17.0` to `1.18.0` for this branch.

## [1.17.0] - 2026-04-20

### Added
- Added `agentkit resume` as a deterministic continuation step after `reconcile`, with stable markdown and JSON output plus per-lane resume packet directories.
- Added schema-backed resume plan structures and dependency-aware resume classification for `relaunch-now`, `waiting`, `review-only`, and `completed` outcomes.
- Added contradiction checks for malformed reconcile summaries, missing upstream artifacts, incomplete saved state, and serialization-group conflicts before any resume plan is emitted.
- Added focused resume engine, CLI, integration, and workflow tests covering `launch -> observe -> supervise -> reconcile -> resume`.

### Changed
- Extended the documented handoff lane so the supported local continuation flow now ends with `resume` after `reconcile`.
- Bumped local version surfaces from `1.16.0` to `1.17.0` for this branch.

## [1.16.0] - 2026-04-20

### Added
- Added `agentkit reconcile` for deterministic post-observe and post-supervise lane closeout from saved `launch.json`, observe artifacts, supervise artifacts, and local dependency state.
- Added stable reconcile markdown and JSON rendering, `--output`, `--output-dir`, per-lane reconciliation packets, next-execution ordering, and newly unblocked lane reporting.
- Added regression coverage for `resolve -> dispatch -> stage -> materialize -> launch -> observe -> supervise -> reconcile`, dirty-lane review handling, launched-without-stable-evidence review handling, missing observe or supervise artifacts, and serialized lane unblocking.

### Docs
- README, BUILD-REPORT, FINAL-SUMMARY, and progress surfaces updated so the supported handoff lane now ends with `reconcile` after `supervise`, with `v1.16.0` left in truthful local release-ready state only.

## [1.15.0] - 2026-04-20

### Added
- Added `agentkit supervise` for deterministic post-launch local lane supervision from saved `launch.json` artifacts and local worktree state.
- Added stable supervision markdown and JSON rendering, `--output`, `--output-dir`, `--launch-path`, and per-lane supervision packets.
- Added regression coverage for `resolve -> dispatch -> stage -> materialize -> launch -> supervise`, serialized unblocking, missing worktrees, missing packets, dirty worktrees, and detached HEAD drift.

### Docs
- README, BUILD-REPORT, FINAL-SUMMARY, and progress surfaces updated so the supported handoff lane now ends with `supervise` after `observe`, with shipped `v1.15.0` chronology reconciled across the tested release commit, remote refs, PyPI payload, and later docs-only branch head.

## [1.14.0] - 2026-04-20

### Added
- Added `agentkit observe` for deterministic post-launch lane outcome observation from saved `launch.json` artifacts, lane worktrees, and explicit `.agentkit/observe/result.json` evidence packets.
- Added stable observe markdown and JSON rendering, `--output`, `--output-dir`, per-lane observe packets, summary counts, and recommended next actions for orchestration.
- Added regression coverage for `resolve -> dispatch -> stage -> materialize -> launch -> observe`, waiting and blocked carry-forward states, manual/generic unknown outcomes, malformed evidence failures, and packet-directory output.

### Docs
- README, BUILD-REPORT, FINAL-SUMMARY, and progress surfaces updated so the supported handoff lane now ends with `observe` after `launch`, with `v1.14.0` left in truthful local release-ready state only.

## [1.13.0] - 2026-04-20

### Added
- Added `agentkit launch` for deterministic post-materialize launch planning from saved `materialize.json` artifacts and per-lane `.agentkit/materialize/` handoff packets.
- Added stable launch markdown and JSON rendering, `--output`, `--output-dir`, and explicit `--execute` support for eligible local `codex` and `claude-code` targets.
- Added portable launch packet directories with top-level `launch.md` and `launch.json`, per-lane `launch.md` and `launch.json`, and reusable helper command files.
- Added regression coverage for `resolve -> dispatch -> stage -> materialize -> launch`, serialized waiting lanes, missing artifacts, unsupported execute targets, and missing-tool failures.

### Docs
- README, BUILD-REPORT, FINAL-SUMMARY, and progress surfaces updated so the supported handoff lane now ends with `launch` after `materialize`, with shipped `v1.13.0` chronology reconciled across the tested tag, remote branch history, and live PyPI truth.

## [1.12.0] - 2026-04-20

### Added
- Added `agentkit materialize` for deterministic local worktree creation from a saved `stage.json`, with dry-run planning, collision refusal, serialized waiting lanes, and local-only `git worktree add` execution.
- Added seeded `.agentkit/materialize/` handoff directories inside each created worktree, including copied lane `stage.json`, copied `stage.md`, machine-readable `materialize.json`, and target-aware `handoff.md`.
- Added regression coverage for `resolve -> dispatch -> stage -> materialize`, dry-run stability, serialized wait preservation, branch-collision failure handling, and target-specific handoff notes.

### Docs
- README, progress, blocker, build-report, and final-summary surfaces updated so the supported handoff lane now ends with `materialize` after `stage`, with shipped `v1.12.0` chronology reconciled across branch, tag, and PyPI truth.

## [1.11.0] - 2026-04-20

### Added
- Added `agentkit stage` for deterministic post-dispatch staging plans with suggested branch names, worktree names, worktree paths, serialization groups, and portable per-lane stage packets.
- Added stage packet directories with `stage.md`, `stage.json`, and per-lane `stage.md` and `stage.json` files under `lanes/<lane-id>/`.
- Added regression coverage for `resolve -> dispatch -> stage`, saved-dispatch validation, target mismatch failures, serialized wait notes, and schema-stable stage JSON output.

### Docs
- README, BUILD-REPORT, and progress surfaces updated so the supported handoff lane now ends with `stage` after `dispatch`.

## [1.10.0] - 2026-04-20

### Added
- Added `agentkit dispatch` for deterministic post-resolve execution planning with explicit phases, lane ownership, dependency edges, and target-aware runner packets.
- Added portable dispatch packet directories with `dispatch.md`, `dispatch.json`, and per-lane markdown and JSON packet files.
- Added regression coverage for `resolve -> dispatch`, overlapping ownership serialization, unresolved-blocker pause behavior, and fallback single-lane planning when no saved upstream planning artifacts exist.

## [1.9.0] - 2026-04-20

### Added
- `agentkit resolve` for consuming a clarify-ready handoff plus explicit answers and turning them into a deterministic resolved packet.
- Stable resolve markdown and JSON rendering with resolved questions, remaining blockers, remaining follow-ups, confirmed assumptions, superseded assumptions, unresolved assumptions, and an updated execution recommendation.
- Focused workflow coverage for the full `source -> source-audit -> map -> contract -> bundle -> taskpack -> clarify -> resolve` lane, including incomplete-answer and contradiction pauses.

### Docs
- README and local build/progress surfaces updated so the supported handoff story now ends with `resolve` after `clarify`.

## [1.8.0] - 2026-04-20

### Added
- `agentkit clarify` for turning the `source -> source-audit -> map -> contract -> bundle -> taskpack` lane into a deterministic clarification brief before coding-agent execution.
- Stable clarify markdown and JSON rendering with explicit blocking questions, follow-up questions, assumptions, contradictions, and execution recommendations.
- Focused workflow coverage for end-to-end clarify handoff, missing upstream surfaces, and contradictory source guidance.

### Docs
- README and progress/build surfaces updated so the supported handoff story is now `source -> audit -> map -> contract -> bundle -> taskpack -> clarify`.

## [1.7.0] - 2026-04-20

### Added
- `agentkit taskpack` for turning the full `source -> source-audit -> map -> contract -> bundle` lane into an execution-ready packet for coding agents.
- Stable taskpack markdown and JSON rendering with explicit durable context, task brief, execution checklist, target-aware instructions, and carried-forward gap reporting.
- Packet-directory output with `taskpack.md` and `taskpack.json`, plus focused workflow coverage for `generic`, `codex`, and `claude-code` handoffs.

### Docs
- README, BUILD-REPORT, BUILD-REPORT-v1.7.0, and progress log updated to make the full handoff story `source -> audit -> map -> contract -> bundle -> taskpack`.

## [1.6.0] - 2026-04-20

### Added
- `agentkit bundle` for deterministic handoff packaging across canonical source, source-audit findings, repo map context, contract artifacts, and explicit gap reporting.
- Stable markdown and JSON bundle rendering so one portable artifact can drive coding-agent handoff without re-stitching intermediate outputs.
- Focused workflow coverage for the full `source -> audit -> map -> contract -> bundle` lane, including partial-upstream and missing-contract cases.

### Docs
- README, BUILD-REPORT, and progress log updated to make the repo-understanding story `source -> audit -> map -> contract -> bundle`.

## [1.5.0] - 2026-04-20

### Added
- `agentkit source-audit` for deterministic canonical-source readiness checks before repo mapping and contract drafting.
- Schema-backed audit output covering missing execution-critical sections, legacy fallback detection, ambiguity heuristics, contradiction hints, and contract-readiness summaries.
- End-to-end `source -> source-audit -> map -> contract` workflow coverage alongside focused source-audit command tests.

### Docs
- README, BUILD-REPORT, and progress log updated for the local v1.5.0 source-audit release-readiness handoff.

## [1.4.0] - 2026-04-20

### Added
- Restored `agentkit contract` on top of the shipped repo-map branch with deterministic markdown and JSON contract output.
- Map-aware `agentkit contract --map` handoff for either a live local target or a saved `agentkit map` JSON artifact.
- Narrow contract/map command-surface validation covering contract, map, main CLI wiring, and release-adjacent docs/help surfaces.

### Docs
- README contract-handoff flow, BUILD-REPORT, versioned build report, and progress log updated for the local v1.4.0 release-readiness handoff.

## [1.3.0] - 2026-04-19

### Added
- `agentkit map` for deterministic repo architecture mapping across local checkouts and GitHub shorthand targets.
- Stable map schema covering repo summary, languages, important paths, entrypoints, scripts, tests, subsystem candidates, risks, and contract handoff guidance.
- Explorer-grade hints for likely work surfaces, missing context files, weak test coverage signals, and subsystem-first next steps.

### Docs
- README, BUILD-REPORT, and progress log updated for the v1.3.0 repo-map release.

## [1.1.0] - 2026-04-19

### Fixed
- `agentkit pages-refresh --from-existing-data` now rewrites `docs/leaderboard.html` and refreshes `docs/data.json` timestamps from the same canonical payload used for `docs/index.html`.
- `.github/workflows/update-pages.yml` now stages `docs/leaderboard.html` alongside `docs/data.json` and `docs/index.html`, so the push-time Pages refresh no longer leaves a mixed docs state behind.

### Added
- `agentkit burn` for local transcript cost observability across Codex, Claude Code, and OpenClaw-style session artifacts.
- Burn adapters and normalized schema for session, turn, tool, and cost-state ingestion.
- Burn analytics for project/model/provider/task/source aggregation, waste detection, and shareable HTML reporting.

### Docs
- README, BUILD-REPORT, and progress log updated for the shipped v1.1.0 burn observability release.

## [1.0.0] - 2026-04-19

### Added
- `agentkit source` for managing one dedicated agentkit-owned canonical source file at `.agentkit/source.md`, with explicit `--init`, `--promote`, `--from`, `--force`, and JSON reporting modes.
- Dedicated canonical-source detection in the projection engine so `.agentkit/source.md` wins over legacy root-level context files when present.

### Changed
- `agentkit project` now prefers `.agentkit/source.md` automatically while preserving backwards-compatible AGENTS/CLAUDE/AGENT/GEMINI/COPILOT/llms detection when the dedicated source is absent.
- `agentkit sync` now treats `.agentkit/source.md` as the drift authority, displays it in sync status output, and can regenerate missing projections from it.
- `agentkit init` now supports `--init-source`, `--promote-source`, and `--source-title` so a repo can enter the dedicated-source workflow during setup.

### Docs
- README, BUILD-REPORT, and progress log updated for the v1.0.0 canonical source workflow release.

## [0.99.0] - 2026-04-18

### Added
- `agentkit project` for projecting one canonical context source into `AGENTS.md`, `CLAUDE.md`, `AGENT.md`, `GEMINI.md`, `COPILOT.md`, and `llms.txt` with dry-run, write, output-dir, drift-check, and JSON reporting modes.
- Shared `context_projections` engine with deterministic target metadata, source auto-detection priority, projection generation, and hash-backed drift detection.

### Changed
- `agentkit sync` now understands the expanded projection set while preserving the classic trio check behavior for existing repos.
- `agentkit init` can optionally fan out projections immediately with `--project-targets` and `--write-projections`.
- `agentkit migrate` now resolves the wider target alias set through the shared projection engine.

### Docs
- README, BUILD-REPORT, and progress log updated for the v0.99.0 context projection release.

## [0.98.0] - 2026-04-18

### Added
- `agentkit optimize --all` repo sweep mode for deterministic discovery of nested `CLAUDE.md` and `AGENTS.md` files, aggregate per-file review data, and machine-readable repo summaries.
- `agentkit optimize --check` CI-friendly exit behavior that fails only when at least one context file has a meaningful rewrite available.

### Changed
- optimize review rendering now supports aggregate text and markdown summaries with per-file verdicts, protected-section signals, warning summaries, and repo totals.
- `agentkit improve --optimize-context` now uses repo sweep semantics so broader workflows can safely optimize multiple context files in one pass.

### Docs
- README, BUILD-REPORT, BUILD-REPORT-v0.98.0, and progress log updated for the v0.98.0 optimize sweep release.

## [0.97.2] - 2026-04-18

### Changed
- Added CLI-level smoke coverage for `agentkit optimize` dry-run and `--apply` flows on realistic context files, including second-pass safe no-op behavior.
- Restored the tracked GitHub Pages front-page hooks and stat ids required by `pages-refresh` and `pages-sync` validation, so optimize release gating no longer trips over a stale `docs/index.html` surface.
- Aligned optimize review rendering tests with the shipped `Meaningful rewrite available` verdict wording and hardened the watch debounce regression test against timing flakes.

### Docs
- README, BUILD-REPORT, and progress log updated for the v0.97.2 optimize smoke-and-guardrails follow-up.

## [0.97.1] - 2026-04-18

### Changed
- Hardened `agentkit optimize` with real-world fixture coverage, stronger protected-section preservation for identity/autonomy/user-critical content, and deterministic no-op detection for already-tight context files.
- `agentkit optimize` review output now highlights protected sections, reports a clear no-op verdict, truncates very large diffs more safely, and skips `--apply` rewrites when the optimized candidate is effectively unchanged.
- `agentkit improve --optimize-context` and `agentkit run --improve --improve-optimize-context` now surface optimize failures as bounded workflow messages instead of corrupting the broader improvement pass.

### Docs
- README, BUILD-REPORT, and progress log updated for the v0.97.1 optimize hardening follow-up.

## [0.97.0] - 2026-04-17

### Added
- `agentkit optimize` command for deterministic dry-run review or in-place optimization of `CLAUDE.md` and `AGENTS.md`, with stats deltas, structured JSON, markdown/text review output, and unified diff rendering.
- `OptimizeEngine` plus optimize result schemas for local-first context analysis, bloat trimming, stale-instruction cleanup, and risky-instruction removal without LLM dependencies.
- `agentkit improve --optimize-context` and `agentkit run --improve --improve-optimize-context` integration so context optimization can compound with the existing improve workflow.

### Docs
- README, BUILD-REPORT, and progress log updated for the v0.97.0 optimize release.

## [0.96.0] - 2026-04-17

### Added
- `agentkit release-check` now hardens the full shipped-release surface with explicit `tests`, `smoke_tests`, `git_push`, `git_tag`, and `registry` checks, plus deterministic markdown summary output for CI and GitHub step summaries.
- `agentkit run --release-check` now appends release verification to the normal pipeline and includes the embedded release-check payload in JSON output.

### Changed
- Git branch and upstream validation now fail clearly on dirty worktrees, detached HEAD, missing upstream configuration, and missing local upstream refs.
- Local and remote tag verification now compare the release tag against `HEAD` correctly, including annotated tags via peeled refs.
- Release-check verdict propagation now updates final pipeline counts, saved last-run state, webhook payloads, and GitHub Checks conclusions consistently.

### Docs
- README, BUILD-REPORT, and release-hardening progress log updated for the v0.96.0 release-check handoff.

## [0.95.1] - 2026-03-23

### Fixed
- `agentkit pages-refresh`: restore `docs/index.html` dynamic sections (fetch script, `renderRecentlyScored`, source-badge CSS, community-scored-stat) after SIGTERM interrupted a prior run left the file in a stripped state.

## [0.95.0] - 2026-03-23

### Added
- `agentkit pages-sync` — reads all local history DB results and syncs them to `docs/data.json`, with optional `--push` to commit and push to GitHub. Supports `--dry-run`, `--json`, `--limit`.
- `--pages` flag on `agentkit analyze` — after a successful analysis, adds the result to the local leaderboard (docs/data.json) without pushing.
- `--pages` flag on `agentkit run` — same as analyze, adds run result to leaderboard.
- `agentkit pages-add github:owner/repo` — analyze a single repo and immediately add it to the leaderboard (+ optional `--push` to publish, `--share` to generate a scorecard URL).
- `source` field in `docs/data.json` — entries now carry `"source": "ecosystem" | "community" | "manual"`, enabling differentiation of organically-added vs ecosystem-scanned repos.
- Source badges in `docs/index.html` — leaderboard renders colored source chips (ecosystem vs community).
- "Community Scored: N" stat counter in `docs/index.html` — shows how many repos were added via community use.

### Changed
- `agentkit pages-refresh` now sets `source="ecosystem"` on all ecosystem-scanned repo entries.

## [0.94.1] - 2026-03-23

### Fixed
- `agentkit pages-refresh`: inject `recently-scored` section and fetch script into `docs/index.html` correctly on repeated runs; add `id="repos-scored-stat"` to the Repos Scored stat element for reliable JS targeting
- `BUILD-REPORT.md`: include verified full test count

## [0.94.0] - 2026-03-23

### Added
- **`agentkit pages-refresh` command**: refreshes the GitHub Pages leaderboard by scoring top repos across `python`, `typescript`, `rust`, and `go` ecosystems. Writes `docs/data.json`, `docs/leaderboard.html`, and updates stat counters in `docs/index.html`.
- **`docs/data.json`**: new JSON feed consumed by the GitHub Pages front-end to display live repo scores.
- **Live leaderboard on front page**: `docs/index.html` now fetches `/agentkit-cli/data.json` and renders a "Recently Scored Repos" section with name, score, grade chip, and ecosystem badge.
- **Repos-scored stat fixed**: the "0 repos scored" embarrassment is gone — the counter now reflects actual scored repo count from `data.json`.
- **Daily GitHub Actions workflow** (`.github/workflows/daily-pages-refresh.yml`): runs `agentkit pages-refresh` daily at 08:00 UTC and commits updated docs. Supports `workflow_dispatch` for manual runs.
- **Seed data**: `docs/data.json` seeded with 10 real repos (scores for `openai/openai-python`, `langchain-ai/langchain`, `vercel/ai`, and more).

## [0.93.0] - 2026-03-23

### Added
- **`agentkit changelog` command**: generates an AI-produced changelog from git commits + quality score deltas, formatted for GitHub releases and PR descriptions.
- **`ChangelogEngine`** (`agentkit_cli/changelog_engine.py`): parses git log (`from_git`), reads score history (`from_history`), and renders markdown or GitHub release body.
- **Conventional-commit grouping**: groups commits by `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, etc.
- **Score delta line**: includes `before → after (+delta)` quality score summary when history DB is available.
- **`--format` options**: `markdown` (default), `release` (GitHub release body with pip install), `json`.
- **`GITHUB_STEP_SUMMARY` support**: when env var is set and `--format release` is used, appends changelog to GitHub step summary.
- **`--create-release`**: creates a GitHub release via `gh release create` (only when `--version` is set and flag is explicitly passed).
- **`agentkit release-check --changelog`**: appends changelog preview to release-check output; adds `changelog_preview` key to `--json` output.
- **README**: added `## Changelog Generation` section with usage examples.

## [0.92.0] - 2026-03-22

### Added
- **`agentkit weekly-digest` command**: generates a curated "State of AI Agent Readiness" report from local history.
- **`WeeklyDigestEngine`** (`agentkit_cli/weekly_digest_engine.py`): assembles `DigestReport` from HistoryDB with graceful empty-state handling and placeholder repos.
- **`WeeklyDigestRenderer`** (`agentkit_cli/renderers/weekly_digest_renderer.py`): dark-theme HTML and Markdown renderers.
- **CLI flags**: `--share` (publish to here.now), `--output FILE`, `--json`, `--quiet`, `--since DAYS`, `--cron` (quiet+share, URL to stdout).
- **README**: added `## Weekly Digest` section with example usage.

## [0.91.0] - 2026-03-22

### Added
- **Interactive `/ui` page**: GitHub repo analysis form with loading spinner, results panel (score/grade/tool breakdown), error handling, and dark-theme styling. Vanilla JS, no frameworks.
- **`POST /analyze`**: Submit `{"repo": "owner/repo"}` for analysis. 120s timeout, max 5 concurrent analyses (in-memory semaphore), DB cache (results < 1h old returned as cached). Returns `{score, grade, tool_results, share_url, elapsed_seconds, cached}`.
- **`GET /analyze?repo=`**: Query-param variant of POST /analyze.
- **`GET /recent?limit=10`**: Recent analyses endpoint returning deduplicated latest results from history DB.
- **Recent analyses panel** in /ui with 30s auto-refresh polling.
- **`agentkit api --interactive`** flag: confirms the /ui form is enabled (always on, for documentation UX).
- **README**: "Interactive Demo" section documenting `agentkit api --share` for public demos.
- **`agentkit quickstart`** output: added `agentkit api --share` as a next-step suggestion.
- **`agentkit demo`** output: added shareable demo URL hint.
- **`docs/api.md`**: updated with POST /analyze, GET /recent, and interactive /ui documentation.
- 40 new tests across D1-D5.

## [0.90.0] - 2026-03-22

### Added
- **`agentkit api`**: Local FastAPI REST server exposing the analysis pipeline as HTTP endpoints. 8 endpoints: `/` (health), `/analyze/{owner}/{repo}`, `/score/{owner}/{repo}`, `/badge/{owner}/{repo}` (shields.io-compatible), `/trending`, `/history/{owner}/{repo}`, `/leaderboard`, and `/ui` (dark-theme HTML status page).
- **`agentkit_cli/api_server.py`**: FastAPI app with CORS enabled, DB-backed endpoints using existing `HistoryDB`, `/analyze` endpoint triggers subprocess on stale/missing cache, shields.io badge with color coding (brightgreen/yellow/orange/red).
- **`agentkit api --share`**: Optional ngrok tunnel for public sharing.
- **`agentkit doctor` api category**: Checks if the local API server is reachable at `http://127.0.0.1:8742`. Reports WARN (non-fatal) when not running.
- **`agentkit run --api-cache`**: Best-effort API cache warm-up after pipeline runs.
- **`docs/api.md`**: Full REST API documentation with curl examples and badge embed snippets.
- **`[api]` optional extras**: `pip install agentkit-cli[api]` installs fastapi, uvicorn, httpx.
- 57 new tests (D1: 29, D2: 11, D3: 8, D4: 9).

## [0.89.0] - 2026-03-22

### Added
- **`agentkit weekly`**: 7-day quality digest across all tracked projects. Shows per-project score changes (start/end/delta), top improvements, regressions, common findings, and recommended actions. Supports `--json`, `--output`, `--share`, `--tweet-only`, `--days`, and `--project` flags.
- **`WeeklyReportEngine`** (`agentkit_cli/weekly_engine.py`): Pure-Python engine reading the shared SQLite history DB. Computes deltas, trends, common findings, and tweet-ready summaries.
- **`render_weekly_html`** (`agentkit_cli/weekly_html.py`): Dark-theme GitHub-style HTML renderer for weekly reports.
- **`scripts/post-weekly.sh`**: Automation-friendly wrapper for cron use. Supports `--tweet-only`, `--share`, `--days`, and `--output`. Does NOT call frigatebird. Logs to `~/.local/share/agentkit/weekly-post-log.jsonl`.
- **docs/weekly.md**: Full documentation for the weekly command and post-weekly.sh.
- 49 new tests (D1: 22, D2: 11, D3: 16).

## [0.88.0] - 2026-03-22

### Fixed
- **`github_api._fetch_page`**: Fixed silent data loss for GitHub Search API responses. The function previously returned `[]` for any non-list response, but GitHub's search endpoint returns `{"items": [...], "total_count": N}`. Commands that rely on topic search — `agentkit populate`, `agentkit topic`, `agentkit topic-rank`, `agentkit topic-duel`, `agentkit topic-league`, `agentkit ecosystem`, `agentkit trending`, `agentkit user-rank`, `agentkit search` — all returned 0 repos silently. Fixed by extracting `data["items"]` when the response is a dict with an `items` key.
- Added 5 regression tests in `tests/test_github_api_fix.py`.

### Added
- **`agentkit frameworks`** (included in v0.87.0 source, now officially documented): detect which frameworks a project uses and check if the agent context file covers them. Supports Next.js, FastAPI, Django, Rails, Express, and 10+ other frameworks. `--generate` adds missing framework-specific sections automatically. 67 tests.

## [0.87.0] - 2026-03-22

### Fixed
- **`site_engine.generate_index()`**: Updated to generate a complete marketing landing page with all required sections: hero headline ("Benchmark AI Coding Agents"), pipeline stages (MEASURE/GENERATE/GUARD/LEARN/BENCHMARK), 6-tool feature grid, stats bar with `data-stat` attributes, commands table (cmd-table), Daily Trending section with `trending.html` nav link, Org Leaderboard section, Developer Profile Card section, and subscribe CTA. Fixes 14 failing tests across `test_landing_d1`, `test_trending_pages_d4`, `test_org_pages_d5`, `test_user_scorecard_d5`, and `test_daily_pages_d4`.
- **`_NAV` template**: Added `trending.html` and `#org-leaderboard` nav links so the global nav reflects current feature set.
- Regenerated `docs/index.html` with updated template to match test requirements.

## [0.86.0] - 2026-03-22

### Added
- **`agentkit hooks`** (D1-D4): new command group for managing pre-commit quality gate hooks.
- **`HookEngine`** (`agentkit_cli/hooks.py`): core engine with `install`, `uninstall`, `status`, and `check` methods.
- **`agentkit hooks install/status/uninstall/run`**: CLI surface for managing hooks.
- **`agentkit doctor` hooks category**: new `hooks.installed` check; `--category hooks` filter supported.
- **`agentkit setup-ci`**: hooks install suggestion in Next Steps.
- **`agentkit run`**: tip shown when hooks not installed.
- **`agentkit report` HTML**: "Hooks" section showing installation status.

## [0.85.0] - 2026-03-22

### Added
- **`agentkit frameworks`** (D1-D3): new command that detects which frameworks a project uses (Next.js, FastAPI, Django, Rails, React, Vue, Nuxt, Flask, Laravel, Express) and checks if CLAUDE.md/AGENTS.md has framework-specific coverage sections. Flags: `--json`, `--quiet`, `--min-score`, `--context-file`, `--share`, `--generate`.
- **`FrameworkDetector`** (`agentkit_cli/frameworks.py`): local file-only detection for 10+ frameworks using `package.json`, `requirements.txt`, `pyproject.toml`, `manage.py`, `Gemfile`, `composer.json`, and framework config files.
- **`FrameworkChecker`** (`agentkit_cli/frameworks.py`): scores each detected framework's agent context coverage (0-100), weighted 80% required / 20% nice-to-have sections.
- **`agentkit frameworks --generate`** (D3): auto-appends missing framework sections to CLAUDE.md/AGENTS.md. Idempotent (skips existing headings). Templates in `agentkit_cli/framework_templates.py` for all 10 frameworks.
- **`agentkit doctor`** framework coverage check (D4): warns if a detected framework scores < 60 in agent context coverage. Fix hint: `agentkit frameworks --generate`.
- **`agentkit run --frameworks`** (D4): runs framework coverage check after pipeline and includes results in JSON output.

## [0.84.1] - 2026-03-22
- **fix:** Restore missing content in `docs/index.html`: pipeline stages, feature grid (6 tools), commands table, Daily Trending / Org Leaderboard / Developer Profile Card sections, nav links. Add `stat-card` class to `site_engine.py` stats items. All 15 previously-failing D4/D5/landing tests now pass.

## [0.84.0] - 2026-03-21

### Added
- **`agentkit populate`** (D1): fetch top GitHub repos for configured topics via GitHub Topics API, score each with `agentkit analyze`, store results in history DB. Flags: `--topics`, `--limit`, `--force`, `--dry-run`, `--json`, `--quiet`.
- **`agentkit site --live`** (D2): implemented (was "not yet implemented"). Calls `PopulateEngine.populate()` before generating the site — single command to score + generate.
- **`agentkit site --deploy`** (D3): improved implementation — copies generated site to `docs/` (or `--deploy-dir`), runs `git add + commit + push`. New flags: `--repo-path`, `--deploy-dir`, `--commit-message`, `--no-push`.
- **`agentkit run --populate`** (D4): after pipeline run, call populate for detected topics. Flags: `--populate-topics`, `--populate-limit`.
- **`agentkit doctor` history check** (D4): warns if history DB has 0 entries, suggests `agentkit populate`.
- **Version bump** 0.83.0 → 0.84.0.

## [0.83.0] - 2026-03-21

### Added
- **`agentkit site`** (D1-D3): multi-page static site generator from history DB. Generates `index.html`, per-topic pages, per-repo detail pages, and `sitemap.xml` with dark theme, SEO meta tags, JSON-LD structured data.
- **`SiteEngine`** (`agentkit_cli/site_engine.py`): core engine with `generate_site()`, `generate_index()`, `generate_topic_page()`, `generate_repo_page()`, `generate_sitemap()`.
- **`agentkit run --site <dir>`** (D4): auto-regenerate site index after a run.
- **`agentkit site --share`**: upload generated `index.html` to here.now and print URL.
- **`agentkit site --deploy`**: copy generated site into `docs/` for GitHub Pages.

## [0.82.0] - 2026-03-21

### Added
- **`agentkit leaderboard-page`** (D1): new command generates a public HTML leaderboard of top agent-ready GitHub repos by ecosystem (python, typescript, rust, go, javascript). Scores repos via `ExistingStateScorer`/heuristics, outputs dark-theme HTML with ecosystem tabs. Flags: `--output`, `--ecosystems`, `--limit`, `--share`, `--json`, `--pages`.
- **GitHub Pages workflow** (D2): `.github/workflows/update-leaderboard.yml` — weekly schedule, runs `leaderboard-page --pages`, commits result to `docs/leaderboard.html`.
- **SEO** (D3): generated HTML includes `<title>`, `<meta description>`, og: tags, JSON-LD ItemList schema.
- **`--embed github:owner/repo`** (D4): outputs markdown badge snippet with shields.io rank+score badge + leaderboard link; `--embed-only` skips full page generation.
- **Version bump** 0.81.1 → 0.82.0.

## [0.81.1] - 2026-03-21

### Fixed
- `agentkit hot`: Fix `ExistingStateScorer` call — use `score_all()`/`composite_score()` instead of non-existent `.score()` method; all repos now score correctly instead of returning N/A.
- `agentkit hot`: Filter sponsor/ad entries from GitHub trending HTML parse (skip owners `sponsors`, `orgs`, `topics`, `trending`).

## [0.81.0] - 2026-03-21

### Added
- **`agentkit hot`** (D1): new command fetches GitHub's daily trending repos, scores each via `ExistingStateScorer`, identifies the most surprising finding (top-trending with low score, or high-scoring top-repo), and outputs a tweet-ready insight. Supports `--language`, `--limit` (max 25), `--tweet-only`, `--share`, and `--json` flags.
- **HTML report** (D2): `agentkit hot` generates a dark-theme HTML table with all scored repos, ranked by ExistingState score, with the most surprising finding highlighted.
- **`scripts/post-hot.sh`** (D3): companion script to post-daily-duel.sh and post-spotlight.sh. Runs `agentkit hot --tweet-only`, posts via frigatebird, logs to `~/.local/share/agentkit/hot-post-log.jsonl`. Supports `--share` and `--dry-run` flags.
- **`agentkit doctor` hot check** (D4): new `hot.trending_access` check verifies GitHub trending page is reachable; degrades gracefully (warns, not fails) when offline — hot uses fallback repo list.
- **Version bump** 0.80.0 → 0.81.0.

## [0.80.0] - 2026-03-21

### Added
- **`agentkit spotlight-queue`** (D1): new command with subcommands `add`, `list`, `next`, `remove`, `clear`, `seed`, `mark-done`. Manages a rotation queue for the spotlight cron so it can run daily without manual `--target` input. Queue stored at `~/.local/share/agentkit/spotlight-queue.json`. `next` outputs plain `owner/repo` for scripting.
- **`scripts/post-spotlight.sh` queue integration** (D2): when no `--target` is given, the script now calls `agentkit spotlight-queue next` to get the next repo automatically. After a successful post, `agentkit spotlight-queue mark-done` is called to update the last-spotlighted date.
- **Auto-seed on first use** (D3): if `spotlight-queue.json` does not exist, it is automatically seeded with 10 default repos on first command invocation.
- **`agentkit doctor` spotlight-queue check** (D4): new check warns when queue is empty or has fewer than 3 repos; shows queue size and next repo on pass.
- **Version bump** 0.79.0 → 0.80.0.

## [0.79.0] - 2026-03-21

### Added
- **`agentkit spotlight --tweet-only`** (D1): outputs a ≤280-char tweet-ready summary to stdout with no Rich formatting. Combines with `--share` to append the here.now URL. Mirrors the existing `daily-duel --tweet-only` pattern.
- **`scripts/post-daily-duel.sh --share`** (D2): new `--share` flag runs `agentkit daily-duel --share --tweet-only`, posts tweet with here.now URL included. Falls back to plain tweet if upload fails. Log entries now include `share_url` field.
- **`scripts/post-spotlight.sh`** (D3): new companion script to `post-daily-duel.sh`. Runs `agentkit spotlight --share --tweet-only`, posts via frigatebird, logs to `~/.local/share/agentkit/spotlight-post-log.jsonl`. Supports `--dry-run` flag (prints tweet text without posting).

## [0.78.0] - 2026-03-21

### Added
- **ExistingStateScorer**: new `agentkit_cli/existing_scorer.py` — scores repos based on pre-existing documentation artifacts (agent context files, README quality, CONTRIBUTING, CHANGELOG, CI config, test coverage, type annotations) without running agentmd generation
- **`--existing` flag** for `agentkit daily-duel` (default: `True`) and `agentkit duel` — skips agentmd generation step and uses ExistingStateScorer instead, fixing the circular scoring problem
- **`analyze_existing()`** function in `analyze.py` — lightweight clone-and-score pipeline using ExistingStateScorer
- `RepoDuelEngine(existing=True)` mode for direct ExistingStateScorer-based duels
- `DailyDuelEngine` defaults `existing=True` — daily-duel now produces real score differences between repos

### Fixed
- **Circular scoring bug**: `daily-duel` previously always returned 100/100 draws because agentmd would generate a valid CLAUDE.md before scoring it. With `--existing` mode, only pre-existing docs artifacts are scored, producing real differentials.

## [0.77.0] - 2026-03-21

### Added
- **Asymmetric pairs**: 24 new asymmetric repo pairs in `PRESET_PAIRS` (legacy vs modern: bottle vs fastapi, pylint vs ruff, tornado vs uvicorn, psycopg2 vs asyncpg, backbone vs react, etc.) — guaranteeing clear winners with real score differentials
- `ASYMMETRIC_PAIRS` and `BALANCED_PAIRS` sub-lists in `daily_duel.py`; `PRESET_PAIRS` is their union (42+ total pairs)
- Each pair tuple gains a 4th element: `narrative_type` — `"asymmetric"` or `"balanced"`
- `pick_pair_full()` method on `DailyDuelEngine` returning full 4-tuple
- `_diff_tier()` helper: classifies score differences as `"large"` (>30), `"medium"` (15-30), or `"small"` (<15)
- Large-diff tweet templates (4) — "crushes", "dominates", "doc gap" framing
- Medium-diff tweet templates (4) — "beats", "edges out", "outpaces" framing
- Both template sets are seeded-deterministic (same seed = same template)
- `--calendar` output now shows **Narrative** column (asymmetric/balanced)
- `DailyDuelResult.narrative_type` field included in JSON output
- New categories: `"cli-tools"`, `"legacy-vs-modern"`

### Changed
- Clear-winner tweet copy (score diff > 5) now uses narrative templates instead of the dry "Winner: X on N/M dimensions" format
- `_build_tweet_text` uses `_diff_tier` to route large/medium/small diffs to appropriate template sets
- Short repo names (sans owner) used in tweet templates for brevity

## [0.76.0] - 2026-03-21

### Added
- `CATEGORY_INSIGHTS` dict in `daily_duel.py` with 3-5 insight phrases per category (web-frameworks, http-clients, ml-ai, testing, async-networking, databases, js-frameworks, devtools)
- `_build_tweet_text()` helper: generates personality-rich tweet text with three cases: draw (champion framing + category insight), near-draw (≤5 pts, margin-first), clear winner (existing format preserved)
- `--tweet-only` flag on `agentkit daily-duel`: prints only tweet text to stdout and exits — designed for piping to `frigatebird tweet`
- `scripts/post-daily-duel.sh`: shell wrapper that runs `daily-duel --tweet-only`, validates tweet length, posts via `frigatebird`, and logs JSON result to `~/.local/share/agentkit/daily-duel-post-log.jsonl`

### Changed
- Draw case tweet no longer says "Winner: draw on 0/4 dimensions" — replaced with category-contextual champion framing
- Near-draw case (score diff ≤ 5) now leads with "extremely close" and the margin
- `_run_explicit_pair` in `daily_duel_cmd.py` updated to use shared `_build_tweet_text()` logic

## [0.75.0] - 2026-03-20

### Added
- `agentkit daily-duel`: zero-input command that auto-selects contrasting GitHub repo pairs (20+ presets across web-frameworks, http-clients, ml-ai, testing, devtools, js-frameworks), runs a repo duel, and outputs tweet-ready text (≤280 chars)
- `DailyDuelEngine` with deterministic `pick_pair(seed)` (default = today's date) and `run_daily_duel()`
- `DailyDuelResult` extending `RepoDuelResult` with `tweet_text`, `pair_category`, `seed`
- `--calendar` flag: shows 7-day schedule preview as a Rich table (no analysis)
- `--pair REPO1 REPO2`: override auto-pick with explicit repos
- `--seed`, `--deep`, `--share`, `--json`, `--output`, `--quiet` flags
- Writes `~/.local/share/agentkit/daily-duel-latest.json` on every run (for cron consumption)
- History DB integration with label `daily_duel`

## [0.74.0] - 2026-03-20

### Added
- `agentkit repo-duel github:owner/repo1 github:owner/repo2` — head-to-head agent-readiness comparison of two GitHub repos
- `RepoDuelEngine` with per-dimension winner computation (composite_score, context_coverage, test_coverage, lint_score, and optional redteam_resistance with `--deep`)
- `RepoDuelResult` and `DimensionResult` dataclasses with `to_dict()` for JSON export
- `RepoDuelHTMLRenderer` — dark-theme standalone HTML duel report (matches existing duel family style)
- `--deep` flag adds redteam resistance dimension, `--share` uploads to here.now, `--json`, `--output`, `--quiet` flags
- `agentkit history --duels` — filter history to show only repo-duel runs
- `agentkit run --repo-duel` integration hook (pass `github:competitor/repo` to run a duel in pipeline)
- README: `agentkit repo-duel` section with fastapi vs flask example

## [0.73.0] - 2026-03-20

### Added
- `agentkit gist` command — publish analysis output as a permanent GitHub Gist (solves here.now 24h expiry problem)
- `GistPublisher` class in `agentkit_cli/gist_publisher.py` — mirrors HereNowPublisher pattern
  - Auth: `GITHUB_TOKEN` env var OR `gh auth token` CLI fallback
  - Public gists: no token required (GitHub allows unauthenticated public gist creation)
  - Private/secret gists: requires token
  - Returns `GistResult` with `url`, `gist_id`, `raw_url`, `created_at`
- `--gist` flag on `agentkit run`, `agentkit report`, `agentkit analyze` — auto-publishes results as gist after completion
- `gist-token` input and `gist-url` output added to `action.yml` for GitHub Actions integration

## [0.72.0] - 2026-03-20

### Added
- `agentkit spotlight` command — Repo of the Day: auto-select trending repo, deep-dive analyze, shareable dark-theme HTML report
- SpotlightEngine with candidate selection (avoids re-spotlighting), GitHub metadata enrichment, history DB recording
- SpotlightHTMLRenderer with dark-theme report including score, grade, findings, stars, language
- `--deep` flag for optional redteam + certify analysis
- `--topic` and `--language` filters for candidate auto-selection
- `--share` publishes HTML report to here.now
- `history --spotlights` flag to filter spotlight runs
- `report --spotlight-feed` flag for spotlight run feed
- `check_spotlight_github_access()` doctor check for GitHub API reachability

## [0.71.0] - 2026-03-20

### Added
- `agentkit ecosystem` — macro "State of AI Agent Readiness" scan across language/tech ecosystems
  - Built-in presets: `default` (python, typescript, rust, go, java), `extended` (12 ecosystems)
  - Custom preset via `--topics "python,rust,go"`
  - `EcosystemEngine` reuses `TopicLeagueEngine` — no duplicated scoring logic
  - Dark-theme HTML report with winner banner, standings table, per-ecosystem detail cards, insight panel
  - `--share` uploads via here.now, `--output` saves locally, `--parallel` (default True)
  - `--json` output with all required keys for pipeline consumers
  - `agentkit run --ecosystem <preset>` integration
  - `agentkit doctor` now verifies `agentkit ecosystem` availability
- `EcosystemHTMLRenderer` in `agentkit_cli/renderers/ecosystem_html.py`
- Language emoji map (python=🐍, rust=🦀, go=🐹, typescript=📘, java=☕, ...)

## [0.70.0] - 2026-03-20

### Added
- `agentkit topic-league <topic1> <topic2> ... <topicN>` — multi-topic standings comparison for 2–10 GitHub topics
- `TopicLeagueEngine` in `agentkit_cli/engines/topic_league.py` — fetch top repos for each topic via `TopicRankEngine`, compute aggregate scores, rank into standings
- `LeagueResult` dataclass with rank, topic, score, repo_count, top_repo, score_distribution (min/mean/max)
- `TopicLeagueHTMLRenderer` in `agentkit_cli/renderers/topic_league_html.py` — dark-theme HTML report with standings table (rank/topic/score bar/grade), per-topic detail cards, footer
- `--repos-per-topic N` (default 5, max 10), `--parallel`, `--json`, `--quiet`, `--output FILE`, `--share` options
- `agentkit run --topic-league "python rust go"` — optional topic-league step appended to the run pipeline
- GITHUB_TOKEN guard: warns without crashing when token is missing
- 50 new tests across 5 test files (D1–D5)

## [0.69.0] - 2026-03-20

### Added
- `agentkit topic-duel <topic1> <topic2>` — head-to-head agent-readiness comparison of two GitHub topics
- `TopicDuelEngine` in `agentkit_cli/engines/topic_duel.py` — fetch top repos for each topic, score via `TopicRankEngine`, compute per-dimension winners and aggregate scores
- `TopicDuelResult` dataclass with both topic results, dimension comparison, and overall winner
- `render_topic_duel_html` in `agentkit_cli/topic_duel_html.py` — dark-theme HTML report with side-by-side ranked tables, winner banner, and dimension comparison table
- `--repos-per-topic N` (default 5, max 10), `--json`, `--quiet`, `--output FILE`, `--share` options
- 41 new tests across 4 test files (D1-D4) + 5 D5 tests

## [0.68.0] - 2026-03-20

### Added
- `agentkit topic <topic>` — discover and rank top GitHub repos for a topic by agent-readiness score
- `TopicRankEngine` in `agentkit_cli/topic_rank.py` — search topic repos via GitHub Search API, score each via agentkit analyze (heuristic fallback), rank by score descending
- `TopicRankHTMLRenderer` in `agentkit_cli/topic_rank_html.py` — dark-theme HTML report with ranked repo table, grade distribution bars, top-repo spotlight, and star counts
- `agentkit run --topic-repos <topic>` — optional topic repo-rank step appended to the run pipeline
- Drill-down hint in `agentkit trending --topic <topic>` output: `agentkit topic <topic> for topic-specific repos`
- `--limit N` (default 10, max 25), `--language LANG`, `--json`, `--output FILE`, `--share`, `--quiet` options
- 48 new tests across 5 test files (D1-D5)

## [0.67.0] - 2026-03-20

### Added
- `agentkit user-rank <topic>` — discover top GitHub contributors for a topic, rank by agent-readiness score
- `UserRankEngine` in `agentkit_cli/user_rank.py` — search topic contributors, score via `UserScorecardEngine`, rank
- `UserRankHTMLRenderer` in `agentkit_cli/user_rank_html.py` — dark-theme HTML report with ranked table, grade distribution, top-scorer spotlight
- `agentkit run --topic <topic>` — optional user-rank step in the run pipeline
- 45 new tests across 5 test files (D1-D5)

## [0.66.0] - 2026-03-20

### Added
- `agentkit user-team github:<org>`: new command — analyze a GitHub org's top contributors for agent-readiness and produce a ranked team scorecard
- `TeamScorecardEngine` (`agentkit_cli/user_team.py`): fetches org contributors, scores each via `UserScorecardEngine`, and aggregates into team result with grade, top scorer, and distribution
- `TeamScorecardHTMLRenderer` (`agentkit_cli/user_team_html.py`): dark-theme HTML report with contributor ranking table, grade distribution bars, top-scorer callout, and GitHub avatars
- `--limit N` (default 10): max contributors to analyze
- `--json`: emit structured `TeamScorecardResult` JSON
- `--output FILE`: save HTML report to file
- `--share`: publish HTML report to here.now
- `--quiet`: suppress progress output for CI use

## [0.65.0] - 2026-03-19

### Added
- `agentkit user-badge github:<user>`: new command — generate a shields.io agent-readiness badge for any GitHub user's profile README
- `UserBadgeEngine` (`agentkit_cli/user_badge.py`): core engine for badge URL generation, README markdown, anybadge-compatible JSON
- `--score N` fast mode: skip GitHub scan, generate badge from provided score directly
- `--grade A` explicit grade override
- `--output FILE`: write badge markdown to file
- `--share`: publish user-scorecard HTML to here.now
- `--inject`: auto-inject badge into local README.md (idempotent, sentinel-based)
- `--dry-run`: preview inject without modifying files
- `--badge` flag on `agentkit user-scorecard`: prints badge markdown after scorecard output; adds `badge_url` to JSON
- `--badge` flag on `agentkit user-card`: prints badge markdown after card output; adds `badge_url` to JSON
- Badge grade thresholds: A≥90 (brightgreen), B≥75 (green), C≥60 (yellow), D≥45 (orange), F<45 (red)

## [0.64.0] - 2026-03-19

### Added
- `agentkit user-card github:<user>`: new command — generate a compact, embeddable agent-readiness card for a GitHub user, showing grade, score, context coverage, and top repo in a dark-theme HTML card
- `UserCardEngine` (`agentkit_cli/user_card.py`): core engine — lightweight wrapper over `UserScorecardEngine` that distils scorecard data into a compact `UserCardResult`
- `UserCardResult` dataclass with full `to_dict()` schema: username, avatar_url, grade, avg_score, total_repos, analyzed_repos, context_coverage_pct, top_repo_name, top_repo_score, agent_ready_count, summary_line
- `UserCardHTMLRenderer` (`agentkit_cli/renderers/user_card_html.py`): 400px dark-theme HTML card with avatar, grade badge, stats row, top-repo chip, and footer; includes Markdown embed snippet as HTML comment when `--share` used
- `upload_user_card`: upload card HTML to here.now, return URL
- `--limit N` (default 10, max 30): max repos to analyze
- `--min-stars N` (default 0): skip repos below star count
- `--skip-forks / --no-skip-forks` (default: True): exclude forked repos
- `--share`: publish HTML card to here.now
- `--json`: emit `UserCardResult` as JSON
- `--quiet`: print only the share URL (cron-friendly)
- `--user-card github:<user>` flag on `agentkit run`: triggers user-card after pipeline
- `--user-card github:<user>` flag on `agentkit report`: includes user-card section in report output
- History DB: each user-card run recorded as a row in `runs` table with `tool="user-card"`

## [0.63.0] - 2026-03-19

### Added
- `agentkit user-improve github:<user>`: new command — find a GitHub user's lowest-scoring public repos, auto-improve them (CLAUDE.md generation + hardening), and display a before/after quality lift report
- `UserImproveEngine` (`agentkit_cli/user_improve.py`): core engine — fetch repos, score them, select targets below threshold, clone and improve each in tempdir (always cleaned up), aggregate results
- `UserRepoScore` / `UserImproveResult` / `UserImproveReport` dataclasses with full `to_dict()` schema
- `UserImproveHTMLRenderer` (`agentkit_cli/renderers/user_improve_html.py`): dark-theme HTML report with avatar header, summary bar, per-repo before/after score bars and lift badges
- `upload_user_improve_report`: upload improvement HTML to here.now, return URL
- `--limit N` (default 5, max 20): max repos to improve
- `--below N` (default 80): only target repos scoring below this threshold
- `--share`: publish HTML improvement report to here.now
- `--json`: emit `UserImproveReport` as JSON
- `--dry-run`: show what would be improved, no changes applied
- `--user-improve github:<user>` flag on `agentkit run`: triggers user-improve after pipeline
- `--user-improve github:<user>` flag on `agentkit report`: includes user-improve section in report output
- History DB: each user-improve run recorded as a row in `runs` table with `tool="user-improve"`

## [0.62.0] - 2026-03-19

### Added
- `agentkit user-tournament github:<u1> github:<u2> [github:<uN>...]`: new command — bracket-style developer agent-readiness tournament for N GitHub users; round-robin for ≤8, bracket mode for >8
- `UserTournamentEngine` (`agentkit_cli/engines/user_tournament.py`): core engine — runs `UserDuelEngine` for each matchup, tracks wins/losses/avg scores, determines champion
- `TournamentResult` / `Standings` dataclasses with full `to_dict()` schema
- `UserTournamentReportRenderer`: self-contained dark-theme HTML report with champion card, standings table, and collapsible match results
- `publish_user_tournament`: upload tournament HTML to here.now, return URL
- `--share`: publish HTML tournament report to here.now
- `--json`: emit `TournamentResult` as JSON
- `--quiet`: suppress progress, print champion only
- `--output PATH`: save HTML report to local path
- `--limit N`: max comparisons cap
- `--timeout N`: per-user scorecard timeout (default: 60s)
- `--user-tournament user1:user2:...` flag on `agentkit run`: triggers tournament after pipeline
- `--user-tournament user1:user2:...` flag on `agentkit report`: includes tournament section in report output

## [0.61.0] - 2026-03-19

### Added
- `agentkit user-duel github:<user1> github:<user2>`: new command — head-to-head agent-readiness comparison between two GitHub developers, with per-dimension winner breakdown and shareable dark-theme HTML duel report
- `UserDuelEngine` (`agentkit_cli/user_duel.py`): core engine — runs `UserScorecardEngine` for each user and compares across four dimensions: avg_score, letter_grade, repo_count, agent_ready_repos
- `UserDuelResult` / `DuelDimension` dataclasses with full `to_dict()` schema
- `UserDuelReportRenderer`: self-contained dark-theme HTML report (`#0d1117` bg) with GitHub avatars side-by-side, dimension table with winner highlights, per-user top-5 repo cards, and overall winner/tie banner
- `--limit N` (default: 10): max repos per user to score
- `--json`: emit `UserDuelResult` as JSON
- `--share`: publish HTML duel report to here.now, print URL
- `--quiet`: suppress progress, print only winner/tie line
- `--user-duel user1:user2` flag on `agentkit run`: triggers duel after pipeline, includes result in JSON output
- `--user-duel user1:user2` flag on `agentkit report`: includes duel section in report output

## [0.60.0] - 2026-03-19

### Added
- `agentkit user-scorecard github:<user>`: new command — fetch all public repos for a GitHub user, score each for agent-readiness, and generate a shareable dark-theme HTML profile card with an A–D developer grade
- `UserScorecardEngine` (`agentkit_cli/user_scorecard.py`): core engine — lists public repos (paginated), runs AnalyzeEngine per repo, aggregates into `UserScorecardResult` + `RepoResult` dataclasses
- `UserScorecardReportRenderer` (`agentkit_cli/user_scorecard_report.py`): self-contained dark-theme HTML profile card with GitHub avatar, grade badge, ranked repo table with score bars, "Needs Improvement" section with copy-paste CLI commands, and footer crediting agentkit-cli
- Grade system: A≥80, B≥65, C≥50, D<50 with matching colors (A=green, B=blue, C=yellow, D=red)
- `--limit N` (default: 20): cap repos analyzed
- `--min-stars N` (default: 0): skip repos below star count
- `--skip-forks / --no-skip-forks` (default: True): exclude forked repos
- `--json`: machine-readable JSON output with full result schema
- `--share`: upload HTML report to here.now and print shareable URL
- `--pages github:<owner>/<repo>`: publish HTML to GitHub Pages using existing OrgPagesEngine git push pattern
- `--quiet`: print only final URL (cron/scripting friendly)
- `--timeout N` (default: 60): per-repo analysis timeout in seconds
- Rich terminal output: grade banner, stats row, top repos table, needs-improvement section
- `context_coverage_pct`: tracks % of repos with CLAUDE.md, AGENTS.md, or AGENTS/ directory
- `docs/index.html`: "Developer Profile Card" feature card added

## [0.59.0] - 2026-03-19

### Added
- `agentkit pages-trending`: new command — fetch today's trending GitHub repos, score them for agent-readiness, publish a dark-theme daily leaderboard to GitHub Pages at `https://<owner>.github.io/<repo>/trending.html`
- `TrendingPagesEngine` (`agentkit_cli/engines/trending_pages.py`): core engine — fetches trending repos, scores with agentkit heuristics, generates `trending.html` + `leaderboard.json`, handles git clone/pull/commit/push
- `--pages-repo github:<owner>/<repo>`: target GitHub Pages repo (auto-detected from current git remote, or defaults to `<owner>/agentkit-trending`)
- `--limit <N>`: cap repos scored (1-50, default: 20)
- `--language <lang>`: filter trending by programming language (e.g. `--language python`)
- `--period <today|week|month>`: trending period (default: `today`)
- `--dry-run`: score and generate HTML but skip git push
- `--quiet`: print only the final Pages URL (cron-friendly)
- `--share`: also publish to here.now for 24h preview link
- GitHub Actions example workflow: `.github/workflows/examples/agentkit-trending-pages.yml` (runs daily at 8 AM UTC)
- `docs/index.html`: "Daily Trending" feature card and nav link with "Subscribe to daily AI-ready repos" CTA
- `agentkit quickstart` next-steps: mentions `agentkit pages-trending`
- SEO-friendly HTML with og:title, og:description, structured JSON data

## [0.58.0] - 2026-03-19

### Added
- `agentkit pages-org github:<owner>`: new command — scores all public repos in a GitHub org and publishes a dark-theme org-wide leaderboard to GitHub Pages at `https://<owner>.github.io/agentkit-scores/`
- `OrgPagesEngine` (`agentkit_cli/engines/org_pages.py`): core engine — generates `index.html` + `leaderboard.json`, handles git clone/pull/commit/push of the Pages repo
- `agentkit org --pages`: flag on the existing `org` command; after scoring, triggers `OrgPagesEngine` to publish results
- `agentkit org --pages-repo <repo>`: override target Pages repo (default: `<owner>/agentkit-scores`)
- `agentkit org --dry-run`: score repos but skip git push (safe preview mode)
- `agentkit pages-org --only-below <N>`: filter to repos below a score threshold
- `agentkit pages-org --limit <N>`: cap repos scored (default: 50)
- `agentkit pages-org --quiet`: print only the final Pages URL (cron-friendly)
- GitHub Actions example workflow: `.github/workflows/examples/agentkit-org-pages.yml` (runs every Monday 8 AM UTC)
- Viral mechanic: one command gives any GitHub org a live, shareable AI-readiness scorecard

## [0.57.0] - 2026-03-19

### Added
- `publish_to_pages()` in `daily_leaderboard.py`: commit and push leaderboard HTML + JSON to GitHub Pages (`docs/leaderboard.html`, `docs/leaderboard-data.json`)
- `agentkit daily --pages`: publish permanent leaderboard to GitHub Pages (auto-detects repo from `git remote`)
- `agentkit daily --pages --pages-repo github:owner/repo`: target a different repo
- `agentkit daily --pages --pages-path <path>`: override output path (default: `docs/leaderboard.html`)
- Falls back to `--share` (here.now) automatically if GitHub Pages publish fails
- GitHub Actions example workflow: `.github/workflows/examples/agentkit-daily-leaderboard-pages.yml` (runs daily at 8 AM UTC)
- `docs/index.html`: "Daily Leaderboard" nav link and feature card
- `docs/leaderboard-data.json`: structured JSON data file published alongside HTML

## [0.56.0] - 2026-03-19

### Added
- `agentkit daily` command: generates a daily leaderboard of the most agent-ready GitHub repos
- `DailyLeaderboardEngine` (`agentkit_cli/engines/daily_leaderboard.py`): fetches trending repos via GitHub Search API and scores each for agent-readiness
- Dark-theme HTML renderer (`agentkit_cli/renderers/daily_leaderboard_renderer.py`) with gold/silver/bronze badges for top 3
- `--share` flag publishes to here.now; `--quiet --share` outputs URL only (cron-friendly)
- GitHub Actions example workflow (`.github/workflows/examples/agentkit-daily-leaderboard.yml`) for automated daily publishing

## [0.55.0] - 2026-03-19

### Added
- GitHub Pages landing site (`docs/index.html`) — dark-theme single-page site at https://mikiships.github.io/agentkit-cli/
  - Hero: "Benchmark AI Coding Agents on YOUR Repo"
  - Pipeline diagram: MEASURE → GENERATE → GUARD → LEARN → BENCHMARK
  - Feature grid: 6 tools with descriptions
  - Live stats bar with test count, package count, versions shipped
  - Command reference table
- `docs/.nojekyll` for GitHub Pages compatibility
- `.github/workflows/update-pages.yml` — auto-updates stats bar on push to main
- `agentkit quickstart` improvements:
  - Prints GitHub Pages URL alongside scorecard
  - "Next steps" section: `agentkit run`, `agentkit analyze github:owner/repo`, `agentkit benchmark`
  - Graceful no-key fallback: completes without error when `HERENOW_API_KEY` is unset
- `agentkit demo --record` — generates `demo.tape` VHS file for terminal recording
  - Prints exact VHS and asciinema recording instructions
- README: Documentation badge, Demo section with VHS recording instructions

### Changed
- `agentkit quickstart`: share step now skipped gracefully when `HERENOW_API_KEY` is not set

## [0.54.0] - 2026-03-18

### Added
- `agentkit benchmark` command: cross-agent benchmarking (Claude vs Codex vs Gemini) on your own codebase
- `BenchmarkEngine` core with configurable agents, tasks, rounds, and timeout
- 5 built-in benchmark tasks: bug-hunt, refactor, concurrent-queue, api-client, context-use
- Dark-theme HTML benchmark report with per-task matrix and aggregate stats
- `--share` flag to publish benchmark report to here.now
- `--agent-benchmark` flag on `agentkit run` to run cross-agent benchmark after pipeline
- `agentkit score` now displays benchmark_score when present in last run data
- Version bumped to 0.54.0

## [0.53.0] - 2026-03-18

### Added

- `agentkit digest` — weekly/daily quality digest across all tracked projects
  - Shows trend (improving/stable/regressing), per-project score deltas, regressions, improvements, top action items
  - Options: `--period N`, `--projects`, `--json`, `--quiet`, `--output FILE`, `--share`, `--notify-slack`, `--notify-discord`
  - Dark-theme HTML report (same palette as all agentkit reports: `#0d1117` bg, `#58a6ff` accent)
  - `--share` publishes to here.now via `HERENOW_API_KEY`
  - `--notify-slack` / `--notify-discord` posts digest summary via existing NotificationManager
- `DigestEngine` class (`agentkit_cli/digest.py`) — read-only HistoryDB query engine, no schema changes
- `DigestReportRenderer` class (`agentkit_cli/digest_report.py`) — HTML renderer with CSS-only bar charts
- `agentkit run --digest` — print project digest after each run
- `agentkit report --digest` — include digest section in existing report output

## [0.52.0] - 2026-03-18

### Added

- `agentkit search` — discover GitHub repos missing CLAUDE.md/AGENTS.md (completes search → campaign → track flywheel)
  - Supports `--language`, `--topic`, `--min-stars`, `--max-stars`, `--missing-only`, `--limit`, `--json`, `--share`, `--output`
  - Dark-theme HTML report with missing-context badge count and action buttons
  - `--share` publishes report to here.now via `HERENOW_API_KEY`
- `agentkit campaign --from-search QUERY` — auto-discover missing-context repos via search before submitting PRs
  - Example: `agentkit campaign --from-search "ai agents" --language python --min-stars 500`
- `SearchEngine` class (`agentkit_cli/search.py`) with GitHub Search + Contents API integration

## [0.51.0] - 2026-03-18

### Added

- `agentkit migrate` — convert between AI agent context file formats (`AGENTS.md`, `CLAUDE.md`, `llms.txt`)
- `agentkit sync` — check and fix sync status between managed context format files
- `agentkit doctor`: new `context-sync` check
- `agentkit run --migrate`: auto-generate missing context format files before analysis
- `agentkit llmstxt --sync-from agents-md|claude-md`: generate `llms.txt` from existing context file

## [0.50.0] - 2026-03-18

### Added

- `agentkit llmstxt` — new command to generate `llms.txt` and `llms-full.txt` for any repository, following the [llms.txt specification](https://llmstxt.org/)
  - Supports local paths and `github:owner/repo` (auto-clone)
  - `--full`: also generate `llms-full.txt` with inline file content
  - `--output DIR`: write files to specified directory
  - `--json`: structured JSON output with section counts and file sizes
  - `--share`: publish to here.now and return a shareable URL
  - `--validate`: check an existing llms.txt against the spec (H1, blockquote, sections, links)
  - `--score`: 0-100 quality score for the generated llms.txt
- `agentkit run --llmstxt`: generate `llms.txt` as part of the standard pipeline; stores `llmstxt_generated`, `llmstxt_path`, `llmstxt_section_count`, `llmstxt_size` in JSON output
- `agentkit report --llmstxt`: includes a quality card for `llms.txt` in the HTML report
- `agentkit doctor`: new `context.llmstxt` readiness check (detects README presence, hints to generate llms.txt)
- `LlmsTxtGenerator` class (`agentkit_cli/llmstxt.py`): `scan_repo()`, `generate_llms_txt()`, `generate_llms_full_txt()`, `validate_llms_txt()`, `score_llms_txt()`

## [0.49.0] - 2026-03-18

### Added
- GitHub Checks API integration: `agentkit run` and `agentkit gate` now post native GitHub Check Runs with score, grade, and per-tool breakdown visible in the PR UI
- `agentkit checks` command group: `verify`, `post`, `status` subcommands for manual Checks API interaction
- `--checks / --no-checks` flag on `agentkit run` and `agentkit gate` (default: auto-detect GitHub Actions)
- `agentkit_cli/checks_client.py`: `GitHubChecksClient` with `create_check_run()` and `update_check_run()`
- `agentkit_cli/checks_formatter.py`: `format_check_output()` converts scores to Check Run markdown output with per-tool table and annotations
- CI workflow template (`agentkit ci`) now includes `checks: write` permission
- 63 new tests (D1: 18, D2: 21, D3: 12, D4: 12)

## [0.48.0] - 2026-03-18

### Added
- `agentkit webhook` command group: inbound GitHub webhook server for push/pull_request events
- `agentkit webhook serve [--port PORT] [--secret SECRET] [--no-verify-sig]`: start HMAC-verified HTTP server
- `agentkit webhook config [--set-secret] [--set-port] [--set-channel] [--show]`: manage `[webhook]` section in `.agentkit.toml`
- `agentkit webhook test [--event push|pull_request] [--repo REPO]`: simulate events locally without HTTP
- `agentkit_cli/webhook/` package: `WebhookServer`, `verify_signature`, `EventProcessor`
- HMAC-SHA256 signature verification (`X-Hub-Signature-256`) — rejects unauthorized payloads with 403
- Non-blocking event queue: responds 200 immediately, processes in background thread
- `EventProcessor.process()`: runs composite analysis, records in history DB, fires notifications on regression, formats PR comment body
- `agentkit doctor` now includes an **Integrations** section with a `webhook config` check
- `agentkit run --webhook-notify`: POST pipeline result to configured webhook URL after run completes
- 58 new tests (D1: 21, D2: 14, D3: 14, D4: 9)

## [0.47.0] - 2026-03-18

### Added
- `agentkit monitor` command: continuous quality monitoring daemon for repos and local paths
- `MonitorTarget` dataclass (`agentkit_cli/monitor_config.py`): stores target, schedule, notification URLs, thresholds, and last run state
- `MonitorConfig` class: load/save from `.agentkit.toml` `[monitor.targets]` section without clobbering other sections
- `MonitorEngine` class (`agentkit_cli/monitor_engine.py`): orchestrates scheduled checks, computes score deltas, fires notifications
- `MonitorResult` dataclass: captures target, score, prev_score, delta, timestamp, notify_fired, error
- `monitor_daemon.py`: background polling process with SIGTERM handling and structured JSON log output
- Daemon PID file: `~/.agentkit/monitor.pid`; log file: `~/.agentkit/monitor.log`
- Subcommands: `add`, `remove`, `list`, `run`, `start`, `stop`, `status`, `logs`
- `--schedule daily|weekly|hourly`, `--notify-slack`, `--notify-discord`, `--notify-webhook`, `--min-score`, `--alert-threshold`
- `agentkit monitor list` shows Rich table with last score, last checked, next due, notify configured
- `agentkit monitor run [--target T] [--all]` forces immediate check with Rich results table
- `agentkit monitor start/stop/status` control daemon lifecycle via PID file
- `agentkit monitor logs [--limit N]` reads structured JSON log, renders Rich table
- Notifications via existing NotificationEngine when abs(score delta) ≥ alert_threshold (default 10 points)

## [0.46.0] - 2026-03-18

### Added
- `agentkit improve` command: end-to-end automated quality improvement workflow
- `ImproveEngine` class (`agentkit_cli/improve_engine.py`): analyze → fix → re-analyze loop
- `ImprovementPlan` dataclass: captures baseline_score, final_score, delta, actions_taken, actions_skipped, context_generated, hardening_applied
- Automatic CLAUDE.md generation when missing or score < 80 (via agentmd)
- Automatic redteam hardening when resistance score < 80
- Dark-theme HTML before/after improvement report (`agentkit_cli/templates/improve_report.html`)
- CLI flags: `--no-generate`, `--no-harden`, `--min-lift N`, `--pr`, `--dry-run`, `--json`, `--share`, `--output FILE`
- `agentkit run --improve`: post-run auto-improvement if score < threshold (default 80)
- `agentkit run --improve-no-generate`, `--improve-no-harden`, `--improve-threshold N` passthrough flags
- `improvement` key in `agentkit run --json` output when `--improve` is active

## [0.45.0] - 2026-03-18

### Added
- `agentkit explain` command: LLM-powered coaching report explaining WHY scores are what they are
- `ExplainEngine` class (`agentkit_cli/explain.py`): loads report JSON, builds prompt, calls Anthropic API, falls back to template
- `build_prompt(report)`: constructs a concise (<2000 token) prompt including composite score, tier, per-tool scores, and top findings
- `call_llm(prompt)`: calls `claude-3-5-haiku-20241022` via Anthropic SDK; graceful fallback if key missing or SDK not installed
- `template_explain(report)`: rule-based markdown coaching report — works offline, no API key needed
- `explain_run_result(result)`: accepts a RunResult dict directly (for `--explain` integration)
- Four coaching sections: "What This Score Means", "Key Findings Explained", "Top 3 Next Steps", "If You Do Nothing Else"
- Score-tier prose: A (≥90), B (70-89), C (50-69), F (<50) each get context-appropriate language
- Plain-language finding explanations: path-rot, year-rot, bloat, script-rot, mcp-security, and more
- `agentkit explain [PATH] [--report JSON] [--model MODEL] [--no-llm] [--json] [--output FILE]`
- `--no-llm` flag: force template mode, offline, no dependencies beyond agentkit-cli
- `--json` output: structured JSON with project, score, tier, explanation, recommendations[], one_thing
- `--output FILE`: write markdown coaching report to file
- `agentkit run --explain`: run full toolkit then append "## Coaching Report" to output
- `agentkit run --no-llm`: combine with `--explain` for offline coaching
- Rich console output: Panel header with score/tier, rendered Markdown coaching report

## [0.44.0] - 2026-03-17

### Added
- `agentkit timeline` command: generate a dark-theme HTML chart showing composite score progression over time
- `TimelineEngine` class (`agentkit_cli/timeline.py`): loads history DB, builds chart data, and computes summary stats
- `build_chart_data(runs)`: extracts dates, composite scores, and per-tool scores (lint, code quality, context, test coverage)
- `compute_stats(runs)`: min/max/avg, trend direction (improving/stable/declining), streak (N consecutive above 80)
- Multi-project mode: groups runs by project name, renders one line per project on the main chart
- Per-tool breakdown section: CSS-bar sparklines for agentlint, coderace, agentmd, agentreflect
- Stats panel: min/max/avg, trend arrow (↑↓→), streak badge
- `--project NAME`: filter to one project
- `--limit N`: max runs to show (default: 50)
- `--since YYYY-MM-DD`: only show runs after this date
- `--output FILE`: write HTML to file (default: timeline.html)
- `--share`: publish to here.now and print URL (requires `HERENOW_API_KEY`)
- `--json`: output raw chart data as JSON
- `agentkit run --timeline`: generate timeline HTML after run completes
- `agentkit doctor` hint: suggests `agentkit timeline` when history DB has ≥3 entries
- Dark-theme HTML report (`agentkit_cli/timeline_report.py`): Chart.js line chart, per-tool sparklines, stats panel, footer

## [0.43.0] - 2026-03-17

### Added
- `agentkit certify` command: generate a dated, shareable certification report proving a repo passed all agentkit quality checks
- `CertEngine` class (`agentkit_cli/certify.py`): runs 4 checks (composite score, redteam resistance, context freshness, test count) and produces a signed `CertResult` with SHA256 content hash and cert_id
- `CertResult` dataclass with PASS/WARN/FAIL verdict logic based on configurable thresholds
- Dark-theme HTML cert card (`agentkit_cli/certify_report.py`): cert_id, project name, timestamp, verdict badge, 4 sub-score rows with progress bars, SHA256 fingerprint
- `--output <file>` option: write HTML cert report to file
- `--json` option: print full JSON cert to stdout for CI integration
- `--min-score N` gate: exit 1 if composite score < N
- `--share` option: upload HTML report to here.now (requires `HERENOW_API_KEY`)
- `--badge` flag: inject/update agentkit certified shields.io badge in README.md (idempotent)
- `--badge --dry-run`: preview badge change without writing to disk
- 62+ new tests (≥1787 total)

## [0.42.0] - 2026-03-17

### Added
- `agentkit redteam --fix`: auto-patch detected vulnerabilities in agent context files in place (with backup), re-scores and shows before/after delta table
- `agentkit redteam --fix --dry-run`: preview what would change without writing to disk
- `agentkit redteam --fix --min-score N`: only fix categories scoring below N (CI gate)
- `agentkit harden [PATH]`: standalone command — detect + auto-remediate all vulnerabilities in one step, with score card and report
- `agentkit harden --output <path>`: write hardened file to a different path
- `agentkit harden --report`: generate dark-theme HTML hardening report
- `agentkit harden --share`: publish HTML report to here.now
- `agentkit harden --json`: structured JSON output for CI integration
- `agentkit run --harden`: run harden on detected context file after full pipeline
- `agentkit score` harden recommendation: suggests `agentkit harden` when redteam score < 70
- `agentkit doctor` redteam recency check: warns if redteam has not been run in the last 7 days
- `RedTeamFixer` class (`agentkit_cli/redteam_fixer.py`): 6 idempotent remediation rule handlers with dry-run and diff support
- `HardenReport` HTML generator (`agentkit_cli/harden_report.py`): dark-theme before/after score card
- 45+ new tests (≥1708 total)

## [0.41.0] - 2026-03-17

### Added
- `agentkit redteam` command: adversarial eval of agent context files with static analysis resistance scoring
- `RedTeamEngine`: deterministic attack generation across 6 categories (48 templates, no LLM required)
- `RedTeamScorer`: static analysis resistance scoring with 7 vulnerability rules, per-category and composite score
- Dark-theme self-contained HTML report with collapsible attack samples and recommendations
- `--min-score` CI gate: exit 1 if overall score < N — fail the build before unsafe configs ship
- `--json`, `--output`, `--share`, `--categories`, `--attacks-per-category` options
- `agentkit run --redteam` flag to run adversarial eval after full pipeline
- `agentkit score` now includes redteam score in composite when context file is present
- 79 new tests (1663 total)

## [0.40.1] - 2026-03-17

### Fixed
- `agentkit trending --share`: here.now publish API call was missing `path` and `size` fields in the files payload, causing HTTP 400 errors. Fixed by aligning `trending_report.publish_report` schema with the working `publish.publish_html` implementation.

## [0.40.0] - 2026-03-17

### Added
- `agentkit track` — PR status tracker that monitors campaign-submitted PRs
  - Queries GitHub API for current PR status (open/merged/closed)
  - Rich table output with status, days open, review count, and submission date
  - `--campaign-id` to filter to a specific campaign
  - `--limit N` / `--all` for controlling output size
  - `--json` for CI/automation integration
  - `--share` uploads a dark-theme HTML status report to here.now
- `agentkit_cli/pr_tracker.py` — PRTracker engine with GitHub API rate-limit handling
- `agentkit_cli/track_report.py` — dark-theme HTML report with campaign grouping and merge rate stats
- `agentkit_cli/commands/track_cmd.py` — CLI command wired into main app
- `tracked_prs` table in history DB with `record_pr`, `get_tracked_prs`, `update_pr_status` helpers
- `record_pr()` now called automatically after each successful `agentkit campaign` PR submission

## [0.39.0] - 2026-03-17

### Added
- `agentkit campaign` — batch PR submission to multiple repos in one command
  - Supports `github:owner`, `topic:TOPIC`, and `repos-file:PATH` target specs
  - Filters repos that already have CLAUDE.md or AGENTS.md
  - Submits PRs via `agentkit pr` (rate-limited, max 5 by default)
  - `--dry-run` mode shows what would happen without opening PRs
  - `--skip-pr` for discovery-only mode
  - `--share` uploads a dark-theme HTML report to here.now
  - Rich table output with per-repo status (✅ PR / ⏭ skip / ❌ err)
- Campaign history: `campaigns` table in history DB, `--campaigns` and `--campaign-id` flags on `agentkit history`
- `agentkit_cli/campaign.py` — CampaignEngine with find_repos, has_context_file, filter_missing_context, run_campaign
- `agentkit_cli/campaign_report.py` — dark-theme HTML campaign report generator

## [0.38.0] - 2026-03-16

### Added
- **`agentkit pr github:<owner>/<repo>`** command: viral distribution mechanic — generates a CLAUDE.md and opens a PR against any public GitHub repo
  - Clones repo (shallow, depth 1), runs `agentmd generate .`, forks under authenticated user, creates branch `agentkit/add-claude-md`, commits and pushes, opens PR
  - `--dry-run`: show all planned steps without any git or API calls
  - `--file`: generate AGENTS.md instead of CLAUDE.md (default: CLAUDE.md)
  - `--force`: overwrite existing context file (default: skip if already present)
  - `--pr-title`: custom PR title override
  - `--pr-body-file`: path to custom PR body markdown file
  - `--json`: structured output `{"pr_url": "...", "repo": "...", "file": "...", "score_before": N, "score_after": N}`
  - Requires `GITHUB_TOKEN` environment variable; gives clear error if missing
  - PR body template at `agentkit_cli/templates/pr_body.md`
  - 30 new tests in `tests/test_pr_cmd.py`

## [0.37.0] - 2026-03-16

### Added
- **`agentkit org --generate`** flag: auto-generates CLAUDE.md files via agentmd for repos below threshold, then re-scores and shows before/after score lift
  - `--generate-only-below N` (default: 80): only regenerate repos scoring below N
  - CLI table shows Before / After / Delta columns instead of Score / Grade when `--generate` is active
  - Color-coded delta: green ≥10pts improvement, yellow <10pts improvement, red if degraded
  - Summary line: "Generated context for X repos. Avg score lift: +Y pts"
  - `--share` with `--generate` produces HTML report with Before / After columns and delta badges
  - No remote writes — all generation happens in local temp clones

## [0.36.0] - 2026-03-16

### Added
- **`agentkit org`** command: score every public repo in a GitHub org or user account in one command
  - Accepts `github:<owner>` or bare owner name (e.g. `agentkit org github:vercel`)
  - Tries GitHub org API first, falls back to user API on 404
  - Paginated repo listing with `GITHUB_TOKEN` support
  - Filters forks, archived, and empty repos by default (`--include-forks`, `--include-archived`)
  - `--limit N` to cap number of repos analyzed
  - Rich live progress display during multi-repo analysis
  - Ranked Rich table output with score, grade, and top finding per repo
  - `--parallel N` flag (default: 3) for concurrent analysis via `ThreadPoolExecutor`
  - Per-repo `--timeout N` (default: 120s) with graceful error handling
  - Summary counts: analyzed / skipped (timeout) / failed
  - `--json` output: `{owner, repo_count, analyzed, skipped, failed, ranked: [...]}`
  - `--output <file>` saves dark-theme HTML report to disk
  - `--share` uploads HTML report to here.now and prints URL
- `agentkit_cli/github_api.py`: GitHub REST API client with pagination and rate-limit awareness
- `agentkit_cli/org_report.py`: dark-theme HTML report generator for org analysis

## [0.35.0] - 2026-03-16

### Added
- **`agentkit quickstart`** command: fastest path to an impressive agentkit result in under 60 seconds
  - Runs doctor check summary, fast composite score (agentlint + agentmd, timeout=30s), Rich panel output
  - Optional score card publish to here.now via `--share` / `HERENOW_API_KEY`
  - `--no-share` flag to skip publishing; `--timeout N` for per-tool timeout
  - Supports `github:owner/repo` targets (delegates to analyze_target)
  - Graceful degradation: partial score when some tools not installed
- **19 new tests** in `tests/test_quickstart.py`
- README: `agentkit quickstart` elevated as primary onboarding entry point in Quick Start and Commands sections

### Changed
- `agentkit --help` now lists `quickstart` prominently as first user-facing command

## [0.34.0] - 2026-03-16

### Added
- **ToolAdapter** class in `agentkit_cli/tools.py`: single source of truth for all quartet tool invocations (agentmd, agentlint, coderace, agentreflect) with canonical correct flags, timeouts, and error handling
- **Golden smoke test suite** (`tests/test_smoke_integration.py`): 9 integration tests exercising every orchestration command against a fixture project. Run `pytest -m smoke` before any release.
- **SmokeTestCheck** in `release_check.py`: `agentkit release-check` now includes smoke suite pass as a blocking check
- `pytest.mark.smoke` marker registered in `pyproject.toml`
- Fixture project at `tests/fixtures/smoke_project/` for smoke testing

### Changed
- All hand-rolled quartet subprocess calls migrated to ToolAdapter (suggest, compare, doctor, analyze, report_runner)
- `report_runner.py` now delegates to ToolAdapter (backward-compatible signatures preserved)
- `check_context_freshness` in doctor.py uses ToolAdapter instead of direct subprocess calls

### Fixed
- Eliminates the M34 architectural debt: flag-wiring bugs can no longer recur across subcommands since all quartet invocations go through a single module

## [0.33.0] - 2026-03-16

### Added
- SSE (Server-Sent Events) live-push to `agentkit serve` dashboard
  - `SseBroker` class: thread-safe client registration, `broadcast()`, auto-remove disconnected clients
  - `GET /events` SSE endpoint in `AgenkitDashboard` — keeps connection open, sends keepalive comments every 15s
  - Dashboard JS: `EventSource('/events')` reconnects automatically; re-renders runs table in-place via `GET /api/runs`
  - Live indicator: **● Live** (green) when SSE connected, **○ Offline** (grey) when disconnected
- `agentkit watch --serve [--port N]`: combined file-watcher + dashboard server in one process
  - Starts HTTP server in a daemon thread before watcher loop
  - After each pipeline run, calls `broker.broadcast({"type": "refresh"})` to push live update
  - Prints: `Watching <path>  •  Dashboard: http://localhost:<port>`
- `agentkit serve --live`: polls DB every 5s, broadcasts SSE refresh event when run count changes
  - Prints: `Dashboard (live): http://localhost:<port>`
- `start_server()` extended with optional `live: bool = False` kwarg (backward-compatible)

## [0.32.0] - 2026-03-16

### Added
- `agentkit serve` command: local web dashboard server showing all toolkit runs from the history SQLite DB
  - Dark-theme HTML dashboard (`#0f172a` background, matching existing agentkit report aesthetic)
  - Summary bar: total runs, unique projects, average score
  - Score-colored table: green ≥80, yellow ≥60, red <60, with A/B/C/D/F grade
  - Auto-refresh every 30s via `<meta http-equiv="refresh">` and JS fallback
  - `--port PORT` (default: 7890), `--open` (auto-open browser), `--once` (render HTML to stdout), `--json` (print URL as JSON)
  - Empty-state message when no runs exist
  - Version in footer
- `agentkit_cli/serve.py`: `AgenkitDashboard(BaseHTTPRequestHandler)` + `start_server()` — stdlib only, no new deps
- `agentkit_cli/commands/serve_cmd.py`: CLI command wrapper
- `agentkit run --serve`: print dashboard URL after pipeline completes
- `agentkit doctor`: new `publish.serve` check verifying serve is importable
- `tests/test_serve.py`: 56 tests covering server, HTML generation, CLI flags, score coloring, grade logic, doctor integration

## [0.31.0] - 2026-03-16

### Added
- `agentkit tournament` command: round-robin bracket across 4-16 repos
- `agentkit_cli/tournament.py`: tournament engine with parallel execution via `concurrent.futures`
- `agentkit_cli/tournament_report.py`: dark-theme HTML bracket report with standings table and match results matrix
- `agentkit_cli/commands/tournament_cmd.py`: CLI with `--share`, `--json`, `--quiet`, `--parallel/--no-parallel`, `--output` flags
- `tests/test_tournament.py`: 57 tests covering engine, CLI, HTML report, and publish flow

## [0.30.0] - 2026-03-16

### Added
- `agentkit duel <repo1> <repo2>` — head-to-head agent-readiness comparison of two GitHub repos
  - Runs both analyses in parallel using `ThreadPoolExecutor(max_workers=2)`
  - Determines winner (or tie if scores within 5 points) with delta visualization
  - `--share` / `--no-share`: publish dark-theme HTML comparison report to here.now
  - `--json`: output structured JSON payload with scores, breakdown, winner, delta
  - `--timeout INT`: per-repo analysis timeout (default: 120s)
  - `--keep`: keep cloned repos after analysis
  - Handles partial failures gracefully (one side can fail, other side wins)
- `agentkit_cli/duel.py`: core duel engine with `DuelResult` dataclass and `run_duel()`
- `agentkit_cli/duel_report.py`: dark-theme two-column HTML report generation and here.now upload

## [0.29.0] - 2026-03-15

### Added
- `agentkit trending` command: fetch trending GitHub repos and rank them by agent quality score
  - `--period [day|week|month]`: trending time window (default: week)
  - `--topic TEXT`: filter by GitHub topic (e.g. ai-agent)
  - `--limit INT`: max repos to fetch (default: 10, max 25)
  - `--category [ai|python|all]`: pre-defined repo category (default: ai)
  - `--share`: publish dark-theme HTML report to here.now and print URL
  - `--json`: output JSON with schema `{period, topic, repos: [{rank, full_name, stars, score, grade, url}]}`
  - `--no-analyze`: fast mode — list repos without scoring
  - `--min-stars INT`: filter repos below this star count (default: 100)
  - `--token TEXT`: GitHub API token (or GITHUB_TOKEN env var)
- `agentkit_cli/trending.py`: `fetch_trending()` and `fetch_popular()` with graceful rate-limit handling
- `agentkit_cli/trending_report.py`: `generate_html()` and `publish_report()` for dark-theme HTML reports
- Fallback: if here.now publish fails, saves HTML to `./trending-report.html`
- 49 new tests (total suite: 1106 tests)

## [0.28.0] - 2026-03-15

### Added
- `agentkit insights` command: cross-repo pattern synthesis across all historical runs
  - Portfolio health summary (avg score, total runs, unique repos, best/worst repo, top issue)
  - `--common-findings`: most common agentlint findings across 2+ repos
  - `--outliers`: repos in the bottom quartile of historical scores
  - `--trending`: repos with score change >10 between last two runs
  - `--all`: all sections in one output
  - `--json`: structured JSON output with full schema
  - `--db`: override history DB path
- `InsightsEngine` class in `agentkit_cli/insights.py` with four methods: `get_common_findings`, `get_outliers`, `get_trending`, `get_portfolio_summary`
- `--record-findings` flag on `agentkit run` and `agentkit analyze`: stores agentlint findings in history DB alongside scores for richer cross-repo analysis
- Schema migration: `findings TEXT` column added to `runs` table (migration-safe, idempotent)
- 45 new tests (total suite: 1057 tests)

## [0.27.0] - 2026-03-15

### Added
- `agentkit release-check` command: verifies the 4-part release surface (tests green, git push confirmed, tag pushed, registry live) for Python (PyPI) and npm packages
- `--release-check` flag on `agentkit run` and `agentkit gate` to append release surface verification after pipeline completes
- `agentkit_cli/release_check.py` engine with structured `ReleaseCheckResult` output, JSON mode, and actionable next-step hints
- 52 new tests covering all check functions, CLI flags, error handling, and dataclass contracts (total suite: 1012 tests)

## [0.26.1] - 2026-03-15

### Fixed
- Version assertions in tests now forward-compatible (no hardcoded minor version numbers)

## [0.25.0] - 2026-03-15

### Added
- **`--share` flag on `agentkit analyze`**: generate and upload a public score card after analyzing any GitHub repo or local path; URL printed to stdout; `--json` output includes `"share_url"`; upload failure is non-fatal
- **`--share` flag on `agentkit sweep`**: generate a combined scorecard for all analyzed targets, upload once, print URL; `--json` output includes `"share_url"` in summary; upload failure is non-fatal
- **`generate_sweep_scorecard_html()`** in `agentkit_cli/share.py`: combined dark-theme HTML scorecard for multi-target sweep results with ranked table
- **`generate_scorecard_html()` improvements** (D3): optional `repo_url` and `repo_name` parameters; repo name rendered as clickable link in card header; analysis timestamp shown in footer; fully backward-compatible (optional params)
- 25 new tests covering D1–D3 (mock upload, URL in output, JSON schema, failure cases)

## [0.24.0] - 2026-03-15

### Added
- **`agentkit share` command** (`agentkit_cli/commands/share_cmd.py`):
  - Generates a shareable score card HTML page (dark theme, standalone)
  - Uploads to here.now and returns a public URL
  - `--report PATH`: load from a saved JSON report file instead of running fresh
  - `--project NAME`: override project name (default: git remote origin or cwd basename)
  - `--no-scores`: hide raw numbers; show pass/fail indicators only
  - `--json`: output `{"url": "...", "score": N}` instead of plain text
  - `--api-key`: override `HERENOW_API_KEY` env var
  - Anonymous publish (no API key) expires in 24h; authenticated is persistent
- **Score card HTML generator** (`agentkit_cli/share.py`):
  - `generate_scorecard_html()`: dark-theme (#0d1117), monospace, no CDN dependencies
  - Hero number with color coding: green ≥80, yellow 60–79, red <60
  - Per-tool breakdown table with pass/fail indicators
  - Footer with agentkit-cli version and PyPI link
  - `upload_scorecard()`: reuses here.now 3-step publish flow from `agentkit_cli/publish.py`
  - Graceful fallback on network failure (prints warning, returns None)
- **`--share` flag on `agentkit run`**: uploads score card after run, prints URL
- **`--share` flag on `agentkit report`**: uploads score card after report, prints URL
- 43 new tests covering D1–D4 (HTML generation, upload, CLI command, flags)

## [0.23.0] - 2026-03-15

### Added
- **Quality profiles system** (`agentkit_cli/profiles.py`):
  - `ProfileDefinition` dataclass: name, description, gate thresholds, notify config, sweep targets
  - `ProfileRegistry`: stores built-in presets + user-defined profiles from `~/.agentkit/profiles/*.toml`
  - Three built-in presets: `strict` (min-score 85, max-drop 3), `balanced` (min-score 70, max-drop 10), `minimal` (min-score 50, max-drop 20, gate disabled)
  - `apply_profile(name, config)` — merges profile values into AgentKitConfig (CLI flags > profile > config > defaults)
  - Case-insensitive profile lookup
  - User-defined profile loading from `~/.agentkit/profiles/*.toml`
- **`agentkit profile` command group**:
  - `agentkit profile list` — list all profiles (built-in + user) in Rich table
  - `agentkit profile show <name>` — show profile config details in key-value table
  - `agentkit profile create <name> [--from <base>]` — create user profile (optionally inheriting from base)
  - `agentkit profile use <name>` — set active profile in `.agentkit.toml`
  - `agentkit profile export <name> [--format toml|json]` — print profile as TOML or JSON
- **`--profile` flag** added to `gate`, `run`, `sweep`, `score`, `analyze` commands
  - Profile name shown in `gate` Rich output (e.g. "Profile: strict")
  - Explicit CLI flags (e.g. `--min-score 90`) always override profile values

## [0.22.0] - 2026-03-15

### Added
- **Project configuration system** (`.agentkit.toml`):
  - Git-style upward traversal to find `.agentkit.toml` from current directory
  - User-level defaults at `~/.config/agentkit/config.toml`
  - `AgentKitConfig` dataclass with typed sections: `gate`, `notify`, `run`, `sweep`, `score`
  - Environment variable overrides for all config keys (e.g. `AGENTKIT_GATE_MIN_SCORE`)
  - Config precedence: CLI flags > env vars > project config > user config > built-in defaults
  - `tomllib` (stdlib, Python 3.11+) with `tomli` fallback for TOML parsing
  - Graceful error handling: invalid or missing TOML never crashes
- **`agentkit config` command group**:
  - `agentkit config init` — write `.agentkit.toml` with all defaults and inline comments
  - `agentkit config init --global` — write to `~/.config/agentkit/config.toml`
  - `agentkit config show` — display effective merged config with source annotations (`[project]`, `[env]`, `[default]`)
  - `agentkit config show --json` — machine-readable JSON output
  - `agentkit config get <key>` — print a single value by dotted key
  - `agentkit config set <key> <value>` — set a value in project (or `--global` user) config
- **Config wired into commands**:
  - `agentkit gate` uses config `gate.min_score`, `gate.max_drop`, and `notify.*` as defaults when flags are not provided
  - `agentkit run` uses config `notify.*` and `run.label` as defaults
  - `agentkit sweep` uses config `sweep.targets`, `sweep.sort_by`, and `sweep.limit` as defaults
  - `agentkit score` uses config `gate.min_score` as default CI threshold
- README: new "Project Configuration" section with annotated `.agentkit.toml` example and environment variable table

## [0.21.0] - 2026-03-15

### Added
- **Webhook notifications** for `agentkit gate` and `agentkit run`:
  - `--notify-slack <url>` — post a color-coded Slack attachment on gate result
  - `--notify-discord <url>` — post a color-coded Discord embed on gate result
  - `--notify-webhook <url>` — post a generic JSON payload to any HTTP endpoint
  - `--notify-on fail|always` — control when notifications fire (default: `fail`)
  - Env vars `AGENTKIT_NOTIFY_SLACK`, `AGENTKIT_NOTIFY_DISCORD`, `AGENTKIT_NOTIFY_WEBHOOK` accepted as fallbacks; CLI flags take precedence
  - Notification failures **never** affect gate exit code — errors are logged and swallowed
  - Single retry with 5 s timeout per attempt
- **`agentkit notify` command group**:
  - `agentkit notify test --slack|--discord|--webhook <url>` — fire a test notification and print ✓/✗ result
  - `agentkit notify config` — show current notification env var configuration
- **`agentkit_cli/notifier.py`** — standalone notification module with `NotifyConfig`, `build_payload`, `notify_result`, `fire_notifications`, `resolve_notify_configs`
- `action.yml` gains `notify-slack`, `notify-discord`, `notify-webhook`, `notify-on` inputs

## [0.20.0] - 2026-03-14

### Added
- `agentkit setup-ci`: one-command CI onboarding. Writes a complete GitHub Actions workflow
  (`.github/workflows/agentkit-quality.yml`), generates an initial baseline report
  (`.agentkit-baseline.json`), and injects the agent quality badge into README.md.
  - `--min-score N` (default: 70): threshold embedded in generated gate command
  - `--workflow-path PATH`: override workflow output path
  - `--force`: overwrite existing workflow file
  - `--dry-run`: print workflow to stdout without writing
  - `--skip-baseline`: skip baseline report generation
  - `--no-badge`: skip README badge injection

## [0.19.0] - 2026-03-14

### Added
- `agentkit gate` command: quality gate that fails the build when agent quality drops
  - **D1 Core engine**: `agentkit gate --min-score 75` — runs full report pipeline and evaluates composite score against threshold; GateResult dataclass with verdict, score, grade, failure_reasons; clean GateError for config problems
  - **D2 Baseline regression gating**: `--baseline-report PATH` loads a prior `agentkit report --json` artifact; `--max-drop N` fails if score dropped more than N points from baseline; both rules checked together with all failure reasons reported
  - **D3 Machine-readable outputs**: `--json` prints stable JSON payload (verdict, score, grade, thresholds, failure_reasons, passed); `--output PATH` writes JSON to disk; `--job-summary` writes markdown verdict block to GITHUB_STEP_SUMMARY (or stdout if not set); `to_json_payload()` method on GateResult
  - **D4 Docs**: README `agentkit gate` section with local usage and GitHub Actions example; CHANGELOG entry; version bump to 0.19.0
- 10 new tests covering min-score, baseline regression pass/fail, invalid baseline file, both rules together, JSON schema, --output file write, --job-summary stdout

## v0.18.0 (2026-03-14)

### Added
- `agentkit sweep` command: multi-target batch analysis with ranked output
  - **D1 Core engine**: `agentkit sweep github:psf/requests github:pallets/flask .` — batch runner reusing existing `analyze` pipeline; `--targets-file` for file-based target lists; deduplication; failure isolation (one bad target doesn't crash the batch)
  - **D2 Ranked output**: Rich table with columns (target | score | grade | status | error); `--sort-by` flag (score, name, grade); `--limit N` for top-N display
  - **D3 JSON output**: `--json` flag with stable schema `{ targets, results: [{rank, target, score, grade, status, error}], summary_counts }`; deterministic, console-noise-free; ranking order preserved in JSON
  - **D4 Docs**: README sweep section with usage examples; CHANGELOG entry; version bump to 0.18.0
- `sort_results()` in `agentkit_cli/sweep.py`: sort sweep results by score (descending), name, or grade
- 20 new tests covering sort, limit, Rich table, JSON schema, and determinism

## v0.17.0 (2026-03-14)

### Added
- `agentkit analyze <target>` command: zero-friction agent quality analysis for any GitHub repo or local path
  - **Target formats**: `github:owner/repo`, `https://github.com/owner/repo`, `owner/repo` (bare shorthand), `./local-path`
  - **Pipeline**: clones repo into temp dir (depth=1), runs `agentmd generate` (if no context), `agentmd score`, `agentlint check-context --format json`, `agentreflect generate`, computes composite score
  - **Output**: Rich table showing Tool / Status / Score / Key Finding + headline `Agent Quality Score: X/100 (Grade)  repo: owner/repo`
  - **Flags**: `--json` (machine-readable output), `--keep` (keep temp clone dir), `--publish` (publish HTML report to here.now), `--timeout N` (default 120s), `--no-generate` (skip agentmd generate)
  - **Error handling**: git not installed → clear error; clone failure → helpful message + temp dir cleanup; individual tool failure isolation; timeout → partial results; 1 retry with 5s backoff on clone
  - **JSON schema**: `target`, `repo_name`, `composite_score`, `grade`, `tools`, `generated_context`, `temp_dir` (if --keep), `report_url` (if --publish succeeded)
- 25 new tests covering URL parsing, mock clone, pipeline execution, JSON schema, and all error paths

## v0.16.2 (2026-03-14)

### Fixed
- `agentkit score`: was passing `--json` to `agentlint check-context` (invalid flag). Corrected to `--format json`.
- `agentkit suggest`: same flag issue in two places (`check-context --json` → `--format json`; bare `agentlint --json` → `agentlint check --format json`).
- `agentkit report`: `coderace benchmark history` now called with `--format json` instead of no format flag.
- Version check test made forward-compatible (checks `"0.16"` prefix, not exact string).

## v0.16.1 (2026-03-14)

### Fixed
- `agentkit doctor` context freshness check: was passing `--json` to `agentlint check-context` (invalid flag). Corrected to `--format json`. Regression test added.

## v0.16.0 (2026-03-14)

### Added
- `agentkit score` command: composite 0-100 agent quality score synthesizing all four toolkit tools
- `CompositeScoreEngine` in `agentkit/composite.py`: weighted scoring with automatic weight renormalization for missing tools
- Grade assignments (A/B/C/D/F) based on composite score thresholds
- `--breakdown` flag for per-component Rich table output
- `--json` output for machine-readable composite score
- `--ci` / `--min-score` flags for CI gate integration
- `agentkit run` now displays composite score line at pipeline completion
- Composite score recorded to history DB as `composite` tool
- `agentkit badge` now defaults to composite score; use `--tool <name>` for single-tool badge
- 50 new tests covering all composite score functionality

## v0.15.0 (2026-03-14)

### Added
- `agentkit leaderboard` command: ranked comparison of agent runs grouped by label
  - **D1 Run labeling**: `--label <str>` flag on `agentkit run`; label stored in history DB via backward-compatible `ALTER TABLE` migration
  - **D2 Leaderboard engine**: `agentkit/leaderboard_cmd.py` with `get_leaderboard_data()` — groups runs by label, computes avg/best/worst/trend (last-3 minus first-3 avg); handles NULL labels as "default"
  - **D3 CLI command**: Rich ranked table with Rank, Label, Runs, Avg Score, Trend (↑/↓/→), Best, Worst; `--json`, `--by`, `--since`, `--project`, `--last` flags
  - **D4 GitHub Actions**: `leaderboard-json` output when `save-history: true`; README example snippet
- 47 new tests; full suite 575 tests passing

## v0.14.0 (2026-03-14)

### Added
- `agentkit history` command: persistent quality score tracking with SQLite backend
  - **D1 HistoryDB**: SQLite store at `~/.config/agentkit/history.db`; `record_run()`, `get_history()`, `clear_history()` with idempotent schema
  - **D2 Auto-record**: `agentkit run` automatically records per-tool and overall scores after each run; `--no-history` flag to skip; DB failures never abort the run
  - **D3 history command**: Rich table with trend arrows and block bars; `--limit`, `--tool`, `--project`, `--graph` (sparkline), `--json`, `--clear` (with confirmation), `--all-projects` flags
  - **D4 GitHub Actions**: `save-history` optional input; `history-json` output; `examples/agentkit-ci.yml` example workflow
- 52 new tests; full suite 528 tests passing

## v0.13.0 (2026-03-14)

### Added
- `agentkit summary` command: maintainer-facing summary for CI, PR, and release workflows
  - **D1 Core command**: `--path` (local analysis) and `--json-input` (file mode); deterministic markdown rendering
  - **D2 Maintainer sections**: verdict logic (`PASSING`, `WARNINGS_PRESENT`, `ACTION_REQUIRED`, `REGRESSION_DETECTED`); per-tool status with concise notes; top-fixes section (up to 5 prioritized findings from agentlint/agentreflect); optional compare/regression section
  - **D3 GitHub-friendly outputs**: `--output <path>` writes markdown to file; `--job-summary` appends to `GITHUB_STEP_SUMMARY`; clear error when job-summary env var is absent
  - **D4 JSON mode**: `--json` emits structured payload (project, verdict, score, tool_status, top_fixes, compare, markdown)
- README `agentkit summary` section with full usage examples and GitHub Actions integration
- 7 new summary tests; full suite 476 tests passing

## v0.12.0 (2026-03-13)

### Added
- `agentkit doctor` expanded to a full preflight command (D2–D4):
  - **D2 Toolchain probes**: checks agentmd, agentlint, coderace, agentreflect (missing = fail); git, python3 (missing = warn); captures version text with noisy-output tolerance
  - **D3 Actionability checks**: source-file presence, context freshness via `agentlint check-context --json` (graceful degradation when unavailable), output-dir write access, HERENOW_API_KEY readiness
  - **D4 CLI ergonomics**: `--category repo|toolchain|context|publish` filter; `--fail-on warn|fail` threshold; `--no-fail-exit` for hooks
- README `agentkit doctor` section rewritten with full check table, troubleshooting checklist, and CI usage example
- 45 new doctor tests (21 → 66); full suite 469 tests passing

## v0.11.0 (2026-03-13)

### Added
- `agentkit suggest` command: prioritized action list from agentlint findings
- `suggest_engine.py`: `Finding` dataclass, `parse_agentlint_check_context`, `parse_agentlint_diff`, `prioritize`, `prioritize_findings`
- `--fix` flag: auto-applies safe fixes (year-rot, trailing-whitespace, duplicate-blank-lines) to context files only
- `--dry-run` flag: shows unified diff without writing changes
- `--all` flag: shows all findings instead of top 5
- `--json` flag: structured JSON output with score + findings array
- 59 new tests (357 → 416 total)

## v0.10.0 (2026-03-13)

### Added

- **`agentkit compare`** — new command to compare agent quality scores between two git refs.
  - `agentkit compare <ref1> <ref2>` (defaults: `HEAD~1`, `HEAD`)
  - Per-tool score deltas shown in a colored Rich table (green = improved, red = degraded)
  - Net delta + verdict: `IMPROVED` (>+5), `NEUTRAL` (-5..+5), `DEGRADED` (<-5)
  - `--json` flag: structured JSON output with all deltas
  - `--quiet` flag: only prints the verdict (IMPROVED/NEUTRAL/DEGRADED) — ideal for shell scripts
  - `--ci` flag: exits with code 1 if verdict is DEGRADED
  - `--min-delta N` flag: exits 1 if net delta is below N (for stricter CI gates)
  - `--tools` flag: limit which quartet tools are compared
  - `--files` flag: show which files changed between refs
  - Graceful handling of tool failures (marks as N/A, does not crash)
  - Uses `git worktree` for safe, isolated checkout of each ref
- **`agentkit_cli/utils/git_utils.py`** — new git helpers (resolve_ref, changed_files, Worktree context manager)
- **GitHub Action `mode: compare`** — new compare mode for action.yml with `compare-base`, `compare-head`, and `min-delta` inputs
- **Example workflow** — `.github/workflows/examples/agentkit-compare.yml`

### Changed

- Version bumped to 0.10.0

## v0.9.0 (2026-03-13)

### Added

- **`agentkit readme`** — new command to inject or update the agent quality badge in README.md.
  - Finds README.md in the current directory (or `--readme path/to/README.md`)
  - Idempotent: if the badge section already exists, updates the score; otherwise appends to end of file
  - `--dry-run`: show what would change without modifying the file
  - `--remove`: remove the injected section cleanly
  - `--section-header`: customize the injected section header (default: `## Agent Quality`)
  - `--score N`: override computed score
  - Prints summary: `Updated README.md — agent quality: 87/100 (green)`
- **`agentkit run --readme`** — runs the full pipeline then injects/updates the README badge
- **`agentkit report --readme`** — generates the HTML report then injects the badge

### Changed

- Version bumped to 0.9.0

## v0.8.0 (2026-03-13)

### Added

- **`agentkit badge`** — new command to generate a shields.io-compatible README badge showing the project's agent quality score. No server required; just a static badge URL.
  - Computes score from agentlint, agentmd, and coderace results (average of available components)
  - Color-coded: green ≥80, yellow 60-79, orange 40-59, red <40
  - Outputs badge URL, Markdown snippet, and HTML snippet
  - `--json` mode for CI integration: `{"score":87,"color":"green","badge_url":"...","markdown":"...","html":"..."}`
  - `--score N` to override computed score (useful for testing or CI gates)
- **Badge in HTML report** — `agentkit report` now embeds the badge at the top of the generated HTML report
- **Badge on publish** — `agentkit report --publish` now also prints the badge Markdown snippet

### Changed

- Version bumped to 0.8.0

## v0.7.0 (2026-03-13)

### Added

- **GitHub Actions composite action** (`action.yml`) — Run the full Agent Quality Toolkit pipeline on every PR. Checks agentlint context score, agentmd drift, and coderace review, then posts an aggregated quality comment to the PR.
  - Inputs: `github-token` (required), `min-lint-score` (default: 70), `post-comment` (default: true), `python-version` (default: 3.11)
  - Outputs: `lint-score`, `drift-status`, `review-summary`
  - Fails the action if lint score < `min-lint-score`
- **`scripts/run-agentkit-action.py`** — orchestrates agentlint, agentmd, and coderace; aggregates results to JSON; sets GitHub Actions outputs.
- **`scripts/post-pr-comment.py`** — posts/updates a formatted markdown quality report comment on the PR via GitHub API (idempotent).
- **`examples/agentkit-quality.yml`** — ready-to-use workflow file for adopters.
- **README GitHub Action section** — explains what the action checks, how to add it in 3 lines, PR comment format, and input/output reference.

## v0.6.0 (2026-03-13)

### Added

- **`agentkit publish`** — new command to upload an HTML report to [here.now](https://here.now) and return a shareable URL. Supports anonymous (24h expiry) and authenticated (persistent) publishes via `HERENOW_API_KEY` env var. Options: `--json`, `--quiet`.
- **`agentkit report --publish`** — generate a report and publish it in one command. Publish failure is non-fatal (prints a warning, does not exit 1).
- **`agentkit run --publish`** — run the full pipeline and publish the resulting report. Publish failure is also non-fatal.

## v0.5.1 (2026-03-13)

### Fixed
- **agentlint runner**: corrected CLI flag from `--json` (nonexistent) to `--format json`
- **coderace runner**: removed `benchmark --json` (no such flag); now uses `benchmark history`
  to check for cached results. Returns `{"status": "no_results", ...}` gracefully if no
  history found — no crash, no live agent run required
- **agentreflect runner**: `--format json` not supported; now uses `--from-git --format markdown`
  and returns `{"suggestions_md": text, "count": N}` instead of trying to parse JSON
- **agentmd summary card**: `_agentmd_summary_card` crashed when agentmd returned a list of
  per-file scored dicts instead of a single dict; now averages scores across the list and
  shows "N files analyzed" subtitle
- Updated `_agentreflect_section` to render `suggestions_md` key (markdown text in `<pre>`)
  with fallback to legacy `summary`/`reflection`/`output` keys

## v0.5.0 (2026-03-13)

### Added
- `agentkit report` — run all toolkit checks and generate a shareable HTML quality report
  - Detects which quartet tools are installed; runs available checks with 60s timeouts
  - `--json` emits structured JSON with coverage score, per-tool status, and tool output
  - `--output PATH` saves HTML report to specified path (default: `./agentkit-report.html`)
  - `--open` auto-opens the report in the default browser after saving
  - `--path PATH` override project directory
  - Self-contained HTML: no CDN, no external fonts, no JS libraries — inline CSS only
  - Dark theme with color-coded scores (green ≥80, yellow 50-79, red <50)
  - Sections: toolkit coverage, context quality (agentlint), context docs (agentmd), agent benchmark (coderace), reflection (agentreflect), pipeline status table
  - Gracefully handles any mix of installed/missing/failing tools (never crashes)
- `agentkit_cli/report_runner.py` — internal module with per-tool runner functions
  - `run_agentlint_check(path)`, `run_agentmd_score(path)`, `run_coderace_bench(path)`, `run_agentreflect_analyze(path)`
  - Each returns parsed JSON dict or `None` (tool missing / non-zero exit / unparseable output)
  - Robust JSON extraction: handles tools that prefix output with non-JSON lines

### Tests
- 201 tests (up from 170). Added 31 tests in `tests/test_report.py`.

## v0.4.0 (2026-03-13)

### Added
- `agentkit demo` — zero-config first-run experience
  - Detects project type (python/typescript/javascript/generic) from directory contents
  - Auto-selects best coderace task for detected project type
  - Auto-detects available AI agents (claude, codex) via PATH
  - Runs generate → lint → reflect pipeline steps without any config file
  - Optional benchmark step when agents are available
  - `--task TEXT` override, `--agents TEXT` override, `--skip-benchmark`, `--json` flags
  - Rich output with step table, benchmark results table, and footer hint
  - Highlights best-scoring agent in green

### Tests
- 157+ tests (up from 142). Added 20 tests in `test_demo.py`.

## v0.3.0 (2026-03-12)

### Added
- `agentkit ci` — generate a ready-to-use `.github/workflows/agentkit.yml` in one command
  - `--python-version`, `--benchmark`, `--min-score`, `--output-dir`, `--dry-run` flags
  - Generated YAML is validated via `yaml.safe_load` before writing
  - Installs all quartet tools and runs `agentkit run --ci` on every PR
- `agentkit watch` — watch the project for file changes and re-run the pipeline automatically
  - Powered by `watchdog` library
  - `--extensions`, `--debounce`, `--ci` flags
  - 2-second debounce by default; graceful Ctrl+C handling
- `agentkit run --ci` flag — CI-friendly non-interactive mode
  - Plain text output (no Rich markup/spinners for clean CI logs)
  - Exits 1 on any step failure
  - `--json` output now includes `success: bool` and `steps[{name, status, duration_ms, output_file}]` per contract spec

### Changed
- `agentkit run --json` output: added `success` top-level key; `steps` now uses contract format `{name, status, duration_ms, output_file}`; legacy `summary.steps` fields preserved for backwards compat
- `pyproject.toml`: added `watchdog>=3.0.0` and `pyyaml>=6.0.0` as runtime dependencies

### Tests
- 142 tests (up from 82). Added 30+ tests across `test_ci.py`, `test_watch.py`, `test_run_ci.py`.

## v0.2.1 (2026-03-12)

### Fixed
- `agentkit run` lint-diff step: was passing project path as command to agentlint (causing "No such command" error). Now correctly calls `agentlint check HEAD~1`.
- `agentkit run` reflect step: was using `--notes` flag (doesn't exist in agentreflect). Now correctly uses `--from-notes`.
- Added `pyyaml` dev dependency for GitHub Action tests.

### Tests
- 82 tests (up from 47). Added regression tests for both bug fixes.

## v0.2.0 (2026-03-12)

### Added
- `agentkit doctor` — diagnose quartet tool installation with Rich table output, `--json` flag, exits 1 on missing tools
- GitHub Action (`action.yml`) — composite action to run agentkit pipeline in CI with configurable inputs
- Example workflow (`.github/workflows/examples/agentkit-pipeline.yml`)
- Improved `agentkit run` summary table with ✓/✗/⊘ status symbols and `X/Y steps passed` line
- `summary` key in `agentkit run --json` output with structured step results

## v0.1.0 (2026-03-12)

Initial release.

### Added
- `agentkit init` — initialize project, detect tools, create `.agentkit.yaml`
- `agentkit run` — sequential pipeline runner (generate → lint → benchmark → reflect)
- `agentkit status` — health check with tool versions and last run summary
- `--json` flag on `run` and `status` for machine-readable output
- `--skip` flag on `run` to skip individual steps
- `--benchmark` flag to opt-in to the coderace benchmark step
- Rich terminal output throughout
- 25+ tests with typer CliRunner

## [0.36.1] - 2026-03-16
### Fixed
- `agentkit org`: Top Finding column now shows human-readable text instead of raw JSON for agentmd findings

## v0.95.1 (2026-03-23)

### Bug Fixes
- **site_engine**: Added `source-badge` CSS, `repos-scored-stat`/`community-scored-stat` IDs, and `recently-scored` section to base template — `agentkit site --deploy` now generates the same rich index.html as `agentkit pages-refresh`
- **site_engine**: Added dynamic `data.json` fetch script to `_SCROLL_JS` template — leaderboard updates in real-time from community scores
- Fixed 4 failing tests: `test_has_fetch_script`, `test_index_html_has_source_badge_css`, `test_index_html_has_community_scored_stat`, `test_index_html_has_repos_scored_stat_id`
