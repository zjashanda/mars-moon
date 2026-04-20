#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Probe scripts for the protocol UART and the audio-to-device chain."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import time
from pathlib import Path
from typing import Any

import serial


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sample.voiceTestLite import SerialReader, play_audio
from tools.audio_playback import get_last_playback_report
from serial_port_config import get_serial_defaults
from tools.dooya_voice_runner import DEFAULT_CONFIG, ToolLogger, load_json


COMMON_BAUDS = [1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200, 230400]
DEFAULT_SERIAL_PORTS = get_serial_defaults()


def default_protocol_port() -> str:
    return str(DEFAULT_SERIAL_PORTS["protocol_port"])


def make_result_dir() -> Path:
    path = ROOT / "result" / dt.datetime.now().strftime("%m%d%H%M%S")
    path.mkdir(parents=True, exist_ok=True)
    return path


class RawSerialTap:
    def __init__(self, port: str, baudrate: int, log_path: Path, logger: ToolLogger) -> None:
        self.port = port
        self.baudrate = baudrate
        self.log_path = log_path
        self.logger = logger
        self.ser: serial.Serial | None = None
        self.byte_count = 0
        self.lines: list[str] = []

    def connect(self) -> bool:
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=0.05)
            self.logger.info(f"协议探针已连接: {self.port} @ {self.baudrate}")
            return True
        except Exception as exc:
            self.logger.error(f"协议探针连接失败: {self.port} @ {self.baudrate} | {exc}")
            return False

    def capture(self, seconds: float) -> dict[str, Any]:
        assert self.ser is not None
        deadline = time.time() + seconds
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as fp:
            while time.time() < deadline:
                chunk = self.ser.read(self.ser.in_waiting or 1)
                if not chunk:
                    continue
                self.byte_count += len(chunk)
                hex_line = " ".join(f"{item:02X}" for item in chunk)
                text = chunk.decode("utf-8", errors="ignore").strip()
                line = f"[{dt.datetime.now().strftime('%H:%M:%S.%f')[:-3]}] {hex_line}"
                if text:
                    line += f" | {text}"
                fp.write(line + "\n")
                fp.flush()
                self.lines.append(line)
        return {
            "baudrate": self.baudrate,
            "byte_count": self.byte_count,
            "sample": self.lines[:20],
        }

    def write_hex(self, value: str) -> None:
        assert self.ser is not None
        hex_text = "".join(ch for ch in value if ch not in {" ", "\t", "\r", "\n"})
        self.ser.write(bytes.fromhex(hex_text))

    def close(self) -> None:
        if self.ser and self.ser.is_open:
            self.ser.close()


def ensure_loglevel(reader: SerialReader, logger: ToolLogger, retries: int = 5) -> bool:
    for index in range(retries):
        before = len(reader.get_recent_lines())
        logger.info(f"设置 loglevel 4，第 {index + 1}/{retries} 次")
        reader.write("loglevel 4")
        deadline = time.time() + 2.5
        while time.time() < deadline:
            time.sleep(0.2)
            if len(reader.get_recent_lines()) > before:
                return True
    return False


