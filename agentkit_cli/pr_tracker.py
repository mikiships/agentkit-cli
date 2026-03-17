"""agentkit PR tracker — fetches GitHub PR statuses for tracked PRs."""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from agentkit_cli.history import HistoryDB


@dataclass
class TrackedPRStatus:
    """Full status for a tracked PR."""

    id: int
    repo: str
    pr_number: Optional[int]
    pr_url: Optional[str]
    campaign_id: Optional[str]
    submitted_at: str
    status: str  # open / merged / closed / unknown
    days_open: int
    review_comments: int
    is_merged: bool

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "repo": self.repo,
            "pr_number": self.pr_number,
            "pr_url": self.pr_url,
            "campaign_id": self.campaign_id,
            "submitted_at": self.submitted_at,
            "status": self.status,
            "days_open": self.days_open,
            "review_comments": self.review_comments,
            "is_merged": self.is_merged,
        }


class PRTracker:
    """Fetches GitHub PR statuses for tracked PRs stored in the history DB."""

    def __init__(self, token: Optional[str] = None) -> None:
        self.token = token

    # ------------------------------------------------------------------
    # DB helpers
    # ------------------------------------------------------------------

    def get_tracked_prs(
        self,
        db_path: Optional[Path] = None,
        campaign_id: Optional[str] = None,
        limit: int = 50,
    ) -> list:
        """Return tracked PR rows from the history DB."""
        db = HistoryDB(db_path=db_path)
        return db.get_tracked_prs(campaign_id=campaign_id, limit=limit)

    # ------------------------------------------------------------------
    # GitHub API
    # ------------------------------------------------------------------

    def fetch_pr_status(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        token: Optional[str] = None,
    ) -> dict:
        """Query GitHub REST API for a single PR.

        Returns a dict with keys: state, merged, mergeable_state,
        created_at, updated_at, review_comments, commits.
        Returns status='unknown' on errors.
        """
        tok = token or self.token
        url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
        headers = {"Accept": "application/vnd.github.v3+json"}
        if tok:
            headers["Authorization"] = f"token {tok}"

        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                # Check rate limit
                remaining = resp.headers.get("X-RateLimit-Remaining", "60")
                try:
                    if int(remaining) < 10:
                        time.sleep(5)
                except (ValueError, TypeError):
                    pass
                data = json.loads(resp.read())
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return {"state": "unknown", "merged": False, "review_comments": 0, "commits": 0, "error": "not_found"}
            if e.code in (403, 429):
                return {"state": "unknown", "merged": False, "review_comments": 0, "commits": 0, "error": "rate_limited"}
            return {"state": "unknown", "merged": False, "review_comments": 0, "commits": 0, "error": f"http_{e.code}"}
        except Exception as e:
            return {"state": "unknown", "merged": False, "review_comments": 0, "commits": 0, "error": str(e)}

        merged = data.get("merged", False) or data.get("merged_at") is not None
        return {
            "state": data.get("state", "unknown"),
            "merged": merged,
            "mergeable_state": data.get("mergeable_state"),
            "created_at": data.get("created_at"),
            "updated_at": data.get("updated_at"),
            "review_comments": data.get("review_comments", 0),
            "commits": data.get("commits", 0),
        }

    # ------------------------------------------------------------------
    # Bulk refresh
    # ------------------------------------------------------------------

    def refresh_statuses(
        self,
        prs: list,
        token: Optional[str] = None,
        db_path: Optional[Path] = None,
    ) -> List[TrackedPRStatus]:
        """Fetch current GitHub status for each tracked PR.

        Sleeps 0.5s between calls to respect rate limits.
        Updates last_status and last_checked_at in the DB.
        """
        tok = token or self.token
        results: List[TrackedPRStatus] = []
        db = HistoryDB(db_path=db_path) if db_path else None

        for pr_row in prs:
            pr_id = pr_row["id"]
            repo = pr_row["repo"]
            pr_number = pr_row.get("pr_number")
            pr_url = pr_row.get("pr_url") or ""
            campaign_id = pr_row.get("campaign_id")
            submitted_at = pr_row.get("submitted_at", "")

            # Compute days_open
            days_open = _compute_days_open(submitted_at)

            if pr_number is None:
                # No PR number — can't check status
                status_rec = TrackedPRStatus(
                    id=pr_id,
                    repo=repo,
                    pr_number=pr_number,
                    pr_url=pr_url,
                    campaign_id=campaign_id,
                    submitted_at=submitted_at,
                    status="unknown",
                    days_open=days_open,
                    review_comments=0,
                    is_merged=False,
                )
                results.append(status_rec)
                continue

            # Parse owner/repo
            parts = repo.split("/", 1)
            if len(parts) != 2:
                status_rec = TrackedPRStatus(
                    id=pr_id,
                    repo=repo,
                    pr_number=pr_number,
                    pr_url=pr_url,
                    campaign_id=campaign_id,
                    submitted_at=submitted_at,
                    status="unknown",
                    days_open=days_open,
                    review_comments=0,
                    is_merged=False,
                )
                results.append(status_rec)
                continue

            owner, repo_name = parts
            api_result = self.fetch_pr_status(owner, repo_name, pr_number, token=tok)

            # Determine status string
            if api_result.get("error") == "not_found":
                status = "unknown"
            elif api_result.get("merged"):
                status = "merged"
            elif api_result.get("state") == "closed":
                status = "closed"
            elif api_result.get("state") == "open":
                status = "open"
            else:
                status = "unknown"

            review_comments = api_result.get("review_comments", 0) or 0

            # Update DB if available
            if db is not None:
                checked_at = datetime.now(timezone.utc).isoformat()
                db.update_pr_status(pr_id, status, checked_at)

            status_rec = TrackedPRStatus(
                id=pr_id,
                repo=repo,
                pr_number=pr_number,
                pr_url=pr_url,
                campaign_id=campaign_id,
                submitted_at=submitted_at,
                status=status,
                days_open=days_open,
                review_comments=review_comments,
                is_merged=(status == "merged"),
            )
            results.append(status_rec)

            time.sleep(0.5)

        return results


def _compute_days_open(submitted_at: str) -> int:
    """Return number of days since submitted_at (ISO string)."""
    try:
        submitted = datetime.fromisoformat(submitted_at.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        return max(0, (now - submitted).days)
    except Exception:
        return 0
