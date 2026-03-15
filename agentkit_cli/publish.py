"""agentkit publish — upload HTML report to here.now and return a shareable URL."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Optional
from urllib import request, error as urllib_error
from urllib.request import Request

HERENOW_API_BASE = "https://here.now/api/v1"
DEFAULT_REPORT_NAMES = ["agentkit-report.html"]
LAST_REPORT_PATH = Path.home() / ".agentkit" / "last-report.html"


class PublishError(Exception):
    """Raised when any step of the here.now publish flow fails."""


def _json_post(url: str, body: dict, headers: Optional[dict] = None) -> dict:
    data = json.dumps(body).encode("utf-8")
    req = Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib_error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")
        raise PublishError(f"HTTP {e.code} from {url}: {body_text}") from e
    except urllib_error.URLError as e:
        raise PublishError(f"Network error reaching {url}: {e.reason}") from e


def _put_file(url: str, content: bytes, content_type: str = "text/html") -> None:
    req = Request(url, data=content, method="PUT")
    req.add_header("Content-Type", content_type)
    try:
        with request.urlopen(req) as resp:
            _ = resp.read()
    except urllib_error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")
        raise PublishError(f"HTTP {e.code} uploading file: {body_text}") from e
    except urllib_error.URLError as e:
        raise PublishError(f"Network error uploading file: {e.reason}") from e


def _finalize(url: str) -> dict:
    req = Request(url, data=b"", method="POST")
    try:
        with request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib_error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")
        raise PublishError(f"HTTP {e.code} finalizing: {body_text}") from e
    except urllib_error.URLError as e:
        raise PublishError(f"Network error finalizing: {e.reason}") from e


def resolve_html_path(path_arg: Optional[Path]) -> Path:
    """Return the HTML file path to publish, or raise FileNotFoundError."""
    if path_arg is not None:
        p = Path(path_arg)
        if not p.exists():
            raise FileNotFoundError(
                f"Report file not found: {p}\n"
                "Hint: run `agentkit report` first to generate a report."
            )
        return p

    # Try defaults
    for name in DEFAULT_REPORT_NAMES:
        candidate = Path.cwd() / name
        if candidate.exists():
            return candidate

    if LAST_REPORT_PATH.exists():
        return LAST_REPORT_PATH

    raise FileNotFoundError(
        "No HTML report found. Run `agentkit report` first, or pass the path explicitly:\n"
        "  agentkit publish path/to/report.html"
    )


def publish_html(html_path: Path, api_key: Optional[str] = None) -> dict:
    """Run the 3-step here.now publish flow. Returns {"url": str, "anonymous": bool}."""
    content = html_path.read_bytes()

    # Step 1: get upload URLs
    headers: dict = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    step1_body = {"files": [{"path": "index.html", "contentType": "text/html"}]}
    step1_resp = _json_post(f"{HERENOW_API_BASE}/publish", step1_body, headers)

    upload_urls = step1_resp.get("uploadUrls") or []
    finalize_url = step1_resp.get("finalizeUrl")
    if not upload_urls or not finalize_url:
        raise PublishError(f"Unexpected response from publish API: {step1_resp}")

    # Step 2: upload each file
    for entry in upload_urls:
        upload_url = entry.get("url")
        if not upload_url:
            raise PublishError(f"Missing upload URL in response: {entry}")
        _put_file(upload_url, content, "text/html")

    # Step 3: finalize
    finalize_resp = _finalize(finalize_url)
    public_url = finalize_resp.get("url")
    if not public_url:
        raise PublishError(f"No URL in finalize response: {finalize_resp}")

    return {"url": public_url, "anonymous": not bool(api_key)}


def publish_command(
    html_path: Optional[Path] = None,
    json_output: bool = False,
    quiet: bool = False,
) -> None:
    """Publish an HTML report to here.now and print the URL."""
    api_key = os.environ.get("HERENOW_API_KEY") or None

    try:
        resolved = resolve_html_path(html_path)
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    try:
        result = publish_html(resolved, api_key=api_key)
    except PublishError as e:
        print(f"Publish failed: {e}", file=sys.stderr)
        sys.exit(1)

    url = result["url"]
    anonymous = result["anonymous"]
    expires_in = "24h" if anonymous else None

    if json_output:
        out: dict = {"url": url}
        if expires_in:
            out["expires_in"] = expires_in
        print(json.dumps(out))
        return

    if quiet:
        print(url)
        return

    print(f"Published: {url}")
    if anonymous:
        print("Note: anonymous publish — link expires in 24h. Set HERENOW_API_KEY for persistent links.")
