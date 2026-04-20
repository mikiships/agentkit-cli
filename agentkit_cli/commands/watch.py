"""agentkit watch command — re-run pipeline on file changes."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import List, Optional

import typer

from agentkit_cli.serve import DEFAULT_PORT, SseBroker, _broker, start_server


def _run_pipeline(cwd: str, ci: bool = False) -> None:
    """Run agentkit run in subprocess."""
    cmd = [sys.executable, "-m", "agentkit_cli.main", "run", "--path", cwd]
    if ci:
        cmd.append("--ci")
    subprocess.run(cmd, cwd=cwd)


class _ChangeHandler:
    """Debounced file-change handler."""

    def __init__(
        self,
        cwd: str,
        extensions: List[str],
        debounce: float,
        ci: bool,
        broker: Optional[SseBroker] = None,
    ) -> None:
        self.cwd = cwd
        self.extensions = [e.lstrip(".") for e in extensions]
        self.debounce = debounce
        self.ci = ci
        self.broker = broker
        self._timer: Optional[threading.Timer] = None
        self._lock = threading.Lock()
        self._last_file: Optional[str] = None
        self._last_event_at: float = 0.0
        self._generation: int = 0
        # Small grace window absorbs timer jitter under load so one rapid burst
        # does not accidentally produce multiple reruns.
        self._debounce_grace: float = min(0.1, max(0.02, debounce / 2))

    def on_modified(self, path: str) -> None:
        ext = Path(path).suffix.lstrip(".")
        if self.extensions and ext not in self.extensions:
            return
        with self._lock:
            self._last_file = path
            self._last_event_at = time.monotonic()
            if self._timer is not None:
                self._timer.cancel()
            self._generation += 1
            gen = self._generation

            def _guarded_fire(expected_gen: int = gen) -> None:
                with self._lock:
                    if expected_gen != self._generation:
                        # Stale timer — a newer event superseded this one.
                        return
                    remaining = (
                        self.debounce + self._debounce_grace
                    ) - (time.monotonic() - self._last_event_at)
                    if remaining > 0:
                        self._timer = threading.Timer(remaining, _guarded_fire)
                        self._timer.daemon = True
                        self._timer.start()
                        return
                self._fire()

            self._timer = threading.Timer(self.debounce + self._debounce_grace, _guarded_fire)
            self._timer.daemon = True
            self._timer.start()

    def _fire(self) -> None:
        with self._lock:
            fname = self._last_file
            self._timer = None
        os.system("clear")
        typer.echo(f"\n[changed] {fname}")
        typer.echo("Re-running agentkit pipeline...\n")
        _run_pipeline(self.cwd, ci=self.ci)
        # Notify SSE clients if broker is active
        if self.broker is not None:
            self.broker.broadcast(json.dumps({"type": "refresh"}))
        typer.echo("\nWatching for changes... (Ctrl+C to stop)")


def watch_command(
    path: Optional[Path] = None,
    extensions: Optional[List[str]] = None,
    debounce: float = 2.0,
    ci: bool = False,
    serve: bool = False,
    port: int = DEFAULT_PORT,
) -> None:
    """Watch the project for file changes and re-run the pipeline."""
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
    except ImportError:
        typer.echo(
            "watchdog is required for 'agentkit watch'. Install it:\n"
            "  pip install watchdog",
            err=True,
        )
        raise typer.Exit(code=1)

    from agentkit_cli.config import find_project_root

    root = path or find_project_root()
    cwd_str = str(root)

    broker: Optional[SseBroker] = None
    if serve:
        broker = _broker
        serve_thread = threading.Thread(
            target=start_server,
            kwargs={"port": port, "open_browser": False, "db_path": None},
            daemon=True,
        )
        serve_thread.start()
        typer.echo(f"Watching {root}  •  Dashboard: http://localhost:{port}")

    ext_list: List[str] = extensions or ["py", "md", "yaml", "yml"]
    handler_obj = _ChangeHandler(
        cwd=cwd_str,
        extensions=ext_list,
        debounce=debounce,
        ci=ci,
        broker=broker,
    )

    class _WatchdogBridge(FileSystemEventHandler):
        def on_modified(self, event):  # type: ignore[override]
            if not event.is_directory:
                handler_obj.on_modified(event.src_path)

        def on_created(self, event):  # type: ignore[override]
            if not event.is_directory:
                handler_obj.on_modified(event.src_path)

    observer = Observer()
    observer.schedule(_WatchdogBridge(), cwd_str, recursive=True)
    observer.start()
    typer.echo(f"Watching {root} for changes... (Ctrl+C to stop)")
    typer.echo(f"Extensions: {', '.join('.' + e for e in handler_obj.extensions)}")
    typer.echo(f"Debounce: {debounce}s")

    try:
        while observer.is_alive():
            observer.join(timeout=1)
    except KeyboardInterrupt:
        pass
    finally:
        observer.stop()
        observer.join()
        typer.echo("\nWatch stopped.")
