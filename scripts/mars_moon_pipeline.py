#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Self-contained pipeline entrypoint for the marsMoon skill."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterable


SKILL_ROOT = Path(__file__).resolve().parents[1]
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from tools.serial_port_config import get_serial_defaults
from tools.codex_skill_bootstrap import (
    REFRESH_ENV,
    available_skill_names,
    collect_skill_status,
    ensure_skills,
    format_report as format_skill_report,
)

MARKER_NAME = ".marsmoon_workspace.json"
DEFAULT_WORKSPACE = "marsmoon-workspace"
DEFAULT_REFERENCE = SKILL_ROOT / "assets" / "reference" / "CSK5062_杜亚窗帘_测试用例v2.xlsx"
DEFAULT_SUPPLEMENT = SKILL_ROOT / "assets" / "reference" / "需求和用例补充说明.txt"
EMBEDDED_BURN_BUNDLE = "burn_bundle"
WINDOWS_BURN_DIR = "windows"
LINUX_BURN_DIR = "linux"
IGNORES = shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo")
DEFAULT_SERIAL_PORTS = get_serial_defaults()
DEFAULT_CTRL_PORT = str(DEFAULT_SERIAL_PORTS["ctrl_port"])
DEFAULT_BURN_PORT = str(DEFAULT_SERIAL_PORTS["burn_port"])
DEFAULT_LOG_PORT = str(DEFAULT_SERIAL_PORTS["log_port"])
DEFAULT_PROTOCOL_PORT = str(DEFAULT_SERIAL_PORTS["protocol_port"])
DEFAULT_CTRL_BAUD = int(DEFAULT_SERIAL_PORTS["ctrl_baud"])
DEFAULT_LOG_BAUD = int(DEFAULT_SERIAL_PORTS["log_baud"])
DEFAULT_PROTOCOL_BAUD = int(DEFAULT_SERIAL_PORTS["protocol_baud"])
DEFAULT_BURN_BAUD = int(DEFAULT_SERIAL_PORTS["burn_baud"])


def resolve_path(value: str) -> Path:
    return Path(value).expanduser().resolve()


def workspace_root(value: str) -> Path:
    return resolve_path(value or DEFAULT_WORKSPACE)


def current_burn_platform() -> str:
    return WINDOWS_BURN_DIR if sys.platform.startswith("win") else LINUX_BURN_DIR


def ensure_file(path: Path, label: str) -> Path:
    if not path.is_file():
        raise FileNotFoundError(f"{label}不存在: {path}")
    return path


def is_runtime_workspace(path: Path) -> bool:
    required = [
        path / "tools",
        path / "sample",
        path / "generated",
        path / "work",
    ]
    return path.is_dir() and all(item.exists() for item in required)


def ensure_workspace(path: Path) -> Path:
    marker = path / MARKER_NAME
    if not path.is_dir():
        raise FileNotFoundError(f"workspace 不存在: {path}")
    # Allow both prepared timestamp workspaces and the checked-in skill root.
    if marker.is_file() or is_runtime_workspace(path):
        return path
    raise FileNotFoundError(f"未找到可用 workspace 布局: {path}")


def copy_tree(src: Path, dst: Path) -> None:
    if not src.is_dir():
        raise FileNotFoundError(f"目录不存在: {src}")
    shutil.copytree(src, dst, dirs_exist_ok=True, ignore=IGNORES)


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def sync_runtime_sources(workspace: Path) -> None:
    ensure_workspace(workspace)
    copy_tree(SKILL_ROOT / "tools", workspace / "tools")
    copy_tree(SKILL_ROOT / "sample", workspace / "sample")
    copy_tree(SKILL_ROOT / "scripts", workspace / "scripts")


