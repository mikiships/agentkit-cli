"""agentkit org — score every public repo in a GitHub org or user account."""
from __future__ import annotations

import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeout
from datetime import datetime, timezone
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TaskID
from rich.table import Table

console = Console()

_MAX_LIMIT = 200


def _score_to_grade(score: Optional[float]) -> Optional[str]:
    if score is None:
        return None
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def _grade_color(grade: Optional[str]) -> str:
    return {"A": "green", "B": "green", "C": "yellow", "D": "red", "F": "red"}.get(grade or "", "dim")


def _score_color(score: Optional[float]) -> str:
    if score is None:
        return "dim"
    if score >= 80:
        return "green"
    if score >= 60:
        return "yellow"
    return "red"


def _analyze_repo(full_name: str, timeout: int = 120) -> dict:
    """Run analyze_target on a GitHub repo and return result dict."""
    from agentkit_cli.analyze import analyze_target

    try:
        result = analyze_target(
            target=f"github:{full_name}",
            keep=False,
            publish=False,
            timeout=timeout,
            no_generate=True,
        )
        # Pick top finding: first tool with a non-empty human-readable finding
        top_finding = ""
        for tool_info in result.tools.values():
            finding = tool_info.get("finding", "") if isinstance(tool_info, dict) else getattr(tool_info, "finding", "")
            if not finding:
                continue
            # Skip raw JSON findings (agentmd returns JSON list)
            stripped = finding.strip()
            if stripped.startswith("[") or stripped.startswith("{"):
                continue
            # Use first non-empty line as the finding summary
            first_line = next((l.strip() for l in stripped.splitlines() if l.strip()), "")
            if first_line:
                top_finding = first_line[:80]
                break
        return {
            "score": result.composite_score,
            "grade": _score_to_grade(result.composite_score),
            "top_finding": top_finding,
            "status": "ok",
        }
    except Exception as exc:
        return {
            "score": None,
            "grade": None,
            "top_finding": str(exc)[:80],
            "status": "error",
        }


