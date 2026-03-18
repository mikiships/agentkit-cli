# All-Day Build Contract: agentkit-cli v0.48.0 — `agentkit webhook`

Status: In Progress
Date: 2026-03-18
Owner: Codex execution pass
Scope type: Deliverable-gated (no hour promises)

## 1. Objective

Add `agentkit webhook` — an inbound GitHub webhook server that triggers agentkit analysis on push and pull_request events. This closes the "outside-in" CI loop: instead of only running agentkit from inside CI, GitHub can push events to agentkit, which auto-analyzes and posts results back as PR comments or notifications.

Architecture:
- `agentkit webhook serve --port 8080 --secret <hmac-secret>` starts a local HTTP server
- Handles GitHub `push` and `pull_request` events (HMAC-SHA256 verified)
- On event: identifies the repo, runs `agentkit analyze` on the cloned path, fires notifications (existing NotificationService)
- `agentkit webhook config` — set/show webhook secret, port, target URL, notification channels
- `agentkit webhook test` — simulate a push event locally for smoke-testing

This contract is considered complete only when every deliverable and validation gate below is satisfied.

## 2. Non-Negotiable Build Rules

1. No time-based completion claims.
2. Completion is allowed only when all checklist items are checked.
3. Full test suite must pass at the end (baseline: 2062 tests).
4. New features must ship with docs and report addendum updates in the same pass.
5. CLI outputs must be deterministic and schema-backed where specified.
6. Never modify files outside the project directory (`~/repos/agentkit-cli/`).
7. Commit after each completed deliverable (not at the end).
8. If stuck on same issue for 3 attempts, stop and write a blocker report.
9. Do NOT refactor, restyle, or "improve" code outside the deliverables.
10. Read existing tests and docs before writing new code.
11. Do NOT run `pip install`, `twine upload`, `git push`, or `git tag`. Build and commit only.
12. Do NOT run `agentkit analyze github:...` or other commands that clone external repos in tests — use mocks.

## 3. Feature Deliverables

### D1. WebhookServer core (`agentkit_cli/webhook/server.py`, `agentkit_cli/webhook/verifier.py`)

Build the HTTP webhook server using Python's stdlib `http.server` (no external HTTP framework). Must handle:
- GitHub `X-Hub-Signature-256` HMAC verification (reject invalid signatures with 403)
- Parse `X-GitHub-Event` header (`push`, `pull_request`, other events ignored with 200)
- Extract repo info from payload (full_name, clone_url, ref, PR number if applicable)
- Queue events for processing (non-blocking: respond 200 immediately, process async in thread)
- Graceful shutdown on SIGTERM/SIGINT

Required files:
- `agentkit_cli/webhook/__init__.py`
- `agentkit_cli/webhook/server.py` — WebhookServer class
- `agentkit_cli/webhook/verifier.py` — verify_signature(secret, payload, header) -> bool
- `agentkit_cli/webhook/event_processor.py` — EventProcessor: receive event dict, run analyze, fire notifications

- [ ] WebhookServer class handles push events
- [ ] WebhookServer class handles pull_request events
- [ ] HMAC-SHA256 signature verification rejects bad signatures
- [ ] Non-blocking response (200) + async processing thread
- [ ] Graceful shutdown
- [ ] Tests for D1 (≥15 tests, all mocked — no real HTTP calls)

### D2. `agentkit webhook` CLI commands

Wire up the CLI under `agentkit webhook`:

- `agentkit webhook serve [--port PORT] [--secret SECRET] [--no-verify-sig]` — start server
- `agentkit webhook config [--set-secret S] [--set-port P] [--set-channel C] [--show]` — manage webhook config stored in `.agentkit.toml` under `[webhook]` section
- `agentkit webhook test [--event push|pull_request] [--repo REPO]` — synthesize a fake event and run through EventProcessor locally (no HTTP)

