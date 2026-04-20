from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from agentkit_cli.bundle import BundleEngine, BundleGap


@dataclass(frozen=True)
class TaskpackSection:
    title: str
    bullets: list[str] = field(default_factory=list)
    preview: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "title": self.title,
            "bullets": list(self.bullets),
            "preview": self.preview,
        }


@dataclass(frozen=True)
class TaskpackChecklistItem:
    label: str
    done: bool = False

    def to_dict(self) -> dict[str, object]:
        return {"label": self.label, "done": self.done}


@dataclass(frozen=True)
class TaskpackInstructionSet:
    target: str
    runner: str
    prompt_style: str
    checklist: list[TaskpackChecklistItem] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "target": self.target,
            "runner": self.runner,
            "prompt_style": self.prompt_style,
            "checklist": [item.to_dict() for item in self.checklist],
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class Taskpack:
    schema_version: str
    project_path: str
    target: str
    durable_context: list[TaskpackSection]
    task_brief: TaskpackSection
    execution: TaskpackInstructionSet
    gaps: list[BundleGap] = field(default_factory=list)
    source_bundle: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "project_path": self.project_path,
            "target": self.target,
            "durable_context": [section.to_dict() for section in self.durable_context],
            "task_brief": self.task_brief.to_dict(),
            "execution": self.execution.to_dict(),
            "gaps": [gap.to_dict() for gap in self.gaps],
            "source_bundle": self.source_bundle,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


class TaskpackEngine:
    def __init__(self) -> None:
        self._bundle = BundleEngine()

    def build(self, project_dir: str | Path, *, target: str = "generic") -> Taskpack:
        normalized_target = self._normalize_target(target)
        bundle = self._bundle.build(project_dir)
        summary = bundle.architecture_map.get("summary") or {}
        readiness = bundle.source_audit.get("readiness") or {}
        subsystems = bundle.architecture_map.get("subsystems") or []
        scripts = bundle.architecture_map.get("scripts") or []
        hints = bundle.architecture_map.get("hints") or []

        durable_context = [
            TaskpackSection(
                title="Source context",
                bullets=[
                    f"Path: {bundle.source.path or 'missing'}",
                    f"Format: {bundle.source.format or 'unknown'}",
                    f"Contract-ready: {'yes' if readiness.get('ready_for_contract') else 'no'}",
                ],
                preview=bundle.source.preview,
            ),
            TaskpackSection(
                title="Architecture map",
                bullets=[
                    f"Repo: {summary.get('name') or Path(bundle.project_path).name}",
                    f"Primary language: {summary.get('primary_language') or 'Unknown'}",
                    *[f"Subsystem: {item['name']} ({item['path']})" for item in subsystems[:4]],
                ],
                preview="\n".join(f"- {item['name']} from {item['source']}: {item['command']}" for item in scripts[:6]),
            ),
            TaskpackSection(
                title="Execution contract",
                bullets=[
                    f"Mode: {bundle.contract.mode}",
                    f"Artifact: {bundle.contract.artifact_path or 'missing'}",
                ],
                preview=bundle.contract.preview,
            ),
        ]
        task_brief = TaskpackSection(
            title="Task brief",
            bullets=[
                f"Assemble and execute work for {summary.get('name') or Path(bundle.project_path).name} without broadening scope.",
                f"Resolve {len(bundle.gaps)} known gap(s) explicitly if they block execution.",
                *[f"Hint: {item['title']} - {item['detail']}" for item in hints[:4]],
            ],
            preview=str(readiness.get("summary") or "Use the attached bundle surfaces as the source of truth."),
        )
        execution = self._instruction_set(normalized_target, scripts)
        return Taskpack(
            schema_version="agentkit.taskpack.v1",
            project_path=bundle.project_path,
            target=normalized_target,
            durable_context=durable_context,
            task_brief=task_brief,
            execution=execution,
            gaps=bundle.gaps,
            source_bundle=bundle.to_dict(),
        )

    def render_markdown(self, pack: Taskpack) -> str:
        lines = [
            f"# Agent taskpack: {Path(pack.project_path).name}",
            "",
            f"- Schema: `{pack.schema_version}`",
            f"- Target: `{pack.target}`",
            f"- Project: `{pack.project_path}`",
            "",
            "## Durable context",
            "",
        ]
        for section in pack.durable_context:
            lines.extend([f"### {section.title}", ""])
            for bullet in section.bullets:
                lines.append(f"- {bullet}")
            lines.extend(["", "```markdown", section.preview or "(no preview available)", "```", ""])
        lines.extend(["## Task brief", ""])
        for bullet in pack.task_brief.bullets:
            lines.append(f"- {bullet}")
        lines.extend(["", "```text", pack.task_brief.preview or "(no task brief preview available)", "```", "", "## Execution checklist", ""])
        for item in pack.execution.checklist:
            marker = "x" if item.done else " "
            lines.append(f"- [{marker}] {item.label}")
        lines.extend(["", "## Target instructions", "", f"- Runner: {pack.execution.runner}", f"- Prompt style: {pack.execution.prompt_style}"])
        if pack.execution.notes:
            lines.extend(["", "### Notes", ""])
            for note in pack.execution.notes:
                lines.append(f"- {note}")
        lines.extend(["", "## Gap report", ""])
        if pack.gaps:
            for gap in pack.gaps:
                lines.extend([f"### {gap.title}", "", f"- Detail: {gap.detail}", f"- Action: {gap.action}", ""])
        else:
            lines.append("- No open gaps detected.")
        return "\n".join(lines).rstrip() + "\n"

    def write_directory(self, pack: Taskpack, output_dir: str | Path) -> Path:
        out = Path(output_dir).expanduser().resolve()
        out.mkdir(parents=True, exist_ok=True)
        (out / "taskpack.md").write_text(self.render_markdown(pack), encoding="utf-8")
        (out / "taskpack.json").write_text(pack.to_json(), encoding="utf-8")
        return out

    def _normalize_target(self, target: str) -> str:
        value = target.strip().lower()
        if value not in {"generic", "codex", "claude-code"}:
            raise ValueError("target must be one of: generic, codex, claude-code")
        return value

    def _instruction_set(self, target: str, scripts: list[dict[str, object]]) -> TaskpackInstructionSet:
        common = [
            TaskpackChecklistItem("Read the durable context and task brief before changing code."),
            TaskpackChecklistItem("Keep edits inside the stated repo and honor the contract preview."),
            TaskpackChecklistItem("Run the most relevant mapped test/build commands before claiming completion."),
            TaskpackChecklistItem("Call out unresolved gaps instead of guessing missing context."),
        ]
        script_note = "Mapped execution surfaces: " + (", ".join(str(item.get("name")) for item in scripts[:4]) or "none detected")
        if target == "codex":
            return TaskpackInstructionSet(target=target, runner="codex exec --full-auto", prompt_style="Paste taskpack.md as the execution prompt.", checklist=common, notes=[script_note, "Prefer short imperative instructions and preserve explicit checklist items."])
        if target == "claude-code":
            return TaskpackInstructionSet(target=target, runner="claude --print --permission-mode bypassPermissions", prompt_style="Paste taskpack.md as the prompt or attach the directory.", checklist=common, notes=[script_note, "Keep instructions concrete and mention any required output files up front."])
        return TaskpackInstructionSet(target=target, runner="generic coding agent", prompt_style="Use taskpack.md as the primary handoff and taskpack.json for machine-readable context.", checklist=common, notes=[script_note, "Do not rely on hidden repo knowledge beyond the included bundle surfaces."])
