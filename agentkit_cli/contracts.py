from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

from agentkit_cli.context_projections import ContextProjectionEngine, FORMAT_AGENTKIT_SOURCE
from agentkit_cli.map_engine import RepoMapEngine
from agentkit_cli.models import RepoMap, RepoMapContractHandoff, RepoMapHint, RepoMapSubsystem, RepoMapSummary


_DOCTRINE_RULES = [
    "No time-based completion claims.",
    "Completion is allowed only when all checklist items are checked.",
    "Full test suite must pass at the end.",
    "Docs, changelog, build report, and progress log updates ship in the same pass.",
    "CLI outputs must remain deterministic and schema-backed where required.",
    "Stay inside this repo worktree only.",
    "Commit after each completed deliverable.",
    "If stuck on the same issue for 3 attempts, stop and write a blocker report.",
    "Do not refactor unrelated code.",
    "Prefer explicit rendering logic over vague prose generation.",
]

_DEFAULT_REPORT_SECTIONS = [
    "Deliverables completed/not completed",
    "Exact tests run and results",
    "Final git status and branch/head",
    "Any blockers or caveats",
]


@dataclass(frozen=True)
class SourceContext:
    path: Optional[str]
    format: Optional[str]
    content: str
    missing: bool = False


@dataclass(frozen=True)
class RepoHints:
    command_hints: list[str] = field(default_factory=list)
    boundaries: list[str] = field(default_factory=list)
    context_notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class MapContext:
    source: Optional[str]
    generated_from: Optional[str]
    summary: Optional[RepoMapSummary]
    subsystems: list[RepoMapSubsystem] = field(default_factory=list)
    hints: list[RepoMapHint] = field(default_factory=list)
    contract_handoff: Optional[RepoMapContractHandoff] = None

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "generated_from": self.generated_from,
            "summary": self.summary.to_dict() if self.summary else None,
            "subsystems": [item.to_dict() for item in self.subsystems],
            "hints": [item.to_dict() for item in self.hints],
            "contract_handoff": self.contract_handoff.to_dict() if self.contract_handoff else None,
        }


@dataclass(frozen=True)
class ContractSpec:
    title: str
    objective: str
    project_path: str
    output_path: str
    source_context: SourceContext
    deliverables: list[str]
    test_requirements: list[str]
    stop_conditions: list[str]
    report_sections: list[str]
    non_negotiable_rules: list[str]
    repo_hints: RepoHints
    map_context: Optional[MapContext] = None

    def to_json(self) -> str:
        payload = asdict(self)
        payload["map_context"] = self.map_context.to_dict() if self.map_context else None
        return json.dumps(payload, indent=2)


def slugify(value: str) -> str:
    lowered = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return lowered or "contract"