def write_marker(path: Path, payload: dict[str, object]) -> None:
    marker = path / MARKER_NAME
    marker.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_marker(path: Path) -> dict[str, object]:
    workspace = ensure_workspace(path)
    marker_path = workspace / MARKER_NAME
    if marker_path.is_file():
        return json.loads(marker_path.read_text(encoding="utf-8"))
    return {
        "skill_root": str(SKILL_ROOT),
        "workspace": str(workspace),
        "artifacts": {
            "firmware_copy": "artifacts/firmware/firmware.bin",
            "burn_dir": "artifacts/burn",
            "burn_log": "artifacts/burn/burn.log",
            "burn_tool_log": "artifacts/burn/burn_tool.log",
            "generated_dir": "generated",
            "work_dir": "work",
            "result_dir": "result",
        },
    }


def save_marker(path: Path, payload: dict[str, object]) -> None:
    write_marker(path, payload)


def read_json_if_exists(path: Path) -> dict[str, object]:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def workspace_runtime_serial_defaults(workspace: Path) -> dict[str, object]:
    settings: dict[str, object] = {
        "ctrl_port": DEFAULT_CTRL_PORT,
        "ctrl_baud": DEFAULT_CTRL_BAUD,
        "burn_port": DEFAULT_BURN_PORT,
        "burn_baud": DEFAULT_BURN_BAUD,
        "log_port": DEFAULT_LOG_PORT,
        "log_baud": DEFAULT_LOG_BAUD,
        "protocol_port": DEFAULT_PROTOCOL_PORT,
        "protocol_baud": DEFAULT_PROTOCOL_BAUD,
    }
    marker = read_json_if_exists(workspace / MARKER_NAME)
    hardware = marker.get("hardware", {})
    if isinstance(hardware, dict):
        for key in settings:
            value = hardware.get(key)
            if value not in (None, ""):
                settings[key] = value

    normalized_spec = read_json_if_exists(workspace / "work" / "normalized_spec.json")
    runtime = normalized_spec.get("runtime", {})
    if isinstance(runtime, dict):
        log_cfg = runtime.get("log_port", {})
        if isinstance(log_cfg, dict):
            if log_cfg.get("port"):
                settings["log_port"] = log_cfg["port"]
            if log_cfg.get("baudrate"):
                settings["log_baud"] = log_cfg["baudrate"]
        proto_cfg = runtime.get("protocol_port", {})
        if isinstance(proto_cfg, dict):
            if proto_cfg.get("port"):
                settings["protocol_port"] = proto_cfg["port"]
            if proto_cfg.get("baudrate"):
                settings["protocol_baud"] = proto_cfg["baudrate"]

    device_info = read_json_if_exists(workspace / "generated" / "deviceInfo_dooya.json")
    device_list = device_info.get("deviceListInfo", {})
    if isinstance(device_list, dict):
        log_cfg = device_list.get("cskApLog", {})
        if isinstance(log_cfg, dict):
            if log_cfg.get("port"):
                settings["log_port"] = log_cfg["port"]
            if log_cfg.get("baudRate"):
                settings["log_baud"] = log_cfg["baudRate"]
        proto_cfg = device_list.get("uart1", {})
        if isinstance(proto_cfg, dict):
            if proto_cfg.get("port"):
                settings["protocol_port"] = proto_cfg["port"]
            if proto_cfg.get("baudRate"):
                settings["protocol_baud"] = proto_cfg["baudRate"]
    power_cfg = device_info.get("powerControl", {})
    if isinstance(power_cfg, dict):
        if power_cfg.get("port"):
            settings["ctrl_port"] = power_cfg["port"]
        if power_cfg.get("baudRate"):
            settings["ctrl_baud"] = power_cfg["baudRate"]

    normalized: dict[str, object] = {}
    for key, value in settings.items():
        if key.endswith("_baud"):
            normalized[key] = int(value)
        else:
            normalized[key] = str(value)
    return normalized


