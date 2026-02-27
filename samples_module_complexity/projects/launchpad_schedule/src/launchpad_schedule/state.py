from __future__ import annotations

SETTINGS: dict[str, object] = {}
CACHE: dict[str, object] = {}

def set_setting(key: str, value: object) -> None:
    SETTINGS[key] = value

def get_setting(key: str, default: object | None = None) -> object | None:
    return SETTINGS.get(key, default)
