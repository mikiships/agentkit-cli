"""HMAC-SHA256 signature verification for GitHub webhooks."""
from __future__ import annotations

import hashlib
import hmac


def verify_signature(secret: str, payload: bytes, header: str) -> bool:
    """Return True if the GitHub signature header matches the expected HMAC.

    Args:
        secret: The webhook secret string configured in GitHub.
        payload: The raw request body bytes.
        header: The value of the X-Hub-Signature-256 header, e.g.
                "sha256=abcdef...".

    Returns:
        True if valid, False if invalid or header is malformed.
    """
    if not secret:
        # No secret configured — skip verification (allow all)
        return True
    if not header:
        return False
    if not header.startswith("sha256="):
        return False

    expected = hmac.new(
        key=secret.encode("utf-8"),
        msg=payload,
        digestmod=hashlib.sha256,
    ).hexdigest()
    received = header[len("sha256="):]
    return hmac.compare_digest(expected, received)
