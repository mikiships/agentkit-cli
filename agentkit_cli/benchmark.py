"""agentkit benchmark engine — cross-agent benchmarking on your own codebase."""
from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


DEFAULT_TASKS = ["bug-hunt", "refactor", "concurrent-queue", "api-client", "context-use"]
DEFAULT_AGENTS = ["claude", "codex", "gemini"]
DEFAULT_TIMEOUT = 300
DEFAULT_ROUNDS = 1


@dataclass
class BenchmarkConfig:
    agents: List[str] = field(default_factory=lambda: list(DEFAULT_AGENTS))
    tasks: List[str] = field(default_factory=lambda: list(DEFAULT_TASKS))
    timeout: int = DEFAULT_TIMEOUT
    rounds: int = DEFAULT_ROUNDS


@dataclass
class BenchmarkResult:
    agent: str
    task: str
    score: float  # 0-100
    duration_s: float
    error: Optional[str] = None
    round_num: int = 1

    def to_dict(self) -> dict:
        return {
            "agent": self.agent,
            "task": self.task,
            "score": self.score,
            "duration_s": self.duration_s,
            "error": self.error,
            "round_num": self.round_num,
        }


@dataclass
class AgentStats:
    agent: str
    mean_score: float
    mean_duration: float
    win_rate: float
    task_scores: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "agent": self.agent,
            "mean_score": self.mean_score,
            "mean_duration": self.mean_duration,
            "win_rate": self.win_rate,
            "task_scores": self.task_scores,
        }


@dataclass
class BenchmarkReport:
    project: str
    timestamp: str
    results: List[BenchmarkResult]
    summary: Dict[str, AgentStats]
    winner: str
    config: BenchmarkConfig

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "timestamp": self.timestamp,
            "results": [r.to_dict() for r in self.results],
            "summary": {a: s.to_dict() for a, s in self.summary.items()},
            "winner": self.winner,
            "config": {
                "agents": self.config.agents,
                "tasks": self.config.tasks,
                "timeout": self.config.timeout,
                "rounds": self.config.rounds,
            },
        }


def _run_coderace(agent: str, task: str, project_path: str, timeout: int) -> tuple[float, Optional[str]]:
    """Run coderace for one agent+task combination. Returns (score, error)."""
    try:
        cmd = ["coderace", "run", "--agent", agent, "--task", task, "--score-only", project_path]
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if proc.returncode != 0:
            return 0.0, proc.stderr.strip() or "coderace exited non-zero"
        # coderace --score-only prints a float 0-100 on stdout
        raw = proc.stdout.strip()
        score = float(raw)
        return max(0.0, min(100.0, score)), None
    except subprocess.TimeoutExpired:
        return 0.0, f"timeout after {timeout}s"
    except FileNotFoundError:
        return 0.0, "coderace not installed"
    except ValueError:
        return 0.0, f"unexpected coderace output: {proc.stdout.strip()!r}"
    except Exception as exc:
        return 0.0, str(exc)


def _compute_summary(results: List[BenchmarkResult], tasks: List[str]) -> Dict[str, AgentStats]:
    """Compute per-agent aggregate stats and win rate."""
    from collections import defaultdict

    # Group results
    by_agent: Dict[str, List[BenchmarkResult]] = defaultdict(list)
    for r in results:
        by_agent[r.agent].append(r)

    # Determine winner per task (averaged across rounds)
    task_winners: Dict[str, str] = {}
    for task in tasks:
        best_agent = None
        best_score = -1.0
        for agent, agent_results in by_agent.items():
            task_results = [r for r in agent_results if r.task == task and r.error is None]
            if not task_results:
                continue
            avg = sum(r.score for r in task_results) / len(task_results)
            if avg > best_score:
                best_score = avg
                best_agent = agent
        if best_agent:
            task_winners[task] = best_agent

    total_tasks = len(task_winners)

    summary: Dict[str, AgentStats] = {}
    for agent, agent_results in by_agent.items():
        scores = [r.score for r in agent_results if r.error is None]
        durations = [r.duration_s for r in agent_results]
        mean_score = sum(scores) / len(scores) if scores else 0.0
        mean_duration = sum(durations) / len(durations) if durations else 0.0
        wins = sum(1 for t, w in task_winners.items() if w == agent)
        win_rate = wins / total_tasks if total_tasks > 0 else 0.0

        task_scores: Dict[str, float] = {}
        for task in tasks:
            task_results = [r for r in agent_results if r.task == task and r.error is None]
            if task_results:
                task_scores[task] = sum(r.score for r in task_results) / len(task_results)

        summary[agent] = AgentStats(
            agent=agent,
            mean_score=round(mean_score, 2),
            mean_duration=round(mean_duration, 2),
            win_rate=round(win_rate, 3),
            task_scores=task_scores,
        )

    return summary


def _pick_winner(summary: Dict[str, AgentStats]) -> str:
    """Return agent with highest mean_score. Ties broken by win_rate."""
    if not summary:
        return "none"
    return max(
        summary.values(),
        key=lambda s: (s.mean_score, s.win_rate),
    ).agent


class BenchmarkEngine:
    """Run structured multi-agent benchmarks against a project."""

    def __init__(self, runner=None):
        # runner: optional callable(agent, task, project_path, timeout) -> (score, error)
        # Used for testing to inject mocks without subprocess.
        self._runner = runner or _run_coderace

    def run(
        self,
        project_path: str,
        config: Optional[BenchmarkConfig] = None,
        progress_callback=None,
    ) -> BenchmarkReport:
        """Run all tasks × agents × rounds and return a BenchmarkReport.

        progress_callback(agent, task, round_num, result) called after each result.
        """
        if config is None:
            config = BenchmarkConfig()

        project = Path(project_path).resolve().name
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        results: List[BenchmarkResult] = []

        for round_num in range(1, config.rounds + 1):
            for task in config.tasks:
                for agent in config.agents:
                    start = time.monotonic()
                    score, error = self._runner(agent, task, project_path, config.timeout)
                    duration = round(time.monotonic() - start, 3)

                    result = BenchmarkResult(
                        agent=agent,
                        task=task,
                        score=score,
                        duration_s=duration,
                        error=error,
                        round_num=round_num,
                    )
                    results.append(result)

                    if progress_callback:
                        progress_callback(agent, task, round_num, result)

        summary = _compute_summary(results, config.tasks)
        winner = _pick_winner(summary)

        return BenchmarkReport(
            project=project,
            timestamp=timestamp,
            results=results,
            summary=summary,
            winner=winner,
            config=config,
        )
