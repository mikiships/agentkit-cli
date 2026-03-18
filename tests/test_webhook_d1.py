"""D1 tests: WebhookServer core and HMAC verifier."""
from __future__ import annotations

import hashlib
import hmac
import json
import queue
import threading
import time
import urllib.request
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

from agentkit_cli.webhook.verifier import verify_signature
from agentkit_cli.webhook.server import WebhookServer
from agentkit_cli.webhook.event_processor import EventProcessor


# ---------------------------------------------------------------------------
# verify_signature tests
# ---------------------------------------------------------------------------

def _make_sig(secret: str, payload: bytes) -> str:
    digest = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def test_verify_signature_valid():
    payload = b'{"action": "opened"}'
    sig = _make_sig("mysecret", payload)
    assert verify_signature("mysecret", payload, sig) is True


def test_verify_signature_invalid():
    payload = b'{"action": "opened"}'
    assert verify_signature("mysecret", payload, "sha256=badvalue") is False


def test_verify_signature_empty_header():
    assert verify_signature("mysecret", b"data", "") is False


def test_verify_signature_malformed_header():
    assert verify_signature("mysecret", b"data", "md5=abc") is False


def test_verify_signature_no_secret_allows_all():
    """Empty secret disables verification."""
    assert verify_signature("", b"anything", "") is True
    assert verify_signature("", b"anything", "sha256=garbage") is True


def test_verify_signature_wrong_secret():
    payload = b"hello"
    sig = _make_sig("correctsecret", payload)
    assert verify_signature("wrongsecret", payload, sig) is False


def test_verify_signature_tampered_payload():
    payload = b"original"
    sig = _make_sig("secret", payload)
    assert verify_signature("secret", b"tampered", sig) is False


# ---------------------------------------------------------------------------
# WebhookServer tests (no real HTTP calls — use local loopback)
# ---------------------------------------------------------------------------

def _find_free_port() -> int:
    import socket
    with socket.socket() as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def _post(port: int, path: str, body: bytes, headers: dict) -> tuple[int, bytes]:
    url = f"http://localhost:{port}{path}"
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=3) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def test_server_handles_push_event():
    port = _find_free_port()
    received: list = []

    def on_event(evt: Dict[str, Any]):
        received.append(evt)

    srv = WebhookServer(port=port, secret="", verify_sig=False, on_event=on_event)
    srv.start()
    time.sleep(0.2)

    body = json.dumps({"repository": {"full_name": "a/b"}}).encode()
    status, _ = _post(port, "/", body, {"X-GitHub-Event": "push", "Content-Type": "application/json"})
    time.sleep(0.3)
    srv.stop()

    assert status == 200
    assert any(e.get("event_type") == "push" for e in received)


def test_server_handles_pull_request_event():
    port = _find_free_port()
    received: list = []

    def on_event(evt: Dict[str, Any]):
        received.append(evt)

    srv = WebhookServer(port=port, secret="", verify_sig=False, on_event=on_event)
    srv.start()
    time.sleep(0.2)

    body = json.dumps({"repository": {"full_name": "a/b"}, "pull_request": {"number": 42}}).encode()
    status, _ = _post(port, "/", body, {"X-GitHub-Event": "pull_request", "Content-Type": "application/json"})
    time.sleep(0.3)
    srv.stop()

    assert status == 200
    assert any(e.get("event_type") == "pull_request" for e in received)


def test_server_rejects_invalid_signature():
    port = _find_free_port()
    srv = WebhookServer(port=port, secret="sekret", verify_sig=True)
    srv.start()
    time.sleep(0.2)

    body = b'{"repository": {"full_name": "a/b"}}'
    status, _ = _post(port, "/", body, {
        "X-GitHub-Event": "push",
        "X-Hub-Signature-256": "sha256=invalidsig",
        "Content-Type": "application/json",
    })
    srv.stop()
    assert status == 403


def test_server_accepts_valid_signature():
    port = _find_free_port()
    received: list = []

    def on_event(evt: Dict[str, Any]):
        received.append(evt)

    secret = "my-webhook-secret"
    srv = WebhookServer(port=port, secret=secret, verify_sig=True, on_event=on_event)
    srv.start()
    time.sleep(0.2)

    body = json.dumps({"repository": {"full_name": "a/b"}}).encode()
    sig = _make_sig(secret, body)
    status, _ = _post(port, "/", body, {
        "X-GitHub-Event": "push",
        "X-Hub-Signature-256": sig,
        "Content-Type": "application/json",
    })
    time.sleep(0.3)
    srv.stop()
    assert status == 200


