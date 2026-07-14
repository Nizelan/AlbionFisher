"""User settings: nested dataclasses + YAML load/save/validate.

All "magic numbers" of the app live here (SPEC §7). Defaults are shipped in
``defaults.yaml`` next to this module; a user file (e.g. ``config/settings.yaml``)
overlays the defaults.
"""

# NOTE: no `from __future__ import annotations` here on purpose —
# validation below relies on dataclasses.fields(...).type being real types.

import dataclasses
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_DEFAULTS_PATH = Path(__file__).with_name("defaults.yaml")


class SettingsError(ValueError):
    """Raised when a settings file is malformed or contains invalid values."""


@dataclass
class DetectionCfg:
    model_path: str = "model/albionfisher.pt"
    conf_threshold: float = 0.5
    idle_fps: int = 3
    wait_bite_fps: int = 15  # bite animation is brief — low FPS would miss it
    minigame_fps: int = 20


@dataclass
class TimeoutsCfg:
    """All values are seconds."""

    find_zone: float = 10.0
    cast_confirm: float = 5.0
    bite: float = 30.0
    minigame_start: float = 3.0


@dataclass
class MinigameCfg:
    """Thresholds are fractions of the minigame BAR width (0 = left edge)."""

    hold_below_frac: float = 0.25  # float at <=25% of the bar -> hold LMB
    release_above_frac: float = 0.75  # float at >=75% of the bar -> release LMB


@dataclass
class CastCfg:
    hold_ms: int = 600


@dataclass
class StopCfg:
    max_consecutive_fails: int = 5
    session_limit: int | None = None  # max fish per session; None = unlimited


@dataclass
class Settings:
    detection: DetectionCfg = field(default_factory=DetectionCfg)
    timeouts: TimeoutsCfg = field(default_factory=TimeoutsCfg)
    minigame: MinigameCfg = field(default_factory=MinigameCfg)
    cast: CastCfg = field(default_factory=CastCfg)
    stop: StopCfg = field(default_factory=StopCfg)


_SECTIONS = {
    "detection": DetectionCfg,
    "timeouts": TimeoutsCfg,
    "minigame": MinigameCfg,
    "cast": CastCfg,
    "stop": StopCfg,
}


def _type_ok(value: Any, expected: Any) -> bool:
    if expected is float:
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected is int:
        return isinstance(value, int) and not isinstance(value, bool)
    if expected is str:
        return isinstance(value, str)
    if expected == (int | None):
        return value is None or (isinstance(value, int) and not isinstance(value, bool))
    return isinstance(value, expected)


def _build_section(cls: type, data: dict, section: str) -> Any:
    known = {f.name: f for f in dataclasses.fields(cls)}
    kwargs: dict[str, Any] = {}
    for key, value in data.items():
        if key not in known:
            raise SettingsError(f"unknown setting '{section}.{key}'")
        expected = known[key].type
        if not _type_ok(value, expected):
            raise SettingsError(
                f"invalid type for '{section}.{key}': expected {expected}, "
                f"got {type(value).__name__} ({value!r})"
            )
        if expected is float:
            value = float(value)
        kwargs[key] = value
    return cls(**kwargs)


def _validate_semantics(s: Settings) -> None:
    if not 0.0 <= s.detection.conf_threshold <= 1.0:
        raise SettingsError("detection.conf_threshold must be within [0, 1]")
    if (
        s.detection.idle_fps <= 0
        or s.detection.wait_bite_fps <= 0
        or s.detection.minigame_fps <= 0
    ):
        raise SettingsError("detection FPS values must be positive")
    for name in ("find_zone", "cast_confirm", "bite", "minigame_start"):
        if getattr(s.timeouts, name) <= 0:
            raise SettingsError(f"timeouts.{name} must be positive")
    if not 0.0 <= s.minigame.hold_below_frac < s.minigame.release_above_frac <= 1.0:
        raise SettingsError(
            "minigame thresholds must satisfy 0 <= hold_below_frac < release_above_frac <= 1"
        )
    if s.cast.hold_ms <= 0:
        raise SettingsError("cast.hold_ms must be positive")
    if s.stop.max_consecutive_fails <= 0:
        raise SettingsError("stop.max_consecutive_fails must be positive")
    if s.stop.session_limit is not None and s.stop.session_limit <= 0:
        raise SettingsError("stop.session_limit must be positive or null")


def _load_yaml(path: Path) -> dict:
    import yaml  # lazy so importing this module never requires PyYAML

    with open(path, encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise SettingsError(f"settings file {path} must contain a YAML mapping")
    return data


def settings_from_dict(data: dict) -> Settings:
    """Build validated :class:`Settings` from a nested plain dict."""
    kwargs: dict[str, Any] = {}
    for section, value in data.items():
        if section not in _SECTIONS:
            raise SettingsError(f"unknown settings section '{section}'")
        if not isinstance(value, dict):
            raise SettingsError(f"section '{section}' must be a mapping")
        kwargs[section] = _build_section(_SECTIONS[section], value, section)
    settings = Settings(**kwargs)
    _validate_semantics(settings)
    return settings


def load_settings(path: "str | Path | None" = None) -> Settings:
    """Load shipped defaults, overlay the user file at *path* if it exists."""
    merged = _load_yaml(_DEFAULTS_PATH)
    if path is not None:
        user_path = Path(path)
        if user_path.exists():
            user = _load_yaml(user_path)
            for section, value in user.items():
                if isinstance(value, dict) and isinstance(merged.get(section), dict):
                    merged[section].update(value)
                else:
                    merged[section] = value
    return settings_from_dict(merged)


def save_settings(settings: Settings, path: "str | Path") -> None:
    import yaml  # lazy

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        yaml.safe_dump(dataclasses.asdict(settings), fh, sort_keys=False)
