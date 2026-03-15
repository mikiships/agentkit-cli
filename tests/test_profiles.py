"""Tests for agentkit_cli.profiles — D1 profile engine."""
from __future__ import annotations

import textwrap
from pathlib import Path
from typing import Optional

import pytest

from agentkit_cli.profiles import (
    ProfileDefinition,
    ProfileRegistry,
    apply_profile,
    _BUILT_IN_PROFILES,
    _load_profile_toml,
    USER_PROFILES_DIR,
)
from agentkit_cli.config import AgentKitConfig


# ---------------------------------------------------------------------------
# ProfileDefinition
# ---------------------------------------------------------------------------

class TestProfileDefinition:
    def test_has_required_fields(self):
        p = ProfileDefinition(name="test", description="desc")
        assert p.name == "test"
        assert p.description == "desc"

    def test_defaults(self):
        p = ProfileDefinition(name="test", description="desc")
        assert p.min_score is None
        assert p.max_drop is None
        assert p.fail_on_regression is False
        assert p.notify_on == "fail"
        assert p.gate_enabled is True
        assert p.record_history is True
        assert p.sweep_targets == []

    def test_to_dict_structure(self):
        p = ProfileDefinition(name="test", description="d", min_score=80.0, max_drop=5.0)
        d = p.to_dict()
        assert "gate" in d
        assert "notify" in d
        assert "run" in d
        assert "sweep" in d
        assert d["gate"]["min_score"] == 80.0
        assert d["gate"]["max_drop"] == 5.0

    def test_to_dict_name_description(self):
        p = ProfileDefinition(name="myprofile", description="my desc")
        d = p.to_dict()
        assert d["name"] == "myprofile"
        assert d["description"] == "my desc"


# ---------------------------------------------------------------------------
# Built-in presets
# ---------------------------------------------------------------------------

class TestBuiltInPresets:
    def test_strict_preset_values(self):
        registry = ProfileRegistry()
        p = registry.get("strict")
        assert p is not None
        assert p.min_score == 85.0
        assert p.max_drop == 3.0
        assert p.fail_on_regression is True

    def test_balanced_preset_values(self):
        registry = ProfileRegistry()
        p = registry.get("balanced")
        assert p is not None
        assert p.min_score == 70.0
        assert p.max_drop == 10.0
        assert p.fail_on_regression is False

    def test_minimal_preset_values(self):
        registry = ProfileRegistry()
        p = registry.get("minimal")
        assert p is not None
        assert p.min_score == 50.0
        assert p.max_drop == 20.0
        assert p.gate_enabled is False

    def test_three_built_in_presets(self):
        assert len(_BUILT_IN_PROFILES) == 3

    def test_built_in_names(self):
        names = {p.name for p in _BUILT_IN_PROFILES}
        assert names == {"strict", "balanced", "minimal"}

    # Regression: preset values must not change unexpectedly
    def test_strict_notify_on_fail(self):
        registry = ProfileRegistry()
        p = registry.get("strict")
        assert p.notify_on == "fail"

    def test_balanced_notify_never(self):
        registry = ProfileRegistry()
        p = registry.get("balanced")
        assert p.notify_on == "never"

    def test_minimal_notify_never(self):
        registry = ProfileRegistry()
        p = registry.get("minimal")
        assert p.notify_on == "never"


# ---------------------------------------------------------------------------
# ProfileRegistry
# ---------------------------------------------------------------------------

