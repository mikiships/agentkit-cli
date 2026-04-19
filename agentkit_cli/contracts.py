from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

from agentkit_cli.context_projections import ContextProjectionEngine, FORMAT_AGENTKIT_SOURCE


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

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)


def slugify(value: str) -> str:
    lowered = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return lowered or "contract"


class ContractEngine:
    def __init__(self) -> None:
        self._projection_engine = ContextProjectionEngine()

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
    ) -> ContractSpec:
        root = Path(project_dir).resolve()
        source_context = self.load_source_context(root)
        repo_hints = self.infer_repo_hints(root, source_context)
        final_deliverables = list(deliverables or self.default_deliverables(objective, source_context, repo_hints))
        final_tests = list(test_requirements or self.default_test_requirements(repo_hints))
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
            non_negotiable_rules=self.non_negotiable_rules(source_context),
            repo_hints=repo_hints,
        )

    def default_deliverables(self, objective: str, source_context: SourceContext, repo_hints: RepoHints) -> list[str]:
        items = [
            f"Implement the objective: {objective}",
            "Add or update focused tests for the changed behavior",
            "Update docs and release/status surfaces touched by the change",
            "Run final validation and record the outcome",
        ]
        if source_context.path:
            items.insert(1, f"Keep the implementation aligned with canonical source context from {Path(source_context.path).name if source_context.format != FORMAT_AGENTKIT_SOURCE else '.agentkit/source.md'}")
        if repo_hints.boundaries:
            items.append(f"Respect repo boundaries: {', '.join(repo_hints.boundaries[:4])}")
        return items

    def default_test_requirements(self, repo_hints: RepoHints) -> list[str]:
        requirements = ["Run focused tests for each deliverable", "Run the full test suite at the end"]
        for hint in repo_hints.command_hints:
            if "pytest" in hint or "test" in hint:
                requirements.append(f"Prefer repo-detected command: {hint}")
                break
        return requirements

    def non_negotiable_rules(self, source_context: SourceContext) -> list[str]:
        rules = list(_DOCTRINE_RULES)
        if source_context.missing:
            rules.append("Missing canonical source: detect and respect existing repo files instead of inventing extra scope.")
        elif source_context.path:
            display = ".agentkit/source.md" if source_context.format == FORMAT_AGENTKIT_SOURCE else Path(source_context.path).name
            rules.append(f"Use {display} as the source-of-truth context when planning implementation details.")
        return rules

    def infer_repo_hints(self, project_dir: Path, source_context: SourceContext) -> RepoHints:
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
        lines.extend(["", "## 3. Non-Negotiable Build Rules", ""])
        for index, rule in enumerate(spec.non_negotiable_rules, start=1):
            lines.append(f"{index}. {rule}")
        lines.extend(["", "## 4. Deliverables", ""])
        for item in spec.deliverables:
            lines.append(f"- [ ] {item}")
        lines.extend(["", "## 5. Test Requirements", ""])
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
        lines.extend(["", "## 6. Reports", ""])
        lines.append(f"- Write or update progress in `progress-log.md` after each completed deliverable")
        for section in spec.report_sections:
            lines.append(f"- Final report must include: {section}")
        lines.extend(["", "## 7. Stop Conditions", ""])
        for item in spec.stop_conditions:
            lines.append(f"- {item}")
        return "\n".join(lines).rstrip() + "\n"

    def write_contract(self, spec: ContractSpec, *, overwrite: bool = False) -> Path:
        output_path = Path(spec.output_path)
        if output_path.exists() and not overwrite:
            raise FileExistsError(f"Refusing to overwrite existing contract: {output_path}")
        output_path.write_text(self.render_markdown(spec), encoding="utf-8")
        return output_path
