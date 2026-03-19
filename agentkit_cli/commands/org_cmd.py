"""agentkit org — score every public repo in a GitHub org or user account."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import sys

from agentkit_cli.engines.org_pages import OrgPagesEngine
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeout
from datetime import datetime, timezone
from pathlib import Path
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


def _delta_color(delta: Optional[float]) -> str:
    if delta is None:
        return "dim"
    if delta >= 10:
        return "green"
    if delta > 0:
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


def _generate_for_repo(full_name: str, timeout: int = 120, generate_threshold: int = 80) -> dict:
    """Clone repo, run agentmd generate, re-score. Returns before/after dict."""
    import agentkit_cli.analyze as _analyze_module
    from agentkit_cli.tools import get_adapter
    analyze_target = _analyze_module.analyze_target
    _clone = _analyze_module._clone
    parse_target = _analyze_module.parse_target

    url, repo_name = parse_target(f"github:{full_name}")

    # Initial score (no_generate=True to get baseline without generation)
    before_result = _analyze_repo(full_name, timeout=timeout)
    before_score = before_result.get("score")

    # Only generate if below threshold
    if before_score is not None and before_score >= generate_threshold:
        return {
            **before_result,
            "score_before": before_score,
            "score_after": before_score,
            "grade_before": _score_to_grade(before_score),
            "grade_after": _score_to_grade(before_score),
            "delta": 0.0,
            "generated": False,
        }

    # Clone to temp dir for generation
    temp_dir = tempfile.mkdtemp(prefix="agentkit-org-generate-")
    try:
        _clone(url, temp_dir, timeout=timeout)

        adapter = get_adapter()
        gen_result = adapter.agentmd_generate(temp_dir)
        generated_ok = gen_result is not None

        if generated_ok:
            # Re-score using local path
            try:
                from agentkit_cli.analyze import analyze_target as _at
                after_result_obj = _at(
                    target=temp_dir,
                    keep=False,
                    publish=False,
                    timeout=timeout,
                    no_generate=True,
                )
                after_score = after_result_obj.composite_score
                top_finding_after = ""
                for tool_info in after_result_obj.tools.values():
                    finding = tool_info.get("finding", "") if isinstance(tool_info, dict) else getattr(tool_info, "finding", "")
                    if not finding:
                        continue
                    stripped = finding.strip()
                    if stripped.startswith("[") or stripped.startswith("{"):
                        continue
                    first_line = next((l.strip() for l in stripped.splitlines() if l.strip()), "")
                    if first_line:
                        top_finding_after = first_line[:80]
                        break
            except Exception:
                after_score = before_score
                top_finding_after = before_result.get("top_finding", "")
        else:
            after_score = before_score
            top_finding_after = before_result.get("top_finding", "")

        delta = (after_score - before_score) if (after_score is not None and before_score is not None) else None

        return {
            "score": after_score,
            "grade": _score_to_grade(after_score),
            "top_finding": top_finding_after or before_result.get("top_finding", ""),
            "status": before_result.get("status", "ok"),
            "score_before": before_score,
            "score_after": after_score,
            "grade_before": _score_to_grade(before_score),
            "grade_after": _score_to_grade(after_score),
            "delta": delta,
            "generated": generated_ok,
        }
    except Exception as exc:
        return {
            **before_result,
            "score_before": before_score,
            "score_after": before_score,
            "grade_before": _score_to_grade(before_score),
            "grade_after": _score_to_grade(before_score),
            "delta": 0.0,
            "generated": False,
            "generate_error": str(exc)[:80],
        }
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


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
        generate: bool = False,
        generate_only_below: int = 80,
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
        self.generate = generate
        self.generate_only_below = generate_only_below

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

        if self.generate:
            generated_count = len([r for r in ranked if r.get("generated")])
            scored_repos = [r for r in ranked if r.get("delta") is not None]
            avg_lift = sum(r["delta"] for r in scored_repos) / len(scored_repos) if scored_repos else 0.0
            out["generate_summary"] = {
                "generated_count": generated_count,
                "avg_score_lift": round(avg_lift, 1),
            }

        # Generate report if requested
        html: Optional[str] = None
        if self.output or self.share:
            from agentkit_cli.org_report import OrgReport
            report = OrgReport(owner=self.owner, results=ranked, generate_mode=self.generate)
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
                if self.generate:
                    r = _generate_for_repo(repo["full_name"], timeout=self.timeout,
                                           generate_threshold=self.generate_only_below)
                else:
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
                    if self.generate:
                        r = _generate_for_repo(repo["full_name"], timeout=self.timeout,
                                               generate_threshold=self.generate_only_below)
                    else:
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

        # Sort by score desc (None last); when generate mode use after score
        filled.sort(key=lambda r: (r["score"] is None, -(r["score"] or 0)))
        for i, r in enumerate(filled, start=1):
            r["rank"] = i

        return filled

    def _render_table(self, ranked: list[dict], summary: dict) -> None:
        """Print a Rich ranked table."""
        console.print()

        if self.generate:
            table = Table(show_header=True, header_style="bold")
            table.add_column("#", style="dim", width=4)
            table.add_column("Repo")
            table.add_column("Before", justify="right")
            table.add_column("After", justify="right")
            table.add_column("Delta", justify="right")

            for r in ranked:
                score_before = r.get("score_before")
                score_after = r.get("score_after")
                delta = r.get("delta")

                before_str = f"{score_before:.1f}" if score_before is not None else "-"
                after_str = f"{score_after:.1f}" if score_after is not None else "-"
                delta_str = f"+{delta:.1f}" if delta and delta > 0 else (f"{delta:.1f}" if delta is not None else "-")

                before_color = _score_color(score_before)
                after_color = _score_color(score_after)
                d_color = _delta_color(delta)

                grade_before = r.get("grade_before") or "-"
                grade_after = r.get("grade_after") or "-"

                table.add_row(
                    str(r.get("rank", "")),
                    r.get("full_name", r.get("repo", "")),
                    f"[{before_color}]{before_str}/{grade_before}[/{before_color}]",
                    f"[{after_color}]{after_str}/{grade_after}[/{after_color}]",
                    f"[{d_color}]{delta_str}[/{d_color}]",
                )

            console.print(table)

            gen_summary = summary.get("generate_summary", {})
            gen_count = gen_summary.get("generated_count", 0)
            avg_lift = gen_summary.get("avg_score_lift", 0.0)
            console.print(
                f"\n  [bold green]Generated context for {gen_count} repos. "
                f"Avg score lift: +{avg_lift} pts[/bold green]"
            )
            console.print(
                f"  [dim]Analyzed: {summary['analyzed']} | "
                f"Skipped (timeout): {summary['skipped']} | "
                f"Failed: {summary['failed']}[/dim]\n"
            )
        else:
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
    generate: bool = False,
    generate_only_below: int = 80,
    pages: bool = False,
    pages_repo: Optional[str] = None,
    dry_run: bool = False,
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
        generate=generate,
        generate_only_below=generate_only_below,
    )
    result = cmd.run()

    # --pages: publish org leaderboard to GitHub Pages
    if pages:
        ranked = result.get("ranked", [])
        engine = OrgPagesEngine(
            org=owner,
            pages_repo=pages_repo,
            token=token,
            dry_run=dry_run,
            _org_results=ranked,
        )
        pages_result = engine.run()

        if pages_result.published:
            if not json_output:
                console.print(f"\n[bold green]Org leaderboard (permanent):[/bold green] {pages_result.pages_url}")
            result["pages_url"] = pages_result.pages_url
        else:
            err = pages_result.error or "unknown error"
            if not json_output:
                console.print(f"[yellow]Warning: GitHub Pages publish failed ({err})[/yellow]")
            result["pages_error"] = err

        if json_output:
            print(json.dumps(result, indent=2))
