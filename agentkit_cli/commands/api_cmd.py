"""agentkit api — start the local REST API server."""
from __future__ import annotations

import shutil
import subprocess
import sys
from typing import Optional

import typer
from rich.console import Console

console = Console()


def api_command(
    host: str = typer.Option("127.0.0.1", "--host", help="Bind host"),
    port: int = typer.Option(8742, "--port", help="Bind port"),
    reload: bool = typer.Option(False, "--reload", help="Enable auto-reload (dev mode)"),
    share: bool = typer.Option(False, "--share", help="Start ngrok tunnel and print public URL"),
    interactive: bool = typer.Option(False, "--interactive", help="Confirm the interactive /ui form is enabled (always on)"),
) -> None:
    """Start the agentkit local REST API server."""
    try:
        import fastapi  # noqa: F401
        import uvicorn  # noqa: F401
    except ImportError:
        console.print(
            "[red]Error:[/red] fastapi/uvicorn not installed.\n"
            "Run: [bold]pip install agentkit-cli[api][/bold]"
        )
        raise typer.Exit(code=1)

    base_url = f"http://{host}:{port}"
    console.print(f"[bold green]agentkit API[/bold green] starting at [cyan]{base_url}[/cyan]")
    console.print(f"  Badge URL example:  {base_url}/badge/owner/repo")
    console.print(f"  Trending:           {base_url}/trending")
    console.print(f"  Interactive UI:     {base_url}/ui")
    if interactive:
        console.print("[green]Interactive mode:[/green] /ui form is enabled (this is always on)")

    if share:
        if shutil.which("ngrok"):
            console.print("[yellow]Starting ngrok tunnel…[/yellow]")
            try:
                proc = subprocess.Popen(
                    ["ngrok", "http", str(port)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                import time; time.sleep(2)
                # Try to get public URL from ngrok API
                try:
                    import urllib.request, json as _json
                    with urllib.request.urlopen("http://127.0.0.1:4040/api/tunnels", timeout=3) as resp:
                        tunnels = _json.loads(resp.read())
                        for t in tunnels.get("tunnels", []):
                            if t.get("proto") == "https":
                                console.print(f"[bold]Public URL:[/bold] {t['public_url']}")
                                break
                except Exception:
                    console.print("[yellow]ngrok running — check http://127.0.0.1:4040 for URL[/yellow]")
            except Exception as e:
                console.print(f"[red]ngrok failed:[/red] {e}")
        else:
            console.print("[yellow]ngrok not found in PATH. Skipping --share.[/yellow]")

    import uvicorn
    uvicorn.run(
        "agentkit_cli.api_server:_make_app",
        factory=True,
        host=host,
        port=port,
        reload=reload,
    )
