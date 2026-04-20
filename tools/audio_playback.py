#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Route bundle audio playback through the listenai-play skill when available."""

from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from tools.audio_device_config import current_platform_key, get_audio_defaults, update_audio_defaults
from tools.codex_skill_bootstrap import ensure_runtime_skills


SCAN_CACHE_TTL_S = 5.0
CODEX_HOME = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
LISTENAI_PLAY_SCRIPT = CODEX_HOME / "skills" / "listenai-play" / "scripts" / "listenai_play.py"

_SCAN_CACHE: dict[str, dict[str, Any]] = {}
_LAST_PLAYBACK_REPORT: dict[str, Any] = {}


def _log(log: Any, level: str, message: str) -> None:
    method = getattr(log, level, None) or getattr(log, "info", None)
    if callable(method):
        method(message)


def _timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _set_last_report(report: dict[str, Any]) -> None:
    global _LAST_PLAYBACK_REPORT
    _LAST_PLAYBACK_REPORT = copy.deepcopy(report)


def get_last_playback_report() -> dict[str, Any]:
    return copy.deepcopy(_LAST_PLAYBACK_REPORT)


def _format_devices(items: list[dict[str, Any]]) -> str:
    if not items:
        return "none"
    return "; ".join(
        f"{item.get('device_key', '')} ({item.get('name', '')} -> {item.get('backend_target', '')})"
        for item in items
    )