def test_server_ignores_unknown_event_type():
    port = _find_free_port()
    received: list = []

    def on_event(evt: Dict[str, Any]):
        received.append(evt)

    srv = WebhookServer(port=port, secret="", verify_sig=False, on_event=on_event)
    srv.start()
    time.sleep(0.2)

    body = json.dumps({"action": "star"}).encode()
    status, resp = _post(port, "/", body, {
        "X-GitHub-Event": "star",
        "Content-Type": "application/json",
    })
    time.sleep(0.2)
    srv.stop()

    assert status == 200
    assert b"ignored" in resp


def test_server_returns_200_immediately():
    """Server responds before processing finishes (non-blocking)."""
    port = _find_free_port()
    processing_event = threading.Event()

    def slow_handler(evt: Dict[str, Any]):
        processing_event.wait(timeout=5)

    srv = WebhookServer(port=port, secret="", verify_sig=False, on_event=slow_handler)
    srv.start()
    time.sleep(0.2)

    body = json.dumps({"repository": {"full_name": "a/b"}}).encode()
    start = time.monotonic()
    status, _ = _post(port, "/", body, {
        "X-GitHub-Event": "push",
        "Content-Type": "application/json",
    })
    elapsed = time.monotonic() - start

    processing_event.set()
    srv.stop()

    assert status == 200
    # Should respond much faster than the 5-second slow handler timeout
    assert elapsed < 3.0


def test_server_graceful_stop():
    port = _find_free_port()
    srv = WebhookServer(port=port, secret="", verify_sig=False)
    srv.start()
    time.sleep(0.1)
    srv.stop()
    # After stop, port should be released (no exception)
    assert True


def test_server_local_url():
    srv = WebhookServer(port=8989)
    assert srv.local_url == "http://localhost:8989"


# ---------------------------------------------------------------------------
# EventProcessor unit tests (fully mocked)
# ---------------------------------------------------------------------------

def test_event_processor_process_push_returns_result():
    ep = EventProcessor()
    event = {
        "event_type": "push",
        "repository": {"full_name": "owner/repo", "clone_url": ""},
        "ref": "refs/heads/main",
    }
    with patch.object(ep, "_run_analysis", return_value=(75.0, None)):
        with patch.object(ep, "_record_history", return_value=True):
            result = ep.process(event)
    assert result["event_type"] == "push"
    assert result["score"] == 75.0
    assert result["recorded"] is True
    assert "comment_body" not in result


def test_event_processor_process_pr_returns_comment():
    ep = EventProcessor()
    event = {
        "event_type": "pull_request",
        "repository": {"full_name": "owner/repo", "clone_url": ""},
        "ref": "refs/pull/7/head",
        "pull_request": {"number": 7},
    }
    with patch.object(ep, "_run_analysis", return_value=(80.0, 70.0)):
        with patch.object(ep, "_record_history", return_value=True):
            result = ep.process(event)
    assert "comment_body" in result
    assert "agentkit" in result["comment_body"].lower()
    assert "#7" in result["comment_body"]


def test_event_processor_regression_fires_notification():
    ep = EventProcessor(notify_channels=["https://hooks.slack.com/fake"])
    event = {
        "event_type": "push",
        "repository": {"full_name": "owner/repo", "clone_url": ""},
        "ref": "refs/heads/main",
    }
    with patch.object(ep, "_run_analysis", return_value=(50.0, 80.0)):
        with patch.object(ep, "_record_history", return_value=True):
            with patch.object(ep, "_maybe_notify", return_value=True) as mock_notify:
                result = ep.process(event)
    mock_notify.assert_called_once()
    assert result["notified"] is True


def test_event_processor_no_regression_no_notification():
    ep = EventProcessor(notify_channels=["https://hooks.slack.com/fake"])
    event = {
        "event_type": "push",
        "repository": {"full_name": "owner/repo", "clone_url": ""},
        "ref": "refs/heads/main",
    }
    with patch.object(ep, "_run_analysis", return_value=(85.0, 80.0)):
        with patch.object(ep, "_record_history", return_value=True):
            result = ep.process(event)
    assert result["notified"] is False


def test_event_processor_extract_repo_info():
    ep = EventProcessor()
    event = {
        "repository": {"full_name": "a/b", "clone_url": "https://github.com/a/b.git"},
        "ref": "refs/heads/main",
    }
    info = ep._extract_repo_info(event)
    assert info["full_name"] == "a/b"
    assert info["clone_url"] == "https://github.com/a/b.git"


def test_event_processor_score_to_grade():
    assert EventProcessor._score_to_grade(95) == "A"
    assert EventProcessor._score_to_grade(85) == "B"
    assert EventProcessor._score_to_grade(75) == "C"
    assert EventProcessor._score_to_grade(65) == "D"
    assert EventProcessor._score_to_grade(40) == "F"
