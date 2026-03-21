"""Tests for D1 — ExistingStateScorer (≥18 tests).

Verifies:
- All dimension scorers return 0-100 values
- Empty repos score 0 on most dimensions
- Well-documented repos score higher
- ruff-like repo scores higher than pylint-like on relevant dimensions
"""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from agentkit_cli.existing_scorer import ExistingStateScorer, score_existing, DIMENSION_WEIGHTS


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def empty_repo(tmp_path) -> Path:
    """Minimal empty repo."""
    root = tmp_path / "empty_repo"
    root.mkdir()
    return root


@pytest.fixture
def basic_repo(tmp_path) -> Path:
    """Repo with README only."""
    root = tmp_path / "basic_repo"
    root.mkdir()
    (root / "README.md").write_text("# My Project\n\nA simple project.\n")
    return root


@pytest.fixture
def well_documented_repo(tmp_path) -> Path:
    """Repo with all docs artifacts."""
    root = tmp_path / "well_repo"
    root.mkdir()
    tmp_path = root  # alias
    # Agent context
    (tmp_path / "CLAUDE.md").write_text("# Claude context\n\nThis is context for Claude.\n")
    (tmp_path / "AGENTS.md").write_text("# Agents\n\nAgent instructions here.\n")
    # README
    readme = textwrap.dedent("""\
        # My Project

        ## Installation

        ```bash
        pip install myproject
        ```

        ## Usage

        ```python
        import myproject
        myproject.run()
        ```

        ## Contributing

        See CONTRIBUTING.md

        ## Changelog

        See CHANGELOG.md

        ## API Reference

        Detailed API docs at https://docs.myproject.io
    """)
    (tmp_path / "README.md").write_text(readme * 5)  # make it long
    # CONTRIBUTING
    (tmp_path / "CONTRIBUTING.md").write_text("# Contributing\n\nPlease follow these guidelines.\n")
    # CHANGELOG
    (tmp_path / "CHANGELOG.md").write_text("# Changelog\n\n## v1.0.0\n- Initial release\n")
    # CI
    gha = tmp_path / ".github" / "workflows"
    gha.mkdir(parents=True)
    (gha / "ci.yml").write_text("name: CI\non: push\njobs:\n  test:\n    runs-on: ubuntu-latest\n")
    # Tests
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    for i in range(25):
        (tests_dir / f"test_module{i}.py").write_text(f"def test_thing{i}(): pass\n")
    # py.typed
    pkg = tmp_path / "mypkg"
    pkg.mkdir()
    (pkg / "py.typed").write_text("")
    return tmp_path


@pytest.fixture
def sparse_repo(tmp_path) -> Path:
    """Sparse repo: old-style, no agent context, minimal README."""
    root = tmp_path / "sparse_repo"
    root.mkdir()
    (root / "README.txt").write_text("My old project.\n")
    # No CONTRIBUTING, no CHANGELOG, no CI, minimal tests
    return root


# ---------------------------------------------------------------------------
# D1: ExistingStateScorer basic API
# ---------------------------------------------------------------------------

def test_scorer_instantiates(empty_repo):
    scorer = ExistingStateScorer(empty_repo)
    assert scorer is not None


def test_score_all_returns_dict(empty_repo):
    scorer = ExistingStateScorer(empty_repo)
    result = scorer.score_all()
    assert isinstance(result, dict)


def test_score_all_has_composite(empty_repo):
    scorer = ExistingStateScorer(empty_repo)
    result = scorer.score_all()
    assert "composite" in result


def test_score_all_composite_in_range(well_documented_repo):
    scorer = ExistingStateScorer(well_documented_repo)
    result = scorer.score_all()
    assert 0.0 <= result["composite"] <= 100.0


def test_composite_score_method(well_documented_repo):
    scorer = ExistingStateScorer(well_documented_repo)
    c = scorer.composite_score()
    assert 0.0 <= c <= 100.0


def test_dimension_weights_sum_to_one():
    total = sum(DIMENSION_WEIGHTS.values())
    assert abs(total - 1.0) < 0.01


# ---------------------------------------------------------------------------
# D1: Empty repo
# ---------------------------------------------------------------------------

def test_empty_repo_agent_context_zero(empty_repo):
    scorer = ExistingStateScorer(empty_repo)
    assert scorer.score_agent_context() == 0.0