def build_workspace_manifest(
    workspace: Path,
    requirement_doc: Path,
    word_table: Path,
    tone_file: Path,
    firmware_bin: Path | None,
    supplement_txt: Path,
    reference_cases: Path,
) -> dict[str, object]:
    prepared_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    return {
        "skill_root": str(SKILL_ROOT),
        "workspace": str(workspace),
        "run_id": run_id,
        "prepared_at": prepared_at,
        "inputs": {
            "requirement_doc": str(requirement_doc),
            "word_table": str(word_table),
            "tone_file": str(tone_file),
            "firmware_bin": str(firmware_bin) if firmware_bin else "",
            "supplement_txt": str(supplement_txt),
            "reference_cases": str(reference_cases),
        },
        "hardware": {
            "ctrl_port": DEFAULT_CTRL_PORT,
            "ctrl_baud": DEFAULT_CTRL_BAUD,
            "burn_port": DEFAULT_BURN_PORT,
            "log_port": DEFAULT_LOG_PORT,
            "log_baud": DEFAULT_LOG_BAUD,
            "protocol_port": DEFAULT_PROTOCOL_PORT,
            "protocol_baud": DEFAULT_PROTOCOL_BAUD,
            "burn_baud": DEFAULT_BURN_BAUD,
        },
        "artifacts": {
            "firmware_copy": "artifacts/firmware/firmware.bin",
            "burn_dir": "artifacts/burn",
            "burn_log": "artifacts/burn/burn.log",
            "burn_tool_log": "artifacts/burn/burn_tool.log",
            "generated_dir": "generated",
            "work_dir": "work",
            "result_dir": "result",
        },
    }


def ensure_runtime_layout(path: Path) -> None:
    for relative in [
        "需求",
        "用例skill参考",
        "tools",
        "sample",
        "generated",
        "work",
        "result",
        "wavSource",
        "artifacts",
        "artifacts/firmware",
        "artifacts/burn",
    ]:
        (path / relative).mkdir(parents=True, exist_ok=True)


def prepare_workspace(
    workspace: Path,
    requirement_doc: Path,
    word_table: Path,
    tone_file: Path,
    firmware_bin: Path | None,
    supplement_txt: Path,
    reference_cases: Path,
) -> Path:
    ensure_runtime_layout(workspace)
    copy_tree(SKILL_ROOT / "tools", workspace / "tools")
    copy_tree(SKILL_ROOT / "sample", workspace / "sample")
    copy_tree(SKILL_ROOT / "scripts", workspace / "scripts")
    copy_tree(SKILL_ROOT / "wavSource", workspace / "wavSource")

    copy_file(requirement_doc, workspace / "需求" / "需求文档.md")
    copy_file(word_table, workspace / "需求" / "词条处理.xlsx")
    copy_file(tone_file, workspace / "需求" / "tone.h")
    copy_file(supplement_txt, workspace / "需求" / "需求和用例补充说明.txt")
    copy_file(reference_cases, workspace / "用例skill参考" / "CSK5062_杜亚窗帘_测试用例v2.xlsx")
    if firmware_bin:
        copy_file(firmware_bin, workspace / "artifacts" / "firmware" / "firmware.bin")

    write_marker(
        workspace,
        build_workspace_manifest(
            workspace,
            requirement_doc,
            word_table,
            tone_file,
            firmware_bin,
            supplement_txt,
            reference_cases,
        ),
    )
    print(f"[marsMoon] workspace 已准备: {workspace}")
    return workspace


def run_python(
    workspace: Path,
    script_relative: str,
    extra_args: Iterable[str] | None = None,
    *,
    check: bool = True,
    env_updates: dict[str, str] | None = None,
) -> int:
    command = [sys.executable, str(workspace / script_relative)]
    if extra_args:
        command.extend(extra_args)
    print(f"[marsMoon] 执行: {' '.join(command)}")
    env = os.environ.copy()
    if env_updates:
        env.update(env_updates)
    completed = subprocess.run(command, cwd=str(workspace), check=False, env=env)
    if check and completed.returncode != 0:
        raise subprocess.CalledProcessError(completed.returncode, command)
    return completed.returncode


