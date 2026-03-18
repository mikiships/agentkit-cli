"""agentkit llmstxt — generate llms.txt and llms-full.txt for any repository."""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# Maximum file size (bytes) to include inline in llms-full.txt
_MAX_INLINE_BYTES = 100 * 1024  # 100 KB

# Patterns for docs directories
_DOCS_DIRS = ("docs", "doc", "documentation", "wiki")
_EXAMPLES_DIRS = ("examples", "example", "samples", "demo", "demos", "tutorials")
_AGENT_CTX_FILES = ("CLAUDE.md", "AGENTS.md", "COPILOT.md", ".cursorrules", "GEMINI.md")
_README_PATTERNS = ("README.md", "README.rst", "README.txt", "README", "readme.md")
_CHANGELOG_PATTERNS = ("CHANGELOG.md", "CHANGELOG.rst", "CHANGELOG", "CHANGES.md", "HISTORY.md")


@dataclass
class DocFile:
    path: str  # relative path from repo root
    title: str
    description: str = ""
    size: int = 0


@dataclass
class RepoInfo:
    root: str
    project_name: str
    readme_path: Optional[str] = None
    changelog_path: Optional[str] = None
    docs_files: list[DocFile] = field(default_factory=list)
    examples_files: list[DocFile] = field(default_factory=list)
    api_files: list[DocFile] = field(default_factory=list)
    agent_context_files: list[DocFile] = field(default_factory=list)
    description: str = ""
    version: str = ""


def _title_from_filename(path: str) -> str:
    """Convert a file path to a human-readable title."""
    name = Path(path).stem.replace("_", " ").replace("-", " ")
    return name.title()


def _extract_description(readme_path: Optional[str], root: str) -> str:
    """Extract first meaningful paragraph from README."""
    if not readme_path:
        return ""
    full = Path(root) / readme_path
    try:
        text = full.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    lines = text.splitlines()
    paragraph: list[str] = []
    in_paragraph = False
    for line in lines:
        stripped = line.strip()
        # Skip headings, badges, empty lines before paragraph
        if stripped.startswith("#"):
            if paragraph:
                break
            continue
        if stripped.startswith("[![") or stripped.startswith("!["):
            continue
        if stripped.startswith("---") or stripped.startswith("==="):
            continue
        if stripped:
            in_paragraph = True
            paragraph.append(stripped)
        elif in_paragraph:
            break
    return " ".join(paragraph)[:500].strip()


def _extract_version(root: str) -> str:
    """Best-effort version extraction from pyproject.toml, package.json, or setup.py."""
    for candidate in ("pyproject.toml", "package.json", "setup.cfg"):
        p = Path(root) / candidate
        if p.exists():
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
                m = re.search(r'version\s*[=:]\s*["\']([^"\']+)["\']', text)
                if m:
                    return m.group(1)
            except OSError:
                pass
    return ""


def _walk_docs_dir(root: str, dir_name: str, max_files: int = 20) -> list[DocFile]:
    """Walk a docs/examples directory and return DocFile entries."""
    docs: list[DocFile] = []
    base = Path(root) / dir_name
    if not base.is_dir():
        return docs
    for p in sorted(base.rglob("*")):
        if not p.is_file():
            continue
        if p.suffix.lower() not in (".md", ".rst", ".txt", ".html"):
            continue
        rel = str(p.relative_to(root))
        title = _title_from_filename(rel)
        docs.append(DocFile(path=rel, title=title, size=p.stat().st_size))
        if len(docs) >= max_files:
            break
    return docs


def _find_api_files(root: str, project_name: str) -> list[DocFile]:
    """Find Python package __init__.py or main module as the API surface."""
    api: list[DocFile] = []
    candidates = [
        Path(root) / project_name / "__init__.py",
        Path(root) / project_name.replace("-", "_") / "__init__.py",
        Path(root) / "src" / project_name / "__init__.py",
        Path(root) / "api.py",
        Path(root) / "api" / "__init__.py",
    ]
    for c in candidates:
        if c.is_file():
            rel = str(c.relative_to(root))
            api.append(DocFile(path=rel, title=f"{project_name} API", size=c.stat().st_size))
            break
    return api