def test_empty_repo_readme_quality_zero(empty_repo):
    scorer = ExistingStateScorer(empty_repo)
    assert scorer.score_readme_quality() == 0.0


def test_empty_repo_contributing_zero(empty_repo):
    scorer = ExistingStateScorer(empty_repo)
    assert scorer.score_contributing() == 0.0


def test_empty_repo_changelog_zero(empty_repo):
    scorer = ExistingStateScorer(empty_repo)
    assert scorer.score_changelog() == 0.0


def test_empty_repo_ci_zero(empty_repo):
    scorer = ExistingStateScorer(empty_repo)
    assert scorer.score_ci_config() == 0.0


def test_empty_repo_test_coverage_zero(empty_repo):
    scorer = ExistingStateScorer(empty_repo)
    assert scorer.score_test_coverage() == 0.0


# ---------------------------------------------------------------------------
# D1: Well-documented repo
# ---------------------------------------------------------------------------

def test_well_documented_agent_context_positive(well_documented_repo):
    scorer = ExistingStateScorer(well_documented_repo)
    assert scorer.score_agent_context() > 0


def test_well_documented_contributing_100(well_documented_repo):
    scorer = ExistingStateScorer(well_documented_repo)
    assert scorer.score_contributing() == 100.0


def test_well_documented_changelog_100(well_documented_repo):
    scorer = ExistingStateScorer(well_documented_repo)
    assert scorer.score_changelog() == 100.0


def test_well_documented_ci_100(well_documented_repo):
    scorer = ExistingStateScorer(well_documented_repo)
    assert scorer.score_ci_config() == 100.0


def test_well_documented_test_coverage_positive(well_documented_repo):
    scorer = ExistingStateScorer(well_documented_repo)
    assert scorer.score_test_coverage() > 0


def test_well_documented_type_annotations_100(well_documented_repo):
    scorer = ExistingStateScorer(well_documented_repo)
    assert scorer.score_type_annotations() == 100.0


# ---------------------------------------------------------------------------
# D1: Well-documented vs sparse comparison
# ---------------------------------------------------------------------------

def test_well_documented_beats_sparse_composite(well_documented_repo, sparse_repo):
    well = ExistingStateScorer(well_documented_repo).composite_score()
    sparse = ExistingStateScorer(sparse_repo).composite_score()
    assert well > sparse, f"well={well}, sparse={sparse}"


def test_well_documented_beats_sparse_readme(well_documented_repo, sparse_repo):
    well = ExistingStateScorer(well_documented_repo).score_readme_quality()
    sparse = ExistingStateScorer(sparse_repo).score_readme_quality()
    assert well > sparse


def test_well_documented_beats_sparse_agent_context(well_documented_repo, sparse_repo):
    well = ExistingStateScorer(well_documented_repo).score_agent_context()
    sparse = ExistingStateScorer(sparse_repo).score_agent_context()
    assert well > sparse


# ---------------------------------------------------------------------------
# D1: ruff vs pylint fixture simulation
# ---------------------------------------------------------------------------

@pytest.fixture
def ruff_like_repo(tmp_path) -> Path:
    """Repo that resembles ruff: CHANGELOG, CI, tests, README with examples."""
    root = tmp_path / "ruff_repo"
    root.mkdir()
    (root / "README.md").write_text(
        "# ruff\n\n## Installation\n\n```bash\npip install ruff\n```\n\n"
        "## Usage\n\n```bash\nruff check .\n```\n\n" * 10
    )
    (root / "CHANGELOG.md").write_text("# Changelog\n\n## v0.1.0\n- First release\n")
    (root / "CONTRIBUTING.md").write_text("# Contributing\n\nFork and PR.\n")
    gha = root / ".github" / "workflows"
    gha.mkdir(parents=True)
    (gha / "ci.yml").write_text("name: CI\non: push\njobs: {}\n")
    tests_dir = root / "tests"
    tests_dir.mkdir()
    for i in range(30):
        (tests_dir / f"test_{i}.py").write_text("def test(): pass\n")
    pkg = root / "ruff"
    pkg.mkdir()
    (pkg / "py.typed").write_text("")
    return root


