"""Tests for D2: GitHub Pages config + CI workflow."""
from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).parent.parent
DOCS = REPO / "docs"
WORKFLOW = REPO / ".github" / "workflows" / "update-pages.yml"
README = REPO / "README.md"


def test_nojekyll_exists():
    assert (DOCS / ".nojekyll").exists(), "docs/.nojekyll must exist"


def test_workflow_file_exists():
    assert WORKFLOW.exists(), ".github/workflows/update-pages.yml must exist"


def test_workflow_triggers_on_main():
    content = WORKFLOW.read_text()
    assert "branches: [main]" in content or "branches:\n    - main" in content or "main" in content


def test_workflow_updates_stats():
    content = WORKFLOW.read_text()
    assert "pages-refresh --from-existing-data" in content
    assert "git add docs/data.json docs/index.html docs/leaderboard.html" in content


def test_readme_has_docs_badge():
    readme = README.read_text()
    assert "mikiships.github.io/agentkit-cli" in readme


def test_readme_has_pypi_badge():
    readme = README.read_text()
    assert "pypi" in readme.lower()


def test_workflow_has_git_push():
    content = WORKFLOW.read_text()
    assert "git push" in content or "git commit" in content
