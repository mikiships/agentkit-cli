"""agentkit campaign — batch PR submission to multiple repos."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple


@dataclass
class RepoSpec:
    owner: str
    repo: str
    stars: int = 0
    language: Optional[str] = None
    description: Optional[str] = None

    @property
    def full_name(self) -> str:
        return f"{self.owner}/{self.repo}"


@dataclass
class PRResult:
    repo: RepoSpec
    pr_url: str
    score_before: Optional[float] = None
    score_after: Optional[float] = None

    def to_dict(self) -> dict:
        return {
            "repo": self.repo.full_name,
            "pr_url": self.pr_url,
            "score_before": self.score_before,
            "score_after": self.score_after,
        }


@dataclass
class CampaignResult:
    campaign_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    submitted: List[PRResult] = field(default_factory=list)
    skipped: List[RepoSpec] = field(default_factory=list)
    failed: List[Tuple[RepoSpec, str]] = field(default_factory=list)
    target_spec: str = ""
    file: str = "CLAUDE.md"

    def to_dict(self) -> dict:
        return {
            "campaign_id": self.campaign_id,
            "target_spec": self.target_spec,
            "file": self.file,
            "submitted": [r.to_dict() for r in self.submitted],
            "skipped": [{"repo": r.full_name, "stars": r.stars} for r in self.skipped],
            "failed": [{"repo": r.full_name, "error": e} for r, e in self.failed],
            "totals": {
                "prs": len(self.submitted),
                "skipped": len(self.skipped),
                "failed": len(self.failed),
            },
        }


def _github_request(url: str, token: Optional[str] = None) -> dict:
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


class CampaignEngine:
    """Discovers repos and orchestrates batch PR submission."""

    def __init__(self, token: Optional[str] = None) -> None:
        self.token = token or os.environ.get("GITHUB_TOKEN")

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def find_repos(
        self,
        target_spec: str,
        limit: int = 10,
        language: Optional[str] = None,
        topic: Optional[str] = None,
        min_stars: Optional[int] = None,
    ) -> List[RepoSpec]:
        """Return candidate repos from target_spec."""
        if target_spec.startswith("github:"):
            owner = target_spec[len("github:"):]
            repos = self._find_org_repos(owner, limit=limit)
        elif target_spec.startswith("topic:"):
            topic_name = target_spec[len("topic:"):]
            repos = self._find_topic_repos(topic_name, limit=limit, language=language)
        elif target_spec.startswith("repos-file:"):
            path = target_spec[len("repos-file:"):]
            repos = self._find_file_repos(path)
        else:
            raise ValueError(f"Unknown target_spec format: {target_spec!r}")

        # Apply filters
        if language:
            repos = [r for r in repos if r.language and r.language.lower() == language.lower()]
        if min_stars is not None:
            repos = [r for r in repos if r.stars >= min_stars]
        return repos[:limit]

    def _find_org_repos(self, owner: str, limit: int = 10) -> List[RepoSpec]:
        url = f"https://api.github.com/orgs/{owner}/repos?type=public&sort=stars&per_page={min(limit, 100)}"
        try:
            data = _github_request(url, self.token)
        except urllib.error.HTTPError:
            # Fall back to users API
            url = f"https://api.github.com/users/{owner}/repos?type=public&sort=stars&per_page={min(limit, 100)}"
            data = _github_request(url, self.token)
        return [
            RepoSpec(
                owner=item["owner"]["login"],
                repo=item["name"],
                stars=item.get("stargazers_count", 0),
                language=item.get("language"),
                description=item.get("description"),
            )
            for item in data
        ]

    def _find_topic_repos(
        self, topic: str, limit: int = 10, language: Optional[str] = None
    ) -> List[RepoSpec]:
        q = f"topic:{topic}"
        if language:
            q += f"+language:{language}"
        url = f"https://api.github.com/search/repositories?q={q}&sort=stars&per_page={min(limit, 100)}"
        data = _github_request(url, self.token)
        items = data.get("items", [])
        return [
            RepoSpec(
                owner=item["owner"]["login"],
                repo=item["name"],
                stars=item.get("stargazers_count", 0),
                language=item.get("language"),
                description=item.get("description"),
            )
            for item in items
        ]

    def _find_file_repos(self, path: str) -> List[RepoSpec]:
        repos = []
        for line in Path(path).read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("/")
            if len(parts) == 2:
                repos.append(RepoSpec(owner=parts[0], repo=parts[1]))
        return repos

    # ------------------------------------------------------------------
    # Context file detection
    # ------------------------------------------------------------------

    def has_context_file(
        self, owner: str, repo: str, token: Optional[str] = None
    ) -> bool:
        """Return True if the repo root contains CLAUDE.md or AGENTS.md."""
        tok = token or self.token
        for filename in ("CLAUDE.md", "AGENTS.md"):
            url = f"https://api.github.com/repos/{owner}/{repo}/contents/{filename}"
            try:
                _github_request(url, tok)
                return True
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    continue
                raise
        return False

    def filter_missing_context(self, repos: List[RepoSpec]) -> List[RepoSpec]:
        """Return repos that don't already have CLAUDE.md or AGENTS.md."""
        return [r for r in repos if not self.has_context_file(r.owner, r.repo)]

    # ------------------------------------------------------------------
    # Campaign run
    # ------------------------------------------------------------------

    def run_campaign(
        self,
        repos: List[RepoSpec],
        dry_run: bool = False,
        file: str = "CLAUDE.md",
        force: bool = False,
        target_spec: str = "",
    ) -> CampaignResult:
        """Submit PRs to each repo. Reuses agentkit pr logic."""
        import subprocess

        result = CampaignResult(target_spec=target_spec, file=file)

        for repo_spec in repos:
            target = f"github:{repo_spec.owner}/{repo_spec.repo}"
            cmd = [
                "agentkit", "pr", target,
                "--file", file,
                "--json",
            ]
            if dry_run:
                cmd.append("--dry-run")
            if force:
                cmd.append("--force")

            try:
                proc = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=120
                )
                if proc.returncode == 0:
                    # Try to parse JSON output
                    try:
                        out = json.loads(proc.stdout.strip())
                        if out.get("dry_run"):
                            pr_url = "[DRY RUN]"
                        else:
                            pr_url = out.get("pr_url", "")
                        result.submitted.append(
                            PRResult(
                                repo=repo_spec,
                                pr_url=pr_url,
                                score_before=out.get("score_before"),
                                score_after=out.get("score_after"),
                            )
                        )
                    except (json.JSONDecodeError, AttributeError):
                        result.submitted.append(PRResult(repo=repo_spec, pr_url=""))
                else:
                    stderr = proc.stderr or proc.stdout or ""
                    # Check if it's a "already exists" skip
                    if "already exists" in stderr.lower() or "skipping" in stderr.lower():
                        result.skipped.append(repo_spec)
                    else:
                        result.failed.append((repo_spec, stderr.strip()[:200]))
            except subprocess.TimeoutExpired:
                result.failed.append((repo_spec, "Timeout after 120s"))
            except Exception as e:
                result.failed.append((repo_spec, str(e)[:200]))

        return result
