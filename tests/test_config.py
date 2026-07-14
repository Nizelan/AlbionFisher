"""Settings loading, validation, and roundtrip tests."""

import pytest

from albionfisher.config.settings import (
    Settings,
    SettingsError,
    load_settings,
    save_settings,
)


def test_defaults_load_without_user_file():
    settings = load_settings(None)
    assert settings.detection.conf_threshold == 0.5
    assert settings.detection.idle_fps == 3
    assert settings.detection.minigame_fps == 20
    assert settings.timeouts.bite == 30.0
    assert settings.stop.max_consecutive_fails == 5
    assert settings.stop.session_limit is None


def test_missing_user_file_falls_back_to_defaults(tmp_path):
    settings = load_settings(tmp_path / "nope.yaml")
    assert settings == Settings()


def test_user_file_overlays_defaults(tmp_path):
    user = tmp_path / "settings.yaml"
    user.write_text("timeouts:\n  bite: 45\n", encoding="utf-8")
    settings = load_settings(user)
    assert settings.timeouts.bite == 45.0
    assert settings.timeouts.find_zone == 10.0  # untouched default


def test_invalid_type_raises(tmp_path):
    user = tmp_path / "settings.yaml"
    user.write_text("detection:\n  conf_threshold: very high\n", encoding="utf-8")
    with pytest.raises(SettingsError, match="conf_threshold"):
        load_settings(user)


def test_unknown_key_raises(tmp_path):
    user = tmp_path / "settings.yaml"
    user.write_text("detection:\n  confidence: 0.5\n", encoding="utf-8")
    with pytest.raises(SettingsError, match="unknown setting"):
        load_settings(user)


def test_unknown_section_raises(tmp_path):
    user = tmp_path / "settings.yaml"
    user.write_text("detektion:\n  conf_threshold: 0.5\n", encoding="utf-8")
    with pytest.raises(SettingsError, match="unknown settings section"):
        load_settings(user)


def test_out_of_range_value_raises(tmp_path):
    user = tmp_path / "settings.yaml"
    user.write_text("detection:\n  conf_threshold: 1.5\n", encoding="utf-8")
    with pytest.raises(SettingsError, match="within"):
        load_settings(user)


def test_roundtrip_save_load(tmp_path):
    settings = load_settings(None)
    settings.timeouts.bite = 42.0
    settings.stop.session_limit = 100
    path = tmp_path / "saved.yaml"
    save_settings(settings, path)
    assert load_settings(path) == settings
