"""agentkit ci command — generate GitHub Actions workflow."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import typer
import yaml

_WORKFLOW_TEMPLATE = """\
name: Agent Quality Toolkit

on:
  pull_request:
{push_trigger}

jobs:
  agentkit:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      checks: write

    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python {python_version}
        uses: actions/setup-python@v5
        with:
          python-version: "{python_version}"

      - name: Install quartet tools
        run: |
          pip install --upgrade pip
          pip install agentmd-gen ai-agentlint coderace ai-agentreflect agentkit-cli

      - name: Run agentkit pipeline
        run: agentkit run --ci{benchmark_flag}

{benchmark_step}{min_score_step}      - name: Upload lint report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: agentkit-lint-report
          path: |
            .agentlint_report.json
            CLAUDE.md
          if-no-files-found: ignore
{benchmark_artifact}
"""

_BENCHMARK_STEP = """\
      - name: Run benchmark
        run: coderace benchmark .

"""

_BENCHMARK_ARTIFACT = """\
      - name: Upload benchmark summary
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: agentkit-benchmark-summary
          path: .coderace_results.json
          if-no-files-found: ignore
"""

_MIN_SCORE_STEP = """\
      - name: Gate on maintainer score
        run: |
          python3 -c "
          import json, sys
          try:
              data = json.load(open('.agentlint_report.json'))
              score = data.get('score', 100)
          except Exception:
              score = 100
          if score < {min_score}:
              print(f'Score {{score}} below minimum {min_score}')
              sys.exit(1)
          print(f'Score {{score}} >= {min_score}: OK')
          "

"""


def generate_workflow(
    python_version: str = "3.12",
    benchmark: bool = False,
    min_score: Optional[int] = None,
    push_to_main: bool = True,
) -> str:
    """Build the workflow YAML string."""
    push_trigger = '  push:\n    branches: [main, master]' if push_to_main else ''
    benchmark_flag = ' --benchmark' if benchmark else ''
    benchmark_step = _BENCHMARK_STEP if benchmark else ''
    benchmark_artifact = _BENCHMARK_ARTIFACT if benchmark else ''
    min_score_step = _MIN_SCORE_STEP.format(min_score=min_score) if min_score is not None else ''

    raw = _WORKFLOW_TEMPLATE.format(
        python_version=python_version,
        push_trigger=push_trigger,
        benchmark_flag=benchmark_flag,
        benchmark_step=benchmark_step,
        benchmark_artifact=benchmark_artifact,
        min_score_step=min_score_step,
    )
    # Validate it's parseable YAML before returning
    yaml.safe_load(raw)
    return raw


def ci_command(
    python_version: str = "3.12",
    benchmark: bool = False,
    min_score: Optional[int] = None,
    output_dir: Path = Path(".github/workflows"),
    dry_run: bool = False,
) -> None:
    """Generate a GitHub Actions workflow for the agentkit pipeline."""
    workflow_yaml = generate_workflow(
        python_version=python_version,
        benchmark=benchmark,
        min_score=min_score,
    )

    if dry_run:
        typer.echo(workflow_yaml)
        return

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "agentkit.yml"
    out_file.write_text(workflow_yaml)
    typer.echo(f"✓ Workflow written to {out_file}")
    typer.echo("  Triggers: pull_request + push to main/master")
    if benchmark:
        typer.echo("  Includes: coderace benchmark step")
    if min_score is not None:
        typer.echo(f"  Gating: score >= {min_score}")
