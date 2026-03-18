"""agentkit monitor daemon — background polling process.

Entry point for the daemon process spawned by `agentkit monitor start`.
Polls `run_all_due()` on a 60-second tick, writes structured JSON lines to
~/.agentkit/monitor.log, and handles SIGTERM gracefully.

Run via: python -m agentkit_cli.monitor_daemon
"""
from __future__ import annotations

import json
import os
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Daemon state files (match monitor.py)
MONITOR_DIR = Path.home() / ".agentkit"
PID_FILE = MONITOR_DIR / "monitor.pid"
LOG_FILE = MONITOR_DIR / "monitor.log"

POLL_INTERVAL = 60  # seconds between due-target polls

_running = True


def _log(entry: dict) -> None:
    """Append a JSON line to the daemon log."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")
        f.flush()


def _sigterm_handler(signum: int, frame: object) -> None:
    """Graceful shutdown on SIGTERM."""
    global _running
    _running = False
    _log({
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": "shutdown",
        "message": "Daemon received SIGTERM, shutting down.",
    })


def run_daemon(
    poll_interval: int = POLL_INTERVAL,
    toml_path: Optional[Path] = None,
    _test_max_cycles: Optional[int] = None,
) -> None:
    """Main daemon loop. Polls run_all_due() every poll_interval seconds."""
    signal.signal(signal.SIGTERM, _sigterm_handler)

    # Allow override for testing
    if toml_path is None:
        env_toml = os.environ.get("AGENTKIT_MONITOR_TOML")
        if env_toml:
            toml_path = Path(env_toml)

    _log({
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": "startup",
        "pid": os.getpid(),
        "poll_interval": poll_interval,
    })

    from agentkit_cli.monitor_config import MonitorConfig
    from agentkit_cli.monitor_engine import MonitorEngine

    cfg = MonitorConfig(toml_path=toml_path) if toml_path else MonitorConfig()
    engine = MonitorEngine(config=cfg)

    cycle = 0
    while _running:
        if _test_max_cycles is not None and cycle >= _test_max_cycles:
            break

        try:
            cfg.load()
            results = engine.run_all_due()
            for result in results:
                entry = {
                    "ts": result.timestamp,
                    "target": result.target,
                    "score": result.score,
                    "prev_score": result.prev_score,
                    "delta": result.delta,
                    "notify_fired": result.notify_fired,
                    "error": result.error,
                }
                _log(entry)
        except Exception as exc:
            _log({
                "ts": datetime.now(timezone.utc).isoformat(),
                "event": "error",
                "message": str(exc),
            })

        cycle += 1
        if _test_max_cycles is not None and cycle >= _test_max_cycles:
            break

        # Sleep in small increments to stay responsive to SIGTERM
        elapsed = 0
        while _running and elapsed < poll_interval:
            time.sleep(min(1, poll_interval - elapsed))
            elapsed += 1

    _log({
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": "exit",
        "cycles": cycle,
    })


if __name__ == "__main__":
    run_daemon()
