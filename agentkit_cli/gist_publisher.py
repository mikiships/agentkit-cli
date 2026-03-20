"""agentkit gist_publisher — publish content as a GitHub Gist."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from urllib import error as urllib_error, request
from urllib.request import Request

GITHUB_API_GISTS = "https://api.github.com/gists"


class GistPublishError(Exception):
    """Raised when any step of the GitHub Gist publish flow fails."""


@dataclass
class GistResult:
    """Result of a successful gist publish."""

    url: str
    gist_id: str
    raw_url: str
    created_at: str


def _get_gh_token() -> Optional[str]:
    """Try to get a GitHub token from gh CLI."""
    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            token = result.stdout.strip()
            if token:
                return token
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass
    return None


def _resolve_token() -> Optional[str]:
    """Resolve GitHub token from GITHUB_TOKEN env var or gh CLI."""
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        return token
    return _get_gh_token()


def _post_gist(payload: dict, token: Optional[str] = None) -> dict:
    """POST to GitHub Gist API. Returns parsed JSON response."""
    data = json.dumps(payload).encode("utf-8")
    req = Request(GITHUB_API_GISTS, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib_error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")
        raise GistPublishError(f"HTTP {e.code} from GitHub Gist API: {body_text}") from e
    except urllib_error.URLError as e:
        raise GistPublishError(f"Network error reaching GitHub Gist API: {e.reason}") from e


class GistPublisher:
    """Publish content as a GitHub Gist.

    Modeled after HereNowPublisher / the publish.py pattern.

    Public gists: no token required (GitHub allows unauthenticated public gist creation).
    Private gists: require GITHUB_TOKEN or gh CLI token.
    """

    def __init__(self, token: Optional[str] = None):
        """
        Args:
            token: GitHub personal access token. If None, resolved automatically
                   from GITHUB_TOKEN env var or `gh auth token`.
        """
        self._token = token

    def _ensure_token(self, public: bool) -> Optional[str]:
        """Return token if available; for private gists, token is required."""
        token = self._token or _resolve_token()
        if not public and not token:
            print(
                "Error: private gists require a GitHub token.\n"
                "Set GITHUB_TOKEN env var or run `gh auth login`, or use --public.",
                file=sys.stderr,
            )
            return None
        return token

    def publish(
        self,
        content: str,
        filename: str = "agentkit-report.md",
        description: str = "agentkit analysis report",
        public: bool = False,
    ) -> Optional[GistResult]:
        """Publish content as a GitHub Gist.

        Args:
            content: Text content to publish.
            filename: Name for the gist file (e.g. 'report.md').
            description: Gist description.
            public: If True, create a public gist (no token needed).
                    If False (default), create a secret/private gist (token required).

        Returns:
            GistResult on success, or None on failure (error printed to stderr).
        """
        token = self._ensure_token(public)
        if not public and token is None:
            return None

        payload = {
            "description": description,
            "public": public,
            "files": {
                filename: {"content": content},
            },
        }

        try:
            resp = _post_gist(payload, token=token)
        except GistPublishError as e:
            print(f"Gist publish failed: {e}", file=sys.stderr)
            return None

        gist_id = resp.get("id", "")
        html_url = resp.get("html_url", "")
        created_at = resp.get("created_at", datetime.now(timezone.utc).isoformat())

        # Build raw URL from files dict
        files_dict = resp.get("files") or {}
        raw_url = ""
        if files_dict:
            first_file = next(iter(files_dict.values()), {})
            raw_url = first_file.get("raw_url", "")

        return GistResult(
            url=html_url,
            gist_id=gist_id,
            raw_url=raw_url,
            created_at=created_at,
        )