def build_assets(workspace: Path) -> None:
    ensure_workspace(workspace)
    run_python(workspace, "tools/dooya_spec_builder.py")
    run_python(workspace, "tools/dooya_case_builder.py")
    run_python(workspace, "tools/dooya_deviceinfo_builder.py")

    device_info_path = workspace / "generated" / "deviceInfo_dooya.json"
    if device_info_path.is_file():
        device_info = json.loads(device_info_path.read_text(encoding="utf-8"))
        device_info["workspaceRoot"] = str(workspace)
        device_info["powerControl"] = {
            "port": DEFAULT_CTRL_PORT,
            "baudRate": DEFAULT_CTRL_BAUD,
            "commandDelayMs": 300,
            "powerOffCmds": ["uut-switch1.off", "uut-switch2.off"],
            "powerOnCmds": ["uut-switch1.on"],
            "note": "复用当前 bundle 内置的控制口上下电逻辑",
        }
        pretest = device_info.setdefault("pretestConfig", {})
        pretest["enabled"] = True
        pretest["ctrlPort"] = DEFAULT_CTRL_PORT
        pretest["ctrlBaudRate"] = DEFAULT_CTRL_BAUD
        pretest["powerOnCmds"] = ["uut-switch1.on"]
        pretest["cmdDelay"] = 0.3
        pretest["bootWait"] = 8.0
        pretest["note"] = "已接入控制口，上下电类用例复用当前 bundle 内置控制逻辑。"
        device_info_path.write_text(json.dumps(device_info, ensure_ascii=False, indent=2), encoding="utf-8")
    marker = load_marker(workspace)
    hardware = marker.setdefault("hardware", {})
    resolved_runtime = workspace_runtime_serial_defaults(workspace)
    hardware.update(
        {
            "ctrl_port": resolved_runtime["ctrl_port"],
            "ctrl_baud": resolved_runtime["ctrl_baud"],
            "burn_port": str(hardware.get("burn_port", DEFAULT_BURN_PORT) or DEFAULT_BURN_PORT),
            "burn_baud": int(hardware.get("burn_baud", DEFAULT_BURN_BAUD) or DEFAULT_BURN_BAUD),
            "log_port": resolved_runtime["log_port"],
            "log_baud": resolved_runtime["log_baud"],
            "protocol_port": resolved_runtime["protocol_port"],
            "protocol_baud": resolved_runtime["protocol_baud"],
        }
    )
    save_marker(workspace, marker)
    print(f"[marsMoon] build 完成: {workspace}")


def require_built_outputs(workspace: Path) -> None:
    ensure_workspace(workspace)
    needed = [
        workspace / "generated" / "cases.json",
        workspace / "generated" / "deviceInfo_dooya.json",
        workspace / "generated" / "CSK5062_杜亚窗帘_测试用例.xlsx",
    ]
    missing = [str(path) for path in needed if not path.is_file()]
    if missing:
        raise FileNotFoundError("缺少 build 产物，请先执行 build:\n" + "\n".join(missing))


def firmware_copy_path(workspace: Path) -> Path:
    marker = load_marker(workspace)
    rel = marker["artifacts"]["firmware_copy"]
    return workspace / str(rel)


def workspace_has_firmware(workspace: Path) -> bool:
    return firmware_copy_path(workspace).is_file()


def burn_dir_path(workspace: Path) -> Path:
    marker = load_marker(workspace)
    rel = marker["artifacts"]["burn_dir"]
    return workspace / str(rel)


def is_burn_bundle_dir(path: Path) -> bool:
    windows_ready = path.is_dir() and (path / "burn.ps1").is_file() and (path / "Uart_Burn_Tool.exe").is_file()
    linux_ready = path.is_dir() and (path / "burn.sh").is_file() and (path / "Uart_Burn_Tool").is_file()
    return windows_ready or linux_ready