class ContractEngine:
    def __init__(self) -> None:
        self._projection_engine = ContextProjectionEngine()
        self._map_engine = RepoMapEngine()

    def load_source_context(self, project_dir: str | Path) -> SourceContext:
        root = Path(project_dir)
        detected = self._projection_engine.detect_source(root)
        if detected is None:
            return SourceContext(path=None, format=None, content="", missing=True)
        source_format, source_path = detected
        return SourceContext(
            path=str(source_path),
            format=source_format,
            content=source_path.read_text(encoding="utf-8", errors="replace"),
            missing=False,
        )

    def load_map_context(self, map_input: Optional[str]) -> Optional[MapContext]:
        if not map_input:
            return None
        candidate = Path(map_input).expanduser()
        if candidate.exists() and candidate.is_file():
            payload = json.loads(candidate.read_text(encoding="utf-8"))
            summary_data = payload.get("summary") or {}
            handoff_data = payload.get("contract_handoff") or {}
            return MapContext(
                source=str(candidate.resolve()),
                generated_from=payload.get("target") or summary_data.get("root"),
                summary=RepoMapSummary(
                    name=summary_data.get("name", candidate.stem),
                    root=summary_data.get("root", payload.get("target", "")),
                    total_files=summary_data.get("total_files", 0),
                    total_dirs=summary_data.get("total_dirs", 0),
                    primary_language=summary_data.get("primary_language"),
                ),
                subsystems=[RepoMapSubsystem(**item) for item in (payload.get("subsystems") or [])],
                hints=[RepoMapHint(**item) for item in (payload.get("hints") or [])],
                contract_handoff=RepoMapContractHandoff(
                    suggested_artifact=handoff_data.get("suggested_artifact", "map.json"),
                    summary_lines=list(handoff_data.get("summary_lines") or []),
                    contract_prompt=handoff_data.get("contract_prompt", ""),
                ),
            )

        repo_map = self._map_engine.map_target(map_input)
        return MapContext(
            source=map_input,
            generated_from=repo_map.target,
            summary=repo_map.summary,
            subsystems=list(repo_map.subsystems),
            hints=list(repo_map.hints),
            contract_handoff=repo_map.contract_handoff,
        )

    def default_output_path(self, project_dir: str | Path, objective: str) -> Path:
        return Path(project_dir) / f"all-day-build-contract-{slugify(objective)}.md"

    def build_spec(
        self,
        project_dir: str | Path,
        objective: str,
        *,
        title: Optional[str] = None,
        deliverables: Optional[list[str]] = None,
        test_requirements: Optional[list[str]] = None,
        output_path: Optional[str | Path] = None,
        map_input: Optional[str] = None,
    ) -> ContractSpec:
        root = Path(project_dir).resolve()
        source_context = self.load_source_context(root)
        map_context = self.load_map_context(map_input)
        repo_hints = self.infer_repo_hints(root, source_context, map_context)
        final_deliverables = list(deliverables or self.default_deliverables(objective, source_context, repo_hints, map_context))
        final_tests = list(test_requirements or self.default_test_requirements(repo_hints, map_context))
        final_output = Path(output_path) if output_path else self.default_output_path(root, objective)
        return ContractSpec(
            title=title or f"All-Day Build Contract: {root.name} {objective}",
            objective=objective,
            project_path=str(root),
            output_path=str(final_output),
            source_context=source_context,
            deliverables=final_deliverables,
            test_requirements=final_tests,
            stop_conditions=[
                "All deliverables checked and all tests passing -> DONE",
                "3 consecutive failed attempts on the same issue -> STOP, write blocker report",
                "Scope creep detected -> STOP and report the new scope",
                "All tests passing but deliverables remain -> continue to next deliverable",
            ],
            report_sections=list(_DEFAULT_REPORT_SECTIONS),
            non_negotiable_rules=self.non_negotiable_rules(source_context, map_context),
            repo_hints=repo_hints,
            map_context=map_context,
        )

    def default_deliverables(self, objective: str, source_context: SourceContext, repo_hints: RepoHints, map_context: Optional[MapContext]) -> list[str]:
        items = [
            f"Implement the objective: {objective}",
            "Add or update focused tests for the changed behavior",
            "Update docs and release/status surfaces touched by the change",
            "Run final validation and record the outcome",
        ]
        if source_context.path:
            items.insert(1, f"Keep the implementation aligned with canonical source context from {Path(source_context.path).name if source_context.format != FORMAT_AGENTKIT_SOURCE else '.agentkit/source.md'}")
        if map_context and map_context.summary:
            items.insert(1, f"Use the repo map for {map_context.summary.name} as the explorer artifact while scoping the change")
        if repo_hints.boundaries:
            items.append(f"Respect repo boundaries: {', '.join(repo_hints.boundaries[:4])}")
        return items

    def default_test_requirements(self, repo_hints: RepoHints, map_context: Optional[MapContext]) -> list[str]:
        requirements = ["Run focused tests for each deliverable", "Run the full test suite at the end"]
        if map_context and map_context.subsystems:
            requirements.append(f"Touch the mapped subsystem(s) deliberately: {', '.join(item.name for item in map_context.subsystems[:3])}")
        for hint in repo_hints.command_hints:
            if "pytest" in hint or "test" in hint:
                requirements.append(f"Prefer repo-detected command: {hint}")
                break
        return requirements

    def non_negotiable_rules(self, source_context: SourceContext, map_context: Optional[MapContext]) -> list[str]:
        rules = list(_DOCTRINE_RULES)
        if source_context.missing:
            rules.append("Missing canonical source: detect and respect existing repo files instead of inventing extra scope.")
        elif source_context.path:
            display = ".agentkit/source.md" if source_context.format == FORMAT_AGENTKIT_SOURCE else Path(source_context.path).name
            rules.append(f"Use {display} as the source-of-truth context when planning implementation details.")
        if map_context:
            rules.append("Treat the repo map as the explorer artifact, not a license to broaden scope beyond the chosen objective.")
        return rules

    def infer_repo_hints(self, project_dir: Path, source_context: SourceContext, map_context: Optional[MapContext]) -> RepoHints:
        command_hints: list[str] = []
        boundaries: list[str] = []
        notes: list[str] = []

        if source_context.content:
            for line in source_context.content.splitlines():
                stripped = line.strip()
                if not stripped:
                    continue
                if stripped.startswith(("uv ", "python ", "python3 ", "pytest ", "make ", "npm ", "pnpm ", "yarn ", "cargo ")):
                    if stripped not in command_hints:
                        command_hints.append(stripped)
                if len(command_hints) >= 6:
                    break

        pyproject = project_dir / "pyproject.toml"
        if pyproject.exists():
            text = pyproject.read_text(encoding="utf-8", errors="replace")
            if "pytest" in text and "uv run pytest -q" not in command_hints:
                command_hints.append("uv run pytest -q")
            if "[project]" in text:
                notes.append("Python project metadata present in pyproject.toml")

        for dirname in ("agentkit_cli", "tests", "docs", "examples", "dist"):
            if (project_dir / dirname).exists():
                boundaries.append(dirname)

        if (project_dir / ".agentkit").exists():
            boundaries.append(".agentkit")
        if source_context.path:
            notes.append(f"Canonical context detected at {source_context.path}")
        if not source_context.path:
            notes.append("No canonical source detected, legacy repo files only")

        if map_context:
            if map_context.source:
                notes.append(f"Repo map source: {map_context.source}")
            for subsystem in map_context.subsystems[:4]:
                if subsystem.path not in boundaries:
                    boundaries.append(subsystem.path)
            for hint in map_context.hints[:4]:
                if hint.kind in {"next_task", "work_surface"}:
                    notes.append(f"Map hint: {hint.title} - {hint.detail}")

        return RepoHints(command_hints=command_hints, boundaries=boundaries, context_notes=notes)

    def render_markdown(self, spec: ContractSpec) -> str:
        lines = [
            f"# {spec.title}",
            "",
            "Status: Draft",
            "Owner: agentkit contract",
            "Scope type: Deliverable-gated (no hour promises)",
            "",
            "## 1. Objective",
            "",
            spec.objective,
            "",
            "## 2. Source of Truth",
            "",
        ]
        if spec.source_context.missing:
            lines.extend([
                "- Canonical source: not found",
                "- Fallback mode: infer only from explicit repo files and commands",
            ])
        else:
            lines.extend([
                f"- Canonical source path: {spec.source_context.path}",
                f"- Canonical source format: {spec.source_context.format}",
            ])
        if spec.repo_hints.context_notes:
            lines.append("")
            for note in spec.repo_hints.context_notes:
                lines.append(f"- {note}")
        if spec.map_context and spec.map_context.summary:
            lines.extend(["", "## 3. Explorer Artifact", ""])
            lines.append(f"- Repo map source: {spec.map_context.source or spec.map_context.generated_from}")
            lines.append(f"- Repo: {spec.map_context.summary.name}")
            lines.append(f"- Primary language: {spec.map_context.summary.primary_language or 'Unknown'}")
            lines.append(f"- Files: {spec.map_context.summary.total_files}")
            if spec.map_context.subsystems:
                lines.append("")
                lines.append("### Mapped subsystems")
                lines.append("")
                for subsystem in spec.map_context.subsystems[:6]:
                    lines.append(f"- `{subsystem.path}` ({subsystem.name}): {subsystem.why}")
            if spec.map_context.hints:
                lines.append("")
                lines.append("### Map handoff hints")
                lines.append("")
                for hint in spec.map_context.hints[:6]:
                    lines.append(f"- {hint.title}: {hint.detail}")
            if spec.map_context.contract_handoff and spec.map_context.contract_handoff.contract_prompt:
                lines.extend(["", "```text", spec.map_context.contract_handoff.contract_prompt, "```"])
        lines.extend(["", f"## {'4' if spec.map_context else '3'}. Non-Negotiable Build Rules", ""])
        for index, rule in enumerate(spec.non_negotiable_rules, start=1):
            lines.append(f"{index}. {rule}")
        deliverables_section = '5' if spec.map_context else '4'
        tests_section = '6' if spec.map_context else '5'
        reports_section = '7' if spec.map_context else '6'
        stops_section = '8' if spec.map_context else '7'
        lines.extend(["", f"## {deliverables_section}. Deliverables", ""])
        for item in spec.deliverables:
            lines.append(f"- [ ] {item}")
        lines.extend(["", f"## {tests_section}. Test Requirements", ""])
        for item in spec.test_requirements:
            lines.append(f"- [ ] {item}")
        if spec.repo_hints.command_hints:
            lines.extend(["", "### Repo command hints", ""])
            for hint in spec.repo_hints.command_hints:
                lines.append(f"- `{hint}`")
        if spec.repo_hints.boundaries:
            lines.extend(["", "### Context boundaries", ""])
            for boundary in spec.repo_hints.boundaries:
                lines.append(f"- {boundary}")
        lines.extend(["", f"## {reports_section}. Reports", ""])
        lines.append("- Write or update progress in `progress-log.md` after each completed deliverable")
        for section in spec.report_sections:
            lines.append(f"- Final report must include: {section}")
        lines.extend(["", f"## {stops_section}. Stop Conditions", ""])
        for item in spec.stop_conditions:
            lines.append(f"- {item}")
        return "\n".join(lines).rstrip() + "\n"

    def write_contract(self, spec: ContractSpec, *, overwrite: bool = False) -> Path:
        output_path = Path(spec.output_path)
        if output_path.exists() and not overwrite:
            raise FileExistsError(f"Refusing to overwrite existing contract: {output_path}")
        output_path.write_text(self.render_markdown(spec), encoding="utf-8")
        return output_path