@pytest.fixture
def pylint_like_repo(tmp_path) -> Path:
    """Repo that resembles pylint: older style, no agent context, less structured."""
    root = tmp_path / "pylint_repo"
    root.mkdir()
    (root / "README.rst").write_text(
        "pylint\n======\n\nA Python linter.\n\nInstall with pip install pylint.\n"
    )
    (root / "ChangeLog").write_text("Changes:\n* 2.0.0: major refactor\n")
    gha = root / ".github" / "workflows"
    gha.mkdir(parents=True)
    (gha / "tests.yml").write_text("name: Tests\non: push\njobs: {}\n")
    tests_dir = root / "tests"
    tests_dir.mkdir()
    for i in range(5):
        (tests_dir / f"test_{i}.py").write_text("def test(): pass\n")
    return root


def test_ruff_like_beats_pylint_like_composite(ruff_like_repo, pylint_like_repo):
    """ruff-like repo should score higher composite than pylint-like."""
    ruff_score = ExistingStateScorer(ruff_like_repo).composite_score()
    pylint_score = ExistingStateScorer(pylint_like_repo).composite_score()
    assert ruff_score > pylint_score, f"ruff={ruff_score}, pylint={pylint_score}"


def test_ruff_like_beats_pylint_like_test_coverage(ruff_like_repo, pylint_like_repo):
    """ruff-like has more tests, should score higher."""
    ruff_score = ExistingStateScorer(ruff_like_repo).score_test_coverage()
    pylint_score = ExistingStateScorer(pylint_like_repo).score_test_coverage()
    assert ruff_score > pylint_score, f"ruff={ruff_score}, pylint={pylint_score}"


def test_ruff_like_beats_pylint_like_type_annotations(ruff_like_repo, pylint_like_repo):
    """ruff-like has py.typed, pylint-like doesn't."""
    ruff_score = ExistingStateScorer(ruff_like_repo).score_type_annotations()
    pylint_score = ExistingStateScorer(pylint_like_repo).score_type_annotations()
    assert ruff_score > pylint_score, f"ruff={ruff_score}, pylint={pylint_score}"


# ---------------------------------------------------------------------------
# D1: score_existing convenience function
# ---------------------------------------------------------------------------

def test_score_existing_returns_dict(well_documented_repo):
    result = score_existing(well_documented_repo)
    assert isinstance(result, dict)
    assert "composite" in result


def test_score_existing_composite_in_range(well_documented_repo):
    result = score_existing(well_documented_repo)
    assert 0.0 <= result["composite"] <= 100.0


# ---------------------------------------------------------------------------
# D1: CHANGELOG variants
# ---------------------------------------------------------------------------

def test_changelog_detects_rst(tmp_path):
    (tmp_path / "CHANGELOG.rst").write_text("Changelog\n=========\n")
    scorer = ExistingStateScorer(tmp_path)
    assert scorer.score_changelog() == 100.0


def test_changelog_detects_history(tmp_path):
    (tmp_path / "HISTORY.md").write_text("# History\n")
    scorer = ExistingStateScorer(tmp_path)
    assert scorer.score_changelog() == 100.0


# ---------------------------------------------------------------------------
# D1: CI variants
# ---------------------------------------------------------------------------

def test_ci_detects_travis(tmp_path):
    (tmp_path / ".travis.yml").write_text("language: python\n")
    scorer = ExistingStateScorer(tmp_path)
    assert scorer.score_ci_config() == 100.0


def test_ci_detects_circleci(tmp_path):
    cc = tmp_path / ".circleci"
    cc.mkdir()
    (cc / "config.yml").write_text("version: 2.1\n")
    scorer = ExistingStateScorer(tmp_path)
    assert scorer.score_ci_config() == 100.0


# ---------------------------------------------------------------------------
# D1: CONTRIBUTING variants
# ---------------------------------------------------------------------------

def test_contributing_detects_github_dir(tmp_path):
    gh = tmp_path / ".github"
    gh.mkdir()
    (gh / "CONTRIBUTING.md").write_text("# Contributing\n")
    scorer = ExistingStateScorer(tmp_path)
    assert scorer.score_contributing() == 100.0


# ---------------------------------------------------------------------------
# D1: type annotation variants
# ---------------------------------------------------------------------------

def test_type_annotations_pyi_stubs(tmp_path):
    for i in range(3):
        (tmp_path / f"mod{i}.pyi").write_text("def func() -> None: ...\n")
    scorer = ExistingStateScorer(tmp_path)
    assert scorer.score_type_annotations() >= 80.0


def test_type_annotations_pyproject_mypy(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[tool.mypy]\nstrict = true\n")
    scorer = ExistingStateScorer(tmp_path)
    assert scorer.score_type_annotations() >= 20.0