def burn_bundle_candidates(base: Path) -> list[Path]:
    bundle_root = base / EMBEDDED_BURN_BUNDLE
    platform_dir = current_burn_platform()
    return [
        bundle_root / platform_dir,
        bundle_root,
    ]


def find_local_burn_bundle_source(workspace: Path) -> Path | None:
    marker = load_marker(workspace)
    inputs = marker.get("inputs", {}) if isinstance(marker, dict) else {}
    firmware_bin = str(inputs.get("firmware_bin", "")).strip() if isinstance(inputs, dict) else ""
    candidates: list[Path] = []
    candidates.extend(burn_bundle_candidates(workspace / "tools"))
    candidates.extend(burn_bundle_candidates(SKILL_ROOT / "tools"))
    if firmware_bin:
        firmware_burn_root = Path(firmware_bin).expanduser().resolve().parent / "burn"
        candidates.append(firmware_burn_root / current_burn_platform())
        candidates.append(firmware_burn_root)
    workspace_burn_root = workspace / "burn"
    candidates.append(workspace_burn_root / current_burn_platform())
    candidates.append(workspace_burn_root)
    for candidate in candidates:
        if is_burn_bundle_dir(candidate):
            return candidate
    return None


def install_burn_bundle(workspace: Path) -> Path:
    if not workspace_has_firmware(workspace):
        raise FileNotFoundError(f"workspace 中未找到固件副本: {firmware_copy_path(workspace)}")
    burn_dir = burn_dir_path(workspace)
    burn_dir.mkdir(parents=True, exist_ok=True)
    bundle_source = find_local_burn_bundle_source(workspace)
    if not bundle_source:
        expected_script = "burn.ps1 / Uart_Burn_Tool.exe" if current_burn_platform() == WINDOWS_BURN_DIR else "burn.sh / Uart_Burn_Tool"
        raise FileNotFoundError(
            f"未找到适用于当前环境({current_burn_platform()})的烧录工具包；请优先在 tools/{EMBEDDED_BURN_BUNDLE}/{current_burn_platform()} 中提供 {expected_script}。"
        )
    if bundle_source.resolve() != burn_dir.resolve():
        print(f"[marsMoon] 复制本地 burn bundle: {bundle_source} -> {burn_dir}")
        copy_tree(bundle_source, burn_dir)
    copy_file(firmware_copy_path(workspace), burn_dir / "firmware.bin")
    return burn_dir


def burn_args_from_namespace(args: argparse.Namespace, workspace: Path) -> list[str]:
    runtime_defaults = workspace_runtime_serial_defaults(workspace)
    result = [
        "-FirmwareBin",
        str(Path(".") / "firmware.bin"),
        "-CtrlPort",
        str(args.ctrl_port or runtime_defaults["ctrl_port"]),
        "-BurnPort",
        str(args.burn_port or runtime_defaults["burn_port"]),
        "-CtrlBaud",
        str(args.ctrl_baud or runtime_defaults["ctrl_baud"]),
        "-LogBaud",
        str(args.log_baud or runtime_defaults["log_baud"]),
        "-BurnBaud",
        str(args.burn_baud or runtime_defaults["burn_baud"]),
        "-MaxRetry",
        str(args.burn_retry if args.burn_retry is not None else 3),
    ]
    if args.verify_only:
        result.append("-VerifyOnly")
    if args.skip_loglevel:
        result.append("-SkipLoglevel")
    return result


def run_burn(workspace: Path, args: argparse.Namespace) -> None:
    ensure_workspace(workspace)
    install_burn_bundle(workspace)
    burn_dir = burn_dir_path(workspace)
    if current_burn_platform() == WINDOWS_BURN_DIR:
        script = burn_dir / "burn.ps1"
        if not script.is_file():
            raise FileNotFoundError(f"未找到烧录脚本: {script}")
        command = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script),
            *burn_args_from_namespace(args, workspace),
        ]
    else:
        script = burn_dir / "burn.sh"
        if not script.is_file():
            raise FileNotFoundError(f"未找到烧录脚本: {script}")
        command = [
            "bash",
            str(script),
            *burn_args_from_namespace(args, workspace),
        ]
    print(f"[marsMoon] 执行烧录: {' '.join(command)}")
    subprocess.run(command, cwd=str(burn_dir), check=True)


