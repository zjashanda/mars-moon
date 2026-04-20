#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Build project-specific deviceInfo for the Dooya curtain test runner."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

try:
    from pypinyin import Style, lazy_pinyin
except ImportError:  # pragma: no cover - optional dependency
    Style = None
    lazy_pinyin = None


ROOT = Path(__file__).resolve().parents[1]
WORK_DIR = ROOT / "work"
GENERATED_DIR = ROOT / "generated"


DEFAULT_REGEX = {
    "wakeKw": r'.*keyword":"(.*?)".*intentStr.*',
    "asrKw": r'.*intentStr":"(.*?)".*',
    "sendMsg": r".*send msg::\s*(([0-9A-Fa-f]{2}\s*)+)",
    "recvMsg": r".*receive msg::\s*(([0-9A-Fa-f]{2}\s*)+)",
    "playId": r".*play id : (\d+)",
    "wakeReady": r".*(wake up ready to asr(?: mode)?).*",
    "configSaved": r".*(save config success).*",
    "timeoutEvent": r".*(TIME_OUT).*",
    "volume": r".*volume\s*:\s*(\d+)",
    "wakeup": r".*wakeup\s*[:=]\s*(\d+)",
    "workMode": r".*(?:work mode\s*:\s*|work_mode\s*[:=]\s*)(\d+)",
    "curtainMode": r".*(?:curtain type\s*:\s*|curtain_type\s*[:=]\s*)(\d+)",
    "modeState": r".*MODE=(\d+)",
    "configRefresh": r".*(refresh config .*).*",
    "factoryRestore": r".*(restore factory mode).*",
    "curtainSettingEntry": r".*(into set curtain type).*",
    "factoryMode": r".*factory mode\s*:\s*(\d+)",
    "reboot": r".*(reboot by user).*",
    "rebootReason": r".*RESET=(.*)",
    "powerOn": r".*vcc_power:(\d+)",
    "version": r".*version\s*:\s*(V[^\s]+)",
    "sdkVersion": r".*SDK:\s*(.*)",
    "shellVersion": r".*VER:\s*(.*)",
}


