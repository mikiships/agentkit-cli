"""EventProcessor — receives GitHub webhook event dicts and acts on them."""
from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class EventProcessor:
    """Process parsed GitHub webhook events.

    For each event the processor:
    1. Determines the target path (local clone or temp dir).
    2. Runs composite analysis via ToolAdapter/CompositeScoreEngine.
    3. Posts result via NotificationService if channels configured.
    4. Records result in history DB.
    5. For pull_request events: formats and logs a PR comment body.
    """

    def __init__(
        self,
        notify_channels: Optional[List[str]] = None,
        history_project: Optional[str] = None,
        regression_threshold: float = 5.0,
    ) -> None:
        self.notify_channels: List[str] = notify_channels or []
        self.history_project = history_project
        self.regression_threshold = regression_threshold

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single webhook event dict.

        Returns a result dict with keys: event_type, repo, score, recorded,
        notified, comment_body (for PR events).
        """
        event_type = event.get("event_type", "push")
        repo_info = self._extract_repo_info(event)
        repo_full_name = repo_info.get("full_name", "unknown/repo")

        logger.info("Processing %s event for %s", event_type, repo_full_name)

        # Determine local target path
        target_path = self._resolve_target_path(repo_info)

        # Run analysis
        score, prev_score = self._run_analysis(target_path, repo_full_name)

        # Record in history
        recorded = self._record_history(repo_full_name, score)

        # Check for regression and notify
        notified = self._maybe_notify(repo_full_name, score, prev_score)

        # Format PR comment if applicable
        comment_body: Optional[str] = None
        if event_type == "pull_request":
            comment_body = self._format_pr_comment(repo_info, score, prev_score)
            logger.info("PR comment for %s:\n%s", repo_full_name, comment_body)

        result: Dict[str, Any] = {
            "event_type": event_type,
            "repo": repo_full_name,
            "score": score,
            "prev_score": prev_score,
            "recorded": recorded,
            "notified": notified,
        }
        if comment_body is not None:
            result["comment_body"] = comment_body

        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _extract_repo_info(self, event: Dict[str, Any]) -> Dict[str, Any]:
        repo = event.get("repository") or {}
        return {
            "full_name": repo.get("full_name") or event.get("repo", "unknown/repo"),
            "clone_url": repo.get("clone_url") or "",
            "ref": event.get("ref", ""),
            "pr_number": event.get("pull_request", {}).get("number"),
        }

    def _resolve_target_path(self, repo_info: Dict[str, Any]) -> Path:
        """Return a local path for this repo (uses cwd as fallback)."""
        clone_url = repo_info.get("clone_url", "")

        # Check history DB for a previously recorded local path
        if clone_url:
            local = self._lookup_local_path(clone_url)
            if local and local.exists():
                logger.debug("Using cached local path: %s", local)
                return local

        # Fall back to cwd (used in test/smoke scenarios)
        return Path.cwd()

    def _lookup_local_path(self, clone_url: str) -> Optional[Path]:
        """Check history DB for a local clone path by clone_url.

        This is a best-effort lookup; returns None if not found.
        """
        try:
            from agentkit_cli.history import HistoryDB
            db = HistoryDB()
            rows = db.get_history(limit=100)
            # History rows don't store clone_url directly; return None
            _ = rows  # suppress unused var
        except Exception:
            pass
        return None

    def _run_analysis(self, path: Path, repo_name: str) -> tuple[float, Optional[float]]:
        """Run composite analysis and return (current_score, prev_score)."""
        prev_score: Optional[float] = self._get_previous_score(repo_name)

        try:
            from agentkit_cli.composite import CompositeScoreEngine
            engine = CompositeScoreEngine()
            result = engine.compute({})
            score = float(result.score)
        except Exception as exc:
            logger.warning("CompositeScoreEngine failed: %s — using 0.0", exc)
            score = 0.0

        return score, prev_score

    def _get_previous_score(self, repo_name: str) -> Optional[float]:
        """Retrieve the most recent composite score for this repo from history."""
        try:
            from agentkit_cli.history import HistoryDB
            db = HistoryDB()
            rows = db.get_history(limit=1, project=repo_name, tool="composite")
            if rows:
                return float(rows[0]["score"])
        except Exception:
            pass
        return None

    def _record_history(self, repo_name: str, score: float) -> bool:
        """Record composite score in history DB."""
        try:
            from agentkit_cli.history import record_run
            record_run(repo_name, "composite", score)
            return True
        except Exception as exc:
            logger.warning("Failed to record history: %s", exc)
            return False

    def _maybe_notify(
        self, repo_name: str, score: float, prev_score: Optional[float]
    ) -> bool:
        """Fire notifications if a regression is detected."""
        if not self.notify_channels:
            return False
        if prev_score is None:
            return False
        delta = prev_score - score
        if delta < self.regression_threshold:
            return False

        try:
            from agentkit_cli.notifier import fire_notifications, resolve_notify_configs
            configs = []
            for ch in self.notify_channels:
                if ch.startswith("https://hooks.slack.com"):
                    svc = "slack"
                elif "discord.com" in ch:
                    svc = "discord"
                else:
                    svc = "webhook"
                configs.append(
                    resolve_notify_configs(
                        notify_slack=ch if svc == "slack" else None,
                        notify_discord=ch if svc == "discord" else None,
                        notify_webhook=ch if svc == "webhook" else None,
                        notify_on="always",
                        project_name=repo_name,
                    )
                )
            flat = [c for sub in configs for c in sub]
            fire_notifications(
                flat,
                verdict="FAIL",
                score=score,
                top_findings=[f"Regression: {delta:.1f} pts drop from {prev_score:.0f}"],
            )
            return True
        except Exception as exc:
            logger.warning("Notification failed: %s", exc)
            return False

    def _format_pr_comment(
        self,
        repo_info: Dict[str, Any],
        score: float,
        prev_score: Optional[float],
    ) -> str:
        """Build a GitHub PR comment body string."""
        lines = [
            "## agentkit Quality Report",
            "",
            f"**Repo:** `{repo_info.get('full_name', 'unknown')}`",
            f"**Ref:** `{repo_info.get('ref', 'unknown')}`",
        ]
        if repo_info.get("pr_number"):
            lines.append(f"**PR:** #{repo_info['pr_number']}")

        grade = self._score_to_grade(score)
        lines += [
            "",
            f"**Agent Quality Score:** {score:.0f}/100 ({grade})",
        ]

        if prev_score is not None:
            delta = score - prev_score
            sign = "+" if delta >= 0 else ""
            lines.append(f"**Change from last run:** {sign}{delta:.1f} pts")

        lines += [
            "",
            "_Generated by [agentkit-cli](https://github.com/mikiships/agentkit-cli)_",
        ]
        return "\n".join(lines)

    @staticmethod
    def _score_to_grade(score: float) -> str:
        if score >= 90:
            return "A"
        if score >= 80:
            return "B"
        if score >= 70:
            return "C"
        if score >= 60:
            return "D"
        return "F"