class LlmsTxtGenerator:
    """Generate llms.txt and llms-full.txt for a repository."""

    def scan_repo(self, path: str) -> RepoInfo:
        """Scan a repository path and collect metadata."""
        root = str(Path(path).resolve())
        project_name = Path(root).name

        # Find README
        readme_path: Optional[str] = None
        for pat in _README_PATTERNS:
            p = Path(root) / pat
            if p.exists():
                readme_path = pat
                break

        # Find CHANGELOG
        changelog_path: Optional[str] = None
        for pat in _CHANGELOG_PATTERNS:
            p = Path(root) / pat
            if p.exists():
                changelog_path = pat
                break

        # Docs files
        docs_files: list[DocFile] = []
        for d in _DOCS_DIRS:
            found = _walk_docs_dir(root, d)
            if found:
                docs_files = found
                break

        # Examples files
        examples_files: list[DocFile] = []
        for d in _EXAMPLES_DIRS:
            found = _walk_docs_dir(root, d)
            if found:
                examples_files = found
                break

        # API files
        api_files = _find_api_files(root, project_name)

        # Agent context files
        agent_context_files: list[DocFile] = []
        for f in _AGENT_CTX_FILES:
            p = Path(root) / f
            if p.exists():
                agent_context_files.append(DocFile(path=f, title=f, size=p.stat().st_size))

        description = _extract_description(readme_path, root)
        version = _extract_version(root)

        return RepoInfo(
            root=root,
            project_name=project_name,
            readme_path=readme_path,
            changelog_path=changelog_path,
            docs_files=docs_files,
            examples_files=examples_files,
            api_files=api_files,
            agent_context_files=agent_context_files,
            description=description,
            version=version,
        )

    def generate_llms_txt(self, repo_info: RepoInfo) -> str:
        """Generate standard llms.txt following the spec."""
        lines: list[str] = []

        # H1 title
        title = repo_info.project_name
        if repo_info.version:
            title += f" v{repo_info.version}"
        lines.append(f"# {title}")
        lines.append("")

        # Blockquote summary
        desc = repo_info.description or f"{repo_info.project_name} project."
        lines.append(f"> {desc}")
        lines.append("")

        # Docs section
        if repo_info.readme_path or repo_info.docs_files or repo_info.changelog_path:
            lines.append("## Docs")
            lines.append("")
            if repo_info.readme_path:
                lines.append(f"- [{_title_from_filename(repo_info.readme_path)}]({repo_info.readme_path}): Project overview and getting started guide.")
            if repo_info.changelog_path:
                lines.append(f"- [{_title_from_filename(repo_info.changelog_path)}]({repo_info.changelog_path}): Version history and release notes.")
            for df in repo_info.docs_files[:10]:
                lines.append(f"- [{df.title}]({df.path})")
            lines.append("")

        # API section
        if repo_info.api_files:
            lines.append("## API")
            lines.append("")
            for df in repo_info.api_files:
                lines.append(f"- [{df.title}]({df.path}): Main API module.")
            lines.append("")

        # Examples section
        if repo_info.examples_files:
            lines.append("## Examples")
            lines.append("")
            for df in repo_info.examples_files[:10]:
                lines.append(f"- [{df.title}]({df.path})")
            lines.append("")

        # Agent Context section
        if repo_info.agent_context_files:
            lines.append("## Agent Context")
            lines.append("")
            for df in repo_info.agent_context_files:
                lines.append(f"- [{df.title}]({df.path}): Agent/AI context file.")
            lines.append("")

        return "\n".join(lines).rstrip() + "\n"

    def generate_llms_full_txt(self, repo_info: RepoInfo) -> str:
        """Generate llms-full.txt with inline content of all referenced files."""
        header = self.generate_llms_txt(repo_info)
        sections: list[str] = [header, "---\n"]

        all_files: list[DocFile] = []
        if repo_info.readme_path:
            all_files.append(DocFile(path=repo_info.readme_path, title="README"))
        if repo_info.changelog_path:
            all_files.append(DocFile(path=repo_info.changelog_path, title="CHANGELOG"))
        all_files.extend(repo_info.docs_files)
        all_files.extend(repo_info.api_files)
        all_files.extend(repo_info.examples_files)
        all_files.extend(repo_info.agent_context_files)

        for df in all_files:
            full_path = Path(repo_info.root) / df.path
            try:
                size = full_path.stat().st_size
                if size > _MAX_INLINE_BYTES:
                    sections.append(f"## {df.path}\n\n[File too large to inline ({size} bytes)]\n")
                    continue
                content = full_path.read_text(encoding="utf-8", errors="replace")
                sections.append(f"## {df.path}\n\n{content.rstrip()}\n")
            except OSError:
                sections.append(f"## {df.path}\n\n[Could not read file]\n")

        return "\n".join(sections)


