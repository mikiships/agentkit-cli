"""Shared data models for agentkit CLI features."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional


@dataclass
class OptimizeStats:
    lines: int
    estimated_tokens: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class OptimizeFinding:
    kind: str
    severity: str
    message: str
    line: Optional[int] = None
    source: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class OptimizationAction:
    kind: str
    description: str
    lines_affected: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class OptimizeResult:
    source_file: str
    original_text: str
    optimized_text: str
    original_stats: OptimizeStats
    optimized_stats: OptimizeStats
    findings: list[OptimizeFinding] = field(default_factory=list)
    actions: list[OptimizationAction] = field(default_factory=list)
    preserved_sections: list[str] = field(default_factory=list)
    protected_sections: list[str] = field(default_factory=list)
    removed_bloat: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    no_op: bool = False

    @property
    def line_delta(self) -> int:
        return self.optimized_stats.lines - self.original_stats.lines

    @property
    def token_delta(self) -> int:
        return self.optimized_stats.estimated_tokens - self.original_stats.estimated_tokens

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_file": self.source_file,
            "original_text": self.original_text,
            "optimized_text": self.optimized_text,
            "original_stats": self.original_stats.to_dict(),
            "optimized_stats": self.optimized_stats.to_dict(),
            "line_delta": self.line_delta,
            "token_delta": self.token_delta,
            "findings": [item.to_dict() for item in self.findings],
            "actions": [item.to_dict() for item in self.actions],
            "preserved_sections": list(self.preserved_sections),
            "protected_sections": list(self.protected_sections),
            "removed_bloat": list(self.removed_bloat),
            "warnings": list(self.warnings),
            "no_op": self.no_op,
        }
