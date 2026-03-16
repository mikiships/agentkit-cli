"""agentkit serve command — local dashboard server."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import typer

from agentkit_cli.serve import DEFAULT_PORT, _render_dashboard_html, start_server


def serve_command(
    port: int = DEFAULT_PORT,
    open_browser: bool = False,
    json_output: bool = False,
    once: bool = False,
    db_path: Optional[Path] = None,
    live: bool = False,
) -> None:
    """Start the agentkit local dashboard server."""
    url = f"http://localhost:{port}"

    if json_output:
        typer.echo(json.dumps({"url": url, "port": port, "status": "ready"}))
        return

    if once:
        html = _render_dashboard_html(db_path)
        sys.stdout.write(html)
        return

    if live:
        typer.echo(f"Dashboard (live): http://localhost:{port}")

    start_server(port=port, open_browser=open_browser, db_path=db_path, live=live)
