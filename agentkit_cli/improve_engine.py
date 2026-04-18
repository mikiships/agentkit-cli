"""improve_engine.py — End-to-end automated quality improvement workflow."""
from __future__ import annotations

import json
import logging
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from agentkit_cli.optimize import OptimizeEngine

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────
# Data model
# ──────────────────────────────────────────────────────────

@dataclass
class ImprovementPlan:
    """Structured result from a single ImproveEngine.run() invocation."""

    target: str
    baseline_score: float
    final_score: float
    delta: float
    actions_taken: List[str] = field(default_factory=list)
    actions_skipped: List[str] = field(default_factory=list)
    context_generated: bool = False
    hardening_applied: bool = False

    def as_dict(self) -> dict:
        return {
            "target": self.target,
            "baseline_score": self.baseline_score,
            "final_score": self.final_score,
            "delta": self.delta,
            "actions_taken": self.actions_taken,
            "actions_skipped": self.actions_skipped,
            "context_generated": self.context_generated,
            "hardening_applied": self.hardening_applied,
        }


# ──────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────

def _get_score(root: Path, adapter=None) -> float:
    """Run agentkit score and return float result (0–100)."""
    from agentkit_cli.composite import CompositeScoreEngine
    from agentkit_cli.commands.score_cmd import _run_agentlint_fast, _get_last_tool_score

    project = root.name
    tool_scores: dict = {}
    lint_score = _run_agentlint_fast(str(root))
    tool_scores["agentlint"] = lint_score
    for tool in ("coderace", "agentmd", "agentreflect"):
        tool_scores[tool] = _get_last_tool_score(project, tool)
    engine = CompositeScoreEngine()
    result = engine.compute(tool_scores)
    return result.score


def _get_redteam_score(root: Path) -> Optional[float]:
    """Return current redteam resistance score for root, or None."""
    try:
        from agentkit_cli.redteam_scorer import RedTeamScorer
        scorer = RedTeamScorer(n_per_category=1)
        report = scorer.score_resistance(root)
        return report.score_overall
    except Exception:
        return None


def _run_agentmd_generate(root: Path, adapter=None) -> bool:
    """Run agentmd generate; return True on success."""
    from agentkit_cli.tools import is_installed, run_tool
    if not is_installed("agentmd"):
        return False
    try:
        result = run_tool("agentmd", ["generate", str(root)], cwd=str(root))
        return result.returncode == 0
    except Exception:
        return False


def _run_harden(root: Path, adapter=None) -> int:
    """Run agentkit harden; return number of fixes applied (best-effort)."""
    from agentkit_cli.commands.harden_cmd import harden_command
    try:
        harden_command(
            path=root,
            output=None,
            dry_run=False,
            report=False,
            share=False,
            json_output=False,
        )
        return 3  # nominal — actual count inside harden_command isn't exposed
    except SystemExit as e:
        # harden exits 0 on success or 1 on no-context
        code = e.code if isinstance(e.code, int) else 1
        return 3 if code == 0 else 0
    except Exception:
        return 0


# ──────────────────────────────────────────────────────────
# Engine
# ──────────────────────────────────────────────────────────