def probe_baud_scan(args: argparse.Namespace) -> int:
    config = load_json(Path(args.config))
    result_dir = make_result_dir()
    logger = ToolLogger(result_dir, verbose=not args.quiet)
    csk = config["deviceListInfo"]["cskApLog"]
    reader = SerialReader(
        args.log_port or csk["port"],
        args.log_baud or csk["baudRate"],
        csk.get("regex", {}),
        logger,
        serial_log_dir=str(result_dir),
    )
    summary: dict[str, Any] = {
        "mode": "baud_scan",
        "time": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "log_port": args.log_port or csk["port"],
        "uart_port": args.uart_port,
        "observe_s": args.observe_s,
        "results": [],
    }
    if not reader.connect():
        logger.close()
        return 2
    reader.start()
    try:
        time.sleep(1.0)
        if args.ensure_loglevel and not ensure_loglevel(reader, logger):
            logger.error("波特率扫描前 loglevel 4 设置失败")
            return 3
        bauds = [int(item.strip()) for item in (args.bauds.split(",") if args.bauds else COMMON_BAUDS) if item.strip()]
        for index, baud in enumerate(bauds, start=1):
            tap = RawSerialTap(args.uart_port, baud, result_dir / f"protocol_scan_{baud}.log", logger)
            if not tap.connect():
                summary["results"].append({"baudrate": baud, "status": "open_failed"})
                continue
            try:
                reader.clear()
                reboot_before = reader.get_reboot_count()
                logger.info(f"[{index}/{len(bauds)}] 扫描波特率 {baud}")
                reader.write("reboot")
                reboot_deadline = time.time() + 6.0
                saw_reboot = False
                while time.time() < reboot_deadline:
                    time.sleep(0.2)
                    if reader.get_reboot_count() > reboot_before or reader.is_rebooted():
                        saw_reboot = True
                        reader.clear_reboot_flag()
                        break
                capture = tap.capture(args.observe_s)
                capture["status"] = "ok"
                capture["saw_reboot"] = saw_reboot
                summary["results"].append(capture)
                time.sleep(args.post_reboot_wait_s)
            finally:
                tap.close()
    finally:
        reader.close()
        logger.close()
    (result_dir / "probe_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


def probe_audio(args: argparse.Namespace) -> int:
    config = load_json(Path(args.config))
    result_dir = make_result_dir()
    logger = ToolLogger(result_dir, verbose=not args.quiet)
    csk = config["deviceListInfo"]["cskApLog"]
    reader = SerialReader(
        args.log_port or csk["port"],
        args.log_baud or csk["baudRate"],
        csk.get("regex", {}),
        logger,
        serial_log_dir=str(result_dir),
    )
    summary: dict[str, Any] = {
        "mode": "audio_probe",
        "time": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "word": args.word,
        "audio_file": "",
        "repeat": args.repeat,
        "observe_s": args.observe_s,
        "results": [],
    }
    if not reader.connect():
        logger.close()
        return 2
    reader.start()
    try:
        time.sleep(1.0)
        if args.ensure_loglevel and not ensure_loglevel(reader, logger):
            logger.error("音频探针前 loglevel 4 设置失败")
            return 3
        audio_file = Path(args.audio_file) if args.audio_file else ROOT / "wavSource" / f"{args.word}.mp3"
        summary["audio_file"] = str(audio_file)
        if not audio_file.is_file():
            logger.error(f"音频文件不存在: {audio_file}")
            return 4
        for index in range(args.repeat):
            reader.clear()
            logger.info(f"音频探针轮次 {index + 1}/{args.repeat}")
            play_ok = play_audio(str(audio_file), logger)
            time.sleep(args.observe_s)
            summary["results"].append(
                {
                    "round": index + 1,
                    "play_ok": play_ok,
                    "playback_route": get_last_playback_report(),
                    "wakeKw": reader.get_all("wakeKw"),
                    "asrKw": reader.get_all("asrKw"),
                    "sendMsg": reader.get_all("sendMsg"),
                    "recvMsg": reader.get_all("recvMsg"),
                    "playId": reader.get_all("playId"),
                    "recent_lines": reader.get_recent_lines()[-20:],
                }
            )
    finally:
        reader.close()
        logger.close()
    (result_dir / "probe_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


def probe_inject_scan(args: argparse.Namespace) -> int:
    config = load_json(Path(args.config))
    result_dir = make_result_dir()
    logger = ToolLogger(result_dir, verbose=not args.quiet)
    csk = config["deviceListInfo"]["cskApLog"]
    reader = SerialReader(
        args.log_port or csk["port"],
        args.log_baud or csk["baudRate"],
        csk.get("regex", {}),
        logger,
        serial_log_dir=str(result_dir),
    )
    summary: dict[str, Any] = {
        "mode": "inject_scan",
        "time": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "log_port": args.log_port or csk["port"],
        "uart_port": args.uart_port,
        "protocol": args.protocol,
        "observe_s": args.observe_s,
        "results": [],
    }
    if not reader.connect():
        logger.close()
        return 2
    reader.start()
    try:
        time.sleep(1.0)
        if args.ensure_loglevel and not ensure_loglevel(reader, logger):
            logger.error("协议注入扫描前 loglevel 4 设置失败")
            return 3
        bauds = [int(item.strip()) for item in (args.bauds.split(",") if args.bauds else COMMON_BAUDS) if item.strip()]
        for index, baud in enumerate(bauds, start=1):
            tap = RawSerialTap(args.uart_port, baud, result_dir / f"inject_scan_{baud}.log", logger)
            if not tap.connect():
                summary["results"].append({"baudrate": baud, "status": "open_failed"})
                continue
            try:
                logger.info(f"[{index}/{len(bauds)}] 注入扫描波特率 {baud}")
                reader.clear()
                before_lines = len(reader.get_recent_lines())
                tap.write_hex(args.protocol)
                capture = tap.capture(args.observe_s)
                recent = reader.get_recent_lines()
                summary["results"].append(
                    {
                        "baudrate": baud,
                        "status": "ok",
                        "protocol_rx_bytes": capture["byte_count"],
                        "protocol_rx_sample": capture["sample"],
                        "log_delta": len(recent) - before_lines,
                        "wakeKw": reader.get_all("wakeKw"),
                        "asrKw": reader.get_all("asrKw"),
                        "sendMsg": reader.get_all("sendMsg"),
                        "recvMsg": reader.get_all("recvMsg"),
                        "playId": reader.get_all("playId"),
                        "recent_lines": recent[-20:],
                    }
                )
            finally:
                tap.close()
    finally:
        reader.close()
        logger.close()
    (result_dir / "probe_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Dooya link probe")
    sub = parser.add_subparsers(dest="mode", required=True)

    baud_scan = sub.add_parser("baud-scan", help="重启联动的协议串口波特率扫描")
    baud_scan.add_argument("-f", "--config", default=str(DEFAULT_CONFIG))
    baud_scan.add_argument("--log-port", default="")
    baud_scan.add_argument("--log-baud", type=int, default=0)
    baud_scan.add_argument("--uart-port", default=default_protocol_port())
    baud_scan.add_argument("--bauds", default="")
    baud_scan.add_argument("--observe-s", type=float, default=8.0)
    baud_scan.add_argument("--post-reboot-wait-s", type=float, default=4.0)
    baud_scan.add_argument("--ensure-loglevel", action="store_true")
    baud_scan.add_argument("--quiet", action="store_true")

    audio_probe = sub.add_parser("audio-probe", help="单音频日志探针")
    audio_probe.add_argument("-f", "--config", default=str(DEFAULT_CONFIG))
    audio_probe.add_argument("--log-port", default="")
    audio_probe.add_argument("--log-baud", type=int, default=0)
    audio_probe.add_argument("--word", default="你好杜亚")
    audio_probe.add_argument("--audio-file", default="")
    audio_probe.add_argument("--repeat", type=int, default=3)
    audio_probe.add_argument("--observe-s", type=float, default=3.0)
    audio_probe.add_argument("--ensure-loglevel", action="store_true")
    audio_probe.add_argument("--quiet", action="store_true")

    inject_scan = sub.add_parser("inject-scan", help="跨波特率协议注入探针")
    inject_scan.add_argument("-f", "--config", default=str(DEFAULT_CONFIG))
    inject_scan.add_argument("--log-port", default="")
    inject_scan.add_argument("--log-baud", type=int, default=0)
    inject_scan.add_argument("--uart-port", default=default_protocol_port())
    inject_scan.add_argument("--protocol", required=True)
    inject_scan.add_argument("--bauds", default="")
    inject_scan.add_argument("--observe-s", type=float, default=3.0)
    inject_scan.add_argument("--ensure-loglevel", action="store_true")
    inject_scan.add_argument("--quiet", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.mode == "baud-scan":
        raise SystemExit(probe_baud_scan(args))
    if args.mode == "audio-probe":
        raise SystemExit(probe_audio(args))
    if args.mode == "inject-scan":
        raise SystemExit(probe_inject_scan(args))
    raise SystemExit(1)


if __name__ == "__main__":
    main()

    main()