def validate_llms_txt(content: str) -> list[dict]:
    """Validate an llms.txt string against the spec. Returns list of check dicts."""
    checks: list[dict] = []
    lines = content.splitlines()

    # Check 1: H1 title
    has_h1 = any(line.startswith("# ") for line in lines)
    checks.append({
        "check": "Has H1 title",
        "passed": has_h1,
        "suggestion": "Add a line starting with '# ProjectName' at the top.",
    })

    # Check 2: Blockquote summary
    has_blockquote = any(line.startswith("> ") for line in lines)
    checks.append({
        "check": "Has blockquote summary",
        "passed": has_blockquote,
        "suggestion": "Add a line starting with '> ' immediately after the title.",
    })

    # Check 3: At least 2 sections (##)
    sections = [l for l in lines if l.startswith("## ")]
    has_sections = len(sections) >= 2
    checks.append({
        "check": "Has ≥2 sections",
        "passed": has_sections,
        "suggestion": f"Add more '## Section' headings. Found: {len(sections)}.",
    })

    # Check 4: At least 3 links
    link_count = len(re.findall(r"\[.+?\]\(.+?\)", content))
    has_links = link_count >= 3
    checks.append({
        "check": "Has ≥3 links",
        "passed": has_links,
        "suggestion": f"Add more markdown links. Found: {link_count}.",
    })

    # Check 5: No obviously broken relative paths
    broken: list[str] = []
    for m in re.finditer(r"\[.+?\]\(([^)]+)\)", content):
        link = m.group(1)
        if link.startswith(("http://", "https://", "#")):
            continue
        # Relative path — we can't check without root, just flag obvious issues
        if link.startswith("/"):
            broken.append(link)
    checks.append({
        "check": "No absolute paths",
        "passed": len(broken) == 0,
        "suggestion": f"Use relative paths instead of absolute: {broken}" if broken else "",
    })

    return checks


def score_llms_txt(content: str) -> int:
    """Score an llms.txt string 0-100."""
    score = 0
    lines = content.splitlines()

    # Has title (20pts)
    if any(line.startswith("# ") for line in lines):
        score += 20

    # Has summary (20pts)
    if any(line.startswith("> ") for line in lines):
        score += 20

    # Has ≥2 sections (20pts)
    sections = [l for l in lines if l.startswith("## ")]
    if len(sections) >= 2:
        score += 20

    # Has ≥3 links (20pts)
    if len(re.findall(r"\[.+?\]\(.+?\)", content)) >= 3:
        score += 20

    # No broken relative paths starting with / (20pts)
    broken = [m.group(1) for m in re.finditer(r"\[.+?\]\(([^)]+)\)", content)
              if not m.group(1).startswith(("http://", "https://", "#")) and m.group(1).startswith("/")]
    if not broken:
        score += 20

    return score
