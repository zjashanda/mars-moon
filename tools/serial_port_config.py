#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Load centralized serial-port defaults for the marsMoon bundle."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "serial_ports.json"

DEFAULT_CONFIG: dict[str, dict[str, Any]] = {
    "windows": {
        "ctrl_port": "COM15",
        "burn_port": "COM14",
        "log_port": "COM14",
        "protocol_port": "COM13",
        "ctrl_baud": 115200,
        "log_baud": 115200,
        "protocol_baud": 9600,
        "burn_baud": 1500000,
    },
    "linux": {
        "ctrl_port": "/dev/ttyACM0",
        "burn_port": "/dev/ttyACM1",
        "log_port": "/dev/ttyACM1",
        "protocol_port": "/dev/ttyACM2",
        "ctrl_baud": 115200,
        "log_baud": 115200,
        "protocol_baud": 9600,
        "burn_baud": 1500000,
    },
}


def current_platform_key() -> str:
    return "windows" if sys.platform.startswith("win") else "linux"


def load_serial_port_matrix() -> dict[str, dict[str, Any]]:
    matrix = {key: value.copy() for key, value in DEFAULT_CONFIG.items()}
    if not CONFIG_PATH.is_file():
        return matrix

    payload = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    for platform_key, defaults in matrix.items():
        overrides = payload.get(platform_key, {})
        if isinstance(overrides, dict):
            defaults.update(overrides)
    return matrix


def get_serial_defaults(platform_key: str | None = None) -> dict[str, Any]:
    key = platform_key or current_platform_key()
    matrix = load_serial_port_matrix()
    if key not in matrix:
        raise KeyError(f"Unsupported platform key: {key}")
    return matrix[key].copy()