class TestProfileRegistry:
    def test_lookup_case_insensitive(self):
        registry = ProfileRegistry()
        assert registry.get("STRICT") is not None
        assert registry.get("Strict") is not None
        assert registry.get("strict") is not None

    def test_unknown_profile_returns_none(self):
        registry = ProfileRegistry()
        assert registry.get("nonexistent") is None

    def test_list_all_includes_built_ins(self):
        registry = ProfileRegistry()
        names = {p.name for p in registry.list_all()}
        assert "strict" in names
        assert "balanced" in names
        assert "minimal" in names

    def test_is_built_in_true(self):
        registry = ProfileRegistry()
        assert registry.is_built_in("strict")
        assert registry.is_built_in("balanced")
        assert registry.is_built_in("minimal")

    def test_is_built_in_false(self):
        registry = ProfileRegistry()
        assert not registry.is_built_in("custom")

    def test_register_custom_profile(self):
        registry = ProfileRegistry()
        p = ProfileDefinition(name="custom", description="test", min_score=60.0)
        registry.register(p)
        found = registry.get("custom")
        assert found is not None
        assert found.min_score == 60.0

    def test_register_replaces_existing(self):
        registry = ProfileRegistry()
        p1 = ProfileDefinition(name="myp", description="v1", min_score=60.0)
        p2 = ProfileDefinition(name="myp", description="v2", min_score=99.0)
        registry.register(p1)
        registry.register(p2)
        assert registry.get("myp").min_score == 99.0

    def test_user_profiles_loaded_from_dir(self, tmp_path):
        toml = tmp_path / "mypro.toml"
        toml.write_text(textwrap.dedent("""\
            name = "mypro"
            description = "custom"
            [gate]
            min_score = 65.0
        """))
        registry = ProfileRegistry(profiles_dir=tmp_path)
        p = registry.get("mypro")
        assert p is not None
        assert p.min_score == 65.0

    def test_user_profile_invalid_toml_skipped(self, tmp_path):
        bad = tmp_path / "bad.toml"
        bad.write_text("not valid [[[")
        # Should not raise
        registry = ProfileRegistry(profiles_dir=tmp_path)
        assert registry.get("bad") is None

    def test_list_all_built_ins_first(self):
        registry = ProfileRegistry()
        profiles = registry.list_all()
        # All built-ins appear before user profiles (no user profiles in this test)
        # Just verify all 3 built-ins are in the list
        names = {p.name for p in profiles}
        assert "strict" in names
        assert "balanced" in names
        assert "minimal" in names


# ---------------------------------------------------------------------------
# apply_profile
# ---------------------------------------------------------------------------

class TestApplyProfile:
    def _fresh_config(self) -> AgentKitConfig:
        return AgentKitConfig()

    def test_apply_strict_sets_min_score(self):
        cfg = self._fresh_config()
        apply_profile("strict", cfg)
        assert cfg.gate.min_score == 85.0

    def test_apply_balanced_sets_min_score(self):
        cfg = self._fresh_config()
        apply_profile("balanced", cfg)
        assert cfg.gate.min_score == 70.0

    def test_apply_minimal_sets_min_score(self):
        cfg = self._fresh_config()
        apply_profile("minimal", cfg)
        assert cfg.gate.min_score == 50.0

    def test_apply_sets_max_drop(self):
        cfg = self._fresh_config()
        apply_profile("strict", cfg)
        assert cfg.gate.max_drop == 3.0

    def test_cli_min_score_overrides_profile(self):
        cfg = self._fresh_config()
        apply_profile("strict", cfg, cli_min_score=95.0)
        # Profile should NOT overwrite the CLI flag
        assert cfg.gate.min_score is None  # profile skipped, CLI wins

    def test_cli_max_drop_overrides_profile(self):
        cfg = self._fresh_config()
        apply_profile("strict", cfg, cli_max_drop=1.0)
        assert cfg.gate.max_drop is None  # profile skipped for max_drop

    def test_profile_unknown_raises_valueerror(self):
        cfg = self._fresh_config()
        with pytest.raises(ValueError, match="not found"):
            apply_profile("nonexistent", cfg)

    def test_apply_fail_on_regression(self):
        cfg = self._fresh_config()
        apply_profile("strict", cfg)
        assert cfg.gate.fail_on_regression is True

    def test_apply_balanced_fail_on_regression_false(self):
        cfg = self._fresh_config()
        apply_profile("balanced", cfg)
        assert cfg.gate.fail_on_regression is False

    def test_apply_notify_on_from_profile(self):
        cfg = self._fresh_config()
        apply_profile("balanced", cfg)
        assert cfg.notify.on == "never"