REGEX_CANDIDATES = {
    "wakeKw": [
        r'.*ncmThreshold.*keyword\\":\\"(.*?)\\".*intentStr.*',
        r'.*keyword\\":\\"(.*?)\\".*intentStr.*',
        r'.*keyword":"(.*?)".*intentStr.*',
        r'.*keyword["\s:=]+([^"\\,]+).*intent.*',
    ],
    "asrKw": [
        r'.*ncmThreshold.*keyword.*intentStr\\":\\"(.*?)\\".*',
        r'.*intentStr\\":\\"(.*?)\\".*',
        r'.*intentStr":"(.*?)".*',
        r'.*intent[Ss]tr["\s:=]+([^"\\,]+).*',
    ],
    "sendMsg": [
        r".*send msg::\s*(([0-9A-Fa-f]{2}\s*)+)",
        r".*send msg:\s*(([0-9A-Fa-f]{2}\s*)+)",
        r".*sendMsg::\s*(([0-9A-Fa-f]{2}\s*)+)",
        r".*send_msg[:\s]+(([0-9A-Fa-f]{2}\s*)+)",
    ],
    "recvMsg": [
        r".*receive msg::\s*(([0-9A-Fa-f]{2}\s*)+)",
        r".*receive msg:\s*(([0-9A-Fa-f]{2}\s*)+)",
        r".*recv msg::\s*(([0-9A-Fa-f]{2}\s*)+)",
        r".*recvMsg::\s*(([0-9A-Fa-f]{2}\s*)+)",
    ],
    "playId": [
        r".*play id : (\d+)",
        r".*play id: (\d+)",
        r".*play id :(\d+)",
        r".*playId[:\s]+(\d+)",
    ],
    "wakeReady": [
        r".*(wake up ready to asr(?: mode)?).*",
        r".*(wake up ready to asr).*",
    ],
    "configSaved": [
        r".*(save config success).*",
    ],
    "timeoutEvent": [
        r".*(TIME_OUT).*",
    ],
    "volume": [
        r".*volume\s*:\s*(\d+)",
        r".*volume\] set scale_vol : (.*)",
        r".*set scale_vol : (.*)",
        r".*scale_vol\s*:\s*(.*)",
    ],
    "wakeup": [
        r".*wakeup\s*[:=]\s*(\d+)",
    ],
    "workMode": [
        r".*work mode\s*:\s*(\d+)",
        r".*work_mode\s*[:=]\s*(\d+)",
    ],
    "curtainMode": [
        r".*curtain type\s*:\s*(\d+)",
        r".*curtain_type\s*[:=]\s*(\d+)",
    ],
    "modeState": [
        r".*MODE=(\d+)",
    ],
    "configRefresh": [
        r".*(refresh config .*).*",
    ],
    "factoryRestore": [
        r".*(restore factory mode).*",
    ],
    "curtainSettingEntry": [
        r".*(into set curtain type).*",
    ],
    "factoryMode": [
        r".*factory mode\s*:\s*(\d+)",
        r".*factory_mode\s*[:=]\s*(\d+)",
        r".*factory.*mode.*?(\d+)",
    ],
    "reboot": [
        r".*(reboot by user).*",
        r".*(reboot).*",
    ],
    "rebootReason": [
        r".*RESET=(.*)",
        r".*boot reason[:\s]+(.*)",
        r".*Boot Reason[:\s]+(.*)",
        r".*reboot reason[:\s]+(.*)",
    ],
    "powerOn": [
        r".*vcc_power:(\d+)",
        r".*power on[:\s]+(.*)",
    ],
    "version": [
        r".*version\s*:\s*(V[^\s]+)",
        r".*VER:\s*(.*)",
    ],
    "sdkVersion": [
        r".*SDK:\s*(.*)",
    ],
    "shellVersion": [
        r".*VER:\s*(.*)",
    ],
}


