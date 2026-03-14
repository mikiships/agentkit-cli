"""agentkit doctor command wrapper."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer

from agentkit_cli.doctor import DoctorReport, render_human_report, run_doctor

_VALID_CATEGORIES = {"repo", "toolchain", "context", "publish"}
_VALID_FAIL_ON = {"warn", "fail"}


def _filter_report(report: DoctorReport, category: str | None) -> DoctorReport:
    """Return a new DoctorReport restricted to *category* (or all)."""
    if category is None:
        return report
    cat = category.lower()
    filtered = [c for c in report.checks if c.category == cat]
    return DoctorReport(root=report.root, checks=filtered)


def _exit_code(report: DoctorReport, fail_on: str, no_fail_exit: bool) -> int:
    """Compute exit code given filtering and fail-on threshold."""
    if no_fail_exit:
        return 0
    if fail_on == "warn":
        return 1 if (report.fail_count + report.warn_count) > 0 else 0
    # default: fail only on fail
    return 1 if report.fail_count > 0 else 0


def doctor_command(
    json_output: bool = False,
    path: Path | None = None,
    category: str | None = None,
    fail_on: str = "fail",
    no_fail_exit: bool = False,
) -> None:
    """Run doctor checks and print either human or JSON output."""
    if category is not None and category.lower() not in _VALID_CATEGORIES:
        typer.echo(
            f"Unknown category '{category}'. Valid categories: {', '.join(sorted(_VALID_CATEGORIES))}",
            err=True,
        )
        raise typer.Exit(code=2)

    if fail_on not in _VALID_FAIL_ON:
        typer.echo(
            f"Invalid --fail-on value '{fail_on}'. Must be one of: {', '.join(_VALID_FAIL_ON)}",
            err=True,
        )
        raise typer.Exit(code=2)

    full_report = run_doctor(root=path)
    report = _filter_report(full_report, category)

    if json_output:
        typer.echo(json.dumps(report.as_dict(), indent=2))
    else:
        render_human_report(report)

    raise typer.Exit(code=_exit_code(report, fail_on=fail_on, no_fail_exit=no_fail_exit))
