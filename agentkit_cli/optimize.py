"""Deterministic context-file optimizer for CLAUDE.md and AGENTS.md."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable, Optional

from agentkit_cli.models import (
    OptimizeFinding,
    OptimizeResult,
    OptimizeStats,
    OptimizationAction,
    OptimizeSweepResult,
    OptimizeSweepSummary,
)
from agentkit_cli.redteam_scorer import RedTeamScorer
from agentkit_cli.suggest_engine import parse_agentlint_check_context
from agentkit_cli.tools import get_adapter

_CONTEXT_FILE_NAMES = ("CLAUDE.md", "AGENTS.md")
_HIGH_SIGNAL_HEADINGS = (
    "project",
    "overview",
    "mission",
    "identity",
    "product",
    "architecture",
    "stack",
    "setup",
    "development",
    "commands",
    "testing",
    "safety",
    "boundaries",
    "constraints",
    "workflow",
    "release",
    "autonomy",
    "user",
    "critical",
)
_PROTECTED_HEADING_KEYWORDS = (
    "project",
    "identity",
    "mission",
    "autonomy",
    "safety",
    "boundaries",
    "constraints",
    "user",
    "critical",
    "owner",
)
_LOW_SIGNAL_HEADINGS = (
    "legacy",
    "scratchpad",
    "notes",
    "requests",
    "reminders",
    "brainstorm",
)
_RISKY_PATTERNS: list[tuple[str, str, str]] = [
    (r"ignore (all )?(previous|prior) instructions", "critical", "Risky instruction override language"),
    (r"(?<!do not )(?:please )?bypass (approval|permissions|security|safety)", "critical", "Approval or safety bypass language"),
    (r"never refuse", "high", "Unbounded compliance language"),
    (r"exfiltrat|copy secrets|print secrets|dump env", "critical", "Secret handling risk"),
]
_YEAR_RE = re.compile(r"\b(20\d{2})\b")


@dataclass
class _Section:
    heading: Optional[str]
    body: list[str]

    @property
    def normalized_heading(self) -> str:
        if not self.heading:
            return "preamble"
        return re.sub(r"[^a-z0-9]+", " ", self.heading.lower()).strip()

    def rendered(self) -> str:
        if self.heading:
            lines = [self.heading, *self.body]
        else:
            lines = list(self.body)
        return "\n".join(lines).strip()


class OptimizeEngine:
    def __init__(self, root: Path | str = "."):
        self.root = Path(root).expanduser().resolve()

    def optimize(self, file: Optional[Path | str] = None) -> OptimizeResult:
        target = self._resolve_target(file)
        return self._optimize_target(target)

    def discover_context_files(self) -> list[Path]:
        files: list[Path] = []
        seen: set[Path] = set()
        for name in _CONTEXT_FILE_NAMES:
            for candidate in self.root.rglob(name):
                resolved = candidate.resolve()
                if resolved in seen or not candidate.is_file():
                    continue
                seen.add(resolved)
                files.append(resolved)
        return sorted(files, key=lambda path: (len(path.relative_to(self.root).parts), path.relative_to(self.root).as_posix(), _CONTEXT_FILE_NAMES.index(path.name)))

    def optimize_sweep(self) -> OptimizeSweepResult:
        targets = self.discover_context_files()
        if not targets:
            return OptimizeSweepResult(
                root=str(self.root),
                results=[],
                summary=OptimizeSweepSummary(total_files=0, rewritable_files=0, noop_files=0),
            )
        results = [self._optimize_target(target) for target in targets]
        return OptimizeSweepResult(
            root=str(self.root),
            results=results,
            summary=OptimizeSweepSummary(
                total_files=len(results),
                rewritable_files=sum(1 for item in results if not item.no_op),
                noop_files=sum(1 for item in results if item.no_op),
                total_line_delta=sum(item.line_delta for item in results),
                total_token_delta=sum(item.token_delta for item in results),
                protected_signal_files=sum(1 for item in results if item.protected_sections),
                warnings_count=sum(len(item.warnings) for item in results),
            ),
        )

    def _optimize_target(self, target: Path) -> OptimizeResult:
        original_text = target.read_text(encoding="utf-8")
        findings = self._collect_findings(target, original_text)
        sections = self._split_sections(original_text)
        optimized_text, actions, preserved, protected, removed_bloat, warnings, no_op = self._rewrite(sections, findings, original_text)
        return OptimizeResult(
            source_file=str(target),
            original_text=original_text,
            optimized_text=optimized_text,
            original_stats=self._stats(original_text),
            optimized_stats=self._stats(optimized_text),
            findings=findings,
            actions=actions,
            preserved_sections=preserved,
            protected_sections=protected,
            removed_bloat=removed_bloat,
            warnings=warnings,
            no_op=no_op,
        )

    def _resolve_target(self, file: Optional[Path | str]) -> Path:
        if file:
            target = (self.root / file).resolve() if not Path(file).is_absolute() else Path(file).resolve()
            if not target.exists():
                raise FileNotFoundError(f"Context file not found: {target}")
            return target
        for name in _CONTEXT_FILE_NAMES:
            candidate = self.root / name
            if candidate.exists():
                return candidate
        raise FileNotFoundError(f"No context file found in {self.root} (expected CLAUDE.md or AGENTS.md)")

    def _collect_findings(self, target: Path, text: str) -> list[OptimizeFinding]:
        findings: list[OptimizeFinding] = []
        adapter = get_adapter()
        lint_json = adapter.agentlint_check_context(str(target.parent))
        for item in parse_agentlint_check_context(lint_json):
            if item.file and Path(item.file).name.lower() != target.name.lower():
                continue
            findings.append(
                OptimizeFinding(
                    kind=item.category,
                    severity=item.severity,
                    message=item.description,
                    line=item.line,
                    source=item.tool,
                )
            )
        lowered = text.lower()
        for pattern, severity, message in _RISKY_PATTERNS:
            for match in re.finditer(pattern, lowered):
                findings.append(
                    OptimizeFinding(
                        kind="risky-instruction",
                        severity=severity,
                        message=message,
                        line=text[: match.start()].count("\n") + 1,
                        source="optimize",
                    )
                )
        scorer = RedTeamScorer(n_per_category=1)
        report = scorer.score_resistance(target)
        for finding in report.findings[:5]:
            findings.append(
                OptimizeFinding(
                    kind=finding.get("rule_id", "redteam"),
                    severity=str(finding.get("severity", "medium")),
                    message=str(finding.get("description", "Redteam finding")),
                    source="redteam",
                )
            )
        dedup: dict[tuple[str, str, Optional[int]], OptimizeFinding] = {}
        for item in findings:
            dedup[(item.kind, item.message, item.line)] = item
        return list(dedup.values())

    def _rewrite(
        self,
        sections: list[_Section],
        findings: list[OptimizeFinding],
        original_text: str,
    ) -> tuple[str, list[OptimizationAction], list[str], list[str], list[str], list[str], bool]:
        actions: list[OptimizationAction] = []
        preserved: list[str] = []
        protected: list[str] = []
        removed_bloat: list[str] = []
        warnings: list[str] = []
        optimized_sections: list[str] = []
        seen_headings: set[str] = set()
        changed_sections: list[tuple[str, bool]] = []
        current_year = max([int(y) for y in _YEAR_RE.findall(original_text)] or [0])

        for section in sections:
            heading = section.normalized_heading
            original_rendered = section.rendered()
            rendered = self._clean_section(section, current_year=current_year or None)
            protected_section = self._is_protected_section(section)
            if not rendered:
                if section.heading:
                    removed_bloat.append(section.heading.lstrip("# "))
                    actions.append(OptimizationAction("remove-empty", f"Removed empty or redundant section: {section.heading}", 1))
                continue
            lines_affected = max(1, len(rendered.splitlines()))
            if heading != "preamble" and heading in seen_headings:
                removed_bloat.append(section.heading.lstrip("# "))
                actions.append(OptimizationAction("dedupe-section", f"Removed duplicate section: {section.heading}", lines_affected))
                continue
            if heading != "preamble":
                seen_headings.add(heading)
            if protected_section:
                protected_name = section.heading.lstrip("# ") if section.heading else "Overview"
                protected.append(protected_name)
            if self._is_high_signal(section) or protected_section:
                preserved.append(section.heading.lstrip("# ") if section.heading else "Overview")
            elif self._is_low_signal(section) and len(rendered.splitlines()) <= 2:
                removed_bloat.append(section.heading.lstrip("# "))
                actions.append(OptimizationAction("drop-low-signal", f"Dropped low-signal section: {section.heading}", lines_affected))
                continue
            elif self._is_bloated(rendered):
                removed_bloat.append(section.heading.lstrip("# ") if section.heading else "Preamble")
                rendered = self._compress(rendered)
                actions.append(OptimizationAction("compress-section", f"Compressed bloated section: {section.heading or 'preamble'}", lines_affected))
            elif len(rendered.splitlines()) < len(section.rendered().splitlines()):
                actions.append(OptimizationAction("compress-section", f"Trimmed repetitive lines in: {section.heading or 'preamble'}", lines_affected))
            if self._meaningfully_changed(original_rendered, rendered):
                changed_sections.append((section.heading.lstrip("# ") if section.heading else "Overview", protected_section))
            optimized_sections.append(rendered)

        if not any("safety" in name.lower() or "boundar" in name.lower() for name in preserved):
            warnings.append("No explicit safety/boundary section preserved; optimizer kept existing constraints in-place only.")
        if not optimized_sections:
            optimized_sections = [self._compress(original_text)]
            actions.append(OptimizationAction("fallback-compress", "Collapsed document to a minimal summary fallback.", len(original_text.splitlines())))

        findings_by_severity = sorted(findings, key=lambda item: (item.severity, item.kind))
        for finding in findings_by_severity[:5]:
            if finding.severity in {"critical", "high"}:
                warnings.append(f"{finding.severity}: {finding.message}")

        optimized_text = "\n\n".join(part.strip() for part in optimized_sections if part.strip()).strip() + "\n"
        protected_only_churn = bool(changed_sections) and all(is_protected for _, is_protected in changed_sections) and not removed_bloat
        no_op = protected_only_churn or self._effectively_unchanged(original_text, optimized_text)
        if no_op:
            optimized_text = original_text if original_text.endswith("\n") else original_text + "\n"
            reason = "Protected sections were already safe; skipped destructive churn." if protected_only_churn else "Already tight, protected, and materially unchanged."
            actions = [OptimizationAction("no-op", reason, 0)]
            removed_bloat = []
        return optimized_text, actions, preserved[:8], protected[:8], removed_bloat[:8], warnings[:8], no_op

    def _split_sections(self, text: str) -> list[_Section]:
        sections: list[_Section] = []
        current = _Section(heading=None, body=[])
        for line in text.splitlines():
            if line.startswith("#"):
                if current.heading or current.body:
                    sections.append(current)
                current = _Section(heading=line.rstrip(), body=[])
            else:
                current.body.append(line.rstrip())
        if current.heading or current.body:
            sections.append(current)
        return sections

    def _clean_section(self, section: _Section, *, current_year: Optional[int]) -> str:
        lines = [line.rstrip() for line in section.body]
        cleaned: list[str] = []
        seen: set[str] = set()
        blank_count = 0
        for line in lines:
            lowered = line.lower().strip()
            if any(re.search(pattern, lowered) for pattern, _, _ in _RISKY_PATTERNS):
                if self._is_legitimate_boundary_line(lowered):
                    cleaned.append(line)
                continue
            if current_year and _YEAR_RE.search(line):
                years = [int(y) for y in _YEAR_RE.findall(line)]
                if years and max(years) < current_year:
                    continue
            if not lowered:
                blank_count += 1
                if blank_count > 1:
                    continue
                cleaned.append("")
                continue
            blank_count = 0
            dedup_key = re.sub(r"\s+", " ", lowered)
            if dedup_key in seen:
                continue
            seen.add(dedup_key)
            cleaned.append(line)
        while cleaned and not cleaned[-1]:
            cleaned.pop()
        body = cleaned
        if self._is_bullet_wall(body):
            body = self._compress_bullets(body)
        if section.heading:
            text = "\n".join([section.heading, *body]).strip()
        else:
            text = "\n".join(body).strip()
        return text

    def _compress(self, text: str) -> str:
        lines = [line.rstrip() for line in text.splitlines() if line.strip()]
        if len(lines) <= 8:
            return "\n".join(lines)
        keep = lines[:3]
        bullets = [line for line in lines[3:] if line.lstrip().startswith(("-", "*"))][:4]
        if bullets:
            return "\n".join(keep + bullets)
        return "\n".join(lines[:7])

    def _compress_bullets(self, lines: list[str]) -> list[str]:
        bullets = [line for line in lines if line.lstrip().startswith(("-", "*"))]
        non_bullets = [line for line in lines if not line.lstrip().startswith(("-", "*"))]
        return non_bullets + bullets[:6]

    def _is_high_signal(self, section: _Section) -> bool:
        heading = section.normalized_heading
        return heading == "preamble" or any(key in heading for key in _HIGH_SIGNAL_HEADINGS)

    def _is_protected_section(self, section: _Section) -> bool:
        heading = section.normalized_heading
        return heading == "preamble" or any(key in heading for key in _PROTECTED_HEADING_KEYWORDS)

    def _is_low_signal(self, section: _Section) -> bool:
        heading = section.normalized_heading
        return any(key in heading for key in _LOW_SIGNAL_HEADINGS)

    def _is_bloated(self, rendered: str) -> bool:
        lines = rendered.splitlines()
        return len(lines) > 14 or rendered.count("\n-") + rendered.count("\n*") > 8

    def _is_bullet_wall(self, lines: Iterable[str]) -> bool:
        bullet_count = sum(1 for line in lines if line.lstrip().startswith(("-", "*")))
        return bullet_count > 8

    def _is_legitimate_boundary_line(self, lowered: str) -> bool:
        return lowered.startswith("do not bypass") or lowered.startswith("never print secrets")

    def _effectively_unchanged(self, original_text: str, optimized_text: str) -> bool:
        original_lines = [line.rstrip() for line in original_text.strip().splitlines()]
        optimized_lines = [line.rstrip() for line in optimized_text.strip().splitlines()]
        if original_lines == optimized_lines:
            return True
        if self._normalized_text(original_text) == self._normalized_text(optimized_text):
            return True
        line_delta = abs(len(optimized_lines) - len(original_lines))
        token_delta = abs(self._stats(original_text).estimated_tokens - self._stats(optimized_text).estimated_tokens)
        return line_delta <= 1 and token_delta <= 4

    def _meaningfully_changed(self, original_text: str, optimized_text: str) -> bool:
        return self._normalized_text(original_text) != self._normalized_text(optimized_text)

    def _normalized_text(self, text: str) -> str:
        lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
        return "\n".join(line for line in lines if line).strip()

    def _stats(self, text: str) -> OptimizeStats:
        lines = len(text.splitlines())
        estimated_tokens = max(1, round(len(text.split()) * 1.3)) if text.strip() else 0
        return OptimizeStats(lines=lines, estimated_tokens=estimated_tokens)
