"""Framework detection and agent context coverage checker for agentkit."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

CONTEXT_FILENAMES = ["CLAUDE.md", "AGENTS.md", "claude.md", "agents.md"]

# Required and nice-to-have checks per framework
FRAMEWORK_CHECKS: dict[str, dict[str, list[str]]] = {
    "Next.js": {
        "required": ["setup", "common patterns", "known gotchas"],
        "nice_to_have": ["testing patterns", "deploy patterns"],
    },
    "FastAPI": {
        "required": ["setup", "common patterns", "known gotchas"],
        "nice_to_have": ["testing patterns", "deploy patterns"],
    },
    "Django": {
        "required": ["setup", "common patterns", "known gotchas"],
        "nice_to_have": ["testing patterns", "deploy patterns"],
    },
    "Rails": {
        "required": ["setup", "common patterns", "known gotchas"],
        "nice_to_have": ["testing patterns", "deploy patterns"],
    },
    "React": {
        "required": ["setup", "common patterns", "known gotchas"],
        "nice_to_have": ["testing patterns", "deploy patterns"],
    },
    "Vue": {
        "required": ["setup", "common patterns", "known gotchas"],
        "nice_to_have": ["testing patterns", "deploy patterns"],
    },
    "Nuxt": {
        "required": ["setup", "common patterns", "known gotchas"],
        "nice_to_have": ["testing patterns", "deploy patterns"],
    },
    "Flask": {
        "required": ["setup", "common patterns", "known gotchas"],
        "nice_to_have": ["testing patterns", "deploy patterns"],
    },
    "Laravel": {
        "required": ["setup", "common patterns", "known gotchas"],
        "nice_to_have": ["testing patterns", "deploy patterns"],
    },
    "Express": {
        "required": ["setup", "common patterns", "known gotchas"],
        "nice_to_have": ["testing patterns", "deploy patterns"],
    },
}


@dataclass
class DetectedFramework:
    name: str
    version_hint: Optional[str]
    confidence: str  # high / medium / low
    detection_files: list[str]


@dataclass
class FrameworkCoverage:
    framework: str
    score: int  # 0-100
    missing_required: list[str]
    missing_nice_to_have: list[str]
    suggestions: list[str]


def _read_json_file(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


def _read_text_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def _package_json_has(pkg: dict, dep_name: str) -> Optional[str]:
    """Check all dependency sections in package.json for dep_name. Returns version hint or None."""
    for section in ("dependencies", "devDependencies", "peerDependencies"):
        deps = pkg.get(section, {})
        if dep_name in deps:
            return str(deps[dep_name])
    return None


class FrameworkDetector:
    """Detect which frameworks are used in a project directory."""

    def detect(self, root: Path) -> list[DetectedFramework]:
        results: list[DetectedFramework] = []
        root = Path(root)

        pkg_path = root / "package.json"
        pkg: dict = _read_json_file(pkg_path) if pkg_path.exists() else {}
        pkg_exists = pkg_path.exists()

        # --- Next.js ---
        next_config = (root / "next.config.js").exists() or (root / "next.config.ts").exists()
        next_dep = _package_json_has(pkg, "next") if pkg_exists else None
        if next_config or next_dep is not None:
            detection_files = []
            if next_config:
                if (root / "next.config.js").exists():
                    detection_files.append("next.config.js")
                if (root / "next.config.ts").exists():
                    detection_files.append("next.config.ts")
            if pkg_exists and next_dep is not None:
                detection_files.append("package.json")
            confidence = "high" if (next_config and next_dep is not None) else ("high" if next_config else "medium")
            results.append(DetectedFramework(
                name="Next.js",
                version_hint=next_dep,
                confidence=confidence,
                detection_files=detection_files,
            ))

        # --- Nuxt (before Vue so we don't double-add) ---
        nuxt_config = (root / "nuxt.config.ts").exists() or (root / "nuxt.config.js").exists()
        nuxt_dep = _package_json_has(pkg, "nuxt") if pkg_exists else None
        if nuxt_config or nuxt_dep is not None:
            detection_files = []
            if (root / "nuxt.config.ts").exists():
                detection_files.append("nuxt.config.ts")
            if (root / "nuxt.config.js").exists():
                detection_files.append("nuxt.config.js")
            if pkg_exists and nuxt_dep is not None:
                detection_files.append("package.json")
            results.append(DetectedFramework(
                name="Nuxt",
                version_hint=nuxt_dep,
                confidence="high" if nuxt_config else "medium",
                detection_files=detection_files,
            ))

        # --- React (not Next.js, not Nuxt) ---
        react_dep = _package_json_has(pkg, "react") if pkg_exists else None
        already_nextjs = any(f.name == "Next.js" for f in results)
        already_nuxt = any(f.name == "Nuxt" for f in results)
        if react_dep is not None and not already_nextjs and not already_nuxt:
            results.append(DetectedFramework(
                name="React",
                version_hint=react_dep,
                confidence="high",
                detection_files=["package.json"],
            ))

        # --- Vue (not Nuxt) ---
        vue_dep = _package_json_has(pkg, "vue") if pkg_exists else None
        if vue_dep is not None and not already_nuxt:
            results.append(DetectedFramework(
                name="Vue",
                version_hint=vue_dep,
                confidence="high",
                detection_files=["package.json"],
            ))

        # --- Express ---
        express_dep = _package_json_has(pkg, "express") if pkg_exists else None
        if express_dep is not None:
            results.append(DetectedFramework(
                name="Express",
                version_hint=express_dep,
                confidence="high",
                detection_files=["package.json"],
            ))

        # --- Python frameworks ---
        req_txt_content = ""
        req_txt_path = root / "requirements.txt"
        if req_txt_path.exists():
            req_txt_content = _read_text_file(req_txt_path).lower()

        pyproject_path = root / "pyproject.toml"
        pyproject_content = ""
        if pyproject_path.exists():
            pyproject_content = _read_text_file(pyproject_path).lower()

        def _python_dep_version(dep_lower: str) -> Optional[str]:
            """Search requirements.txt / pyproject.toml for a dep name, return version hint."""
            for line in req_txt_content.splitlines():
                line = line.strip()
                if line.lower().startswith(dep_lower):
                    return line
            # pyproject.toml search
            for line in pyproject_content.splitlines():
                line = line.strip().strip('"').strip("'").strip(",")
                if dep_lower in line.lower():
                    return line
            return None

        # FastAPI
        fastapi_req = _python_dep_version("fastapi")
        if fastapi_req is not None or "fastapi" in pyproject_content:
            detection_files = []
            if req_txt_path.exists() and "fastapi" in req_txt_content:
                detection_files.append("requirements.txt")
            if pyproject_path.exists() and "fastapi" in pyproject_content:
                detection_files.append("pyproject.toml")
            if detection_files:
                results.append(DetectedFramework(
                    name="FastAPI",
                    version_hint=fastapi_req,
                    confidence="high",
                    detection_files=detection_files,
                ))

        # Django
        django_in_req = "django" in req_txt_content
        manage_py = (root / "manage.py").exists()
        settings_py = (root / "settings.py").exists()
        django_in_pyproject = "django" in pyproject_content
        if django_in_req or manage_py or settings_py or django_in_pyproject:
            detection_files = []
            if manage_py:
                detection_files.append("manage.py")
            if settings_py:
                detection_files.append("settings.py")
            if req_txt_path.exists() and django_in_req:
                detection_files.append("requirements.txt")
            if pyproject_path.exists() and django_in_pyproject:
                detection_files.append("pyproject.toml")
            confidence = "high" if (manage_py or settings_py) else "medium"
            results.append(DetectedFramework(
                name="Django",
                version_hint=_python_dep_version("django"),
                confidence=confidence,
                detection_files=detection_files,
            ))

        # Flask
        flask_in_req = "flask" in req_txt_content
        flask_in_pyproject = "flask" in pyproject_content
        if flask_in_req or flask_in_pyproject:
            detection_files = []
            if req_txt_path.exists() and flask_in_req:
                detection_files.append("requirements.txt")
            if pyproject_path.exists() and flask_in_pyproject:
                detection_files.append("pyproject.toml")
            results.append(DetectedFramework(
                name="Flask",
                version_hint=_python_dep_version("flask"),
                confidence="high",
                detection_files=detection_files,
            ))

        # Rails
        gemfile_path = root / "Gemfile"
        if gemfile_path.exists():
            gemfile_content = _read_text_file(gemfile_path).lower()
            if "rails" in gemfile_content:
                results.append(DetectedFramework(
                    name="Rails",
                    version_hint=None,
                    confidence="high",
                    detection_files=["Gemfile"],
                ))

        # Laravel
        composer_path = root / "composer.json"
        if composer_path.exists():
            composer = _read_json_file(composer_path)
            require_section = composer.get("require", {})
            if "laravel/framework" in require_section:
                results.append(DetectedFramework(
                    name="Laravel",
                    version_hint=str(require_section["laravel/framework"]),
                    confidence="high",
                    detection_files=["composer.json"],
                ))

        return results


class FrameworkChecker:
    """Check whether agent context files cover detected frameworks."""

    def find_context_file(self, root: Path) -> Optional[Path]:
        for name in CONTEXT_FILENAMES:
            p = root / name
            if p.exists():
                return p
        return None

    def check(self, framework: DetectedFramework, context_file: Optional[Path]) -> FrameworkCoverage:
        checks = FRAMEWORK_CHECKS.get(framework.name, {
            "required": ["setup", "common patterns", "known gotchas"],
            "nice_to_have": ["testing patterns", "deploy patterns"],
        })
        required = checks["required"]
        nice_to_have = checks["nice_to_have"]

        if context_file is None or not context_file.exists():
            return FrameworkCoverage(
                framework=framework.name,
                score=0,
                missing_required=list(required),
                missing_nice_to_have=list(nice_to_have),
                suggestions=[
                    f"Create CLAUDE.md or AGENTS.md with a '{framework.name}' section.",
                    f"Add: setup instructions, common patterns, known gotchas for {framework.name}.",
                ],
            )

        content = _read_text_file(context_file).lower()
        fw_lower = framework.name.lower()

        # Check framework name is mentioned
        name_mentioned = fw_lower in content
        if not name_mentioned:
            # For Next.js also check "next.js" / "nextjs"
            alt_names = {
                "next.js": ["nextjs", "next js"],
                "fastapi": ["fast api"],
                "express": ["expressjs", "express.js"],
            }
            alts = alt_names.get(fw_lower, [])
            name_mentioned = any(alt in content for alt in alts)

        if not name_mentioned:
            return FrameworkCoverage(
                framework=framework.name,
                score=0,
                missing_required=list(required),
                missing_nice_to_have=list(nice_to_have),
                suggestions=[f"Add a section mentioning {framework.name} to your agent context file."],
            )

        missing_required = []
        missing_nice = []

        def _has_coverage(keyword: str) -> bool:
            return keyword.lower() in content

        for req in required:
            if not _has_coverage(req):
                missing_required.append(req)

        for nice in nice_to_have:
            if not _has_coverage(nice):
                missing_nice.append(nice)

        n_req = len(required)
        n_req_hit = n_req - len(missing_required)
        n_nice = len(nice_to_have)
        n_nice_hit = n_nice - len(missing_nice)

        required_score = (n_req_hit / n_req * 80) if n_req > 0 else 80
        nice_score = (n_nice_hit / n_nice * 20) if n_nice > 0 else 20
        score = round(required_score + nice_score)

        suggestions = []
        if missing_required:
            suggestions.append(
                f"Add required sections for {framework.name}: {', '.join(missing_required)}."
            )
        if missing_nice:
            suggestions.append(
                f"Consider adding: {', '.join(missing_nice)} for {framework.name}."
            )

        return FrameworkCoverage(
            framework=framework.name,
            score=score,
            missing_required=missing_required,
            missing_nice_to_have=missing_nice,
            suggestions=suggestions,
        )

    def check_all(
        self,
        frameworks: list[DetectedFramework],
        root: Path,
        context_file: Optional[Path] = None,
    ) -> list[FrameworkCoverage]:
        if context_file is None:
            context_file = self.find_context_file(root)
        return [self.check(fw, context_file) for fw in frameworks]