def runner_args_from_namespace(args: argparse.Namespace, workspace: Path) -> list[str]:
    runtime_defaults = workspace_runtime_serial_defaults(workspace)
    result: list[str] = []
    result.extend(["--result-dir", str(workspace / "result" / datetime.now().strftime("%m%d%H%M%S"))])
    result.extend(["--ctrl-port", str(args.ctrl_port or runtime_defaults["ctrl_port"])])
    result.extend(["--ctrl-baud", str(args.ctrl_baud or runtime_defaults["ctrl_baud"])])
    if args.case_id:
        result.extend(["--case-id", str(args.case_id)])
    if args.module:
        result.extend(["--module", str(args.module)])
    if args.priority:
        result.extend(["--priority", str(args.priority)])
    if args.limit:
        result.extend(["--limit", str(args.limit)])
    result.extend(["--log-port", str(args.log_port or runtime_defaults["log_port"])])
    result.extend(["--log-baud", str(getattr(args, "log_baud", 0) or runtime_defaults["log_baud"])])
    result.extend(["--uart1-port", str(args.uart1_port or runtime_defaults["protocol_port"])])
    result.extend(["--uart1-baud", str(args.uart1_baud or runtime_defaults["protocol_baud"])])
    if args.uart1_frame_header:
        result.extend(["--uart1-frame-header", str(args.uart1_frame_header)])
    if args.uart1_frame_length:
        result.extend(["--uart1-frame-length", str(args.uart1_frame_length)])
    if args.failed_case_reruns is not None:
        result.extend(["--failed-case-reruns", str(args.failed_case_reruns)])
    if args.dry_run:
        result.append("--dry-run")
    if args.manual_block_as_fail:
        result.append("--manual-block-as-fail")
    if args.quiet:
        result.append("--quiet")
    return result


def run_runner(workspace: Path, args: argparse.Namespace) -> int:
    require_built_outputs(workspace)
    sync_runtime_sources(workspace)
    return run_python(
        workspace,
        "tools/dooya_voice_runner.py",
        runner_args_from_namespace(args, workspace),
        check=False,
        env_updates={REFRESH_ENV: "1"} if getattr(args, "refresh_codex_skills", False) else None,
    )


def run_probe(workspace: Path, mode: str, probe_args: list[str]) -> int:
    ensure_workspace(workspace)
    sync_runtime_sources(workspace)
    cleaned_args = _clean_probe_args(probe_args)
    env_updates = {REFRESH_ENV: "1"} if _probe_refresh_requested(probe_args) else None
    return run_python(workspace, "tools/dooya_link_probe.py", [mode, *cleaned_args], check=False, env_updates=env_updates)


def add_workspace_argument(parser: argparse.ArgumentParser, *, required: bool = False) -> None:
    parser.add_argument(
        "--workspace",
        default="" if required else DEFAULT_WORKSPACE,
        required=required,
        help="目标 workspace 目录；默认是当前目录下的 marsmoon-workspace",
    )


def add_prepare_inputs(parser: argparse.ArgumentParser, *, required: bool) -> None:
    parser.add_argument("--requirement-doc", required=required, default="", help="需求文档路径")
    parser.add_argument("--word-table", required=required, default="", help="词条处理 Excel 路径")
    parser.add_argument("--tone-file", required=required, default="", help="tone.h 路径")
    parser.add_argument("--firmware-bin", required=False, default="", help="可选，待烧录 bin 路径")
    parser.add_argument(
        "--supplement-txt",
        default="",
        help="可选，覆盖默认补充说明；默认使用 skill 内置的 需求和用例补充说明.txt",
    )
    parser.add_argument(
        "--reference-cases",
        default="",
        help="可选，覆盖默认参考 Excel；默认使用 skill 内置资产",
    )


