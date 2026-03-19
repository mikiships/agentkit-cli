"""Tests for D3: agentkit quickstart improvements."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from agentkit_cli.main import app

runner = CliRunner()


def _mock_doctor():
    m = MagicMock()
    m.checks = []
    return m


def _mock_analysis():
    tool_scores = {"agentlint": 75.0, "agentmd": 80.0, "coderace": None, "agentreflect": None}
    tool_results = {}
    return tool_scores, tool_results


def test_quickstart_shows_next_steps(tmp_path):
    """Next steps block must appear in quickstart output."""
    with (
        patch("agentkit_cli.commands.quickstart_cmd.run_doctor", return_value=_mock_doctor()),
        patch("agentkit_cli.commands.quickstart_cmd._run_fast_analysis", return_value=_mock_analysis()),
        patch("agentkit_cli.commands.quickstart_cmd.upload_scorecard", return_value=None),
        patch("agentkit_cli.commands.quickstart_cmd.generate_scorecard_html", return_value="<html>"),
    ):
        result = runner.invoke(app, ["quickstart", str(tmp_path), "--timeout", "5"])

    assert result.exit_code == 0
    assert "Next steps" in result.output


def test_quickstart_next_steps_includes_run(tmp_path):
    with (
        patch("agentkit_cli.commands.quickstart_cmd.run_doctor", return_value=_mock_doctor()),
        patch("agentkit_cli.commands.quickstart_cmd._run_fast_analysis", return_value=_mock_analysis()),
        patch("agentkit_cli.commands.quickstart_cmd.upload_scorecard", return_value=None),
        patch("agentkit_cli.commands.quickstart_cmd.generate_scorecard_html", return_value="<html>"),
    ):
        result = runner.invoke(app, ["quickstart", str(tmp_path), "--timeout", "5"])

    assert "agentkit run" in result.output


def test_quickstart_next_steps_includes_analyze(tmp_path):
    with (
        patch("agentkit_cli.commands.quickstart_cmd.run_doctor", return_value=_mock_doctor()),
        patch("agentkit_cli.commands.quickstart_cmd._run_fast_analysis", return_value=_mock_analysis()),
        patch("agentkit_cli.commands.quickstart_cmd.upload_scorecard", return_value=None),
        patch("agentkit_cli.commands.quickstart_cmd.generate_scorecard_html", return_value="<html>"),
    ):
        result = runner.invoke(app, ["quickstart", str(tmp_path), "--timeout", "5"])

    assert "analyze" in result.output


def test_quickstart_next_steps_includes_benchmark(tmp_path):
    with (
        patch("agentkit_cli.commands.quickstart_cmd.run_doctor", return_value=_mock_doctor()),
        patch("agentkit_cli.commands.quickstart_cmd._run_fast_analysis", return_value=_mock_analysis()),
        patch("agentkit_cli.commands.quickstart_cmd.upload_scorecard", return_value=None),
        patch("agentkit_cli.commands.quickstart_cmd.generate_scorecard_html", return_value="<html>"),
    ):
        result = runner.invoke(app, ["quickstart", str(tmp_path), "--timeout", "5"])

    assert "benchmark" in result.output


def test_quickstart_shows_pages_url(tmp_path):
    """GitHub Pages URL should be printed."""
    with (
        patch("agentkit_cli.commands.quickstart_cmd.run_doctor", return_value=_mock_doctor()),
        patch("agentkit_cli.commands.quickstart_cmd._run_fast_analysis", return_value=_mock_analysis()),
        patch("agentkit_cli.commands.quickstart_cmd.upload_scorecard", return_value=None),
        patch("agentkit_cli.commands.quickstart_cmd.generate_scorecard_html", return_value="<html>"),
    ):
        result = runner.invoke(app, ["quickstart", str(tmp_path), "--timeout", "5"])

    assert "mikiships.github.io" in result.output


def test_quickstart_no_api_key_graceful(tmp_path):
    """Without HERENOW_API_KEY, quickstart should still complete successfully."""
    with (
        patch("agentkit_cli.commands.quickstart_cmd.run_doctor", return_value=_mock_doctor()),
        patch("agentkit_cli.commands.quickstart_cmd._run_fast_analysis", return_value=_mock_analysis()),
        patch.dict("os.environ", {}, clear=False),
    ):
        # Remove key if set
        import os
        os.environ.pop("HERENOW_API_KEY", None)
        result = runner.invoke(app, ["quickstart", str(tmp_path), "--timeout", "5"])

    assert result.exit_code == 0, f"Expected exit 0, got {result.exit_code}: {result.output}"


def test_quickstart_no_api_key_prints_skip_message(tmp_path):
    """Without HERENOW_API_KEY, should print skip message not an error."""
    import os
    os.environ.pop("HERENOW_API_KEY", None)
    with (
        patch("agentkit_cli.commands.quickstart_cmd.run_doctor", return_value=_mock_doctor()),
        patch("agentkit_cli.commands.quickstart_cmd._run_fast_analysis", return_value=_mock_analysis()),
    ):
        result = runner.invoke(app, ["quickstart", str(tmp_path), "--timeout", "5"])

    output = result.output
    # Should mention skipping or set env var, not crash
    assert "HERENOW_API_KEY" in output or "Skipping" in output or "skip" in output.lower()


def test_quickstart_with_no_share_flag(tmp_path):
    """--no-share flag should suppress share step entirely."""
    with (
        patch("agentkit_cli.commands.quickstart_cmd.run_doctor", return_value=_mock_doctor()),
        patch("agentkit_cli.commands.quickstart_cmd._run_fast_analysis", return_value=_mock_analysis()),
        patch("agentkit_cli.commands.quickstart_cmd.upload_scorecard") as mock_upload,
    ):
        result = runner.invoke(app, ["quickstart", str(tmp_path), "--no-share", "--timeout", "5"])

    assert result.exit_code == 0
    mock_upload.assert_not_called()


def test_quickstart_share_with_api_key(tmp_path):
    """With HERENOW_API_KEY set, upload_scorecard should be called."""
    with (
        patch("agentkit_cli.commands.quickstart_cmd.run_doctor", return_value=_mock_doctor()),
        patch("agentkit_cli.commands.quickstart_cmd._run_fast_analysis", return_value=_mock_analysis()),
        patch("agentkit_cli.commands.quickstart_cmd.upload_scorecard", return_value="https://here.now/xyz") as mock_upload,
        patch("agentkit_cli.commands.quickstart_cmd.generate_scorecard_html", return_value="<html>"),
        patch.dict("os.environ", {"HERENOW_API_KEY": "test-key"}),
    ):
        result = runner.invoke(app, ["quickstart", str(tmp_path), "--timeout", "5"])

    assert result.exit_code == 0
    mock_upload.assert_called_once()


def test_quickstart_share_exception_graceful(tmp_path):
    """Share upload exception should not crash quickstart."""
    with (
        patch("agentkit_cli.commands.quickstart_cmd.run_doctor", return_value=_mock_doctor()),
        patch("agentkit_cli.commands.quickstart_cmd._run_fast_analysis", return_value=_mock_analysis()),
        patch("agentkit_cli.commands.quickstart_cmd.upload_scorecard", side_effect=RuntimeError("network down")),
        patch("agentkit_cli.commands.quickstart_cmd.generate_scorecard_html", return_value="<html>"),
        patch.dict("os.environ", {"HERENOW_API_KEY": "test-key"}),
    ):
        result = runner.invoke(app, ["quickstart", str(tmp_path), "--timeout", "5"])

    assert result.exit_code == 0
