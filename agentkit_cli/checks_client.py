"""GitHub Checks API client for posting Check Runs to PRs.

Creates and updates GitHub Check Runs via the REST API so that
agentkit quality scores appear natively in the PR UI.
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Optional
from urllib import error as urllib_error, request as urllib_request
from urllib.request import Request

logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"


@dataclass
class ChecksEnv:
    """Resolved GitHub Actions environment variables."""

    owner: str
    repo: str
    sha: str
    token: str
    is_actions: bool = True

    @property
    def full_repo(self) -> str:
        return f"{self.owner}/{self.repo}"


def detect_github_env() -> Optional[ChecksEnv]:
    """Read GitHub Actions env vars. Returns None when not in CI."""
    if os.environ.get("GITHUB_ACTIONS") != "true":
        return None

    repo_full = os.environ.get("GITHUB_REPOSITORY", "")
    if "/" not in repo_full:
        return None

    owner, repo = repo_full.split("/", 1)
    sha = os.environ.get("GITHUB_SHA", "")
    token = os.environ.get("GITHUB_TOKEN", "")

    if not sha or not token:
        return None

    return ChecksEnv(owner=owner, repo=repo, sha=sha, token=token)


def _build_headers(token: str) -> dict[str, str]:
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
    }


class GitHubChecksClient:
    """Thin client for the GitHub Checks API.

    All methods are no-ops when *env* is None (i.e. not running in
    GitHub Actions).
    """

    def __init__(self, env: Optional[ChecksEnv] = None) -> None:
        self.env = env

    @property
    def active(self) -> bool:
        """True when we have a valid GitHub environment."""
        return self.env is not None

    def create_check_run(
        self,
        name: str = "agentkit",
        head_sha: Optional[str] = None,
        status: str = "queued",
    ) -> Optional[int]:
        """Create a Check Run. Returns the check_run_id or None on failure/no-op."""
        if not self.active:
            return None

        assert self.env is not None  # for type checker
        url = f"{GITHUB_API_BASE}/repos/{self.env.full_repo}/check-runs"
        body: dict[str, Any] = {
            "name": name,
            "head_sha": head_sha or self.env.sha,
            "status": status,
        }

        result = self._post(url, body)
        if result is not None:
            return int(result.get("id", 0)) or None
        return None

    def update_check_run(
        self,
        check_run_id: int,
        *,
        status: str = "completed",
        conclusion: Optional[str] = None,
        output: Optional[dict[str, Any]] = None,
    ) -> bool:
        """Update an existing Check Run. Returns True on success."""
        if not self.active:
            return False

        assert self.env is not None
        url = f"{GITHUB_API_BASE}/repos/{self.env.full_repo}/check-runs/{check_run_id}"
        body: dict[str, Any] = {"status": status}
        if conclusion is not None:
            body["conclusion"] = conclusion
        if output is not None:
            body["output"] = output

        result = self._patch(url, body)
        return result is not None

    def _post(self, url: str, body: dict[str, Any]) -> Optional[dict[str, Any]]:
        """POST JSON to *url*. Returns parsed response or None."""
        assert self.env is not None
        return self._request(url, body, method="POST")

    def _patch(self, url: str, body: dict[str, Any]) -> Optional[dict[str, Any]]:
        """PATCH JSON to *url*. Returns parsed response or None."""
        assert self.env is not None
        return self._request(url, body, method="PATCH")

    def _request(
        self, url: str, body: dict[str, Any], method: str = "POST"
    ) -> Optional[dict[str, Any]]:
        """Execute an HTTP request. Returns parsed JSON or None on error."""
        assert self.env is not None
        data = json.dumps(body).encode("utf-8")
        req = Request(url, data=data, headers=_build_headers(self.env.token), method=method)
        try:
            with urllib_request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib_error.HTTPError as exc:
            logger.warning("Checks API %s %s failed: HTTP %s", method, url, exc.code)
            return None
        except urllib_error.URLError as exc:
            logger.warning("Checks API network error: %s", exc.reason)
            return None
        except Exception as exc:  # noqa: BLE001
            logger.warning("Checks API unexpected error: %s", exc)
            return None
