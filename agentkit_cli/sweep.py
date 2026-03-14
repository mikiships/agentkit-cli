"""Core sweep engine for `agentkit sweep`."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional, Sequence

from agentkit_cli.analyze import AnalyzeResult, analyze_target, parse_target

CORE_TOOL_KEYS = ("agentmd", "agentlint", "agentreflect")


@dataclass
class SweepTargetResult:
    target: str
    status: str
    repo_name: Optional[str]
    composite_score: Optional[float]
    grade: Optional[str]
    successful_tools: int
    total_tools: int
    generated_context: bool = False
    report_url: Optional[str] = None
    tools: dict[str, dict] = field(default_factory=dict)
    error: Optional[str] = None

    def to_dict(self) -> dict:
        data = asdict(self)
        if data["repo_name"] is None:
            del data["repo_name"]
        if data["report_url"] is None:
            del data["report_url"]
        if data["error"] is None:
            del data["error"]
        return data

    @classmethod
    def from_analyze_result(cls, result: AnalyzeResult) -> "SweepTargetResult":
        return cls(
            target=result.target,
            status="succeeded",
            repo_name=result.repo_name,
            composite_score=result.composite_score,
            grade=result.grade,
            successful_tools=_count_successful_tools(result.tools),
            total_tools=len(CORE_TOOL_KEYS),
            generated_context=result.generated_context,
            report_url=result.report_url,
            tools=result.tools,
        )

    @classmethod
    def from_error(cls, target: str, error: str) -> "SweepTargetResult":
        repo_name: Optional[str]
        try:
            _url_or_path, repo_name = parse_target(target)
        except ValueError:
            repo_name = None
        return cls(
            target=target,
            status="failed",
            repo_name=repo_name,
            composite_score=None,
            grade=None,
            successful_tools=0,
            total_tools=len(CORE_TOOL_KEYS),
            error=error,
        )


@dataclass
class SweepRunResult:
    targets: list[str]
    results: list[SweepTargetResult]

    def summary_counts(self) -> dict[str, int]:
        succeeded = sum(1 for result in self.results if result.status == "succeeded")
        failed = sum(1 for result in self.results if result.status == "failed")
        analyzed_with_scores = sum(
            1
            for result in self.results
            if result.status == "succeeded" and result.composite_score is not None
        )
        return {
            "total": len(self.targets),
            "succeeded": succeeded,
            "failed": failed,
            "analyzed_with_scores": analyzed_with_scores,
        }

    def to_dict(self) -> dict:
        return {
            "summary": self.summary_counts(),
            "targets": list(self.targets),
            "results": [result.to_dict() for result in self.results],
        }


def sort_results(
    results: list[SweepTargetResult],
    sort_by: str = "score",
) -> list[SweepTargetResult]:
    """Sort sweep results by the given key (score, name, grade).

    Score sorts descending (highest first); name and grade sort ascending.
    Failed targets (no score) sort to the bottom for score/grade sorts.
    """
    if sort_by == "name":
        return sorted(results, key=lambda r: r.target.lower())
    elif sort_by == "grade":
        grade_order = {"A": 0, "B": 1, "C": 2, "D": 3, "F": 4}
        return sorted(
            results,
            key=lambda r: (
                grade_order.get(r.grade, 99) if r.grade else 99,
                r.target.lower(),
            ),
        )
    else:  # score (default)
        return sorted(
            results,
            key=lambda r: (
                0 if r.composite_score is not None else 1,
                -(r.composite_score or 0),
                r.target.lower(),
            ),
        )


def _count_successful_tools(tools: dict[str, dict]) -> int:
    return sum(1 for key in CORE_TOOL_KEYS if tools.get(key, {}).get("status") == "pass")


def _read_targets_file(targets_file: Path) -> list[str]:
    targets: list[str] = []
    for raw_line in targets_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        targets.append(line)
    return targets


def resolve_targets(
    positional_targets: Sequence[str],
    targets_file: Optional[Path] = None,
) -> list[str]:
    ordered_targets: list[str] = []
    seen: set[str] = set()

    for target in positional_targets:
        if target not in seen:
            ordered_targets.append(target)
            seen.add(target)

    if targets_file is not None:
        for target in _read_targets_file(targets_file):
            if target not in seen:
                ordered_targets.append(target)
                seen.add(target)

    return ordered_targets


def run_sweep(
    targets: Sequence[str],
    *,
    keep: bool = False,
    publish: bool = False,
    timeout: int = 120,
    no_generate: bool = False,
) -> SweepRunResult:
    results: list[SweepTargetResult] = []

    for target in targets:
        try:
            analyze_result = analyze_target(
                target=target,
                keep=keep,
                publish=publish,
                timeout=timeout,
                no_generate=no_generate,
            )
        except Exception as exc:
            results.append(SweepTargetResult.from_error(target, str(exc)))
            continue

        results.append(SweepTargetResult.from_analyze_result(analyze_result))

    return SweepRunResult(targets=list(targets), results=results)