TTS_CONFIG = {
    "app_id": "5af3aa4f",
    "api_key": "fe85d97976354eeeaf3d0122fb44ba2b",
    "vcn": "x4_yezi",
    "speed": "50",
    "pitch": "50",
    "volume": "100",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def unique_keep_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if not item or item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def find_latest_legacy_deviceinfo() -> Path | None:
    candidates: list[Path] = []
    direct = GENERATED_DIR / "deviceInfo_dooya.json"
    if direct.is_file():
        candidates.append(direct)
    for pattern in [
        "work/*/generated/deviceInfo_dooya.json",
        "work/*/result/*/deviceInfo_dooya.json",
    ]:
        candidates.extend(path for path in ROOT.glob(pattern) if path.is_file())
    if not candidates:
        return None
    candidates.sort(key=lambda item: item.stat().st_mtime, reverse=True)
    return candidates[0]


def load_legacy_spell2zh() -> dict[str, str]:
    legacy = find_latest_legacy_deviceinfo()
    if not legacy:
        return {}
    try:
        payload = json.loads(legacy.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    mapping = payload.get("spell2zh", {})
    if not isinstance(mapping, dict):
        return {}
    return {
        str(key).strip(): str(value).strip()
        for key, value in mapping.items()
        if str(key).strip() and str(value).strip()
    }


def pinyin_variants(text: str) -> set[str]:
    if lazy_pinyin is None or Style is None:
        return {text.strip()} if text and text.strip() else set()
    tone3 = lazy_pinyin(text, style=Style.TONE3, neutral_tone_with_five=True)
    normal = lazy_pinyin(text, style=Style.NORMAL)
    variants = {
        text,
        " ".join(tone3),
        "".join(tone3),
        " ".join(normal),
        "".join(normal),
    }
    return {variant.strip() for variant in variants if variant and variant.strip()}


def build_word_list(spec: dict[str, Any], cases: list[dict[str, Any]]) -> list[str]:
    words: list[str] = []
    wake_rules = spec["behavior_rules"]["wake_word_setting"]
    words.append(wake_rules["default_wake_word"])
    words.extend(wake_rules.get("candidate_wake_words", []))
    if wake_rules.get("candidate_wake_words"):
        words.append(wake_rules["candidate_wake_words"][0])
    words.append("嘀嗒模式")
    words.append("滴答模式")
    words.append("语音模式")
    for row in spec["word_sheet"]["rows"]:
        words.append(row["semantic"])
    for case_item in cases:
        for action in case_item["actions"]:
            if action["type"] in {"wake", "say", "assert_wake_repeats"}:
                words.append(action["word"])
            elif action["type"] == "assert_no_wake":
                words.extend(action.get("words", []))
            elif action["type"] == "phrase_check":
                wake_word = str(action.get("wake_word", "")).strip()
                if wake_word:
                    words.append(wake_word)
                for item in action.get("items", []):
                    word = str(item.get("word", "")).strip()
                    if word:
                        words.append(word)
    return unique_keep_order(words)


def build_kw2protocol(spec: dict[str, Any]) -> dict[str, str]:
    kw2protocol: dict[str, str] = {}
    for row in spec["word_sheet"]["rows"]:
        semantic = row["semantic"]
        send_protocol = (row.get("send_protocol") or "").strip()
        if semantic and send_protocol:
            kw2protocol[semantic] = send_protocol.upper()

    factory_reset = spec["behavior_rules"].get("factory_reset", {})
    entry = factory_reset.get("entry", {})
    entry_word = str(entry.get("semantic", "")).strip()
    send_protocol = str(entry.get("send_protocol", "")).strip().upper()
    if entry_word and send_protocol and entry_word not in kw2protocol:
        kw2protocol[entry_word] = send_protocol

    return kw2protocol


def build_absorb(kw2protocol: dict[str, str]) -> dict[str, list[str]]:
    absorb: dict[str, list[str]] = {}
    proto_groups: dict[str, list[str]] = defaultdict(list)
    for word, protocol in kw2protocol.items():
        proto_groups[protocol].append(word)

    for words in proto_groups.values():
        if len(words) < 2:
            continue
        for word in words:
            absorb[word] = [other for other in words if other != word]

    mode_aliases = ["滴答模式", "嘀嗒模式"]
    for word in mode_aliases:
        absorb[word] = [other for other in mode_aliases if other != word]

    return dict(sorted(absorb.items()))


def build_spell2zh(words: list[str], absorb: dict[str, list[str]]) -> dict[str, str]:
    spell2zh: dict[str, str] = load_legacy_spell2zh()
    for word in words:
        for variant in pinyin_variants(word):
            spell2zh.setdefault(variant, word)
    for word, aliases in absorb.items():
        for alias in aliases:
            for variant in pinyin_variants(alias):
                spell2zh.setdefault(variant, alias)
    return dict(sorted(spell2zh.items()))


def main() -> None:
    GENERATED_DIR.mkdir(exist_ok=True)
    spec = load_json(WORK_DIR / "normalized_spec.json")
    cases = load_json(GENERATED_DIR / "cases.json")

    if lazy_pinyin is None:
        legacy = find_latest_legacy_deviceinfo()
        if legacy:
            print(f"pypinyin 未安装，回退复用历史 spell2zh: {legacy}")
        else:
            print("pypinyin 未安装，未找到历史 spell2zh，仅输出中文原文映射")

    word_list = build_word_list(spec, cases)
    kw2protocol = build_kw2protocol(spec)
    absorb = build_absorb(kw2protocol)
    spell2zh = build_spell2zh(word_list, absorb)
    work_mode_candidates = spec.get("behavior_rules", {}).get("work_mode_setting", {}).get("candidates", []) or []
    tick_candidate = next(
        (
            item
            for item in work_mode_candidates
            if str(item.get("semantic", "")).strip() in {"滴答模式", "嘀嗒模式"}
        ),
        {},
    )
    wake_tone_by_work_mode = {
        "0": ["TONE_ID_0"],
    }
    tick_tone_id = str(tick_candidate.get("tone_id", "")).strip()
    if tick_tone_id:
        wake_tone_by_work_mode["1"] = [tick_tone_id]

    config = {
        "projectInfo": spec["requirement"]["project"]["project_name"],
        "projectBranch": spec["requirement"]["project"]["branch_name"],
        "firmwareVersion": spec["requirement"]["project"]["firmware_version"],
        "wakeupWord": spec["behavior_rules"]["wake_word_setting"]["default_wake_word"],
        "wordList": word_list,
        "kw2protocol": kw2protocol,
        "spell2zh": spell2zh,
        "absorb": absorb,
        "ttsConfig": TTS_CONFIG,
        "commandRandom": 0,
        "caseSource": {
            "json": str((GENERATED_DIR / "cases.json").relative_to(ROOT)).replace("\\", "/"),
            "workbook": str((GENERATED_DIR / "CSK5062_杜亚窗帘_测试用例.xlsx").relative_to(ROOT)).replace("\\", "/"),
        },
        "deviceListInfo": {
            "cskApLog": {
                "port": spec["runtime"]["log_port"]["port"],
                "baudRate": spec["runtime"]["log_port"]["baudrate"],
                "regex": DEFAULT_REGEX,
                "regexCandidates": REGEX_CANDIDATES,
            },
            "uart1": {
                "port": spec["runtime"]["protocol_port"]["port"],
                "baudRate": spec["runtime"]["protocol_port"]["baudrate"],
                "frameHeader": "55 AA",
                "frameLength": 8,
                "hexUpper": True,
            },
        },
        "executionPolicy": {
            "resultRoot": "result",
            "resultDirTimeFormat": "%m%d%H%M%S",
            "wavRoot": "wavSource",
            "toolLogName": "tool.log",
            "serialLogName": "serial_raw.log",
            "protocolLogName": "protocol_raw.log",
            "regexDiscoveryLogName": "regex_discovery_raw.log",
            "resultWorkbookName": "testResult.xlsx",
            "summaryName": "execution_summary.md",
            "loglevelCommand": spec["runtime"]["loglevel_command"],
            "rebootCommand": spec["runtime"]["reboot_command"],
            "wakeRetries": 10,
            "commandRetries": 3,
            "rebootRetries": 5,
            "silenceObserveS": 2.5,
            "commandObserveS": 3.0,
            "postWakeGapS": 2.0,
            "postBootReadyDelayS": 4.0,
            "rebootRecoveryS": 30.0,
            "setLogLevelRetries": 5,
            "wakeToneByWorkMode": wake_tone_by_work_mode,
            "wakeReadyMarkers": ["wake up ready to asr"],
            "requireWakeReadySignal": True,
            "requireWakeProtocolWhenConfigured": True,
        },
        "pretestConfig": {
            "enabled": False,
            "ctrlPort": "",
            "ctrlBaudRate": 115200,
            "powerOnCmds": [],
            "cmdDelay": 0.3,
            "bootWait": 5.0,
            "note": "控制上下电接口暂未接入；掉电类用例先以 manual_power_cycle 动作占位。",
        },
        "gaps": spec.get("gaps", []),
    }

    output_path = GENERATED_DIR / "deviceInfo_dooya.json"
    write_json(output_path, config)
    print(f"Wrote {output_path}")
    print(f"word_count={len(word_list)}")
    print(f"protocol_word_count={len(kw2protocol)}")
    print(f"absorb_count={len(absorb)}")


if __name__ == "__main__":
    main()
