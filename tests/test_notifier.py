"""Tests for agentkit_cli.notifier — all HTTP mocked."""
from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from agentkit_cli.notifier import (
    NotifyConfig,
    _build_discord_payload,
    _build_generic_payload,
    _build_slack_payload,
    _post,
    _send_with_retry,
    build_payload,
    fire_notifications,
    notify_result,
    resolve_notify_configs,
)


# ---------------------------------------------------------------------------
# NotifyConfig
# ---------------------------------------------------------------------------

class TestNotifyConfig:
    def test_valid_slack(self):
        cfg = NotifyConfig(url="https://hooks.slack.com/test", service="slack")
        assert cfg.service == "slack"
        assert cfg.notify_on == "fail"

    def test_valid_discord(self):
        cfg = NotifyConfig(url="https://discord.com/api/webhooks/test", service="discord")
        assert cfg.service == "discord"

    def test_valid_webhook(self):
        cfg = NotifyConfig(url="https://example.com/hook", service="webhook")
        assert cfg.service == "webhook"

    def test_invalid_service(self):
        with pytest.raises(ValueError, match="service must be"):
            NotifyConfig(url="https://example.com", service="teams")

    def test_invalid_notify_on(self):
        with pytest.raises(ValueError, match="notify_on must be"):
            NotifyConfig(url="https://example.com", service="slack", notify_on="never")

    def test_notify_on_always(self):
        cfg = NotifyConfig(url="https://example.com", service="slack", notify_on="always")
        assert cfg.notify_on == "always"


# ---------------------------------------------------------------------------
# Payload builders
# ---------------------------------------------------------------------------

class TestSlackPayload:
    def test_pass_has_green_color(self):
        payload = _build_slack_payload("myproject", 88.0, "PASS", [], None)
        assert payload["attachments"][0]["color"] == "#36a64f"

    def test_fail_has_red_color(self):
        payload = _build_slack_payload("myproject", 42.0, "FAIL", ["finding1"], None)
        assert payload["attachments"][0]["color"] == "#cc0000"

    def test_score_in_text(self):
        payload = _build_slack_payload("myproject", 73.5, "PASS", [], None)
        text = payload["attachments"][0]["text"]
        assert "73.5" in text

    def test_findings_in_fields(self):
        payload = _build_slack_payload("myproject", 50.0, "FAIL", ["issue A", "issue B"], None)
        fields = payload["attachments"][0]["fields"]
        assert any("issue A" in str(f) for f in fields)

    def test_delta_in_text_when_provided(self):
        payload = _build_slack_payload("myproject", 70.0, "PASS", [], -5.0)
        text = payload["attachments"][0]["text"]
        assert "-5.0" in text

    def test_no_delta_text_when_none(self):
        payload = _build_slack_payload("myproject", 70.0, "PASS", [], None)
        text = payload["attachments"][0]["text"]
        assert "delta" not in text

    def test_findings_truncated_at_3(self):
        many = [f"finding {i}" for i in range(10)]
        payload = _build_slack_payload("proj", 60.0, "FAIL", many, None)
        fields_text = str(payload["attachments"][0]["fields"])
        # only first 3 findings should appear
        assert "finding 0" in fields_text
        assert "finding 3" not in fields_text


class TestDiscordPayload:
    def test_pass_has_green_color(self):
        payload = _build_discord_payload("proj", 90.0, "PASS", [], None)
        assert payload["embeds"][0]["color"] == 0x36A64F

    def test_fail_has_red_color(self):
        payload = _build_discord_payload("proj", 30.0, "FAIL", [], None)
        assert payload["embeds"][0]["color"] == 0xCC0000

    def test_score_in_description(self):
        payload = _build_discord_payload("proj", 77.0, "PASS", [], None)
        desc = payload["embeds"][0]["description"]
        assert "77.0" in desc

    def test_has_timestamp(self):
        payload = _build_discord_payload("proj", 77.0, "PASS", [], None)
        assert "timestamp" in payload["embeds"][0]