class OrgCommand:
    """Analyze all public repos in a GitHub org or user account."""

    def __init__(
        self,
        owner: str,
        include_forks: bool = False,
        include_archived: bool = False,
        limit: Optional[int] = None,
        parallel: int = 3,
        timeout: int = 120,
        share: bool = False,
        output: Optional[str] = None,
        json_output: bool = False,
        token: Optional[str] = None,
    ) -> None:
        self.owner = owner
        self.include_forks = include_forks
        self.include_archived = include_archived
        self.limit = limit
        self.parallel = max(1, parallel)
        self.timeout = timeout
        self.share = share
        self.output = output
        self.json_output = json_output
        self.token = token or os.environ.get("GITHUB_TOKEN")

    def run(self) -> dict:
        from agentkit_cli.github_api import list_repos

        if not self.json_output:
            console.print(f"\n[bold]agentkit org[/bold] — fetching repos for [bold]{self.owner}[/bold]…")

        try:
            repos = list_repos(
                owner=self.owner,
                include_forks=self.include_forks,
                include_archived=self.include_archived,
                token=self.token,
                limit=self.limit,
            )
        except (ValueError, RuntimeError) as exc:
            if self.json_output:
                print(json.dumps({"error": str(exc)}))
            else:
                console.print(f"[red]Error:[/red] {exc}")
            raise typer.Exit(code=1)

        if not repos:
            msg = f"No public repos found for '{self.owner}' (after filters)."
            if self.json_output:
                print(json.dumps({"owner": self.owner, "repo_count": 0, "ranked": [], "message": msg}))
            else:
                console.print(f"[yellow]{msg}[/yellow]")
            return {"owner": self.owner, "repo_count": 0, "ranked": []}

        total = len(repos)
        if not self.json_output:
            console.print(f"  Found [bold]{total}[/bold] repos. Analyzing…\n")

        ranked = self._analyze_all(repos)

        # Build output structure
        out = {
            "owner": self.owner,
            "repo_count": total,
            "analyzed": len([r for r in ranked if r["status"] == "ok"]),
            "skipped": len([r for r in ranked if r["status"] == "timeout"]),
            "failed": len([r for r in ranked if r["status"] == "error"]),
            "ranked": ranked,
        }

        # Generate report if requested
        html: Optional[str] = None
        if self.output or self.share:
            from agentkit_cli.org_report import OrgReport
            report = OrgReport(owner=self.owner, results=ranked)
            html = report.render()

        if self.output and html:
            with open(self.output, "w", encoding="utf-8") as f:
                f.write(html)
            if not self.json_output:
                console.print(f"[bold green]Report written:[/bold green] {self.output}")

        share_url: Optional[str] = None
        if self.share and html:
            from agentkit_cli.share import upload_scorecard
            share_url = upload_scorecard(html)
            if share_url:
                out["share_url"] = share_url
                if not self.json_output:
                    console.print(f"\n[bold green]Org report published:[/bold green] {share_url}")

        if self.json_output:
            print(json.dumps(out, indent=2))
        else:
            self._render_table(ranked, out)

        return out

    def _analyze_all(self, repos: list[dict]) -> list[dict]:
        """Analyze repos with parallel workers and progress display."""
        total = len(repos)
        results: list[Optional[dict]] = [None] * total

        if self.json_output:
            # Silent parallel analysis
            def _worker(idx: int, repo: dict) -> tuple[int, dict]:
                r = _analyze_repo(repo["full_name"], timeout=self.timeout)
                r["repo"] = repo["name"]
                r["full_name"] = repo["full_name"]
                r["stars"] = repo.get("stars", 0)
                r["description"] = repo.get("description", "")
                return idx, r

            with ThreadPoolExecutor(max_workers=self.parallel) as ex:
                futures = {ex.submit(_worker, i, repo): i for i, repo in enumerate(repos)}
                for fut in as_completed(futures):
                    try:
                        idx, r = fut.result(timeout=self.timeout + 10)
                        results[idx] = r
                    except Exception as exc:
                        i = futures[fut]
                        results[i] = {
                            "repo": repos[i]["name"],
                            "full_name": repos[i]["full_name"],
                            "stars": repos[i].get("stars", 0),
                            "description": repos[i].get("description", ""),
                            "score": None,
                            "grade": None,
                            "top_finding": str(exc)[:80],
                            "status": "error",
                        }
        else:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=console,
            ) as progress:
                task = progress.add_task(f"Analyzing {total} repos…", total=total)

                completed = [0]

                def _worker(idx: int, repo: dict) -> tuple[int, dict]:
                    r = _analyze_repo(repo["full_name"], timeout=self.timeout)
                    r["repo"] = repo["name"]
                    r["full_name"] = repo["full_name"]
                    r["stars"] = repo.get("stars", 0)
                    r["description"] = repo.get("description", "")
                    return idx, r

                with ThreadPoolExecutor(max_workers=self.parallel) as ex:
                    futures = {ex.submit(_worker, i, repo): i for i, repo in enumerate(repos)}
                    for fut in as_completed(futures):
                        try:
                            idx, r = fut.result(timeout=self.timeout + 10)
                            results[idx] = r
                        except Exception as exc:
                            i = futures[fut]
                            results[i] = {
                                "repo": repos[i]["name"],
                                "full_name": repos[i]["full_name"],
                                "stars": repos[i].get("stars", 0),
                                "description": repos[i].get("description", ""),
                                "score": None,
                                "grade": None,
                                "top_finding": str(exc)[:80],
                                "status": "timeout" if "timeout" in str(exc).lower() else "error",
                            }
                        completed[0] += 1
                        progress.update(task, advance=1, description=f"Analyzing {total} repos… [{completed[0]}/{total}]")

        # Fill any None slots (shouldn't happen)
        filled: list[dict] = []
        for i, r in enumerate(results):
            if r is None:
                filled.append({
                    "repo": repos[i]["name"],
                    "full_name": repos[i]["full_name"],
                    "stars": repos[i].get("stars", 0),
                    "description": repos[i].get("description", ""),
                    "score": None,
                    "grade": None,
                    "top_finding": "unknown error",
                    "status": "error",
                })
            else:
                filled.append(r)

        # Sort by score desc (None last)
        filled.sort(key=lambda r: (r["score"] is None, -(r["score"] or 0)))
        for i, r in enumerate(filled, start=1):
            r["rank"] = i

        return filled

    def _render_table(self, ranked: list[dict], summary: dict) -> None:
        """Print a Rich ranked table."""
        console.print()
        table = Table(show_header=True, header_style="bold")
        table.add_column("#", style="dim", width=4)
        table.add_column("Repo")
        table.add_column("Score", justify="right")
        table.add_column("Grade", justify="center")
        table.add_column("Top Finding")

        for r in ranked:
            grade = r.get("grade") or "-"
            score = r.get("score")
            score_str = f"{score:.1f}" if score is not None else "-"
            grade_color = _grade_color(grade if grade != "-" else None)
            score_color = _score_color(score)
            table.add_row(
                str(r.get("rank", "")),
                r.get("full_name", r.get("repo", "")),
                f"[{score_color}]{score_str}[/{score_color}]",
                f"[{grade_color}]{grade}[/{grade_color}]",
                r.get("top_finding", "") or "",
            )

        console.print(table)
        console.print(
            f"\n  [dim]Analyzed: {summary['analyzed']} | "
            f"Skipped (timeout): {summary['skipped']} | "
            f"Failed: {summary['failed']}[/dim]\n"
        )


def org_command(
    target: str,
    include_forks: bool = False,
    include_archived: bool = False,
    limit: Optional[int] = None,
    parallel: int = 3,
    timeout: int = 120,
    share: bool = False,
    output: Optional[str] = None,
    json_output: bool = False,
    token: Optional[str] = None,
) -> None:
    """Analyze all public repos in a GitHub org or user account."""
    # Parse github:<owner> or bare owner
    if target.startswith("github:"):
        owner = target[len("github:"):]
    else:
        owner = target

    if not owner:
        console.print("[red]Error:[/red] Provide a target like 'github:vercel' or 'vercel'")
        raise typer.Exit(code=1)

    cmd = OrgCommand(
        owner=owner,
        include_forks=include_forks,
        include_archived=include_archived,
        limit=limit,
        parallel=parallel,
        timeout=timeout,
        share=share,
        output=output,
        json_output=json_output,
        token=token,
    )
    cmd.run()
