from __future__ import annotations

from typer.testing import CliRunner

from agentkit_cli.main import app

runner = CliRunner()


def test_contract_end_to_end_generates_expected_sections_in_temp_repo(tmp_path):
    (tmp_path / ".agentkit").mkdir()
    (tmp_path / ".agentkit" / "source.md").write_text(
        "# Repo Soul\n\n## Overview\nUseful repo.\n\n## Commands\nuv run pytest -q\n",
        encoding="utf-8",
    )
    (tmp_path / "tests").mkdir()
    (tmp_path / "agentkit_cli").mkdir()

    result = runner.invoke(app, ["contract", "Ship source-aware contracts", "--path", str(tmp_path)])

    assert result.exit_code == 0
    contract_path = tmp_path / "all-day-build-contract-ship-source-aware-contracts.md"
    content = contract_path.read_text(encoding="utf-8")
    assert "## 1. Objective" in content
    assert "## 2. Source of Truth" in content
    assert "## 3. Non-Negotiable Build Rules" in content
    assert "## 4. Deliverables" in content
    assert "## 5. Test Requirements" in content
    assert "## 6. Reports" in content
    assert "## 7. Stop Conditions" in content
    assert ".agentkit/source.md" in content
    assert "- tests" in content
    assert "- agentkit_cli" in content