class TestGenericPayload:
    def test_contains_required_keys(self):
        payload = _build_generic_payload("proj", 80.0, "PASS", ["f1"], 2.0)
        for key in ("project", "score", "verdict", "top_findings", "timestamp", "delta"):
            assert key in payload

    def test_no_delta_key_when_none(self):
        payload = _build_generic_payload("proj", 80.0, "PASS", [], None)
        assert "delta" not in payload


class TestBuildPayload:
    def test_routes_to_slack(self):
        cfg = NotifyConfig(url="https://hooks.slack.com", service="slack")
        payload = build_payload(cfg, 85.0, "PASS", [])
        assert "attachments" in payload

    def test_routes_to_discord(self):
        cfg = NotifyConfig(url="https://discord.com/api/webhooks/x", service="discord")
        payload = build_payload(cfg, 85.0, "PASS", [])
        assert "embeds" in payload

    def test_routes_to_generic(self):
        cfg = NotifyConfig(url="https://example.com/hook", service="webhook")
        payload = build_payload(cfg, 85.0, "PASS", [])
        assert "project" in payload


# ---------------------------------------------------------------------------
# HTTP / retry
# ---------------------------------------------------------------------------

class TestPost:
    def _make_response(self, status: int = 200):
        mock_resp = MagicMock()
        mock_resp.status = status
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        return mock_resp

    def test_success_200(self):
        with patch("agentkit_cli.notifier.urlopen") as mock_urlopen:
            mock_urlopen.return_value = self._make_response(200)
            ok, msg = _post("https://example.com", {"key": "val"})
        assert ok is True

    def test_failure_500(self):
        with patch("agentkit_cli.notifier.urlopen") as mock_urlopen:
            mock_urlopen.return_value = self._make_response(500)
            ok, msg = _post("https://example.com", {"key": "val"})
        assert ok is False
        assert "500" in msg

    def test_url_error_returns_false(self):
        from urllib.error import URLError
        with patch("agentkit_cli.notifier.urlopen", side_effect=URLError("connection refused")):
            ok, msg = _post("https://example.com", {})
        assert ok is False
        assert msg


class TestSendWithRetry:
    def test_succeeds_on_first_try(self):
        with patch("agentkit_cli.notifier._post", return_value=(True, "HTTP 200")) as mock_post:
            ok, msg = _send_with_retry("https://example.com", {})
        assert ok is True
        assert mock_post.call_count == 1

    def test_retries_once_on_failure(self):
        with patch("agentkit_cli.notifier._post", return_value=(False, "HTTP 503")) as mock_post:
            with patch("agentkit_cli.notifier.time.sleep"):
                ok, msg = _send_with_retry("https://example.com", {})
        assert ok is False
        assert mock_post.call_count == 2  # 2 attempts

    def test_succeeds_on_second_try(self):
        responses = [(False, "err"), (True, "HTTP 200")]
        with patch("agentkit_cli.notifier._post", side_effect=responses) as mock_post:
            with patch("agentkit_cli.notifier.time.sleep"):
                ok, msg = _send_with_retry("https://example.com", {})
        assert ok is True
        assert mock_post.call_count == 2


# ---------------------------------------------------------------------------
# notify_result
# ---------------------------------------------------------------------------

class TestNotifyResult:
    def test_skips_when_notify_on_fail_and_passed(self):
        cfg = NotifyConfig(url="https://example.com", service="slack", notify_on="fail")
        with patch("agentkit_cli.notifier._send_with_retry") as mock_send:
            result = notify_result(cfg, verdict="PASS", score=90.0)
        mock_send.assert_not_called()
        assert result is True

    def test_fires_when_notify_on_fail_and_failed(self):
        cfg = NotifyConfig(url="https://example.com", service="slack", notify_on="fail")
        with patch("agentkit_cli.notifier._send_with_retry", return_value=(True, "ok")) as mock_send:
            result = notify_result(cfg, verdict="FAIL", score=40.0)
        mock_send.assert_called_once()
        assert result is True

    def test_fires_when_notify_on_always_and_passed(self):
        cfg = NotifyConfig(url="https://example.com", service="slack", notify_on="always")
        with patch("agentkit_cli.notifier._send_with_retry", return_value=(True, "ok")) as mock_send:
            result = notify_result(cfg, verdict="PASS", score=90.0)
        mock_send.assert_called_once()

    def test_error_does_not_propagate(self):
        cfg = NotifyConfig(url="https://example.com", service="slack", notify_on="always")
        with patch("agentkit_cli.notifier._send_with_retry", side_effect=RuntimeError("boom")):
            result = notify_result(cfg, verdict="FAIL", score=0.0)
        assert result is False  # returns False but doesn't raise


