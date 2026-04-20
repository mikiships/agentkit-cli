from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from agentkit_cli.contracts import ContractEngine
from agentkit_cli.map_engine import RepoMapEngine
from agentkit_cli.source_audit import SourceAuditEngine


@dataclass(frozen=True)
class BundleGap:
    code: str
    title: str
    detail: str
    action: str

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "title": self.title,
            "detail": self.detail,
            "action": self.action,
        }


@dataclass(frozen=True)
class BundleSourceSurface:
    path: Optional[str]
    format: Optional[str]
    missing: bool
    preview: str

    def to_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "format": self.format,
            "missing": self.missing,
            "preview": self.preview,
        }


@dataclass(frozen=True)
class BundleContractSurface:
    artifact_path: Optional[str]
    missing: bool
    mode: str
    preview: str

    def to_dict(self) -> dict[str, object]:
        return {
            "artifact_path": self.artifact_path,
            "missing": self.missing,
            "mode": self.mode,
            "preview": self.preview,
        }


@dataclass(frozen=True)
class HandoffBundle:
    schema_version: str
    project_path: str
    source: BundleSourceSurface
    source_audit: dict[str, object]
    architecture_map: dict[str, object]
    contract: BundleContractSurface
    gaps: list[BundleGap] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "project_path": self.project_path,
            "source": self.source.to_dict(),
            "source_audit": self.source_audit,
            "architecture_map": self.architecture_map,
            "contract": self.contract.to_dict(),
            "gaps": [item.to_dict() for item in self.gaps],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


class BundleEngine:
    def __init__(self) -> None:
        self._contracts = ContractEngine()
        self._audit = SourceAuditEngine()
        self._map = RepoMapEngine()

    def build(self, project_dir: str | Path) -> HandoffBundle:
        root = Path(project_dir).expanduser().resolve()
        source_context = self._contracts.load_source_context(root)
        audit_result = self._audit.audit(root)
        repo_map = self._map.map_local_path(root)
        contract_surface = self._load_contract_surface(root, repo_map.contract_handoff.contract_prompt)
        gaps = self._collect_gaps(source_context, audit_result.to_dict(), contract_surface)
        return HandoffBundle(
            schema_version="agentkit.bundle.v1",
            project_path=str(root),
            source=BundleSourceSurface(
                path=source_context.path,
                format=source_context.format,
                missing=source_context.missing,
                preview=self._preview(source_context.content),
            ),
            source_audit=audit_result.to_dict(),
            architecture_map=repo_map.to_dict(),
            contract=contract_surface,
            gaps=gaps,
        )

    def render_markdown(self, bundle: HandoffBundle) -> str:
        source = bundle.source
        audit = bundle.source_audit
        readiness = audit.get("readiness") or {}
        repo_map = bundle.architecture_map
        summary = repo_map.get("summary") or {}
        lines = [
            f"# Agent handoff bundle: {summary.get('name') or Path(bundle.project_path).name}",
            "",
            f"- Schema: `{bundle.schema_version}`",
            f"- Project: `{bundle.project_path}`",
            "",
            "## Source",
            "",
            f"- Path: `{source.path or 'missing'}`",
            f"- Format: `{source.format or 'unknown'}`",
            f"- Missing: {'yes' if source.missing else 'no'}",
            "",
            "```markdown",
            source.preview or "(no source preview available)",
            "```",
            "",
            "## Source audit",
            "",
            f"- Ready for contract: {'yes' if readiness.get('ready_for_contract') else 'no'}",
            f"- Blockers: {readiness.get('blocker_count', 0)}",
            f"- Warnings: {readiness.get('warning_count', 0)}",
            f"- Summary: {readiness.get('summary', 'n/a')}",
            "",
            "## Architecture map",
            "",
            f"- Primary language: {summary.get('primary_language') or 'Unknown'}",
            f"- Files: {summary.get('total_files', 0)}",
            f"- Directories: {summary.get('total_dirs', 0)}",
            "",
            "### Subsystems",
            "",
        ]
        subsystems = repo_map.get("subsystems") or []
        if subsystems:
            for item in subsystems[:8]:
                lines.append(f"- `{item['path']}` ({item['name']}): {item['why']}")
        else:
            lines.append("- None inferred")
        lines.extend(["", "### Execution surfaces", ""])
        scripts = repo_map.get("scripts") or []
        if scripts:
            for item in scripts[:8]:
                lines.append(f"- `{item['name']}` from `{item['source']}`: `{item['command']}`")
        else:
            lines.append("- None detected")
        lines.extend(["", "## Execution contract", ""])
        lines.append(f"- Artifact path: `{bundle.contract.artifact_path or 'missing'}`")
        lines.append(f"- Mode: `{bundle.contract.mode}`")
        lines.extend(["", "```markdown", bundle.contract.preview or "(no contract preview available)", "```", "", "## Open gaps", ""])
        if bundle.gaps:
            for gap in bundle.gaps:
                lines.extend([
                    f"### {gap.title}",
                    "",
                    f"- Detail: {gap.detail}",
                    f"- Action: {gap.action}",
                    "",
                ])
        else:
            lines.append("- No open gaps detected across source, audit, map, and contract surfaces.")
        return "\n".join(lines).rstrip() + "\n"

    def _load_contract_surface(self, root: Path, fallback_prompt: str) -> BundleContractSurface:
        candidates = sorted(root.glob("all-day-build-contract-*.md"))
        if candidates:
            path = candidates[0]
            return BundleContractSurface(
                artifact_path=str(path),
                missing=False,
                mode="existing-contract",
                preview=self._preview(path.read_text(encoding="utf-8", errors="replace")),
            )
        return BundleContractSurface(
            artifact_path=None,
            missing=True,
            mode="map-handoff-fallback",
            preview=self._preview(fallback_prompt),
        )

    def _collect_gaps(self, source_context, audit: dict[str, object], contract: BundleContractSurface) -> list[BundleGap]:
        gaps: list[BundleGap] = []
        if source_context.missing:
            gaps.append(BundleGap(
                code="missing_source",
                title="Missing canonical source",
                detail="No canonical or legacy source file was detected.",
                action="Create .agentkit/source.md or promote an existing context file before relying on this bundle.",
            ))
        readiness = audit.get("readiness") or {}
        if not readiness.get("ready_for_contract"):
            gaps.append(BundleGap(
                code="source_not_ready",
                title="Source is not contract-ready",
                detail=str(readiness.get("summary") or "Source audit reported unresolved issues."),
                action="Resolve source-audit blockers or warnings before handing the bundle to a coding agent.",
            ))
        if contract.missing:
            gaps.append(BundleGap(
                code="missing_contract_artifact",
                title="Missing saved contract artifact",
                detail="No all-day build contract markdown file was found in the repo root.",
                action="Run agentkit contract to save a concrete execution contract, or use the fallback prompt included here.",
            ))
        return gaps

    def _preview(self, text: str, limit: int = 1200) -> str:
        cleaned = text.strip()
        if not cleaned:
            return ""
        if len(cleaned) <= limit:
            return cleaned
        return cleaned[:limit].rstrip() + "\n... [truncated]"
