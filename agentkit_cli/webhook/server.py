"""WebhookServer — stdlib HTTP server that handles GitHub webhook events."""
from __future__ import annotations

import json
import logging
import queue
import signal
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from agentkit_cli.webhook.verifier import verify_signature

logger = logging.getLogger(__name__)

_SUPPORTED_EVENTS = {"push", "pull_request"}


class _WebhookHandler(BaseHTTPRequestHandler):
    """HTTP request handler for GitHub webhook POSTs."""

    # Set by WebhookServer before starting
    secret: str = ""
    verify_sig: bool = True
    event_queue: "queue.Queue[Dict[str, Any]]" = None  # type: ignore[assignment]

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        logger.debug("WebhookHandler: " + format, *args)

    def do_POST(self) -> None:  # noqa: N802
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        # HMAC verification
        if self.verify_sig:
            sig_header = self.headers.get("X-Hub-Signature-256", "")
            if not verify_signature(self.secret, body, sig_header):
                self._respond(403, {"error": "invalid signature"})
                return

        # Parse event type
        event_type = self.headers.get("X-GitHub-Event", "")
        if event_type not in _SUPPORTED_EVENTS:
            # Acknowledge unsupported events without processing
            self._respond(200, {"status": "ignored", "event": event_type})
            return

        # Parse payload
        try:
            payload = json.loads(body)
        except json.JSONDecodeError as exc:
            self._respond(400, {"error": f"invalid JSON: {exc}"})
            return

        # Enqueue for async processing (respond immediately)
        event = dict(payload)
        event["event_type"] = event_type
        self.event_queue.put_nowait(event)

        self._respond(200, {"status": "queued", "event": event_type})

    def _respond(self, status: int, body: Dict[str, Any]) -> None:
        data = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


class WebhookServer:
    """Inbound GitHub webhook server.

    Usage::

        server = WebhookServer(port=8080, secret="my-secret")
        server.start()   # starts background threads
        ...
        server.stop()    # graceful shutdown
    """

    def __init__(
        self,
        port: int = 8080,
        secret: str = "",
        verify_sig: bool = True,
        notify_channels: Optional[List[str]] = None,
        on_event: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> None:
        self.port = port
        self.secret = secret
        self.verify_sig = verify_sig
        self.notify_channels = notify_channels or []
        self.on_event = on_event  # override for testing

        self._event_queue: queue.Queue[Dict[str, Any]] = queue.Queue()
        self._httpd: Optional[HTTPServer] = None
        self._server_thread: Optional[threading.Thread] = None
        self._worker_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start HTTP server and event-processing worker threads."""
        self._httpd = self._build_server()

        self._server_thread = threading.Thread(
            target=self._serve_forever, daemon=True, name="webhook-http"
        )
        self._server_thread.start()

        self._worker_thread = threading.Thread(
            target=self._process_queue, daemon=True, name="webhook-worker"
        )
        self._worker_thread.start()

        logger.info("WebhookServer started on port %d", self.port)

    def stop(self) -> None:
        """Gracefully shut down the server and worker."""
        self._stop_event.set()
        if self._httpd is not None:
            self._httpd.shutdown()
        logger.info("WebhookServer stopped.")

    def serve_forever(self) -> None:
        """Block until SIGTERM/SIGINT, then shut down cleanly."""
        self.start()

        def _handler(signum: int, frame: Any) -> None:
            logger.info("Signal %d received — shutting down.", signum)
            self.stop()

        signal.signal(signal.SIGTERM, _handler)
        signal.signal(signal.SIGINT, _handler)

        self._stop_event.wait()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _build_server(self) -> HTTPServer:
        """Build the HTTPServer with a handler class wired to our state."""
        secret = self.secret
        verify_sig = self.verify_sig
        event_queue = self._event_queue

        class _Handler(_WebhookHandler):
            pass

        _Handler.secret = secret
        _Handler.verify_sig = verify_sig
        _Handler.event_queue = event_queue  # type: ignore[assignment]

        return HTTPServer(("", self.port), _Handler)

    def _serve_forever(self) -> None:
        assert self._httpd is not None
        try:
            self._httpd.serve_forever()
        except Exception as exc:
            logger.debug("serve_forever exited: %s", exc)

    def _process_queue(self) -> None:
        """Worker thread: drain the event queue and process each event."""
        from agentkit_cli.webhook.event_processor import EventProcessor
        processor = EventProcessor(notify_channels=self.notify_channels)

        while not self._stop_event.is_set():
            try:
                event = self._event_queue.get(timeout=0.5)
            except queue.Empty:
                continue
            try:
                if self.on_event is not None:
                    self.on_event(event)
                else:
                    processor.process(event)
            except Exception as exc:
                logger.exception("Error processing event: %s", exc)
            finally:
                self._event_queue.task_done()

    def enqueue_event(self, event: Dict[str, Any]) -> None:
        """Directly enqueue an event (used by `agentkit webhook test`)."""
        self._event_queue.put_nowait(event)

    @property
    def local_url(self) -> str:
        return f"http://localhost:{self.port}"
