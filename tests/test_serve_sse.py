"""Tests for SSE broker and live dashboard features (D1-D4)."""
from __future__ import annotations

import json
import queue
import subprocess
import sys
import threading
import time
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from http.server import HTTPServer

import pytest


# ---------------------------------------------------------------------------
# D1: SseBroker tests
# ---------------------------------------------------------------------------

class TestSseBroker:
    """Tests for the SseBroker class."""

    def test_sse_broker_broadcast(self):
        """Two clients both receive a broadcast message."""
        from agentkit_cli.serve import SseBroker

        broker = SseBroker()
        q1 = broker.subscribe()
        q2 = broker.subscribe()

        broker.broadcast("hello")

        assert q1.get_nowait() == "hello"
        assert q2.get_nowait() == "hello"

    def test_sse_broker_subscribe_returns_queue(self):
        from agentkit_cli.serve import SseBroker

        broker = SseBroker()
        q = broker.subscribe()
        assert isinstance(q, queue.Queue)

    def test_sse_broker_unsubscribe(self):
        """Unsubscribed clients do not receive further broadcasts."""
        from agentkit_cli.serve import SseBroker

        broker = SseBroker()
        q1 = broker.subscribe()
        q2 = broker.subscribe()
        broker.unsubscribe(q1)
        broker.broadcast("msg")

        # q1 should be empty
        with pytest.raises(queue.Empty):
            q1.get_nowait()
        # q2 should have the message
        assert q2.get_nowait() == "msg"

    def test_sse_broker_broadcast_multiple(self):
        """Multiple broadcasts are all received in order."""
        from agentkit_cli.serve import SseBroker

        broker = SseBroker()
        q = broker.subscribe()
        for i in range(5):
            broker.broadcast(f"msg{i}")

        for i in range(5):
            assert q.get_nowait() == f"msg{i}"

    def test_sse_broker_thread_safety(self):
        """Concurrent broadcasts don't cause errors."""
        from agentkit_cli.serve import SseBroker

        broker = SseBroker()
        queues = [broker.subscribe() for _ in range(10)]
        errors = []

        def do_broadcast():
            try:
                for i in range(20):
                    broker.broadcast(f"data{i}")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=do_broadcast) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors


# ---------------------------------------------------------------------------
# D1: /api/runs endpoint test
# ---------------------------------------------------------------------------

class TestApiRunsEndpoint:
    """Test the /api/runs HTTP endpoint."""

    def _make_db(self, tmp_path: Path) -> Path:
        db = tmp_path / "history.db"
        conn = sqlite3.connect(str(db))
        conn.execute("""
            CREATE TABLE runs (
                id INTEGER PRIMARY KEY,
                project TEXT,
                tool TEXT,
                score REAL,
                ts TEXT,
                details TEXT
            )
        """)
        conn.execute(
            "INSERT INTO runs VALUES (1, 'myproject', 'overall', 87.5, '2026-03-16T10:00:00', '{}')"
        )
        conn.commit()
        conn.close()
        return db

    def test_api_runs_endpoint(self, tmp_path):
        """GET /api/runs returns JSON array with run data."""
        from agentkit_cli.serve import AgenkitDashboard, SseBroker

        db = self._make_db(tmp_path)
        broker = SseBroker()
        handler_class = type(
            "BoundHandler",
            (AgenkitDashboard,),
            {"db_path": db, "broker": broker},
        )

        # Use a free port
        server = HTTPServer(("localhost", 0), handler_class)
        port = server.server_address[1]

        t = threading.Thread(target=server.handle_request)
        t.start()

        import urllib.request
        url = f"http://localhost:{port}/api/runs"
        resp = urllib.request.urlopen(url, timeout=5)
        data = json.loads(resp.read())

        server.server_close()
        t.join(timeout=2)

        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["project"] == "myproject"
        assert data[0]["score"] == 87.5

    def test_api_runs_empty_db(self, tmp_path):
        """GET /api/runs returns empty list when DB has no runs."""
        from agentkit_cli.serve import _query_latest_runs

        # Non-existent DB -> empty list
        result = _query_latest_runs(tmp_path / "nonexistent.db")
        assert result == []


# ---------------------------------------------------------------------------
# D3 / D4: CLI flags
# ---------------------------------------------------------------------------

class TestCliFlags:
    """Test that --serve and --live flags exist in CLI help text."""

    def test_watch_serve_flag_exists(self):
        """agentkit watch --help contains --serve."""
        result = subprocess.run(
            [sys.executable, "-m", "agentkit_cli.main", "watch", "--help"],
            capture_output=True,
            text=True,
        )
        assert "--serve" in result.stdout

    def test_serve_live_flag_exists(self):
        """agentkit serve --help contains --live."""
        result = subprocess.run(
            [sys.executable, "-m", "agentkit_cli.main", "serve", "--help"],
            capture_output=True,
            text=True,
        )
        assert "--live" in result.stdout

    def test_watch_port_flag_exists(self):
        """agentkit watch --help contains --port."""
        result = subprocess.run(
            [sys.executable, "-m", "agentkit_cli.main", "watch", "--help"],
            capture_output=True,
            text=True,
        )
        assert "--port" in result.stdout


# ---------------------------------------------------------------------------
# D2: Dashboard HTML content
# ---------------------------------------------------------------------------

class TestDashboardHtml:
    """Test that the dashboard HTML includes SSE JS."""

    def test_dashboard_has_eventsource(self):
        """Dashboard HTML includes EventSource connection code."""
        from agentkit_cli.serve import _render_dashboard_html

        html = _render_dashboard_html()
        assert "EventSource" in html

    def test_dashboard_has_live_indicator(self):
        """Dashboard HTML includes live indicator element."""
        from agentkit_cli.serve import _render_dashboard_html

        html = _render_dashboard_html()
        assert "live-indicator" in html

    def test_dashboard_has_api_runs_fetch(self):
        """Dashboard JS fetches /api/runs on SSE message."""
        from agentkit_cli.serve import _render_dashboard_html

        html = _render_dashboard_html()
        assert "/api/runs" in html
