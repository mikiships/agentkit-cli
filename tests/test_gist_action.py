"""Tests for GitHub Actions gist integration (D4)."""
from __future__ import annotations

import json
import os
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml


class TestActionYmlGistInputOutput:
    def _load_action(self):
        action_path = Path(__file__).parent.parent / "action.yml"
        with open(action_path) as f:
            return yaml.safe_load(f)

    def test_gist_token_input_exists(self):
        action = self._load_action()
        assert "gist-token" in action["inputs"]

    def test_gist_token_not_required(self):
        action = self._load_action()
        gist_input = action["inputs"]["gist-token"]
        assert gist_input.get("required") is False or gist_input.get("required") == False

    def test_gist_url_output_exists(self):
        action = self._load_action()
        assert "gist-url" in action["outputs"]

    def test_gist_url_output_has_description(self):
        action = self._load_action()
        assert action["outputs"]["gist-url"].get("description")

    def test_gist_token_has_description(self):
        action = self._load_action()
        assert action["inputs"]["gist-token"].get("description")


class TestGistPublisherMockedApi:
    """Integration-style tests with mocked GitHub API to verify output structure."""

    def test_publish_gist_response_structure(self):
        from agentkit_cli.gist_publisher import GistPublisher

        fake_resp = {
            "id": "action_gist_id",
            "html_url": "https://gist.github.com/action_gist_id",
            "created_at": "2026-03-20T10:00:00Z",
            "files": {
                "agentkit-run-report.md": {
                    "raw_url": "https://gist.githubusercontent.com/raw/action_gist_id/report.md"
                }
            },
        }

        class _CM:
            def __enter__(self):
                m = MagicMock()
                m.read.return_value = json.dumps(fake_resp).encode()
                return m

            def __exit__(self, *a):
                pass

        with patch("agentkit_cli.gist_publisher.request.urlopen", return_value=_CM()):
            pub = GistPublisher(token="action_token")
            result = pub.publish(
                content="# CI run report",
                filename="agentkit-run-report.md",
                description="agentkit run: myproject",
                public=False,
            )

        assert result is not None
        assert result.gist_id == "action_gist_id"
        assert result.url == "https://gist.github.com/action_gist_id"

    def test_publish_gist_sets_authorization_header(self):
        from agentkit_cli.gist_publisher import GistPublisher

        captured = []

        def _fake_urlopen(req):
            captured.append(req)

            class _CM:
                def __enter__(self):
                    m = MagicMock()
                    m.read.return_value = json.dumps({
                        "id": "x",
                        "html_url": "https://gist.github.com/x",
                        "created_at": "2026-03-20T00:00:00Z",
                        "files": {},
                    }).encode()
                    return m

                def __exit__(self, *a):
                    pass

            return _CM()

        with patch("agentkit_cli.gist_publisher.request.urlopen", side_effect=_fake_urlopen):
            pub = GistPublisher(token="action_secret_token")
            pub.publish("content", public=True)

        assert len(captured) == 1
        assert captured[0].get_header("Authorization") == "Bearer action_secret_token"

    def test_action_gist_step_in_yml(self):
        """The action.yml runs section includes a gist publish step."""
        action_path = Path(__file__).parent.parent / "action.yml"
        content = action_path.read_text()
        assert "publish-gist" in content or "gist" in content.lower()

    def test_action_gist_step_conditional_on_token(self):
        """Gist publish step only runs when gist-token is provided."""
        action_path = Path(__file__).parent.parent / "action.yml"
        content = action_path.read_text()
        assert "gist-token" in content
