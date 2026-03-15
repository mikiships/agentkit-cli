"""agentkit notification module — Slack / Discord / generic webhook support.

Notification failures NEVER affect the caller's exit code. All errors are
logged as warnings and swallowed.
"""
from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.error import URLError
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SUPPORTED_SERVICES = ("slack", "discord", "webhook")
NOTIFY_ON_OPTIONS = ("fail", "always")

_TIMEOUT = 5  # seconds per attempt
_MAX_ATTEMPTS = 2


@dataclass
class NotifyConfig:
    url: str
    service: str  # slack | discord | webhook
    notify_on: str = "fail"  # fail | always
    project_name: str = "agentkit"

    def __post_init__(self) -> None:
        if self.service not in SUPPORTED_SERVICES:
            raise ValueError(f"service must be one of {SUPPORTED_SERVICES}")
        if self.notify_on not in NOTIFY_ON_OPTIONS:
            raise ValueError(f"notify_on must be one of {NOTIFY_ON_OPTIONS}")


# ---------------------------------------------------------------------------
# Payload builders
# ---------------------------------------------------------------------------

_COLOR_PASS = "#36a64f"   # green
_COLOR_FAIL = "#cc0000"   # red

# Slack uses decimal integers for attachment colors when not hex
_DISCORD_PASS = 0x36A64F
_DISCORD_FAIL = 0xCC0000


def _truncate(findings: list[str], limit: int = 3) -> list[str]:
    return findings[:limit]


def _build_slack_payload(
    project: str,
    score: float,
    verdict: str,
    top_findings: list[str],
    delta: Optional[float],
) -> dict[str, Any]:
    passed = verdict.upper() == "PASS"
    color = _COLOR_PASS if passed else _COLOR_FAIL
    status_emoji = ":white_check_mark:" if passed else ":x:"
    delta_text = f"  |  delta: {delta:+.1f}" if delta is not None else ""

    finding_lines = "\n".join(f"• {f}" for f in _truncate(top_findings)) or "No findings."
    attachment: dict[str, Any] = {
        "color": color,
        "title": f"{status_emoji} agentkit gate — {project}",
        "text": f"Score: *{score:.1f}/100*{delta_text}\nVerdict: *{verdict}*",
        "fields": [
            {
                "title": "Top Findings",
                "value": finding_lines,
                "short": False,
            }
        ],
        "footer": "agentkit-cli",
        "ts": int(time.time()),
    }
    return {"attachments": [attachment]}