def _run_listenai_play(command: list[str]) -> subprocess.CompletedProcess[str]:
    ensure_runtime_skills()
    if not LISTENAI_PLAY_SCRIPT.is_file():
        raise RuntimeError(f"listenai-play script not found: {LISTENAI_PLAY_SCRIPT}")
    return subprocess.run(
        [sys.executable, str(LISTENAI_PLAY_SCRIPT), *command],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def _scan_render_devices(platform_key: str, force: bool = False) -> list[dict[str, Any]]:
    cached = _SCAN_CACHE.get(platform_key)
    now = time.time()
    if cached and not force and now - float(cached.get("timestamp", 0.0)) <= SCAN_CACHE_TTL_S:
        return copy.deepcopy(cached.get("items", []))

    result = _run_listenai_play(["scan", "--platform", platform_key, "--direction", "Render", "--json"])
    if result.returncode != 0:
        details = (result.stderr or result.stdout or "listenai-play scan failed").strip()
        raise RuntimeError(details)

    payload = (result.stdout or "").strip() or "[]"
    items = json.loads(payload)
    if isinstance(items, dict):
        items = [items]
    if not isinstance(items, list):
        raise RuntimeError("listenai-play scan returned an unexpected payload")

    normalized = [item for item in items if isinstance(item, dict)]
    _SCAN_CACHE[platform_key] = {"timestamp": now, "items": copy.deepcopy(normalized)}
    return normalized


def _find_record(items: list[dict[str, Any]], device_key: str) -> dict[str, Any] | None:
    target = (device_key or "").strip().upper()
    if not target:
        return None
    for item in items:
        if str(item.get("device_key", "")).strip().upper() == target:
            return copy.deepcopy(item)
    return None


def _log_listenai_output(log: Any, result: subprocess.CompletedProcess[str]) -> None:
    for line in (result.stdout or "").splitlines():
        line = line.strip()
        if line:
            _log(log, "info", f"[listenai-play] {line}")
    for line in (result.stderr or "").splitlines():
        line = line.strip()
        if line:
            _log(log, "warn", f"[listenai-play] {line}")


def _attempt_skill_play(
    audio_file: Path,
    platform_key: str,
    device_key: str | None,
    log: Any,
) -> tuple[bool, subprocess.CompletedProcess[str] | None, str]:
    command = ["play", "--platform", platform_key, "--audio-file", str(audio_file)]
    if device_key:
        command.extend(["--device-key", device_key])
    try:
        result = _run_listenai_play(command)
    except Exception as exc:  # pylint: disable=broad-except
        return False, None, str(exc)

    _log_listenai_output(log, result)
    if result.returncode == 0:
        return True, result, ""
    details = (result.stderr or result.stdout or f"listenai-play exited with {result.returncode}").strip()
    return False, result, details


def _persist_success(
    platform_key: str,
    route_mode: str,
    record: dict[str, Any] | None,
    error: str = "",
) -> None:
    updates: dict[str, Any] = {
        "last_route_mode": route_mode,
        "last_success_at": _timestamp(),
        "last_error": error,
    }
    if record:
        updates.update(
            {
                "playback_device_key": str(record.get("device_key", "")).strip(),
                "last_verified_device_key": str(record.get("device_key", "")).strip(),
                "last_verified_device_name": str(record.get("name", "")).strip(),
                "last_verified_backend_target": str(record.get("backend_target", "")).strip(),
            }
        )
    update_audio_defaults(platform_key, **updates)


def _persist_failure(platform_key: str, error: str) -> None:
    update_audio_defaults(platform_key, last_error=error)


def play_audio_with_routing(
    filepath: str,
    log: Any,
    legacy_player: Callable[[str, Any], bool] | None = None,
) -> bool:
    audio_file = Path(filepath).resolve()
    if not audio_file.is_file():
        message = f"音频不存在: {audio_file}"
        _persist_failure(current_platform_key(), message)
        _set_last_report({"status": "failed", "message": message, "audio_file": str(audio_file)})
        _log(log, "error", message)
        return False

    platform_key = current_platform_key()
    config = get_audio_defaults(platform_key)
    preferred_key = str(config.get("playback_device_key", "")).strip()
    default_mode = str(config.get("default_device_mode", "auto")).strip().lower() or "auto"
    allow_default_fallback = bool(config.get("use_default_when_unavailable", True))

    try:
        ensure_runtime_skills(log=log)
    except Exception as exc:  # pylint: disable=broad-except
        _log(log, "warn", f"外部 Codex skills 准备失败：{exc}")

    report: dict[str, Any] = {
        "status": "pending",
        "audio_file": str(audio_file),
        "platform": platform_key,
        "config": {
            "playback_device_key": preferred_key,
            "default_device_mode": default_mode,
            "use_default_when_unavailable": allow_default_fallback,
        },
        "selected_route": "",
        "selected_device_key": "",
        "fallback_used": False,
        "message": "",
        "active_render_devices": [],
    }

    def finalize(ok: bool, message: str, route: str, record: dict[str, Any] | None = None) -> bool:
        report["status"] = "success" if ok else "failed"
        report["message"] = message
        report["selected_route"] = route
        report["selected_device_key"] = str(record.get("device_key", "")).strip() if record else ""
        _set_last_report(report)
        if ok:
            _persist_success(platform_key, route, record)
        else:
            _persist_failure(platform_key, message)
        return ok

    def try_default(reason: str) -> bool:
        report["fallback_used"] = True
        _log(log, "warn", f"回退默认声卡播放：{reason}")
        ok, _, error = _attempt_skill_play(audio_file, platform_key, None, log)
        if ok:
            return finalize(True, f"默认声卡播放成功：{reason}", "default")
        if legacy_player is not None:
            _log(log, "warn", f"listenai-play 默认声卡播放失败，尝试历史默认播放链路：{error}")
            legacy_ok = legacy_player(str(audio_file), log)
            if legacy_ok:
                return finalize(True, f"历史默认播放链路成功：{reason}", "default")
        return finalize(False, f"默认声卡播放失败：{error}", "default")

    if default_mode == "force_default":
        _log(log, "info", "声卡配置指定为显式默认声卡，跳过设备 key 绑定。")
        ok, _, error = _attempt_skill_play(audio_file, platform_key, None, log)
        if ok:
            return finalize(True, "显式默认声卡播放成功", "default")
        if legacy_player is not None:
            _log(log, "warn", f"listenai-play 显式默认声卡播放失败，尝试历史默认播放链路：{error}")
            legacy_ok = legacy_player(str(audio_file), log)
            if legacy_ok:
                return finalize(True, "历史默认播放链路成功（显式默认声卡模式）", "default")
        return finalize(False, f"显式默认声卡播放失败：{error}", "default")

    if preferred_key:
        _log(log, "info", f"优先使用配置声卡播报：{preferred_key}")
        ok, _, error = _attempt_skill_play(audio_file, platform_key, preferred_key, log)
        if ok:
            matched = None
            try:
                scan_items = _scan_render_devices(platform_key, force=True)
            except Exception as exc:  # pylint: disable=broad-except
                report["active_render_devices"] = []
                _log(log, "warn", f"指定声卡播放已成功，但补充扫描声卡信息失败：{exc}")
            else:
                report["active_render_devices"] = scan_items
                matched = _find_record(scan_items, preferred_key)
            message = f"指定声卡播报成功：{preferred_key}"
            if matched:
                message = f"指定声卡播报成功：{preferred_key} -> {matched.get('backend_target', '')}"
            return finalize(True, message, "device_key", matched)

        _log(log, "warn", f"指定声卡播报失败：{preferred_key} | {error}")
        if not allow_default_fallback:
            return finalize(False, f"指定声卡播报失败且已禁用默认声卡回退：{error}", "device_key")

        try:
            scan_items = _scan_render_devices(platform_key, force=True)
        except Exception as exc:  # pylint: disable=broad-except
            return finalize(False, f"指定声卡播报失败，且重新扫描声卡失败：{exc}", "device_key")

        report["active_render_devices"] = scan_items
        if len(scan_items) > 1:
            detail = _format_devices(scan_items)
            return finalize(
                False,
                "当前检测到多个 ListenAI 播放设备，禁止自动回退默认声卡；"
                f"当前设备列表：{detail}；请测试人员指定其他声卡或显式默认声卡后再继续。",
                "device_key",
            )
        return try_default(f"配置声卡不可用：{preferred_key}")

    try:
        scan_items = _scan_render_devices(platform_key, force=True)
    except Exception as exc:  # pylint: disable=broad-except
        report["active_render_devices"] = []
        if legacy_player is not None:
            _log(log, "warn", f"listenai-play 扫描失败，尝试历史默认播放链路：{exc}")
            legacy_ok = legacy_player(str(audio_file), log)
            if legacy_ok:
                return finalize(True, "历史默认播放链路成功（listenai-play 扫描失败）", "default")
        return finalize(False, f"声卡扫描失败：{exc}", "default")

    report["active_render_devices"] = scan_items
    if len(scan_items) > 1:
        detail = _format_devices(scan_items)
        return finalize(
            False,
            "当前检测到多个 ListenAI 播放设备，禁止自动使用默认声卡；"
            f"当前设备列表：{detail}；请测试人员指定其他声卡或显式默认声卡后再继续。",
            "default",
        )

    ok, _, error = _attempt_skill_play(audio_file, platform_key, None, log)
    if ok:
        return finalize(True, "默认声卡播放成功", "default")
    if legacy_player is not None:
        _log(log, "warn", f"listenai-play 默认声卡播放失败，尝试历史默认播放链路：{error}")
        legacy_ok = legacy_player(str(audio_file), log)
        if legacy_ok:
            return finalize(True, "历史默认播放链路成功", "default")
    return finalize(False, f"默认声卡播放失败：{error}", "default")