def add_burn_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--ctrl-port", default="", help="控制上下电/boot 串口；默认从 workspace/集中配置解析")
    parser.add_argument("--burn-port", default="", help="烧录串口；默认从 workspace/集中配置解析")
    parser.add_argument("--ctrl-baud", type=int, default=0, help="控制串口波特率；默认从 workspace/集中配置解析")
    parser.add_argument("--log-baud", type=int, default=0, help="烧录后日志串口波特率；有需求文档产物时优先跟随需求文档")
    parser.add_argument("--burn-baud", type=int, default=0, help="烧录工具波特率；默认从 workspace/集中配置解析")
    parser.add_argument("--burn-retry", type=int, default=3, help="烧录重试次数")
    parser.add_argument("--verify-only", action="store_true", help="只做联机验证，不实际烧录")
    parser.add_argument("--skip-loglevel", action="store_true", help="烧录后跳过 loglevel 4")


def add_power_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--ctrl-port", default="", help="控制上下电/boot 串口；默认从 workspace/集中配置解析")
    parser.add_argument("--ctrl-baud", type=int, default=0, help="控制串口波特率；默认从 workspace/集中配置解析")


def add_runner_options(parser: argparse.ArgumentParser, *, include_log_baud: bool = True) -> None:
    parser.add_argument("--case-id", default="", help="只跑指定 case，逗号分隔")
    parser.add_argument("--module", default="", help="只跑指定模块，逗号分隔")
    parser.add_argument("--priority", default="", help="只跑指定优先级，逗号分隔")
    parser.add_argument("--limit", type=int, default=0, help="最多执行前 N 条")
    parser.add_argument("--dry-run", action="store_true", help="仅做静态执行验证")
    parser.add_argument("--manual-block-as-fail", action="store_true", help="把 manual_power_cycle 当作 FAIL")
    parser.add_argument("--quiet", action="store_true", help="减少控制台输出")
    parser.add_argument("--log-port", default="", help="覆盖日志串口")
    if include_log_baud:
        parser.add_argument("--log-baud", type=int, default=0, help="覆盖日志串口波特率；未传时优先沿用需求文档解析值")
    parser.add_argument("--uart1-port", default="", help="覆盖协议串口")
    parser.add_argument("--uart1-baud", type=int, default=0, help="覆盖协议串口波特率；未传时优先沿用需求文档解析值")
    parser.add_argument("--uart1-frame-header", default="", help="覆盖协议帧头，如 55 AA")
    parser.add_argument("--uart1-frame-length", type=int, default=0, help="覆盖协议帧长度")
    parser.add_argument("--failed-case-reruns", type=int, default=2, help="FAIL 用例收尾重跑次数")
    parser.add_argument("--refresh-codex-skills", action="store_true", help="执行前先刷新 listenai-play / listenai-laid-installer")


def add_skill_manager_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--mode", choices=["status", "ensure", "refresh"], default="status", help="status=仅查看，ensure=缺失时安装，refresh=拉取远端更新")
    parser.add_argument("--skill", action="append", default=[], choices=available_skill_names(), help="可选，仅处理指定 skill；默认处理全部")
    parser.add_argument("--json", action="store_true", help="输出 JSON")


def _probe_refresh_requested(probe_args: list[str]) -> bool:
    return "--refresh-codex-skills" in probe_args


def _clean_probe_args(probe_args: list[str]) -> list[str]:
    cleaned_args = list(probe_args)
    if cleaned_args and cleaned_args[0] == "--":
        cleaned_args = cleaned_args[1:]
    return [item for item in cleaned_args if item != "--refresh-codex-skills"]


