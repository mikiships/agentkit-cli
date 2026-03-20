"""Tests for `agentkit gist` command (D2) — all HTTP calls mocked."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from agentkit_cli.main import app
from agentkit_cli.gist_publisher import GistResult

runner = CliRunner()

SAMPLE_RESULT = GistResult(
    url="https://gist.github.com/test123",
    gist_id="test123",
    raw_url="https://gist.githubusercontent.com/raw/test123/file.md",
    created_at="2026-03-20T00:00:00Z",
)


def _mock_publisher(result=SAMPLE_RESULT):
    mock = MagicMock()
    mock.publish.return_value = result
    return mock


class TestGistCommandRegistered:
    def test_gist_command_exists_in_app(self):
        """agentkit gist is a registered command."""
        result = runner.invoke(app, ["gist", "--help"])
        assert result.exit_code == 0
        assert "gist" in result.output.lower() or "publish" in result.output.lower()

    def test_gist_help_shows_from_flag(self):
        result = runner.invoke(app, ["gist", "--help"])
        assert result.exit_code == 0
        assert "--from" in result.output

    def test_gist_help_shows_public_flag(self):
        result = runner.invoke(app, ["gist", "--help"])
        assert "--public" in result.output

    def test_gist_help_shows_description_flag(self):
        result = runner.invoke(app, ["gist", "--help"])
        assert "--description" in result.output

    def test_gist_help_shows_format_flag(self):
        result = runner.invoke(app, ["gist", "--help"])
        assert "--format" in result.output


class TestGistCommandFromFile:
    def test_publish_from_file(self, tmp_path):
        """--from <file> publishes file content and prints gist URL."""
        f = tmp_path / "report.md"
        f.write_text("# My Report\n")

        with patch("agentkit_cli.commands.gist_cmd.GistPublisher", return_value=_mock_publisher()):
            result = runner.invoke(app, ["gist", "--from", str(f)])

        assert result.exit_code == 0
        assert "https://gist.github.com/test123" in result.output

    def test_publish_from_nonexistent_file_exits_1(self, tmp_path):
        result = runner.invoke(app, ["gist", "--from", str(tmp_path / "missing.md")])
        assert result.exit_code == 1

    def test_publish_public_flag_passed_to_publisher(self, tmp_path):
        f = tmp_path / "r.md"
        f.write_text("content")
        mock_pub = _mock_publisher()

        with patch("agentkit_cli.commands.gist_cmd.GistPublisher", return_value=mock_pub):
            runner.invoke(app, ["gist", "--from", str(f), "--public"])

        mock_pub.publish.assert_called_once()
        kwargs = mock_pub.publish.call_args
        assert kwargs[1].get("public") is True or (kwargs[0] and kwargs[0][3] is True)

    def test_description_passed_to_publisher(self, tmp_path):
        f = tmp_path / "r.md"
        f.write_text("content")
        mock_pub = _mock_publisher()

        with patch("agentkit_cli.commands.gist_cmd.GistPublisher", return_value=mock_pub):
            runner.invoke(app, ["gist", "--from", str(f), "--description", "My custom desc"])

        mock_pub.publish.assert_called_once()
        call_kwargs = mock_pub.publish.call_args[1]
        assert "My custom desc" in (call_kwargs.get("description", "") or "")

    def test_publisher_failure_exits_1(self, tmp_path):
        f = tmp_path / "r.md"
        f.write_text("content")
        mock_pub = _mock_publisher(result=None)

        with patch("agentkit_cli.commands.gist_cmd.GistPublisher", return_value=mock_pub):
            result = runner.invoke(app, ["gist", "--from", str(f)])

        assert result.exit_code == 1

    def test_secret_gist_note_printed(self, tmp_path):
        """Secret gist prints a note about the URL."""
        f = tmp_path / "r.md"
        f.write_text("content")

        with patch("agentkit_cli.commands.gist_cmd.GistPublisher", return_value=_mock_publisher()):
            result = runner.invoke(app, ["gist", "--from", str(f)])

        assert result.exit_code == 0
        assert "secret" in result.output.lower() or "only accessible" in result.output.lower()

    def test_filename_preserved_from_input_file(self, tmp_path):
        """Filename from the input file is used."""
        f = tmp_path / "my-special-report.md"
        f.write_text("content")
        mock_pub = _mock_publisher()

        with patch("agentkit_cli.commands.gist_cmd.GistPublisher", return_value=mock_pub):
            runner.invoke(app, ["gist", "--from", str(f)])

        call_kwargs = mock_pub.publish.call_args[1]
        assert call_kwargs.get("filename") == "my-special-report.md"

    def test_public_gist_no_secret_note(self, tmp_path):
        """Public gist does not print the secret note."""
        f = tmp_path / "r.md"
        f.write_text("content")

        with patch("agentkit_cli.commands.gist_cmd.GistPublisher", return_value=_mock_publisher()):
            result = runner.invoke(app, ["gist", "--from", str(f), "--public"])

        assert result.exit_code == 0
        assert "secret" not in result.output.lower()


class TestGistCommandInAppHelp:
    def test_gist_appears_in_main_help(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "gist" in result.output
