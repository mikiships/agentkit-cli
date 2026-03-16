"""agentkit pr command — generate and submit a CLAUDE.md PR to a public GitHub repo."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

console = Console()

_BRANCH_NAME = "agentkit/add-claude-md"
_DEFAULT_FILE = "CLAUDE.md"
_DEFAULT_PR_TITLE = "feat: add CLAUDE.md for AI coding agents"


def _templates_dir() -> Path:
    return Path(__file__).parent.parent / "templates"


def _default_pr_body_template() -> str:
    tpl = _templates_dir() / "pr_body.md"
    if tpl.exists():
        return tpl.read_text()
    return "Add CLAUDE.md for AI coding agents."


def _render_pr_body(template: str, owner: str, repo: str) -> str:
    return template.replace("{owner}", owner).replace("{repo}", repo)


def _run(cmd: list[str], cwd: Optional[str] = None, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, check=check, capture_output=True, text=True)


def _get_authenticated_user(token: str) -> str:
    import urllib.request
    req = urllib.request.Request(
        "https://api.github.com/user",
        headers={"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"},
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    return data["login"]


def _get_fork(token: str, owner: str, repo: str, authenticated_user: str) -> Optional[dict]:
    import urllib.request
    import urllib.error
    url = f"https://api.github.com/repos/{authenticated_user}/{repo}"
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def _create_fork(token: str, owner: str, repo: str) -> dict:
    import urllib.request
    url = f"https://api.github.com/repos/{owner}/{repo}/forks"
    data = json.dumps({}).encode()
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def _create_pull_request(
    token: str,
    owner: str,
    repo: str,
    head_user: str,
    branch: str,
    title: str,
    body: str,
) -> dict:
    import urllib.request
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    payload = json.dumps({
        "title": title,
        "body": body,
        "head": f"{head_user}:{branch}",
        "base": "main",
    }).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        method="POST",
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def _compute_score(path: str) -> Optional[float]:
    """Try to compute agentlint score for a path. Returns None if unavailable."""
    try:
        result = subprocess.run(
            ["agentlint", "score", path],
            capture_output=True, text=True, timeout=15
        )
        for line in result.stdout.splitlines():
            line = line.strip()
            if line.replace(".", "", 1).isdigit():
                return float(line)
    except Exception:
        pass
    return None


def pr_command(
    target: str = typer.Argument(..., help="Target repo in format github:owner/repo"),
    file: str = typer.Option(_DEFAULT_FILE, "--file", "-f", help="Context file to generate (CLAUDE.md or AGENTS.md)"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing context file"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be done without making any git or API calls"),
    pr_title: str = typer.Option(_DEFAULT_PR_TITLE, "--pr-title", help="Custom PR title"),
    pr_body_file: Optional[Path] = typer.Option(None, "--pr-body-file", help="Path to custom PR body markdown file"),
    json_output: bool = typer.Option(False, "--json", help="Output result as JSON"),
) -> None:
    """Submit a CLAUDE.md PR to a public GitHub repository."""

    # Parse target
    if not target.startswith("github:"):
        console.print("[red]Error:[/red] Target must be in format github:owner/repo")
        raise typer.Exit(code=1)

    repo_path = target[len("github:"):]
    parts = repo_path.split("/")
    if len(parts) != 2 or not parts[0] or not parts[1]:
        console.print("[red]Error:[/red] Invalid format. Use github:owner/repo")
        raise typer.Exit(code=1)

    owner, repo = parts[0], parts[1]
    clone_url = f"https://github.com/{owner}/{repo}.git"

    if dry_run:
        console.print(f"[bold][DRY RUN][/bold] Would perform the following steps:")
        console.print(f"  1. Clone [cyan]{clone_url}[/cyan] (depth 1)")
        console.print(f"  2. Run [cyan]agentmd generate .[/cyan] → {file}")
        console.print(f"  3. Create fork under authenticated user")
        console.print(f"  4. Create branch [cyan]{_BRANCH_NAME}[/cyan]")
        console.print(f"  5. Commit {file}")
        console.print(f"  6. Push branch to fork")
        console.print(f"  7. Open PR: [cyan]{pr_title}[/cyan]")
        if json_output:
            typer.echo(json.dumps({"dry_run": True, "repo": f"{owner}/{repo}", "file": file}))
        return

    # Check GITHUB_TOKEN
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        console.print(
            "[red]Error:[/red] GITHUB_TOKEN environment variable is required.\n"
            "Set it with: [cyan]export GITHUB_TOKEN=your_token[/cyan]"
        )
        raise typer.Exit(code=1)

    tmpdir = tempfile.mkdtemp(prefix="agentkit_pr_")
    try:
        clone_dir = os.path.join(tmpdir, repo)

        # Step 1: Clone
        console.print(f"[bold]→ Clone[/bold] {clone_url}")
        try:
            _run(["git", "clone", "--depth", "1", clone_url, clone_dir])
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Clone failed:[/red] {e.stderr}")
            raise typer.Exit(code=1)

        # Check if file already exists
        ctx_file = Path(clone_dir) / file
        if ctx_file.exists() and not force:
            console.print(f"[yellow]Skipping:[/yellow] {file} already exists in {owner}/{repo}. Use --force to overwrite.")
            raise typer.Exit(code=0)

        # Step 2: Generate
        console.print(f"[bold]→ Generate[/bold] {file}")
        score_before = _compute_score(clone_dir)
        try:
            gen_result = _run(["agentmd", "generate", "."], cwd=clone_dir, check=False)
            if gen_result.returncode != 0:
                console.print(f"[yellow]agentmd warning:[/yellow] {gen_result.stderr or gen_result.stdout}")
        except FileNotFoundError:
            console.print("[red]Error:[/red] agentmd not found. Install with: pip install agentmd")
            raise typer.Exit(code=1)

        # Rename to --file target if different from default CLAUDE.md
        generated = Path(clone_dir) / "CLAUDE.md"
        if file != "CLAUDE.md" and generated.exists() and not ctx_file.exists():
            generated.rename(ctx_file)

        if not ctx_file.exists():
            console.print(f"[red]Error:[/red] {file} was not generated.")
            raise typer.Exit(code=1)

        score_after = _compute_score(clone_dir)

        # Step 3: Get authenticated user & fork info
        console.print("[bold]→ Fork[/bold] checking / creating fork")
        try:
            authenticated_user = _get_authenticated_user(token)
        except Exception as e:
            console.print(f"[red]GitHub API error:[/red] {e}")
            raise typer.Exit(code=1)

        fork_data = _get_fork(token, owner, repo, authenticated_user)
        if fork_data is None:
            try:
                fork_data = _create_fork(token, owner, repo)
                console.print(f"  Created fork: {fork_data.get('html_url', '')}")
            except Exception as e:
                console.print(f"[red]Fork creation failed:[/red] {e}")
                raise typer.Exit(code=1)
        else:
            console.print(f"  Using existing fork: {fork_data.get('html_url', '')}")

        fork_clone_url = fork_data.get("clone_url") or f"https://github.com/{authenticated_user}/{repo}.git"

        # Step 4: Create branch on fork
        console.print(f"[bold]→ Branch[/bold] {_BRANCH_NAME}")
        # Configure authenticated remote URL
        auth_fork_url = fork_clone_url.replace("https://", f"https://{token}@")

        # Create a fresh local branch from the clone
        try:
            _run(["git", "checkout", "-b", _BRANCH_NAME], cwd=clone_dir)
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Branch creation failed:[/red] {e.stderr}")
            raise typer.Exit(code=1)

        # Step 5: Commit
        console.print(f"[bold]→ Commit[/bold] {file}")
        try:
            _run(["git", "config", "user.email", "agentkit@example.com"], cwd=clone_dir)
            _run(["git", "config", "user.name", "agentkit-cli"], cwd=clone_dir)
            _run(["git", "add", file], cwd=clone_dir)
            _run(["git", "commit", "-m", f"feat: add {file} for AI coding agents"], cwd=clone_dir)
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Commit failed:[/red] {e.stderr}")
            raise typer.Exit(code=1)

        # Step 6: Push to fork
        console.print("[bold]→ Push[/bold] branch to fork")
        try:
            _run(["git", "remote", "add", "fork", auth_fork_url], cwd=clone_dir)
            _run(["git", "push", "fork", _BRANCH_NAME], cwd=clone_dir)
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Push failed:[/red] {e.stderr}")
            raise typer.Exit(code=1)

        # Step 7: Open PR
        console.print("[bold]→ PR[/bold] opening pull request")
        if pr_body_file and pr_body_file.exists():
            pr_body_template = pr_body_file.read_text()
        else:
            pr_body_template = _default_pr_body_template()
        pr_body = _render_pr_body(pr_body_template, owner, repo)

        try:
            pr_data = _create_pull_request(
                token=token,
                owner=owner,
                repo=repo,
                head_user=authenticated_user,
                branch=_BRANCH_NAME,
                title=pr_title,
                body=pr_body,
            )
            pr_url = pr_data.get("html_url", "")
        except Exception as e:
            console.print(f"[red]PR creation failed:[/red] {e}")
            raise typer.Exit(code=1)

        if json_output:
            output = {
                "pr_url": pr_url,
                "repo": f"{owner}/{repo}",
                "file": file,
                "score_before": score_before,
                "score_after": score_after,
            }
            typer.echo(json.dumps(output))
        else:
            console.print(f"\n[bold green]✓ PR opened:[/bold green] {pr_url}")
            if score_before is not None and score_after is not None:
                console.print(f"  Score: {score_before:.1f} → {score_after:.1f}")

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