Config keys in `.agentkit.toml`:
```toml
[webhook]
port = 8080
secret = ""  # HMAC secret from GitHub webhook settings
notify_channels = []  # reuse existing NotificationService channels
```

Required files:
- `agentkit_cli/commands/webhook.py` — Click group + serve/config/test subcommands
- Update `agentkit_cli/main.py` to register `webhook` group

- [ ] `agentkit webhook serve` starts server, prints local URL
- [ ] `agentkit webhook config --show` displays current settings
- [ ] `agentkit webhook config --set-secret` persists to .agentkit.toml
- [ ] `agentkit webhook test` runs EventProcessor end-to-end with mocked analyze
- [ ] Tests for D2 (≥12 tests)

### D3. EventProcessor integration with existing toolkit

EventProcessor.process(event) must:
1. Determine target path: if repo is already cloned locally (check history DB by clone_url), use local path; else clone to a temp dir
2. Run `ToolAdapter.run_all()` or equivalent to get a composite score
3. Post result via NotificationService if channels configured
4. Record in history DB (reuse existing HistoryManager.record_run)
5. For `pull_request` events: format a PR comment body (reuse `format_review_comment.py` pattern) and print to stdout (actual GitHub PR comment posting is out of scope — stub it with a logged message)

- [ ] EventProcessor.process() runs analyze on event repo
- [ ] Records result in history DB
- [ ] Fires notification on regression (score < previous run - 5)
- [ ] PR comment body formatted and logged
- [ ] Tests for D3 (≥12 tests, all mocked analyze calls)

### D4. `agentkit webhook` in `agentkit doctor` and `agentkit run`

- `agentkit doctor` should check: is a webhook server configured? If yes, is the secret non-empty?
- `agentkit run --webhook-notify` flag: after run, POST result to a configured webhook URL (outbound, not inbound — reuse existing notify pattern for this)
- Add webhook section to `agentkit doctor` output under "Integrations"

- [ ] `agentkit doctor` checks webhook config
- [ ] `agentkit run --webhook-notify` sends outbound POST on completion
- [ ] Tests for D4 (≥8 tests)

### D5. Docs, CHANGELOG, version bump to 0.48.0, BUILD-REPORT

- Update README.md: add "GitHub Webhook Integration" section after CI section
- Update CHANGELOG.md: add v0.48.0 entry
- Bump version in `pyproject.toml` from 0.47.0 to 0.48.0
- Write `BUILD-REPORT.md` in repo root with: deliverables status, test count delta, known limitations
- Full test suite must pass: `python3 -m pytest -q` — target ≥2100 tests (2062 baseline + ≥38 new)

- [ ] README updated with webhook section
- [ ] CHANGELOG updated
- [ ] pyproject.toml version = "0.48.0"
- [ ] BUILD-REPORT.md written
- [ ] Full suite passes at ≥2100 tests

## 4. Validation Gates (all must pass before marking complete)

1. `python3 -m pytest -q` — ≥2100 tests, 0 failures
2. `agentkit webhook --help` shows serve/config/test subcommands
3. `agentkit webhook config --show` prints webhook settings without crashing
4. `agentkit webhook test --event push --repo .` runs without errors (uses mocked analyze)
5. `agentkit doctor` includes "Webhook" section in output
6. `grep -r "0.47.0" pyproject.toml` returns nothing (version bumped)
7. Git log shows 5 commits (one per deliverable)

## 5. Stop Conditions

Stop and write a blocker report if:
- stdlib HTTP server approach proves insufficient (e.g., async threading issues that can't be solved in 2 attempts)
- EventProcessor integration with ToolAdapter requires more than 30 lines of plumbing changes
- Any deliverable takes more than 3 failed attempts

## 6. Out of Scope

- Actual outbound GitHub API calls to post PR comments (stub/log only)
- ngrok/tunnel setup (that's a user responsibility)
- OAuth or GitHub App auth
- Docker deployment

## 7. Working Directory

`~/repos/agentkit-cli/`

Run tests with: `python3 -m pytest -q`
