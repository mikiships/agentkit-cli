#!/usr/bin/env python3
"""
post-pr-comment.py — Post an Agent Quality Report comment to a GitHub PR.
Idempotent: updates an existing comment if one was already posted by this action.

Required env vars:
  GITHUB_TOKEN  — GitHub token with pull-requests: write permission
  REPO          — owner/repo (e.g. mikiships/agentkit-cli)
  PR_NUMBER     — pull request number

Optional:
  QUALITY_SUMMARY_FILE — path to the JSON file produced by run-agentkit-action.py
                         (default: /tmp/agentkit-quality-summary.json)
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

MARKER = "<!-- agentkit-quality-report -->"
SUMMARY_FILE = Path(os.environ.get("QUALITY_SUMMARY_FILE", "/tmp/agentkit-quality-summary.json"))
GITHUB_API = "https://api.github.com"


def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
    }


def _request(method: str, url: str, token: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=_headers(token), method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"GitHub API {method} {url} → {e.code}: {e.read().decode()}") from e


def list_comments(repo: str, pr_number: int, token: str) -> list[dict]:
    url = f"{GITHUB_API}/repos/{repo}/issues/{pr_number}/comments?per_page=100"
    return _request("GET", url, token)


def create_comment(repo: str, pr_number: int, body: str, token: str) -> dict:
    url = f"{GITHUB_API}/repos/{repo}/issues/{pr_number}/comments"
    return _request("POST", url, token, {"body": body})


def update_comment(repo: str, comment_id: int, body: str, token: str) -> dict:
    url = f"{GITHUB_API}/repos/{repo}/issues/comments/{comment_id}"
    return _request("PATCH", url, token, {"body": body})


def build_comment_body(summary: dict) -> str:
    md = summary.get("comment_markdown", "")
    if not md:
        agg = summary.get("aggregated", {})
        lint_score = agg.get("lint_score", 0)
        drift_status = agg.get("drift_status", "unknown")
        review_summary = agg.get("review_summary", "N/A")
        md = f"""## 🔬 Agent Quality Report

| Check | Result |
|-------|--------|
| Context Lint Score | {lint_score}/100 |
| Context Drift | {drift_status} |
| Code Review | {review_summary} |

[Details in workflow logs]"""
    return f"{MARKER}\n{md}"


def main() -> int:
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        print("GITHUB_TOKEN not set — skipping comment post", file=sys.stderr)
        return 0  # Non-fatal: don't fail the action just because we can't comment

    repo = os.environ.get("REPO", "")
    pr_number_str = os.environ.get("PR_NUMBER", "")

    if not repo or not pr_number_str:
        print("REPO or PR_NUMBER not set — skipping comment post", file=sys.stderr)
        return 0

    try:
        pr_number = int(pr_number_str)
    except ValueError:
        print(f"Invalid PR_NUMBER: {pr_number_str!r}", file=sys.stderr)
        return 1

    if not SUMMARY_FILE.exists():
        print(f"Summary file not found: {SUMMARY_FILE}", file=sys.stderr)
        return 1

    summary = json.loads(SUMMARY_FILE.read_text())
    body = build_comment_body(summary)

    # Find existing comment from this action
    comments = list_comments(repo, pr_number, token)
    existing_id = None
    for c in comments:
        if MARKER in c.get("body", ""):
            existing_id = c["id"]
            break

    if existing_id:
        update_comment(repo, existing_id, body, token)
        print(f"Updated existing quality comment (id={existing_id}) on PR #{pr_number}")
    else:
        result = create_comment(repo, pr_number, body, token)
        print(f"Posted quality comment (id={result['id']}) on PR #{pr_number}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
