from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from agentkit_cli.contracts import ContractEngine, MapContext, SourceContext
from agentkit_cli.source_audit import SourceAuditEngine, SourceAuditResult


_WORKFLOW_ARTIFACTS = (
    ("README.md", "readme"),
    ("CHANGELOG.md", "changelog"),
    ("BUILD-REPORT.md", "build-report"),
    ("FINAL-SUMMARY.md", "final-summary"),
    ("progress-log.md", "progress-log"),
)


@dataclass(frozen=True)
class SpecWorkflowArtifact:
    path: str
    kind: str
    status: Optional[str] = None
    version: Optional[str] = None
    lanes: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "kind": self.kind,
            "status": self.status,
            "version": self.version,
            "lanes": list(self.lanes),
            "evidence": list(self.evidence),
        }


@dataclass(frozen=True)
class SpecContractSeed:
    objective: str
    title: str
    deliverables: list[str] = field(default_factory=list)
    test_requirements: list[str] = field(default_factory=list)
    map_input: Optional[str] = None

    def to_dict(self) -> dict[str, object]:
        return {
            "objective": self.objective,
            "title": self.title,
            "deliverables": list(self.deliverables),
            "test_requirements": list(self.test_requirements),
            "map_input": self.map_input,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "SpecContractSeed":
        return cls(
            objective=str(payload.get("objective") or ""),
            title=str(payload.get("title") or ""),
            deliverables=[str(item) for item in (payload.get("deliverables") or [])],
            test_requirements=[str(item) for item in (payload.get("test_requirements") or [])],
            map_input=str(payload.get("map_input")) if payload.get("map_input") else None,
        )


@dataclass(frozen=True)
class SpecRecommendation:
    slug: str
    kind: str
    score: int
    title: str
    objective: str
    why_now: list[str] = field(default_factory=list)
    scope_boundaries: list[str] = field(default_factory=list)
    validation_hints: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    contract_seed: SpecContractSeed = field(default_factory=lambda: SpecContractSeed(objective="", title=""))

    def to_dict(self) -> dict[str, object]:
        return {
            "slug": self.slug,
            "kind": self.kind,
            "score": self.score,
            "title": self.title,
            "objective": self.objective,
            "why_now": list(self.why_now),
            "scope_boundaries": list(self.scope_boundaries),
            "validation_hints": list(self.validation_hints),
            "evidence": list(self.evidence),
            "contract_seed": self.contract_seed.to_dict(),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "SpecRecommendation":
        return cls(
            slug=str(payload.get("slug") or ""),
            kind=str(payload.get("kind") or "generic"),
            score=int(payload.get("score") or 0),
            title=str(payload.get("title") or ""),
            objective=str(payload.get("objective") or ""),
            why_now=[str(item) for item in (payload.get("why_now") or [])],
            scope_boundaries=[str(item) for item in (payload.get("scope_boundaries") or [])],
            validation_hints=[str(item) for item in (payload.get("validation_hints") or [])],
            evidence=[str(item) for item in (payload.get("evidence") or [])],
            contract_seed=SpecContractSeed.from_dict(dict(payload.get("contract_seed") or {})),
        )


@dataclass(frozen=True)
class RepoSpec:
    schema_version: str
    project_path: str
    source_context_path: Optional[str]
    source_context_format: Optional[str]
    source_ready_for_contract: bool
    source_readiness_summary: str
    map_context: Optional[dict[str, object]]
    recent_workflow_artifacts: list[SpecWorkflowArtifact] = field(default_factory=list)
    primary_recommendation: Optional[SpecRecommendation] = None
    alternate_recommendations: list[SpecRecommendation] = field(default_factory=list)
    contract_seed: Optional[SpecContractSeed] = None

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "project_path": self.project_path,
            "source_context_path": self.source_context_path,
            "source_context_format": self.source_context_format,
            "source_ready_for_contract": self.source_ready_for_contract,
            "source_readiness_summary": self.source_readiness_summary,
            "map_context": self.map_context,
            "recent_workflow_artifacts": [item.to_dict() for item in self.recent_workflow_artifacts],
            "primary_recommendation": self.primary_recommendation.to_dict() if self.primary_recommendation else None,
            "alternate_recommendations": [item.to_dict() for item in self.alternate_recommendations],
            "contract_seed": self.contract_seed.to_dict() if self.contract_seed else None,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "RepoSpec":
        return cls(
            schema_version=str(payload.get("schema_version") or "agentkit.spec.v1"),
            project_path=str(payload.get("project_path") or ""),
            source_context_path=str(payload.get("source_context_path")) if payload.get("source_context_path") else None,
            source_context_format=str(payload.get("source_context_format")) if payload.get("source_context_format") else None,
            source_ready_for_contract=bool(payload.get("source_ready_for_contract")),
            source_readiness_summary=str(payload.get("source_readiness_summary") or ""),
            map_context=dict(payload.get("map_context") or {}) or None,
            recent_workflow_artifacts=[SpecWorkflowArtifact(**item) for item in (payload.get("recent_workflow_artifacts") or [])],
            primary_recommendation=SpecRecommendation.from_dict(dict(payload.get("primary_recommendation") or {})) if payload.get("primary_recommendation") else None,
            alternate_recommendations=[SpecRecommendation.from_dict(dict(item)) for item in (payload.get("alternate_recommendations") or [])],
            contract_seed=SpecContractSeed.from_dict(dict(payload.get("contract_seed") or {})) if payload.get("contract_seed") else None,
        )


class SpecEngine:
    def __init__(self) -> None:
        self._contracts = ContractEngine()
        self._audit = SourceAuditEngine()

    def build(self, project_dir: str | Path, *, map_input: Optional[str] = None) -> RepoSpec:
        root = Path(project_dir).expanduser().resolve()
        if not root.exists() or not root.is_dir():
            raise FileNotFoundError(f"Path not found: {root}")

        source_context = self._contracts.load_source_context(root)
        audit_result = self._audit.audit(root)
        self._validate_upstream(root, source_context, audit_result)
        map_context = self._contracts.load_map_context(map_input or str(root))
        self._validate_map_context(root, map_context)
        repo_hints = self._contracts.infer_repo_hints(root, source_context, map_context)
        workflow_artifacts = self._workflow_artifacts(root)
        recommendations = self._build_recommendations(root, source_context, audit_result, map_context, repo_hints, workflow_artifacts)
        if not recommendations:
            raise ValueError("Unable to derive a deterministic next-build recommendation from the available repo artifacts.")
        primary = recommendations[0]
        alternates = recommendations[1:3]
        return RepoSpec(
            schema_version="agentkit.spec.v1",
            project_path=str(root),
            source_context_path=source_context.path,
            source_context_format=source_context.format,
            source_ready_for_contract=bool(audit_result.readiness.ready_for_contract),
            source_readiness_summary=audit_result.readiness.summary,
            map_context=map_context.to_dict() if map_context else None,
            recent_workflow_artifacts=workflow_artifacts,
            primary_recommendation=primary,
            alternate_recommendations=alternates,
            contract_seed=primary.contract_seed,
        )

    def render_markdown(self, spec: RepoSpec) -> str:
        lines = [
            f"# Next-build spec: {Path(spec.project_path).name}",
            "",
            f"- Schema: `{spec.schema_version}`",
            f"- Project: `{spec.project_path}`",
            f"- Source: `{spec.source_context_path or 'missing'}` ({spec.source_context_format or 'unknown'})",
            f"- Contract-ready source: {'yes' if spec.source_ready_for_contract else 'no'}",
            f"- Readiness summary: {spec.source_readiness_summary}",
            "",
            "## Recent workflow artifacts",
            "",
        ]
        if spec.recent_workflow_artifacts:
            for artifact in spec.recent_workflow_artifacts:
                lines.append(f"### {artifact.path}")
                lines.append("")
                lines.append(f"- Kind: {artifact.kind}")
                if artifact.status:
                    lines.append(f"- Status: {artifact.status}")
                if artifact.version:
                    lines.append(f"- Version: {artifact.version}")
                for lane in artifact.lanes[:3]:
                    lines.append(f"- Lane: `{lane}`")
                for evidence in artifact.evidence[:3]:
                    lines.append(f"- Evidence: {evidence}")
                lines.append("")
        else:
            lines.append("- No shipped workflow artifacts detected. Falling back to source + map evidence only.")
            lines.append("")

        if spec.map_context:
            summary = dict(spec.map_context.get("summary") or {})
            lines.extend([
                "## Repo map grounding",
                "",
                f"- Repo: {summary.get('name') or Path(spec.project_path).name}",
                f"- Primary language: {summary.get('primary_language') or 'Unknown'}",
                f"- Files: {summary.get('total_files', 0)}",
                f"- Directories: {summary.get('total_dirs', 0)}",
                "",
            ])

        if spec.primary_recommendation:
            self._render_recommendation(lines, "Primary recommendation", spec.primary_recommendation)
        lines.extend(["", "## Alternates", ""])
        if spec.alternate_recommendations:
            for index, recommendation in enumerate(spec.alternate_recommendations, start=1):
                self._render_recommendation(lines, f"Alternate {index}", recommendation)
        else:
            lines.append("- None. The repo evidence supported one clearly best adjacent build.")
        return "\n".join(lines).rstrip() + "\n"

    def write_directory(self, spec: RepoSpec, output_dir: str | Path) -> Path:
        out = Path(output_dir).expanduser().resolve()
        out.mkdir(parents=True, exist_ok=True)
        (out / "spec.md").write_text(self.render_markdown(spec), encoding="utf-8")
        (out / "spec.json").write_text(spec.to_json(), encoding="utf-8")
        return out

    def load_artifact(self, path: str | Path) -> RepoSpec:
        candidate = Path(path).expanduser().resolve()
        payload = json.loads(candidate.read_text(encoding="utf-8"))
        return RepoSpec.from_dict(payload)

    def _render_recommendation(self, lines: list[str], heading: str, recommendation: SpecRecommendation) -> None:
        lines.extend([
            f"## {heading}",
            "",
            f"### {recommendation.title}",
            "",
            f"- Kind: `{recommendation.kind}`",
            f"- Score: {recommendation.score}",
            f"- Objective: {recommendation.objective}",
            "",
            "#### Why now",
            "",
        ])
        for item in recommendation.why_now:
            lines.append(f"- {item}")
        lines.extend(["", "#### Scope boundaries", ""])
        for item in recommendation.scope_boundaries:
            lines.append(f"- {item}")
        lines.extend(["", "#### Validation hints", ""])
        for item in recommendation.validation_hints:
            lines.append(f"- {item}")
        lines.extend(["", "#### Evidence", ""])
        for item in recommendation.evidence:
            lines.append(f"- {item}")
        lines.extend(["", "#### Contract seed", ""])
        lines.append(f"- Objective: {recommendation.contract_seed.objective}")
        lines.append(f"- Title: {recommendation.contract_seed.title}")
        if recommendation.contract_seed.map_input:
            lines.append(f"- Map input: `{recommendation.contract_seed.map_input}`")
        if recommendation.contract_seed.deliverables:
            lines.extend(["", "##### Deliverables", ""])
            for item in recommendation.contract_seed.deliverables:
                lines.append(f"- {item}")
        if recommendation.contract_seed.test_requirements:
            lines.extend(["", "##### Test requirements", ""])
            for item in recommendation.contract_seed.test_requirements:
                lines.append(f"- {item}")
        lines.append("")

    def _validate_upstream(self, root: Path, source_context: SourceContext, audit_result: SourceAuditResult) -> None:
        if source_context.missing:
            raise ValueError("agentkit spec requires a canonical or legacy source file before it can recommend the next build.")
        contradiction = next((item for item in audit_result.findings if item.code == "contradiction"), None)
        if contradiction is not None:
            raise ValueError(f"Contradictory upstream source guidance: {contradiction.evidence}")
        if audit_result.readiness.blocker_count:
            raise ValueError(audit_result.readiness.summary)
        if not audit_result.section_checks:
            raise ValueError("agentkit spec could not inspect any source sections. Run agentkit source-audit and tighten the source first.")
        if not audit_result.readiness.ready_for_contract and not audit_result.used_fallback:
            raise ValueError(audit_result.readiness.summary)

    def _validate_map_context(self, root: Path, map_context: Optional[MapContext]) -> None:
        if map_context is None or map_context.summary is None:
            raise ValueError("agentkit spec requires repo-map context before it can recommend the next build.")
        generated_from = map_context.generated_from or ""
        if generated_from.startswith("/"):
            try:
                generated_path = Path(generated_from).expanduser().resolve()
            except Exception:
                generated_path = None
            if generated_path and generated_path.exists() and generated_path != root:
                raise ValueError(f"Contradictory upstream map input: {generated_path} does not match target repo {root}.")

    def _build_recommendations(
        self,
        root: Path,
        source_context: SourceContext,
        audit_result: SourceAuditResult,
        map_context: MapContext,
        repo_hints,
        workflow_artifacts: list[SpecWorkflowArtifact],
    ) -> list[SpecRecommendation]:
        candidates: list[SpecRecommendation] = []
        workflow_gap = self._workflow_gap_candidate(root, workflow_artifacts, map_context, repo_hints)
        if workflow_gap is not None:
            candidates.append(workflow_gap)
        fallback = self._fallback_source_candidate(root, audit_result, map_context, repo_hints)
        if fallback is not None:
            candidates.append(fallback)
        shipped_truth_sync = self._shipped_truth_sync_candidate(root, source_context, audit_result, workflow_artifacts, map_context, repo_hints)
        if shipped_truth_sync is not None:
            candidates.append(shipped_truth_sync)
        flagship_post_closeout = self._flagship_post_closeout_advance_candidate(root, source_context, audit_result, workflow_artifacts, map_context, repo_hints)
        if flagship_post_closeout is not None:
            candidates.append(flagship_post_closeout)
        flagship_concrete_next = self._flagship_concrete_next_candidate(root, source_context, audit_result, workflow_artifacts, map_context, repo_hints)
        if flagship_concrete_next is not None:
            candidates.append(flagship_concrete_next)
        flagship_post_closeout = self._flagship_post_closeout_advance_candidate(root, source_context, audit_result, workflow_artifacts, map_context, repo_hints)
        if flagship_post_closeout is not None:
            candidates.append(flagship_post_closeout)
        adjacent_grounding = self._adjacent_grounding_candidate(root, source_context, audit_result, workflow_artifacts, map_context, repo_hints)
        if adjacent_grounding is not None:
            candidates.append(adjacent_grounding)
        coverage = self._coverage_candidate(root, map_context, repo_hints)
        if coverage is not None:
            candidates.append(coverage)
        subsystem = self._subsystem_candidate(root, source_context, map_context, repo_hints)
        if subsystem is not None:
            candidates.append(subsystem)
        deduped: dict[tuple[str, str], SpecRecommendation] = {}
        for candidate in candidates:
            deduped[(candidate.slug, candidate.title)] = candidate
        return sorted(deduped.values(), key=lambda item: (-item.score, item.title, item.slug))

    def _workflow_gap_candidate(self, root: Path, workflow_artifacts: list[SpecWorkflowArtifact], map_context: MapContext, repo_hints) -> Optional[SpecRecommendation]:
        lanes = self._ordered_unique(
            lane
            for artifact in workflow_artifacts
            for lane in artifact.lanes
        )
        gap_lanes = [lane for lane in lanes if "map -> contract" in lane and "spec" not in lane]
        if not gap_lanes or self._has_spec_command(root):
            return None
        latest_version = next((artifact.version for artifact in workflow_artifacts if artifact.version), None)
        evidence = [
            f"Workflow lane still jumps directly from map to contract: {gap_lanes[0]}",
            "agentkit_cli/main.py exposes map and contract but no spec command.",
        ]
        if latest_version:
            evidence.append(f"Latest documented shipped line is {latest_version}, which keeps the repo on small deterministic workflow increments.")
        objective = "Add a deterministic `agentkit spec` step between `map` and `contract` so repo-understanding artifacts produce a contract-ready next-build plan."
        deliverables = [
            "Add a first-class `agentkit spec` engine that consumes source context, source-audit readiness, repo-map context, and recent shipped workflow artifacts when present.",
            "Emit one primary recommended next build plus bounded alternates, with why-now reasoning, scope boundaries, validation hints, and contract-seeding fields.",
            "Wire `agentkit spec` into the CLI with stable markdown/stdout output, `--json`, `--output`, `--output-dir`, and direct `agentkit contract --spec` seeding.",
            "Update README, CHANGELOG, BUILD-REPORT, FINAL-SUMMARY, and version surfaces so the supported lane becomes `source -> audit -> map -> spec -> contract`.",
        ]
        tests = [
            "Run focused spec-engine, CLI, workflow, and contract-seeding tests.",
            "Re-run the release-confidence suite with `uv run python -m pytest -q`.",
            "Verify the same input produces the same spec JSON and markdown ordering.",
        ]
        return SpecRecommendation(
            slug="map-contract-spec-gap",
            kind="workflow-gap",
            score=95,
            title="Add deterministic spec planning between map and contract",
            objective=objective,
            why_now=self._ordered_unique([
                "README and current handoff docs still present `map -> contract` as a direct jump.",
                "This repo has been shipping one deterministic lane extension per version, so the missing planning step is the clean adjacent increment.",
                *([f"Recent shipped line: {latest_version}." ] if latest_version else []),
            ]),
            scope_boundaries=self._ordered_unique([
                "Keep the feature local-only and artifact-driven, with no agent execution or remote mutation.",
                "Ground the recommendation in current repo artifacts instead of generic ideation.",
                "Preserve the repo-understanding storyline by strengthening `source -> audit -> map -> spec -> contract`.",
                *list(repo_hints.boundaries[:3]),
            ]),
            validation_hints=self._ordered_unique([
                *tests,
                *list(repo_hints.command_hints[:2]),
            ]),
            evidence=evidence,
            contract_seed=SpecContractSeed(
                objective=objective,
                title=f"All-Day Build Contract: {root.name} spec",
                deliverables=deliverables,
                test_requirements=tests,
                map_input=str(map_context.source or map_context.generated_from or root),
            ),
        )

    def _fallback_source_candidate(self, root: Path, audit_result: SourceAuditResult, map_context: MapContext, repo_hints) -> Optional[SpecRecommendation]:
        if not audit_result.used_fallback:
            return None
        objective = "Promote the legacy source into `.agentkit/source.md` so later repo-understanding steps share one canonical planning surface."
        return SpecRecommendation(
            slug="canonicalize-source-surface",
            kind="fallback-hardening",
            score=82,
            title="Canonicalize the source surface before deeper automation",
            objective=objective,
            why_now=[
                "The current spec can proceed from a legacy source file, but the audit marked that path as fallback-only rather than canonical.",
                "Canonical source promotion removes ambiguity for later map, spec, and contract handoffs.",
            ],
            scope_boundaries=self._ordered_unique([
                "Limit the change to source-surface promotion and related deterministic projections.",
                "Do not broaden into unrelated feature work while canonicalizing the source surface.",
                *list(repo_hints.boundaries[:3]),
            ]),
            validation_hints=self._ordered_unique([
                "Run `agentkit source-audit . --json` again and confirm ready-for-contract truth or truthful fallback messaging.",
                *list(repo_hints.command_hints[:2]),
            ]),
            evidence=[
                audit_result.readiness.summary,
                f"Fallback source path: {audit_result.source_path}",
                f"Mapped repo: {map_context.summary.name}",
            ],
            contract_seed=SpecContractSeed(
                objective=objective,
                title=f"All-Day Build Contract: {root.name} canonical source",
                deliverables=[
                    "Promote the best legacy source file into `.agentkit/source.md` without dropping existing instructions.",
                    "Keep projections and downstream repo-understanding steps aligned with the new canonical source.",
                    "Record the resulting canonical-source truth in docs or release surfaces if they mention the old fallback-only path.",
                ],
                test_requirements=[
                    "Re-run `agentkit source-audit . --json` and confirm the fallback warning or blocker disappears truthfully.",
                    "Run the most relevant focused tests for source/project/sync surfaces after the promotion.",
                ],
                map_input=str(map_context.source or map_context.generated_from or root),
            ),
        )

    def _adjacent_grounding_candidate(
        self,
        root: Path,
        source_context: SourceContext,
        audit_result: SourceAuditResult,
        workflow_artifacts: list[SpecWorkflowArtifact],
        map_context: MapContext,
        repo_hints,
    ) -> Optional[SpecRecommendation]:
        objective_summary = self._first_section_text(source_context.content, "objective")
        if not objective_summary:
            return None
        objective_lower = objective_summary.lower()
        if "self-hosted" not in objective_lower and "canonical source" not in objective_lower:
            return None
        if audit_result.used_fallback or not audit_result.readiness.ready_for_contract:
            return None
        if self._has_shipped_adjacent_grounding(workflow_artifacts):
            return None

        shipped_artifact = next(
            (
                artifact
                for artifact in workflow_artifacts
                if artifact.kind in {"build-report", "final-summary", "progress-log"}
                and artifact.status in {"SHIPPED", "RELEASE-READY (LOCAL-ONLY)"}
            ),
            None,
        )
        lane_artifact = next(
            (
                artifact
                for artifact in workflow_artifacts
                if any("source -> audit -> map -> spec -> contract" in lane for lane in artifact.lanes)
            ),
            None,
        )
        if shipped_artifact is None or lane_artifact is None:
            return None

        objective = "Ground `agentkit spec` in current repo truth so the flagship repo recommends the next honest adjacent build instead of recycling already-satisfied source-readiness work."
        evidence = [
            f"Source objective is stale relative to current repo truth: {objective_summary}",
            f"Current readiness already passes canonically: {audit_result.readiness.summary}",
            f"Recent shipped artifacts already document `{lane_artifact.lanes[0]}`.",
        ]
        if shipped_artifact.version:
            evidence.append(f"Latest shipped/local-ready artifact version: {shipped_artifact.version}.")
        return SpecRecommendation(
            slug="adjacent-spec-grounding",
            kind="adjacent-grounding",
            score=91,
            title="Ground spec recommendations in current repo truth",
            objective=objective,
            why_now=[
                "The repo already ships the canonical source and passes `agentkit source-audit` without fallback.",
                "Recent shipped workflow artifacts already show the `source -> audit -> map -> spec -> contract` lane, so re-proposing self-hosting is stale.",
                "The next honest increment is to make `agentkit spec` reason from current shipped evidence instead of repeating a completed prerequisite.",
            ],
            scope_boundaries=self._ordered_unique([
                "Limit the change to spec-planner grounding, recommendation ranking, and the user-visible explanation fields that seed the next contract.",
                "Do not reopen canonical-source or source-audit implementation work that current repo truth already satisfies.",
                *list(repo_hints.boundaries[:3]),
            ]),
            validation_hints=self._ordered_unique([
                "Reproduce the stale recommendation from the current flagship repo truth before changing planner logic.",
                "Add regression coverage for already-satisfied prerequisite suppression plus markdown/JSON explanation output.",
                *list(repo_hints.command_hints[:2]),
            ]),
            evidence=evidence,
            contract_seed=SpecContractSeed(
                objective=objective,
                title=f"All-Day Build Contract: {root.name} spec grounding",
                deliverables=[
                    "Teach the spec planner to ingest current canonical-source readiness and recent shipped workflow evidence before ranking objectives.",
                    "Suppress or down-rank stale prerequisite recommendations that the repo already satisfies locally.",
                    "Emit a concrete adjacent-build explanation and contract seed for the honest next increment instead of a generic subsystem fallback.",
                ],
                test_requirements=[
                    "Run focused spec-engine, spec command, and spec workflow regression tests for the flagship stale-objective case.",
                    *list(repo_hints.command_hints[:2]),
                ],
                map_input=str(map_context.source or map_context.generated_from or root),
            ),
        )

    def _shipped_truth_sync_candidate(
        self,
        root: Path,
        source_context: SourceContext,
        audit_result: SourceAuditResult,
        workflow_artifacts: list[SpecWorkflowArtifact],
        map_context: MapContext,
        repo_hints,
    ) -> Optional[SpecRecommendation]:
        objective_summary = self._first_section_text(source_context.content, "objective")
        if not objective_summary:
            return None
        objective_lower = objective_summary.lower()
        if "self-hosted" not in objective_lower and "canonical source" not in objective_lower:
            return None
        if audit_result.used_fallback or not audit_result.readiness.ready_for_contract:
            return None
        if not self._has_shipped_adjacent_grounding(workflow_artifacts):
            return None

        shipped_artifact = next(
            (
                artifact
                for artifact in workflow_artifacts
                if artifact.kind in {"build-report", "final-summary", "progress-log", "changelog"}
                and artifact.status in {None, "SHIPPED", "RELEASE-READY (LOCAL-ONLY)"}
                and self._artifact_mentions_adjacent_grounding(artifact)
            ),
            None,
        )
        objective = "Refresh the flagship source objective and closeout surfaces so `agentkit spec` starts from current shipped repo truth instead of re-proposing the already-shipped spec-grounding increment."
        evidence = [
            f"Canonical source objective is now behind shipped repo truth: {objective_summary}",
            f"Current readiness already passes canonically: {audit_result.readiness.summary}",
            "Recent shipped/local-ready artifacts already record the adjacent spec-grounding increment as done.",
        ]
        if shipped_artifact is not None and shipped_artifact.version:
            evidence.append(f"Latest shipped/local-ready artifact version carrying that closeout: {shipped_artifact.version}.")
        return SpecRecommendation(
            slug="shipped-truth-sync",
            kind="shipped-truth-sync",
            score=93,
            title="Sync the flagship source objective to shipped spec truth",
            objective=objective,
            why_now=[
                "The repo already ships canonical-source readiness and the adjacent spec-grounding increment, so the old self-hosting objective is doubly stale.",
                "Refreshing the canonical objective and local closeout surfaces is the smallest honest step that prevents `agentkit spec` from recycling the just-shipped recommendation.",
                "Once the source narrative matches shipped truth, the next recommendation can move on to a genuinely new adjacent build.",
            ],
            scope_boundaries=self._ordered_unique([
                "Limit the change to canonical source truth, spec-planner ranking for shipped adjacent work, and the local build/report surfaces that describe the active lane.",
                "Do not reopen the already-shipped canonical-source or adjacent-grounding implementation work.",
                *list(repo_hints.boundaries[:3]),
            ]),
            validation_hints=self._ordered_unique([
                "Reproduce the shipped-adjacent stale recommendation from current flagship repo truth before changing planner logic.",
                "Add regression coverage proving shipped adjacent-grounding evidence suppresses that same recommendation and yields a source-truth-sync follow-up.",
                *list(repo_hints.command_hints[:2]),
            ]),
            evidence=evidence,
            contract_seed=SpecContractSeed(
                objective=objective,
                title=f"All-Day Build Contract: {root.name} shipped truth sync",
                deliverables=[
                    "Teach the spec planner to recognize when adjacent spec grounding is already shipped or release-ready in local workflow artifacts.",
                    "Refresh `.agentkit/source.md` and nearby local closeout/build surfaces so the flagship repo objective matches current shipped repo truth.",
                    "Emit a concrete follow-up recommendation and contract seed that advances from the refreshed source truth instead of reusing the shipped adjacent-grounding step.",
                ],
                test_requirements=[
                    "Run focused spec-engine, spec command, and spec workflow regression tests for the shipped-adjacent stale-objective case.",
                    *list(repo_hints.command_hints[:2]),
                ],
                map_input=str(map_context.source or map_context.generated_from or root),
            ),
        )

    def _flagship_post_closeout_advance_candidate(
        self,
        root: Path,
        source_context: SourceContext,
        audit_result: SourceAuditResult,
        workflow_artifacts: list[SpecWorkflowArtifact],
        map_context: MapContext,
        repo_hints,
    ) -> Optional[SpecRecommendation]:
        objective_summary = self._first_section_text(source_context.content, "objective")
        if not objective_summary:
            return None
        objective_lower = objective_summary.lower()
        has_current_flagship_trigger = (
            "teach the flagship self-spec flow" in objective_lower
            and "concrete adjacent build recommendation" in objective_lower
            and "contract seed" in objective_lower
            and "shipped-truth sync" in objective_lower
        )
        if not has_current_flagship_trigger:
            return None
        if audit_result.used_fallback or not audit_result.readiness.ready_for_contract:
            return None
        flagship_next_artifact = next(
            (
                artifact
                for artifact in workflow_artifacts
                if artifact.status in {"SHIPPED", "RELEASE-READY (LOCAL-ONLY)"}
                and self._artifact_mentions_flagship_concrete_next_step(artifact)
            ),
            None,
        )
        if flagship_next_artifact is None:
            return None

        objective = "Teach the flagship self-spec flow to suppress replay of the closed `flagship-concrete-next-step` lane from the just-shipped v1.27.0 work and advance to one fresh adjacent recommendation with an updated flagship contract seed."
        evidence = [
            f"Canonical source objective still names the already-closed flagship lane: {objective_summary}",
            "Recent shipped/local-ready artifacts already record the `flagship-concrete-next-step` increment as done.",
            "Without replay suppression, the live flagship command path keeps recommending the just-finished concrete-next lane instead of advancing to a fresh adjacent build.",
        ]
        if flagship_next_artifact.version:
            evidence.append(f"Latest shipped/local-ready artifact version carrying that closeout: {flagship_next_artifact.version}.")
        return SpecRecommendation(
            slug="flagship-post-closeout-advance",
            kind="flagship-post-closeout-advance",
            score=90,
            title="Advance the flagship planner past the closed concrete-next-step lane",
            objective=objective,
            why_now=[
                "The flagship repo already completed shipped-truth sync and the concrete-next-step increment, so replaying that same lane is now the main self-spec truth gap.",
                "The next honest increment is planner self-advancement: detect the closed lane, suppress replay, and emit one fresh adjacent flagship recommendation.",
                "Updating the flagship source objective in the same pass keeps repo truth aligned with the new recommendation.",
            ],
            scope_boundaries=self._ordered_unique([
                "Limit the change to spec-planner replay detection, the new flagship recommendation/contract seed, and truthful local source or closeout surfaces.",
                "Do not reopen already-shipped shipped-truth-sync or concrete-next-step implementation work except as evidence for replay suppression.",
                *list(repo_hints.boundaries[:3]),
            ]),
            validation_hints=self._ordered_unique([
                "Reproduce the replay where `agentkit spec . --json` still returns `flagship-concrete-next-step` from current flagship repo truth before changing planner logic.",
                "Add regression coverage for shipped-vs-local-ready concrete-next closeout evidence and the promoted post-closeout recommendation.",
                *list(repo_hints.command_hints[:2]),
            ]),
            evidence=evidence,
            contract_seed=SpecContractSeed(
                objective=objective,
                title=f"All-Day Build Contract: {root.name} flagship post-closeout advance",
                deliverables=[
                    "Detect when the flagship repo has already closed the active `flagship-concrete-next-step` lane through shipped or truthful local-release-ready artifacts.",
                    "Suppress replay of that completed lane and emit one new bounded flagship recommendation with contract-seed detail specific enough to open the next build directly.",
                    "Refresh `.agentkit/source.md` and nearby local closeout surfaces so the active flagship objective no longer names the already-finished concrete-next-step lane.",
                ],
                test_requirements=[
                    "Run focused spec-engine, spec command, spec workflow, and CLI entry regressions for the post-v1.27.0 replay case.",
                    *list(repo_hints.command_hints[:1]),
                ],
                map_input=str(map_context.source or map_context.generated_from or root),
            ),
        )

    def _flagship_concrete_next_candidate(
        self,
        root: Path,
        source_context: SourceContext,
        audit_result: SourceAuditResult,
        workflow_artifacts: list[SpecWorkflowArtifact],
        map_context: MapContext,
        repo_hints,
    ) -> Optional[SpecRecommendation]:
        objective_summary = self._first_section_text(source_context.content, "objective")
        if not objective_summary:
            return None
        objective_lower = objective_summary.lower()
        has_legacy_flagship_trigger = "self-spec truthful" in objective_lower and "shipped repo evidence" in objective_lower
        has_current_flagship_trigger = (
            "teach the flagship self-spec flow" in objective_lower
            and (
                (
                    "concrete adjacent build recommendation" in objective_lower
                    and "contract seed" in objective_lower
                    and "shipped-truth sync" in objective_lower
                )
                or (
                    "suppress replay" in objective_lower
                    and "flagship-concrete-next-step" in objective_lower
                    and (
                        "contract seed" in objective_lower
                        or "updated flagship source truth" in objective_lower
                        or "fresh adjacent recommendation" in objective_lower
                    )
                )
            )
        )
        if not has_legacy_flagship_trigger and not has_current_flagship_trigger:
            return None
        if audit_result.used_fallback or not audit_result.readiness.ready_for_contract:
            return None
        if any(
            artifact.status in {"SHIPPED", "RELEASE-READY (LOCAL-ONLY)"}
            and self._artifact_mentions_flagship_concrete_next_step(artifact)
            for artifact in workflow_artifacts
        ):
            return None
        shipped_truth_artifact = next(
            (
                artifact
                for artifact in workflow_artifacts
                if artifact.status in {"SHIPPED", "RELEASE-READY (LOCAL-ONLY)"}
                and self._artifact_mentions_shipped_truth_sync(artifact)
            ),
            None,
        )
        if shipped_truth_artifact is None:
            return None
        if self._has_completed_flagship_concrete_next_step(workflow_artifacts):
            return None

        objective = "Teach the flagship self-spec flow to emit a concrete adjacent build recommendation and contract seed after shipped-truth sync, instead of falling back to the generic subsystem-next-step recommendation for `agentkit_cli`."
        evidence = [
            f"Canonical source objective already targets post-shipped-truth self-spec behavior: {objective_summary}",
            "Recent shipped/local-ready artifacts already record the shipped-truth-sync increment as done.",
            "Current flagship command-path still falls through to the generic `subsystem-next-step` recommendation instead of naming the next bounded lane.",
        ]
        if shipped_truth_artifact.version:
            evidence.append(f"Latest shipped/local-ready artifact version carrying that closeout: {shipped_truth_artifact.version}.")
        return SpecRecommendation(
            slug="flagship-concrete-next-step",
            kind="flagship-concrete-next-step",
            score=89,
            title="Emit a concrete next flagship lane after shipped-truth sync",
            objective=objective,
            why_now=[
                "The flagship repo already finished canonical-source sync, adjacent grounding, and shipped-truth sync, so the generic subsystem fallback is now the remaining truth gap.",
                "The next honest increment is planner specificity: recommend one bounded adjacent build with enough detail to open the next lane directly.",
                "This keeps the self-spec flow actionable without reopening already-shipped prerequisite work.",
            ],
            scope_boundaries=self._ordered_unique([
                "Limit the change to spec-planner logic, recommendation text, contract seeding, and the nearest regression tests or truthful local surfaces.",
                "Do not reopen the already-shipped canonical-source, adjacent-grounding, or shipped-truth-sync implementation work.",
                *list(repo_hints.boundaries[:3]),
            ]),
            validation_hints=self._ordered_unique([
                "Reproduce the current flagship fallback where `agentkit spec . --json` returns `subsystem-next-step` before changing planner logic.",
                "Add regression coverage across engine, command, and workflow paths for the post-shipped-truth flagship case.",
                *list(repo_hints.command_hints[:2]),
            ]),
            evidence=evidence,
            contract_seed=SpecContractSeed(
                objective=objective,
                title=f"All-Day Build Contract: {root.name} spec concrete next step",
                deliverables=[
                    "Add planner logic that detects when the flagship repo has already completed shipped-truth sync and should advance to a concrete next build recommendation instead of the generic subsystem fallback.",
                    "Emit a concrete recommendation title, objective, why-now reasoning, scope boundaries, and contract seed that are specific enough to open the next lane without human reinterpretation.",
                    "Add or update focused regression coverage for the post-shipped-truth flagship case across engine, command, and workflow paths.",
                ],
                test_requirements=[
                    "Run `uv run python -m pytest -q tests/test_spec_cmd.py tests/test_spec_workflow.py tests/test_main.py`.",
                    *list(repo_hints.command_hints[:1]),
                ],
                map_input=str(map_context.source or map_context.generated_from or root),
            ),
        )

    def _flagship_post_closeout_advance_candidate(
        self,
        root: Path,
        source_context: SourceContext,
        audit_result: SourceAuditResult,
        workflow_artifacts: list[SpecWorkflowArtifact],
        map_context: MapContext,
        repo_hints,
    ) -> Optional[SpecRecommendation]:
        objective_summary = self._first_section_text(source_context.content, "objective")
        if not objective_summary:
            return None
        objective_lower = objective_summary.lower()
        has_current_flagship_trigger = (
            "teach the flagship self-spec flow" in objective_lower
            and (
                (
                    "concrete adjacent build recommendation" in objective_lower
                    and "contract seed" in objective_lower
                    and "shipped-truth sync" in objective_lower
                )
                or (
                    "suppress replay" in objective_lower
                    and "flagship-concrete-next-step" in objective_lower
                    and (
                        "contract seed" in objective_lower
                        or "updated flagship source truth" in objective_lower
                        or "fresh adjacent recommendation" in objective_lower
                    )
                )
            )
        )
        has_replay_suppression_trigger = (
            "detect that the shipped `flagship-concrete-next-step` lane is already complete" in objective_lower
            or "stop recommending the just-shipped v1.27.0 work" in objective_lower
            or "advance to one fresh adjacent recommendation" in objective_lower
            or "suppress replay of the already-completed `flagship-concrete-next-step` lane" in objective_lower
        )
        if not has_current_flagship_trigger and not has_replay_suppression_trigger:
            return None
        if audit_result.used_fallback or not audit_result.readiness.ready_for_contract:
            return None
        if not self._has_completed_flagship_concrete_next_step(workflow_artifacts):
            return None

        completed_artifact = next(
            (
                artifact
                for artifact in workflow_artifacts
                if self._artifact_closes_flagship_concrete_next_step(artifact)
            ),
            None,
        )
        objective = "Teach the flagship self-spec flow to suppress replay of the closed `flagship-concrete-next-step` lane from the just-shipped v1.27.0 work and advance to one fresh adjacent recommendation with an updated flagship contract seed."
        evidence = [
            f"Canonical source objective is still anchored in the already-completed flagship-next-step lane: {objective_summary}",
            "Recent shipped/local-ready artifacts already record the `flagship-concrete-next-step` increment as done.",
            "The planner must now suppress replay of that shipped lane and advance to one fresh adjacent flagship recommendation.",
        ]
        if completed_artifact is not None and completed_artifact.version:
            evidence.append(f"Latest shipped/local-ready artifact carrying the closed lane: {completed_artifact.version}.")
        return SpecRecommendation(
            slug="flagship-post-closeout-advance",
            kind="flagship-post-closeout-advance",
            score=92,
            title="Advance the flagship planner past the closed concrete-next-step lane",
            objective=objective,
            why_now=[
                "The flagship repo already shipped or reached local release-ready truth for `flagship-concrete-next-step`, so replaying that lane is now stale.",
                "The next honest increment is replay suppression plus one fresh adjacent recommendation and contract seed.",
                "This keeps the self-spec flow truthful and actionable after local closeout surfaces move ahead of the old objective.",
            ],
            scope_boundaries=self._ordered_unique([
                "Limit the change to replay detection, recommendation ranking, contract seed advancement, and the nearest truthful local surfaces.",
                "Do not reopen the already-completed `flagship-concrete-next-step` implementation lane.",
                *list(repo_hints.boundaries[:3]),
            ]),
            validation_hints=self._ordered_unique([
                "Prove the current repo truth already includes shipped or local release-ready evidence for `flagship-concrete-next-step`.",
                "Add regression coverage showing that replay is suppressed and a fresh adjacent recommendation wins deterministically.",
                *list(repo_hints.command_hints[:2]),
            ]),
            evidence=evidence,
            contract_seed=SpecContractSeed(
                objective=objective,
                title=f"All-Day Build Contract: {root.name} flagship post-closeout advance",
                deliverables=[
                    "Detect when the active `flagship-concrete-next-step` lane is already shipped or truthfully local release-ready in current repo artifacts.",
                    "Suppress replay of the closed lane and emit one fresh adjacent flagship recommendation with concrete why-now, scope, and validation fields.",
                    "Refresh the flagship source objective and local closeout surfaces so they name the new adjacent lane truthfully.",
                ],
                test_requirements=[
                    "Run focused spec-engine, spec command, and spec workflow regressions for the post-closeout replay case.",
                    *list(repo_hints.command_hints[:1]),
                ],
                map_input=str(map_context.source or map_context.generated_from or root),
            ),
        )

    def _coverage_candidate(self, root: Path, map_context: MapContext, repo_hints) -> Optional[SpecRecommendation]:
        risks = list(map_context.hints) + ([] if map_context.summary is None else [])
        risk = next((item for item in map_context.hints if item.kind == "risk"), None)
        if risk is None:
            risk = next((item for item in map_context.hints if item.severity == "warn"), None)
        if risk is None:
            return None
        area = self._area_from_risk(risk.title) or (map_context.subsystems[0].path if map_context.subsystems else root.name)
        objective = f"Tighten deterministic validation around `{area}` before the next broader workflow increment."
        return SpecRecommendation(
            slug=f"coverage-{self._slug(area)}",
            kind="coverage-gap",
            score=70,
            title=f"Close the validation gap around {area}",
            objective=objective,
            why_now=[
                risk.detail,
                "The repo map already surfaced this as a concrete gap, so tightening validation is a bounded next move rather than generic cleanup.",
            ],
            scope_boundaries=self._ordered_unique([
                f"Work in or directly adjacent to `{area}` only.",
                "Add validation without broad unrelated refactors.",
                *list(repo_hints.boundaries[:3]),
            ]),
            validation_hints=self._ordered_unique([
                "Add focused tests for the affected area and keep the recommendation reproducible from the same repo map.",
                *list(repo_hints.command_hints[:2]),
            ]),
            evidence=[risk.title, risk.detail],
            contract_seed=SpecContractSeed(
                objective=objective,
                title=f"All-Day Build Contract: {root.name} validation gap",
                deliverables=[
                    f"Add or tighten deterministic tests around `{area}`.",
                    "Document the validation boundary and any remaining known risk explicitly.",
                    "Keep the rest of the repo state untouched unless the validation work requires a narrowly-scoped companion edit.",
                ],
                test_requirements=[
                    f"Run focused tests covering `{area}`.",
                    "Re-run the smallest release-confidence slice that exercises the touched area.",
                ],
                map_input=str(map_context.source or map_context.generated_from or root),
            ),
        )

    def _subsystem_candidate(self, root: Path, source_context: SourceContext, map_context: MapContext, repo_hints) -> Optional[SpecRecommendation]:
        primary_area = map_context.subsystems[0].path if map_context.subsystems else root.name
        subsystem_name = map_context.subsystems[0].name if map_context.subsystems else root.name
        objective_summary = self._first_section_text(source_context.content, "objective") or f"Advance the next scoped increment for {root.name}."
        objective = f"Advance the next scoped increment in `{primary_area}` to support: {objective_summary}"
        evidence = [
            f"Primary mapped subsystem: {subsystem_name} ({primary_area})",
        ]
        if map_context.contract_handoff and map_context.contract_handoff.summary_lines:
            evidence.extend(map_context.contract_handoff.summary_lines[:2])
        return SpecRecommendation(
            slug=f"subsystem-{self._slug(primary_area)}",
            kind="subsystem-next-step",
            score=58,
            title=f"Use {primary_area} as the next scoped build surface",
            objective=objective,
            why_now=[
                "The repo map already points at this subsystem as the primary implementation surface.",
                "This keeps the next increment bounded while still advancing the source-stated objective.",
            ],
            scope_boundaries=self._ordered_unique([
                f"Center the work in `{primary_area}` and its nearest tests.",
                "Keep status and release surfaces truthful if the build changes public repo guidance.",
                *list(repo_hints.boundaries[:3]),
            ]),
            validation_hints=self._ordered_unique([
                *list(repo_hints.command_hints[:2]),
                "Use the mapped subsystem tests and scripts before broadening to full-suite validation.",
            ]),
            evidence=evidence,
            contract_seed=SpecContractSeed(
                objective=objective,
                title=f"All-Day Build Contract: {root.name} {self._slug(primary_area)}",
                deliverables=self._ordered_unique([
                    f"Implement the next scoped increment in `{primary_area}`.",
                    "Add or update focused tests for the touched behavior.",
                    "Update the nearest docs or status surfaces if the behavior change alters the supported workflow.",
                ]),
                test_requirements=self._ordered_unique([
                    "Run focused tests for the touched subsystem.",
                    *list(repo_hints.command_hints[:1]),
                ]),
                map_input=str(map_context.source or map_context.generated_from or root),
            ),
        )

    def _workflow_artifacts(self, root: Path) -> list[SpecWorkflowArtifact]:
        artifacts: list[SpecWorkflowArtifact] = []
        for relative_path, kind in _WORKFLOW_ARTIFACTS:
            path = root / relative_path
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            artifacts.append(
                SpecWorkflowArtifact(
                    path=relative_path,
                    kind=kind,
                    status=self._extract_status(text),
                    version=self._extract_version(text),
                    lanes=self._extract_lanes(text),
                    evidence=lines[:12],
                )
            )
        return artifacts

    def _has_spec_command(self, root: Path) -> bool:
        main_py = root / "agentkit_cli" / "main.py"
        if not main_py.exists():
            return False
        text = main_py.read_text(encoding="utf-8", errors="replace")
        return '@app.command("spec")' in text or "from agentkit_cli.commands.spec_cmd import spec_command" in text

    def _extract_status(self, text: str) -> Optional[str]:
        match = re.search(r"^Status:\s*(.+)$", text, re.MULTILINE)
        return match.group(1).strip() if match else None

    def _extract_version(self, text: str) -> Optional[str]:
        patterns = [
            r"## \[(\d+\.\d+\.\d+)\]",
            r"v(\d+\.\d+\.\d+)",
            r'version\s*=\s*"(\d+\.\d+\.\d+)"',
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return None

    def _extract_lanes(self, text: str) -> list[str]:
        lanes: list[str] = []
        for match in re.finditer(r"([`']?[a-z0-9.-]+(?:\s*->\s*[a-z0-9.-]+)+[`']?)", text, re.IGNORECASE):
            lane = match.group(1).strip("`'")
            normalized = self._normalize_lane(lane)
            if normalized.count("->") >= 1:
                lanes.append(normalized)
        return self._ordered_unique(lanes)

    def _artifact_mentions_adjacent_grounding(self, artifact: SpecWorkflowArtifact) -> bool:
        haystacks = [artifact.path, artifact.kind, artifact.status or "", artifact.version or "", *artifact.evidence, *artifact.lanes]
        joined = "\n".join(haystacks).lower()
        return "adjacent-grounding" in joined or "spec grounding" in joined

    def _artifact_mentions_shipped_truth_sync(self, artifact: SpecWorkflowArtifact) -> bool:
        haystacks = [artifact.path, artifact.kind, artifact.status or "", artifact.version or "", *artifact.evidence, *artifact.lanes]
        joined = "\n".join(haystacks).lower()
        return "shipped truth sync" in joined or "shipped-truth-sync" in joined

    def _artifact_mentions_flagship_concrete_next_step(self, artifact: SpecWorkflowArtifact) -> bool:
        haystacks = [artifact.path, artifact.kind, artifact.status or "", artifact.version or "", *artifact.evidence, *artifact.lanes]
        joined = "\n".join(haystacks).lower()
        return "flagship-concrete-next-step" in joined or "concrete next lane after shipped-truth sync" in joined or "spec concrete next step" in joined

    def _has_shipped_adjacent_grounding(self, workflow_artifacts: list[SpecWorkflowArtifact]) -> bool:
        return any(
            artifact.status in {"SHIPPED", "RELEASE-READY (LOCAL-ONLY)"}
            and self._artifact_mentions_adjacent_grounding(artifact)
            for artifact in workflow_artifacts
        )

    def _artifact_closes_flagship_concrete_next_step(self, artifact: SpecWorkflowArtifact) -> bool:
        if not self._artifact_mentions_flagship_concrete_next_step(artifact):
            return False
        return artifact.status in {"SHIPPED", "RELEASE-READY (LOCAL-ONLY)"} or artifact.kind == "changelog"

    def _has_completed_flagship_concrete_next_step(self, workflow_artifacts: list[SpecWorkflowArtifact]) -> bool:
        return any(
            self._artifact_closes_flagship_concrete_next_step(artifact)
            for artifact in workflow_artifacts
        )

    def _normalize_lane(self, lane: str) -> str:
        parts = [part.strip().lower() for part in lane.split("->")]
        normalized = ["audit" if part == "source-audit" else part for part in parts if part.strip()]
        return " -> ".join(normalized)

    def _first_section_text(self, text: str, heading: str) -> str:
        pattern = re.compile(rf"^##\s+{re.escape(heading)}\s*$", re.IGNORECASE | re.MULTILINE)
        match = pattern.search(text)
        if not match:
            return ""
        start = match.end()
        tail = text[start:]
        next_heading = re.search(r"^##\s+", tail, re.MULTILINE)
        body = tail[: next_heading.start()] if next_heading else tail
        lines = [line.strip() for line in body.splitlines() if line.strip()]
        return lines[0] if lines else ""

    def _area_from_risk(self, title: str) -> str:
        match = re.search(r"near\s+([A-Za-z0-9_./-]+)$", title)
        if match:
            return match.group(1)
        if title.lower() == "no tests detected":
            return "repo"
        return ""

    def _slug(self, value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "spec"

    def _ordered_unique(self, values) -> list[str]:
        seen: set[str] = set()
        ordered: list[str] = []
        for value in values:
            if not value:
                continue
            if value not in seen:
                seen.add(value)
                ordered.append(value)
        return ordered
