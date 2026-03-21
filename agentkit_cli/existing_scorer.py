"""agentkit ExistingStateScorer — measures repo documentation quality without generation.

Scores repos based on observable, already-present artifacts:
- Agent-context files (CLAUDE.md, AGENTS.md, llms.txt)
- README quality (length, sections, code examples, install instructions)
- CONTRIBUTING.md presence
- CHANGELOG/HISTORY presence
- CI config presence
- Test coverage (tests/ directory + rough count)
- Type annotations (py.typed marker or .pyi stubs)
- Docs site link in README or pyproject.toml
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Scoring weights
# ---------------------------------------------------------------------------

DIMENSION_WEIGHTS: dict[str, float] = {
    "agent_context": 0.30,   # CLAUDE.md, AGENTS.md, llms.txt
    "readme_quality": 0.25,  # README thoroughness
    "contributing": 0.10,    # CONTRIBUTING.md
    "changelog": 0.10,       # CHANGELOG presence
    "ci_config": 0.10,       # CI pipelines
    "test_coverage": 0.10,   # Tests directory
    "type_annotations": 0.05, # py.typed / stubs
}


# ---------------------------------------------------------------------------
# ExistingStateScorer
# ---------------------------------------------------------------------------

class ExistingStateScorer:
    """Score a cloned repo directory for existing documentation artifacts."""

    def __init__(self, repo_path: Path) -> None:
        self.root = Path(repo_path)

    # ------------------------------------------------------------------
    # Dimension scorers (return 0–100)
    # ------------------------------------------------------------------

    def score_agent_context(self) -> float:
        """Presence of CLAUDE.md, AGENTS.md, llms.txt (binary, high weight)."""
        files = ["CLAUDE.md", "AGENTS.md", "llms.txt", ".claude/CLAUDE.md", "docs/AGENTS.md"]
        score = 0.0
        for f in files:
            if (self.root / f).exists():
                score += 33.0
        return min(100.0, score)

    def score_readme_quality(self) -> float:
        """README quality: length, sections, code examples, install instructions."""
        readme = self._find_readme()
        if readme is None:
            return 0.0
        try:
            content = readme.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return 0.0

        score = 0.0
        length = len(content)

        # Length score (up to 30 pts)
        if length > 5000:
            score += 30.0
        elif length > 2000:
            score += 20.0
        elif length > 500:
            score += 10.0

        # Has sections/headers (up to 20 pts)
        headers = len(re.findall(r'^#{1,4}\s+\S', content, re.MULTILINE))
        if headers >= 5:
            score += 20.0
        elif headers >= 2:
            score += 10.0

        # Has code examples (up to 20 pts)
        code_blocks = len(re.findall(r'```', content))
        if code_blocks >= 4:
            score += 20.0
        elif code_blocks >= 2:
            score += 10.0

        # Has install instructions (up to 20 pts)
        install_patterns = [
            r'pip install', r'npm install', r'cargo add', r'go get',
            r'brew install', r'## install', r'## installation',
        ]
        for pat in install_patterns:
            if re.search(pat, content, re.IGNORECASE):
                score += 20.0
                break

        # Has usage/quickstart (up to 10 pts)
        usage_patterns = [r'## usage', r'## quickstart', r'## getting started', r'## example']
        for pat in usage_patterns:
            if re.search(pat, content, re.IGNORECASE):
                score += 10.0
                break

        return min(100.0, score)

    def score_contributing(self) -> float:
        """Presence of CONTRIBUTING.md or CONTRIBUTING/ directory."""
        candidates = [
            "CONTRIBUTING.md", "CONTRIBUTING.rst", "CONTRIBUTING.txt",
            "CONTRIBUTING/", ".github/CONTRIBUTING.md",
        ]
        for c in candidates:
            p = self.root / c
            if p.exists():
                return 100.0
        return 0.0

    def score_changelog(self) -> float:
        """Presence of CHANGELOG or HISTORY file."""
        candidates = [
            "CHANGELOG.md", "CHANGELOG.rst", "CHANGELOG.txt", "CHANGELOG",
            "HISTORY.md", "HISTORY.rst", "HISTORY.txt", "HISTORY",
            "NEWS.md", "RELEASES.md",
        ]
        for c in candidates:
            p = self.root / c
            if p.exists():
                return 100.0
        return 0.0

    def score_ci_config(self) -> float:
        """Presence of CI configuration files."""
        # GitHub Actions
        gha = self.root / ".github" / "workflows"
        if gha.is_dir():
            ymls = list(gha.glob("*.yml")) + list(gha.glob("*.yaml"))
            if ymls:
                return 100.0

        # Other CI systems
        ci_files = [
            ".travis.yml", ".circleci/config.yml", "Jenkinsfile",
            ".gitlab-ci.yml", "azure-pipelines.yml", "bitbucket-pipelines.yml",
            ".buildkite/pipeline.yml", "tox.ini",
        ]
        for f in ci_files:
            if (self.root / f).exists():
                return 100.0
        return 0.0

    def score_test_coverage(self) -> float:
        """Presence and density of test files."""
        test_dirs = ["tests", "test", "spec", "specs", "__tests__"]
        total_tests = 0

        for td in test_dirs:
            d = self.root / td
            if d.is_dir():
                # Count test files
                py_tests = list(d.rglob("test_*.py")) + list(d.rglob("*_test.py"))
                js_tests = list(d.rglob("*.test.js")) + list(d.rglob("*.spec.js"))
                ts_tests = list(d.rglob("*.test.ts")) + list(d.rglob("*.spec.ts"))
                total_tests += len(py_tests) + len(js_tests) + len(ts_tests)

        # Also check for pytest.ini, setup.cfg with [tool:pytest], pyproject.toml [tool.pytest]
        has_pytest_config = False
        for cfg in ["pytest.ini", "setup.cfg", "pyproject.toml"]:
            p = self.root / cfg
            if p.exists():
                try:
                    content = p.read_text(encoding="utf-8", errors="replace")
                    if "pytest" in content:
                        has_pytest_config = True
                        break
                except OSError:
                    pass

        score = 0.0
        if total_tests >= 50:
            score = 100.0
        elif total_tests >= 20:
            score = 80.0
        elif total_tests >= 5:
            score = 60.0
        elif total_tests >= 1:
            score = 40.0

        if has_pytest_config and score == 0.0:
            score = 20.0

        return score

    def score_type_annotations(self) -> float:
        """Presence of py.typed marker or .pyi stub files."""
        # py.typed marker (PEP 561)
        for py_typed in self.root.rglob("py.typed"):
            return 100.0

        # .pyi stub files
        stubs = list(self.root.rglob("*.pyi"))
        if len(stubs) >= 3:
            return 80.0
        elif stubs:
            return 50.0

        # Type hints in pyproject.toml
        pyproject = self.root / "pyproject.toml"
        if pyproject.exists():
            try:
                content = pyproject.read_text(encoding="utf-8", errors="replace")
                if "mypy" in content or "pyright" in content:
                    return 30.0
            except OSError:
                pass

        return 0.0

    # ------------------------------------------------------------------
    # Composite
    # ------------------------------------------------------------------

    def score_all(self) -> dict[str, float]:
        """Return dict of all dimension scores and composite."""
        dims = {
            "agent_context": self.score_agent_context(),
            "readme_quality": self.score_readme_quality(),
            "contributing": self.score_contributing(),
            "changelog": self.score_changelog(),
            "ci_config": self.score_ci_config(),
            "test_coverage": self.score_test_coverage(),
            "type_annotations": self.score_type_annotations(),
        }

        # Weighted composite
        composite = sum(
            dims[d] * DIMENSION_WEIGHTS[d]
            for d in dims
        )
        dims["composite"] = round(composite, 2)
        return dims

    def composite_score(self) -> float:
        """Return weighted composite score (0–100)."""
        return self.score_all()["composite"]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _find_readme(self) -> Optional[Path]:
        """Find the main README file."""
        candidates = [
            "README.md", "README.rst", "README.txt", "README",
            "Readme.md", "readme.md",
        ]
        for c in candidates:
            p = self.root / c
            if p.exists():
                return p
        return None


# ---------------------------------------------------------------------------
# Convenience: score two repo paths and return a comparable result dict
# ---------------------------------------------------------------------------

def score_existing(repo_path: Path) -> dict[str, float]:
    """Score an existing repo at *repo_path* and return dimension scores."""
    scorer = ExistingStateScorer(repo_path)
    return scorer.score_all()