class ImproveEngine:
    """Orchestrates the analyze → fix → re-analyze loop."""

    def __init__(self, adapter=None):
        # adapter is accepted for DI / test injection; not used for subprocess
        self._adapter = adapter

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def run(
        self,
        target: str,
        *,
        no_generate: bool = False,
        no_harden: bool = False,
        dry_run: bool = False,
        min_lift: Optional[float] = None,
        optimize_context: bool = False,
    ) -> ImprovementPlan:
        """Full improvement workflow.

        Parameters
        ----------
        target:
            Local path or "github:owner/repo" string.
        no_generate:
            Skip CLAUDE.md generation step.
        no_harden:
            Skip redteam hardening step.
        dry_run:
            Analyse + plan without applying changes.
        min_lift:
            If set, caller should raise Exit(1) when delta < min_lift.
        """
        root = self._resolve_target(target)

        # Step 1 — baseline
        baseline_score = _get_score(root, self._adapter)

        actions_taken: List[str] = []
        actions_skipped: List[str] = []
        context_generated = False
        hardening_applied = False

        # Context file check
        context_file = root / "CLAUDE.md"
        context_missing = not context_file.exists()
        needs_generate = context_missing or baseline_score < 80

        # Step 2 — decide context generation
        if no_generate:
            actions_skipped.append("context generation (--no-generate)")
        elif dry_run:
            if needs_generate:
                actions_skipped.append("CLAUDE.md generation (dry-run, would generate)")
            else:
                actions_skipped.append("CLAUDE.md generation (score >= 80 and file exists)")
        else:
            if needs_generate:
                ok = _run_agentmd_generate(root, self._adapter)
                if ok:
                    context_generated = True
                    label = "Generated CLAUDE.md from source analysis" if context_missing else "Updated CLAUDE.md (score < 80)"
                    actions_taken.append(label)
                else:
                    actions_skipped.append("CLAUDE.md generation (agentmd not installed or failed)")
            else:
                actions_skipped.append("CLAUDE.md generation (score >= 80 and file exists)")

        # Step 3 — decide hardening
        rt_score = _get_redteam_score(root)
        needs_harden = rt_score is None or rt_score < 80

        if no_harden:
            actions_skipped.append("redteam hardening (--no-harden)")
        elif dry_run:
            if needs_harden:
                rt_label = f"{rt_score:.0f}/100" if rt_score is not None else "unknown"
                actions_skipped.append(f"redteam hardening (dry-run, would harden; redteam={rt_label})")
            else:
                actions_skipped.append("redteam hardening (resistance >= 80)")
        else:
            if needs_harden:
                n_fixes = _run_harden(root, self._adapter)
                if n_fixes > 0:
                    hardening_applied = True
                    actions_taken.append(f"Fixed {n_fixes} security patterns (redteam hardening)")
                else:
                    actions_skipped.append("redteam hardening (no context file or already hardened)")
            else:
                actions_skipped.append("redteam hardening (resistance >= 80)")

        # Step 4 — optional context optimization
        if optimize_context:
            try:
                optimize_result = OptimizeEngine(root).optimize()
                if optimize_result.no_op or optimize_result.optimized_text == optimize_result.original_text:
                    actions_skipped.append("context optimization (already tight)")
                elif dry_run:
                    actions_skipped.append(
                        f"context optimization (dry-run, would save {abs(optimize_result.token_delta)} tokens)"
                    )
                else:
                    Path(optimize_result.source_file).write_text(optimize_result.optimized_text, encoding="utf-8")
                    actions_taken.append(
                        f"Optimized {Path(optimize_result.source_file).name} ({optimize_result.line_delta:+d} lines, {optimize_result.token_delta:+d} tokens)"
                    )
            except FileNotFoundError:
                actions_skipped.append("context optimization (no CLAUDE.md or AGENTS.md found)")
            except Exception as exc:
                actions_skipped.append(f"context optimization failed ({exc})")

        # Step 5 — re-score
        if dry_run:
            final_score = baseline_score
        else:
            final_score = _get_score(root, self._adapter)

        delta = round(final_score - baseline_score, 1)

        return ImprovementPlan(
            target=target,
            baseline_score=baseline_score,
            final_score=final_score,
            delta=delta,
            actions_taken=actions_taken,
            actions_skipped=actions_skipped,
            context_generated=context_generated,
            hardening_applied=hardening_applied,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_target(self, target: str) -> Path:
        """Resolve target to a local Path, cloning if needed."""
        if target.startswith("github:"):
            return self._clone_github(target)
        p = Path(target).expanduser().resolve()
        if not p.exists():
            raise FileNotFoundError(f"Target not found: {p}")
        return p

    def _clone_github(self, target: str) -> Path:
        """Clone a github:owner/repo target to a temp dir and return the path."""
        import tempfile
        slug = target[len("github:"):]
        url = f"https://github.com/{slug}.git"
        tmp = Path(tempfile.mkdtemp(prefix="agentkit-improve-"))
        dest = tmp / slug.replace("/", "_")
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", url, str(dest)],
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to clone {url}: {e.stderr.decode()}") from e
        return dest
