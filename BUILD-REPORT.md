# BUILD-REPORT: agentkit-cli v0.21.0

**Date:** 2026-03-15
**Builder:** build-loop subagent

## What Was Built

Added full Slack/Discord/generic webhook notification support to agentkit-cli as specified in contract `agentkit-cli-v0.21.0-notify.md`.

### Deliverables

- [x] **D1: `agentkit_cli/notifier.py`** — `NotifyConfig` dataclass, `build_payload` (Slack attachment / Discord embed / generic JSON), `notify_result`, `fire_notifications`, `resolve_notify_configs`. HTTP POST via stdlib `urllib` (no new dependencies), single retry with 5s timeout. Notification errors never propagate to caller exit code.

- [x] **D2: CLI flags** — `--notify-slack`, `--notify-discord`, `--notify-webhook`, `--notify-on` added to `agentkit gate` and `agentkit run`. Env vars `AGENTKIT_NOTIFY_SLACK` / `AGENTKIT_NOTIFY_DISCORD` / `AGENTKIT_NOTIFY_WEBHOOK` / `AGENTKIT_NOTIFY_ON` accepted as fallbacks; CLI flags take precedence. `action.yml` updated with matching inputs.

- [x] **D3: `agentkit notify` command group** — `agentkit notify test --slack|--discord|--webhook <url>` fires a test notification and prints ✓/✗ result. `agentkit notify config` shows current env var config.

- [x] **D4: Tests + docs + version bump** — 57 new tests across `test_notifier.py`, `test_notify_command.py`, `test_gate_notify_integration.py`. All HTTP mocked via `unittest.mock`. README Notifications section written. CHANGELOG v0.21.0 entry added. Version bumped `0.20.0 → 0.21.0` in `pyproject.toml` and `agentkit_cli/__init__.py`.

## Test Count

| | Count |
|---|---|
| Before | 702 |
| After | 759 |
| New tests added | 57 |

## Deviations from Contract

None. All deliverables match spec. The `fire_notifications` wrapper catches per-config exceptions to ensure one failing notification never blocks the others (slightly more defensive than the contract required, which only specified gate exit code safety).

## READY TO SHIP