def _build_discord_payload(
    project: str,
    score: float,
    verdict: str,
    top_findings: list[str],
    delta: Optional[float],
) -> dict[str, Any]:
    passed = verdict.upper() == "PASS"
    color = _DISCORD_PASS if passed else _DISCORD_FAIL
    delta_text = f" | delta: {delta:+.1f}" if delta is not None else ""

    finding_text = "\n".join(f"• {f}" for f in _truncate(top_findings)) or "No findings."
    embed: dict[str, Any] = {
        "title": f"agentkit gate — {project}",
        "description": f"**Score:** {score:.1f}/100{delta_text}\n**Verdict:** {verdict}",
        "color": color,
        "fields": [
            {
                "name": "Top Findings",
                "value": finding_text,
                "inline": False,
            }
        ],
        "footer": {"text": "agentkit-cli"},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return {"embeds": [embed]}


def _build_generic_payload(
    project: str,
    score: float,
    verdict: str,
    top_findings: list[str],
    delta: Optional[float],
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "project": project,
        "score": score,
        "verdict": verdict,
        "top_findings": top_findings,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if delta is not None:
        payload["delta"] = delta
    return payload


def build_payload(
    config: NotifyConfig,
    score: float,
    verdict: str,
    top_findings: list[str],
    delta: Optional[float] = None,
) -> dict[str, Any]:
    """Build the service-specific POST payload."""
    if config.service == "slack":
        return _build_slack_payload(config.project_name, score, verdict, top_findings, delta)
    if config.service == "discord":
        return _build_discord_payload(config.project_name, score, verdict, top_findings, delta)
    return _build_generic_payload(config.project_name, score, verdict, top_findings, delta)


# ---------------------------------------------------------------------------
# HTTP sender
# ---------------------------------------------------------------------------

def _post(url: str, payload: dict[str, Any]) -> tuple[bool, str]:
    """POST JSON to *url*. Returns (success, message)."""
    body = json.dumps(payload).encode("utf-8")
    req = Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", "User-Agent": "agentkit-cli/notifier"},
        method="POST",
    )
    try:
        with urlopen(req, timeout=_TIMEOUT) as resp:
            status = resp.status
            if 200 <= status < 300:
                return True, f"HTTP {status}"
            return False, f"HTTP {status}"
    except URLError as exc:
        return False, str(exc.reason)
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


def _send_with_retry(url: str, payload: dict[str, Any]) -> tuple[bool, str]:
    """Try up to _MAX_ATTEMPTS times. Returns (success, last_message)."""
    last_msg = "unknown error"
    for attempt in range(1, _MAX_ATTEMPTS + 1):
        ok, msg = _post(url, payload)
        if ok:
            return True, msg
        last_msg = msg
        if attempt < _MAX_ATTEMPTS:
            time.sleep(1)
    return False, last_msg


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def notify_result(
    config: NotifyConfig,
    verdict: str,
    score: float,
    top_findings: Optional[list[str]] = None,
    delta: Optional[float] = None,
) -> bool:
    """Fire a notification. Returns True on success.

    Errors are logged but NEVER propagated — notification failures must not
    affect the gate exit code.
    """
    try:
        if top_findings is None:
            top_findings = []

        passed = verdict.upper() == "PASS"
        if config.notify_on == "fail" and passed:
            return True  # nothing to do

        payload = build_payload(config, score, verdict, top_findings, delta)
        ok, msg = _send_with_retry(config.url, payload)
        if ok:
            logger.debug("Notification delivered to %s (%s)", config.service, msg)
        else:
            logger.warning("Notification to %s failed: %s", config.service, msg)
        return ok
    except Exception as exc:  # noqa: BLE001
        logger.warning("Unexpected error in notifier: %s", exc)
        return False


# ---------------------------------------------------------------------------
# Env-var helpers
# ---------------------------------------------------------------------------

def notify_config_from_env() -> list[NotifyConfig]:
    """Read AGENTKIT_NOTIFY_* env vars and return NotifyConfig list."""
    configs: list[NotifyConfig] = []
    mapping = [
        ("AGENTKIT_NOTIFY_SLACK", "slack"),
        ("AGENTKIT_NOTIFY_DISCORD", "discord"),
        ("AGENTKIT_NOTIFY_WEBHOOK", "webhook"),
    ]
    for var, service in mapping:
        url = os.environ.get(var, "").strip()
        if url:
            notify_on = os.environ.get("AGENTKIT_NOTIFY_ON", "fail")
            try:
                configs.append(NotifyConfig(url=url, service=service, notify_on=notify_on))
            except ValueError as exc:
                logger.warning("Invalid env var config for %s: %s", var, exc)
    return configs


def resolve_notify_configs(
    notify_slack: Optional[str] = None,
    notify_discord: Optional[str] = None,
    notify_webhook: Optional[str] = None,
    notify_on: str = "fail",
    project_name: str = "agentkit",
) -> list[NotifyConfig]:
    """Build list of NotifyConfig from CLI flags + env vars.

    CLI flags take precedence over env vars for the same service.
    """
    effective_slack = notify_slack or os.environ.get("AGENTKIT_NOTIFY_SLACK", "").strip() or None
    effective_discord = notify_discord or os.environ.get("AGENTKIT_NOTIFY_DISCORD", "").strip() or None
    effective_webhook = notify_webhook or os.environ.get("AGENTKIT_NOTIFY_WEBHOOK", "").strip() or None

    configs: list[NotifyConfig] = []
    for url, service in [
        (effective_slack, "slack"),
        (effective_discord, "discord"),
        (effective_webhook, "webhook"),
    ]:
        if url:
            try:
                configs.append(
                    NotifyConfig(url=url, service=service, notify_on=notify_on, project_name=project_name)
                )
            except ValueError as exc:
                logger.warning("Invalid notify config for %s: %s", service, exc)
    return configs


def fire_notifications(
    configs: list[NotifyConfig],
    verdict: str,
    score: float,
    top_findings: Optional[list[str]] = None,
    delta: Optional[float] = None,
) -> None:
    """Fire all configured notifications. Never raises."""
    for cfg in configs:
        try:
            notify_result(cfg, verdict=verdict, score=score, top_findings=top_findings, delta=delta)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Notification fire error for %s: %s", cfg.service, exc)