def run_skill_manager(args: argparse.Namespace) -> int:
    selected = args.skill or None
    if args.mode == "status":
        report = collect_skill_status(selected)
    elif args.mode == "ensure":
        report = ensure_skills(selected=selected, refresh=False)
    else:
        report = ensure_skills(selected=selected, refresh=True)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(format_skill_report(report))
    if args.mode != "status" and any(not item.get("ok") for item in report.get("skills", [])):
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="marsMoon 自包含用例生成、烧录与执行流水线")
    sub = parser.add_subparsers(dest="command", required=True)

    prepare = sub.add_parser("prepare", help="创建独立 workspace 并复制 bundle")
    add_workspace_argument(prepare)
    add_prepare_inputs(prepare, required=True)

    build = sub.add_parser("build", help="在 workspace 内生成 spec/cases/deviceInfo")
    add_workspace_argument(build)

    burn = sub.add_parser("burn", help="在 workspace 内安装 burn bundle 并执行烧录")
    add_workspace_argument(burn)
    add_burn_options(burn)

    run = sub.add_parser("run", help="在 workspace 内执行 runner")
    add_workspace_argument(run)
    add_power_options(run)
    add_runner_options(run, include_log_baud=True)

    full = sub.add_parser("full", help="prepare -> build -> burn -> run")
    add_workspace_argument(full)
    add_prepare_inputs(full, required=True)
    add_burn_options(full)
    add_runner_options(full, include_log_baud=False)

    probe = sub.add_parser("probe", help="透传参数给 workspace 内的 dooya_link_probe.py")
    add_workspace_argument(probe)
    probe.add_argument("--mode", required=True, choices=["baud-scan", "audio-probe", "inject-scan"])
    probe.add_argument("probe_args", nargs=argparse.REMAINDER, help="透传给 probe 脚本的参数")

    skills = sub.add_parser("skills", help="检查或同步 mars-moon 依赖的外部 Codex skills")
    add_skill_manager_options(skills)
    return parser


def prepare_from_args(args: argparse.Namespace) -> Path:
    workspace = workspace_root(args.workspace)
    requirement_doc = ensure_file(resolve_path(args.requirement_doc), "需求文档")
    word_table = ensure_file(resolve_path(args.word_table), "词条处理 Excel")
    tone_file = ensure_file(resolve_path(args.tone_file), "tone.h")
    firmware_bin = ensure_file(resolve_path(args.firmware_bin), "固件 bin") if args.firmware_bin else None
    supplement_txt = ensure_file(
        resolve_path(args.supplement_txt) if args.supplement_txt else DEFAULT_SUPPLEMENT,
        "补充说明",
    )
    reference_cases = ensure_file(
        resolve_path(args.reference_cases) if args.reference_cases else DEFAULT_REFERENCE,
        "参考 Excel",
    )
    return prepare_workspace(
        workspace,
        requirement_doc,
        word_table,
        tone_file,
        firmware_bin,
        supplement_txt,
        reference_cases,
    )


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "skills":
        raise SystemExit(run_skill_manager(args))
    if args.command == "prepare":
        prepare_from_args(args)
        return
    if args.command == "build":
        build_assets(workspace_root(args.workspace))
        return
    if args.command == "burn":
        run_burn(workspace_root(args.workspace), args)
        return
    if args.command == "run":
        raise SystemExit(run_runner(workspace_root(args.workspace), args))
    if args.command == "full":
        workspace = prepare_from_args(args)
        build_assets(workspace)
        if workspace_has_firmware(workspace):
            run_burn(workspace, args)
        else:
            print(f"[marsMoon] workspace 未提供固件，跳过 burn，直接执行最大化直验路径: {workspace}")
        raise SystemExit(run_runner(workspace, args))
    if args.command == "probe":
        raise SystemExit(run_probe(workspace_root(args.workspace), args.mode, args.probe_args))
    raise SystemExit(f"不支持的命令: {args.command}")


if __name__ == "__main__":
    main()