# ---------------------------------------------------------------------------
# resolve_notify_configs / env vars
# ---------------------------------------------------------------------------

class TestResolveNotifyConfigs:
    def test_cli_flag_creates_config(self):
        configs = resolve_notify_configs(notify_slack="https://hooks.slack.com/x")
        assert len(configs) == 1
        assert configs[0].service == "slack"

    def test_env_var_creates_config(self, monkeypatch):
        monkeypatch.setenv("AGENTKIT_NOTIFY_SLACK", "https://hooks.slack.com/env")
        monkeypatch.delenv("AGENTKIT_NOTIFY_DISCORD", raising=False)
        monkeypatch.delenv("AGENTKIT_NOTIFY_WEBHOOK", raising=False)
        configs = resolve_notify_configs()
        assert any(c.service == "slack" for c in configs)

    def test_cli_flag_overrides_env_var(self, monkeypatch):
        monkeypatch.setenv("AGENTKIT_NOTIFY_SLACK", "https://hooks.slack.com/env")
        configs = resolve_notify_configs(notify_slack="https://hooks.slack.com/cli")
        slack_configs = [c for c in configs if c.service == "slack"]
        assert len(slack_configs) == 1
        assert slack_configs[0].url == "https://hooks.slack.com/cli"

    def test_multiple_services(self):
        configs = resolve_notify_configs(
            notify_slack="https://hooks.slack.com/x",
            notify_discord="https://discord.com/webhooks/y",
            notify_webhook="https://example.com/z",
        )
        assert len(configs) == 3
        services = {c.service for c in configs}
        assert services == {"slack", "discord", "webhook"}

    def test_empty_returns_empty_list(self, monkeypatch):
        monkeypatch.delenv("AGENTKIT_NOTIFY_SLACK", raising=False)
        monkeypatch.delenv("AGENTKIT_NOTIFY_DISCORD", raising=False)
        monkeypatch.delenv("AGENTKIT_NOTIFY_WEBHOOK", raising=False)
        configs = resolve_notify_configs()
        assert configs == []


# ---------------------------------------------------------------------------
# fire_notifications
# ---------------------------------------------------------------------------

class TestFireNotifications:
    def test_fires_all_configs(self):
        configs = [
            NotifyConfig(url="https://s.com", service="slack", notify_on="always"),
            NotifyConfig(url="https://d.com", service="discord", notify_on="always"),
        ]
        with patch("agentkit_cli.notifier.notify_result", return_value=True) as mock_notify:
            fire_notifications(configs, verdict="PASS", score=90.0)
        assert mock_notify.call_count == 2

    def test_empty_configs_no_error(self):
        fire_notifications([], verdict="PASS", score=90.0)  # should not raise

    def test_exception_in_one_does_not_stop_others(self):
        configs = [
            NotifyConfig(url="https://s.com", service="slack", notify_on="always"),
            NotifyConfig(url="https://d.com", service="discord", notify_on="always"),
        ]
        call_count = 0

        def mock_notify(cfg, **kwargs):
            nonlocal call_count
            call_count += 1
            if cfg.service == "slack":
                raise RuntimeError("slack down")
            return True

        with patch("agentkit_cli.notifier.notify_result", side_effect=mock_notify):
            fire_notifications(configs, verdict="FAIL", score=30.0)
        # Both were attempted; fire_notifications swallows errors
        assert call_count == 2
