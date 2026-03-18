"""agentkit llmstxt command — generate llms.txt and llms-full.txt for any repository."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from agentkit_cli.llmstxt import LlmsTxtGenerator, validate_llms_txt, score_llms_txt

console = Console()


def _is_github_target(target: str) -> bool:
    return target.startswith("github:") or (
        "/" in target
        and not target.startswith((".", "/", "~"))
        and not Path(target).exists()
    )


def _clone_repo(target: str) -> tuple[str, str]:
    """Clone a github:owner/repo target. Returns (tmpdir, repo_name)."""
    if target.startswith("github:"):
        slug = target[len("github:"):]
    else:
        slug = target
    parts = slug.split("/")
    if len(parts) < 2:
        raise ValueError(f"Invalid GitHub target: {target}")
    repo_name = parts[-1]
    url = f"https://github.com/{slug}.git"
    tmpdir = tempfile.mkdtemp(prefix="agentkit-llmstxt-")
    result = subprocess.run(
        ["git", "clone", "--depth=1", url, tmpdir],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise RuntimeError(f"Clone failed: {result.stderr.strip()}")
    return tmpdir, repo_name


def _upload_llmstxt(llmstxt_content: str, project_name: str) -> Optional[str]:
    """Upload llms.txt to here.now and return URL."""
    try:
        from agentkit_cli.share import upload_scorecard
        html = f"<pre>{llmstxt_content}</pre>"
        return upload_scorecard(html)
    except Exception as e:
        console.print(f"[yellow]Warning: share upload failed — {e}[/yellow]")
        return None


def llmstxt_command(
    target: str,
    full: bool,
    output_dir: Optional[Path],
    json_output: bool,
    share: bool,
    validate: bool,
    score: bool,
) -> None:
    """Generate llms.txt (and optionally llms-full.txt) for a repository."""
    gen = LlmsTxtGenerator()
    tmpdir: Optional[str] = None
    repo_path: str

    # Resolve target
    if _is_github_target(target):
        if not json_output:
            console.print(f"\n[bold]agentkit llmstxt[/bold] — cloning {target} …")
        try:
            tmpdir, _ = _clone_repo(target)
            repo_path = tmpdir
        except (ValueError, RuntimeError) as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(code=1)
    else:
        repo_path = str(Path(target).expanduser().resolve())
        if not Path(repo_path).is_dir():
            console.print(f"[red]Error:[/red] Path not found: {target}")
            raise typer.Exit(code=1)
        if not json_output:
            console.print(f"\n[bold]agentkit llmstxt[/bold] — scanning {repo_path} …")

    try:
        info = gen.scan_repo(repo_path)

        # --validate mode: validate an existing llms.txt
        if validate:
            llmstxt_path = Path(repo_path) / "llms.txt"
            if not llmstxt_path.exists():
                console.print(f"[red]Error:[/red] No llms.txt found at {llmstxt_path}")
                raise typer.Exit(code=1)
            content = llmstxt_path.read_text(encoding="utf-8", errors="replace")
            checks = validate_llms_txt(content)
            quality_score = score_llms_txt(content)

            if json_output:
                print(json.dumps({"checks": checks, "score": quality_score}))
                return

            table = Table(title=f"llms.txt Validation: {info.project_name}", show_header=True, header_style="bold")
            table.add_column("Check")
            table.add_column("Status")
            table.add_column("Suggestion", max_width=60)
            for c in checks:
                status = "[green]✓ pass[/green]" if c["passed"] else "[red]✗ fail[/red]"
                table.add_row(c["check"], status, c.get("suggestion", ""))
            console.print()
            console.print(table)
            color = "green" if quality_score >= 80 else ("yellow" if quality_score >= 60 else "red")
            console.print(f"\n[bold]Quality Score:[/bold] [{color}]{quality_score}/100[/{color}]")
            return

        # Generate content
        llmstxt_content = gen.generate_llms_txt(info)
        full_content = gen.generate_llms_full_txt(info) if full else None

        # Resolve output directory
        out_dir = Path(output_dir) if output_dir else Path.cwd()
        out_dir.mkdir(parents=True, exist_ok=True)
        llmstxt_file = out_dir / "llms.txt"
        llmstxt_file.write_text(llmstxt_content, encoding="utf-8")
        files_written = [str(llmstxt_file)]

        llms_full_file: Optional[Path] = None
        if full and full_content:
            llms_full_file = out_dir / "llms-full.txt"
            llms_full_file.write_text(full_content, encoding="utf-8")
            files_written.append(str(llms_full_file))

        # --score
        quality_score = score_llms_txt(llmstxt_content) if score else None

        # --share
        share_url: Optional[str] = None
        if share:
            share_url = _upload_llmstxt(llmstxt_content, info.project_name)

        if json_output:
            sections = []
            for line in llmstxt_content.splitlines():
                if line.startswith("## "):
                    sections.append(line[3:])
            out: dict = {
                "project": info.project_name,
                "files": files_written,
                "llmstxt_size": len(llmstxt_content),
                "llms_full_size": len(full_content) if full_content else 0,
                "section_count": len(sections),
                "sections": sections,
                "links_count": llmstxt_content.count("]("),
            }
            if quality_score is not None:
                out["score"] = quality_score
            if share_url:
                out["share_url"] = share_url
            print(json.dumps(out, indent=2))
            return

        # Rich table output
        sections = [l[3:] for l in llmstxt_content.splitlines() if l.startswith("## ")]
        table = Table(title=f"llms.txt — {info.project_name}", show_header=True, header_style="bold")
        table.add_column("Section", style="bold")
        table.add_column("Details")
        for s in sections:
            table.add_row(s, "")
        table.add_row("─" * 20, "─" * 30)
        table.add_row("llms.txt", f"{len(llmstxt_content):,} bytes → {llmstxt_file}")
        if llms_full_file:
            table.add_row("llms-full.txt", f"{len(full_content):,} bytes → {llms_full_file}")

        console.print()
        console.print(table)

        if quality_score is not None:
            color = "green" if quality_score >= 80 else ("yellow" if quality_score >= 60 else "red")
            console.print(f"\n[bold]Quality Score:[/bold] [{color}]{quality_score}/100[/{color}]")

        if share_url:
            console.print(f"\n[bold green]Published:[/bold green] {share_url}")

    finally:
        if tmpdir:
            shutil.rmtree(tmpdir, ignore_errors=True)
