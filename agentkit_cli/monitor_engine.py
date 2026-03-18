"""MonitorEngine — orchestrates scheduled quality checks for monitored repos.

Uses MonitorConfig to track targets and their check state.
Calls agentkit analyze via ToolAdapter (or subprocess) to get scores.
Fires notifications via NotificationEngine on significant score changes.
"""
from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from agentkit_cli.monitor_config import MonitorConfig, MonitorTarget


@dataclass
class MonitorResult:
    """Result of a single monitor check."""
    target: str
    score: float
    prev_score: Optional[float]
    delta: float
    timestamp: str
    notify_fired: bool = False
    error: Optional[str] = None

    @property
    def passed(self) -> bool:
        return self.error is None


def _run_analyze(target: str, timeout: int = 120) -> Optional[float]:
    """Run `agentkit analyze <target> --json` and return the overall score.

    Returns None on failure.
    """
    cmd = [sys.executable, "-m", "agentkit_cli.main", "analyze", target, "--json"]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            return None
        data = json.loads(result.stdout)
        # analyze --json returns {"score": N, ...} or {"overall": N, ...}
        if isinstance(data, dict):
            return float(data.get("score") or data.get("overall") or 0.0)
        return None
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, json.JSONDecodeError, ValueError):
        return None


class MonitorEngine:
    """Orchestrates scheduled quality checks and notifications."""

    def __init__(
        self,
        config: Optional[MonitorConfig] = None,
        analyze_fn: Optional[Any] = None,
    ) -> None:
        """
        Args:
            config: MonitorConfig instance (defaults to disk config).
            analyze_fn: Optional callable(target) -> Optional[float] for testing.
        """
        self._config = config or MonitorConfig()
        self._analyze_fn = analyze_fn or _run_analyze

    def check_target(self, target: MonitorTarget) -> MonitorResult:
        """Run agentkit analyze on the target and return a MonitorResult."""
        ts = datetime.now(timezone.utc).isoformat()
        prev_score = target.last_score

        score = self._analyze_fn(target.target)
        if score is None:
            return MonitorResult(
                target=target.target,
                score=0.0,
                prev_score=prev_score,
                delta=0.0,
                timestamp=ts,
                notify_fired=False,
                error=f"analyze failed for {target.target}",
            )

        delta = score - prev_score if prev_score is not None else 0.0
        return MonitorResult(
            target=target.target,
            score=score,
            prev_score=prev_score,
            delta=round(delta, 2),
            timestamp=ts,
            notify_fired=False,
        )

    def should_notify(self, result: MonitorResult, target: MonitorTarget) -> bool:
        """Return True if a notification should be fired.

        Fires when:
        - abs(delta) >= alert_threshold, AND
        - score >= min_score check fails (or min_score triggers), OR
        - any significant drop is detected.
        """
        if result.error is not None:
            return False
        if abs(result.delta) >= target.alert_threshold:
            return True
        # Also fire if score drops below min_score
        if target.min_score is not None and result.score < target.min_score:
            if result.prev_score is None or result.prev_score >= target.min_score:
                return True
        return False

    def _fire_notification(self, result: MonitorResult, target: MonitorTarget) -> None:
        """Send notification via notifier module if any channel is configured."""
        if not target.has_notify():
            return
        try:
            from agentkit_cli.notifier import NotifyConfig, notify_result as send_notification
            channels = []
            if target.notify_slack:
                channels.append(("slack", target.notify_slack))
            if target.notify_discord:
                channels.append(("discord", target.notify_discord))
            if target.notify_webhook:
                channels.append(("webhook", target.notify_webhook))

            verdict = "ALERT" if result.delta < 0 else "INFO"
            findings = []
            if result.delta != 0:
                findings.append(f"Score changed by {result.delta:+.1f} points")
            if target.min_score is not None and result.score < target.min_score:
                findings.append(f"Score {result.score:.1f} is below min_score {target.min_score}")

            for service, url in channels:
                try:
                    cfg = NotifyConfig(
                        url=url,
                        service=service,
                        notify_on="always",
                        project_name=result.target,
                    )
                    send_notification(
                        config=cfg,
                        score=result.score,
                        verdict=verdict,
                        top_findings=findings,
                        delta=result.delta,
                    )
                except Exception:
                    pass
        except ImportError:
            pass

    def run_check(self, target: MonitorTarget) -> MonitorResult:
        """Check a target, update config, and send notification if needed."""
        result = self.check_target(target)
        if result.error is None:
            self._config.update_last_run(target.target, result.score, result.timestamp)
            if self.should_notify(result, target):
                self._fire_notification(result, target)
                result.notify_fired = True
        return result

    def run_all_due(self) -> List[MonitorResult]:
        """Check all targets whose last_checked is older than their schedule period."""
        self._config.load()
        results: List[MonitorResult] = []
        for mt in self._config.list_targets():
            if mt.is_due():
                result = self.run_check(mt)
                results.append(result)
        return results

    def run_target(self, target_name: str) -> Optional[MonitorResult]:
        """Force-run a specific target by name."""
        self._config.load()
        mt = self._config.get_target(target_name)
        if mt is None:
            return None
        return self.run_check(mt)
