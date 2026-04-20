#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Load centralized playback-device defaults for the marsMoon bundle."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "audio_devices.json"

DEFAULT_CONFIG: dict[str, dict[str, Any]] = {
    "windows": {
        "playback_device_key": "",
        "default_device_mode": "auto",
        "use_default_when_unavailable": True,
        "last_route_mode": "",
        "last_success_at": "",
        "last_verified_device_key": "",
        "last_verified_device_name": "",
        "last_verified_backend_target": "",
        "last_error": "",
    },
    "linux": {
        "playback_device_key": "VID_8765&PID_5678:USB_0_4_3_1_0",
        "default_device_mode": "auto",
        "use_default_when_unavailable": True,
        "last_route_mode": "",
        "last_success_at": "",
        "last_verified_device_key": "",
        "last_verified_device_name": "",
        "last_verified_backend_target": "",
        "last_error": "",
    },
}


def current_platform_key() -> str:
    return "windows" if sys.platform.startswith("win") else "linux"


def load_audio_device_matrix() -> dict[str, dict[str, Any]]:
    matrix = {key: value.copy() for key, value in DEFAULT_CONFIG.items()}
    if not CONFIG_PATH.is_file():
        return matrix

    payload = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    for platform_key, defaults in matrix.items():
        overrides = payload.get(platform_key, {})
        if isinstance(overrides, dict):
            defaults.update(overrides)
    return matrix


def write_audio_device_matrix(matrix: dict[str, dict[str, Any]]) -> None:
    CONFIG_PATH.write_text(json.dumps(matrix, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def get_audio_defaults(platform_key: str | None = None) -> dict[str, Any]:
    key = platform_key or current_platform_key()
    matrix = load_audio_device_matrix()
    if key not in matrix:
        raise KeyError(f"Unsupported platform key: {key}")
    return matrix[key].copy()


def update_audio_defaults(platform_key: str, **updates: Any) -> dict[str, Any]:
    matrix = load_audio_device_matrix()
    if platform_key not in matrix:
        matrix[platform_key] = {}
    matrix[platform_key].update(updates)
    write_audio_device_matrix(matrix)
    return matrix[platform_key].copy()
