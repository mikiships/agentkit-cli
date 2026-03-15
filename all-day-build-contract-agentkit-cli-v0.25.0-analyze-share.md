# All-Day Build Contract: agentkit-cli v0.25.0 — `--share` on analyze + sweep

Status: In Progress
Date: 2026-03-15
Owner: Codex execution pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Add `--share` to `agentkit analyze` and `agentkit sweep` so users can generate a public scorecard URL
for any analyzed repo with a single flag. This is the viral mechanic: `agentkit analyze github:owner/repo --share`
analyzes a public repo and returns a here.now URL. Perfect for Show HN comments, README badges, and social proof.

This contract is considered complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Full test suite must pass at the end (935 baseline, target 970+).
4. New features must ship with docs and CHANGELOG updates in the same pass.
5. CLI outputs must be deterministic and schema-backed where specified.
6. Never modify files outside ~/repos/agentkit-cli/.
7. Commit after each completed deliverable (not at the end).
8. If stuck on same issue for 3 attempts, stop and write a blocker report.
9. Do NOT refactor, restyle, or "improve" code outside the deliverables.
10. Read existing tests and docs before writing new code.

## 3. Context

Current state of share system (v0.24.0):
- `agentkit_cli/share.py` has `generate_scorecard_html()` and `upload_scorecard()`
- `agentkit share` standalone command works
- `--share` flag exists on `agentkit run` and `agentkit report`
- `agentkit analyze github:owner/repo` clones repo, runs toolkit, shows results — but NO `--share` flag
- `agentkit sweep <targets...>` does batch analysis — but NO `--share` flag

## 4. Feature Deliverables

### D1. `--share` on `agentkit analyze`

Add `--share` flag to the `analyze` command. When set:
- After analysis completes, call `generate_scorecard_html()` with the analysis result
- Upload via `upload_scorecard()`
- Print the public URL prominently: "Score card published: https://..."
- If `--json` is also set, include `"share_url": "https://..."` in the JSON output
- Non-fatal: if upload fails, warn and continue (don't crash analysis)

Files to modify:
- `agentkit_cli/commands/analyze.py` — add `--share` / `--no-share` option
- `agentkit_cli/share.py` — ensure `generate_scorecard_html()` accepts a project name + score dict that analyze can provide

- [ ] `--share` flag parsed and wired in analyze.py
- [ ] score card generated from analyze result
- [ ] URL printed to stdout (and in JSON if --json)
- [ ] Upload failure is non-fatal (warn, don't exit 1)
- [ ] Tests for D1 (mock upload, check URL in output)

### D2. `--share` on `agentkit sweep`

Add `--share` flag to the `sweep` command. When set:
- Generate a combined scorecard showing all analyzed targets in a ranked table
- Upload once (not once per target — one combined card)
- Print the shared URL
- JSON output includes `"share_url"` in the summary object

Files to modify:
- `agentkit_cli/commands/sweep.py` — add `--share` flag
- `agentkit_cli/share.py` — add `generate_sweep_scorecard_html()` or extend existing to handle multi-target input

- [ ] `--share` flag parsed and wired in sweep.py
- [ ] Combined scorecard generated for all targets
- [ ] Single upload, single URL printed
- [ ] JSON includes share_url in summary
- [ ] Non-fatal upload failure
- [ ] Tests for D2

### D3. Scorecard HTML improvements for external repos

When sharing an `analyze` result (external GitHub repo), the scorecard should:
- Show the repo name/URL prominently (not just "current project")  
- Include a "Analyzed by agentkit-cli" footer with link to PyPI
- Timestamp the analysis

Extend `generate_scorecard_html()` in `share.py`:
- Accept optional `repo_url` and `repo_name` parameters
- Render them in the card header
- Add analysis timestamp

- [ ] `repo_url` + `repo_name` params on `generate_scorecard_html()`
- [ ] Rendered in card header
- [ ] Timestamp shown
- [ ] Backward-compatible (optional params, existing callers unaffected)
- [ ] Tests for D3

### D4. README + docs + version bump

- [ ] README: add `--share` to the analyze and sweep usage examples
- [ ] CHANGELOG: v0.25.0 section with D1-D3 summary
- [ ] Version bump: `agentkit_cli/__init__.py` and `pyproject.toml` → 0.25.0
- [ ] BUILD-REPORT.md created at repo root with: what was built, test count, any issues

## 5. Test Requirements

- [ ] Unit tests for each deliverable (mock `upload_scorecard` to avoid real HTTP)
- [ ] Test `--share` on analyze with mock upload → URL in output
- [ ] Test `--share` on sweep with mock upload → single URL in combined output
- [ ] Test JSON output includes `share_url` when `--share` used
- [ ] Test upload failure is non-fatal (upload raises, analyze still exits 0)
- [ ] All existing 935 tests must still pass
- [ ] Target: 970+ total tests

## 6. Reports

- Write progress to `progress-log.md` after each deliverable
- Final BUILD-REPORT.md when all deliverables done

## 7. Stop Conditions

Stop and write a blocker report if:
- Unable to make upload mock work in tests after 3 attempts
- Any existing test breaks and the root cause isn't obvious
- The share.py interface doesn't cleanly accept the analyze output format

## 8. Out of Scope

- Do NOT add --share to any other command (run/report already have it)
- Do NOT change the here.now upload API integration
- Do NOT redesign the scorecard HTML template
- Do NOT publish to PyPI (build-loop handles publishing)
- Do NOT push to GitHub (build-loop handles git push)
