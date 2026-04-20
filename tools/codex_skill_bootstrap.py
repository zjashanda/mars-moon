#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Bootstrap external Codex skills used by the mars-moon bundle."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CODEX_HOME = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser()
SKILLS_DIR = CODEX_HOME / "skills"
STATE_DIR = CODEX_HOME / "state"
STATE_PATH = STATE_DIR / "mars-moon-skill-bootstrap.json"
BACKUP_DIR = SKILLS_DIR / ".mars-moon-skill-backups"
REFRESH_ENV = "MARS_MOON_REFRESH_CODEX_SKILLS"
GIT_TIMEOUT_ENV = "MARS_MOON_SKILL_GIT_TIMEOUT_S"
DEFAULT_GIT_TIMEOUT_S = 15.0

SKILL_SPECS: dict[str, dict[str, Any]] = {
    "listenai-play": {
        "repo": "https://github.com/zjashanda/listenai-play.git",
        "branch": "main",
        "required_files": [
            "SKILL.md",
            "README.md",
            "scripts/listenai_play.py",
            "scripts/install_laid_linux.sh",
            "scripts/install_laid_windows.ps1",
        ],
    },
    "listenai-laid-installer": {
        "repo": "https://github.com/zjashanda/listenai-laid-installer.git",
        "branch": "main",
        "required_files": [
            "SKILL.md",
            "README.md",
            "scripts/install_laid_linux.sh",
            "scripts/install_laid_windows.ps1",
        ],
    },
}

_RUNTIME_CACHE: dict[str, Any] = {"ensured": False, "refreshed": False, "report": {}}


class SkillBootstrapError(RuntimeError):
    """Raised when required external skills cannot be prepared."""


def _timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _log(log: Any, level: str, message: str) -> None:
    if log is None:
        return
    method = getattr(log, level, None) or getattr(log, "info", None)
    if callable(method):
        method(message)


def _run_command(
    command: list[str],
    *,
    cwd: Path | None = None,
    check: bool = False,
    timeout_s: float | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    merged_env = os.environ.copy()
    merged_env.setdefault("GIT_TERMINAL_PROMPT", "0")
    if env:
        merged_env.update(env)
    try:
        completed = subprocess.run(
            command,
            cwd=str(cwd) if cwd else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=timeout_s,
            env=merged_env,
        )
    except subprocess.TimeoutExpired as exc:
        raise SkillBootstrapError(
            f"command timed out after {float(timeout_s or 0.0):.1f}s: {' '.join(command)}"
        ) from exc
    if check and completed.returncode != 0:
        details = (completed.stderr or completed.stdout or f"command failed: {' '.join(command)}").strip()
        raise SkillBootstrapError(details)
    return completed


def _require_git() -> str:
    git_bin = shutil.which("git")
    if not git_bin:
        raise SkillBootstrapError("当前机器未安装 git，无法自动下载或更新外部 Codex skills")
    return git_bin


def git_timeout_s() -> float:
    raw = str(os.environ.get(GIT_TIMEOUT_ENV, DEFAULT_GIT_TIMEOUT_S)).strip()
    try:
        value = float(raw)
    except ValueError:
        value = DEFAULT_GIT_TIMEOUT_S
    return max(1.0, value)


def _state_payload_fallback() -> dict[str, Any]:
    return {
        "updated_at": "",
        "mode": "",
        "skills": [],
    }


def load_bootstrap_state() -> dict[str, Any]:
    if not STATE_PATH.is_file():
        return _state_payload_fallback()
    try:
        payload = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _state_payload_fallback()
    return payload if isinstance(payload, dict) else _state_payload_fallback()


def write_bootstrap_state(payload: dict[str, Any]) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def available_skill_names() -> list[str]:
    return sorted(SKILL_SPECS)


def target_skill_names(selected: list[str] | None = None) -> list[str]:
    if not selected:
        return available_skill_names()
    unknown = sorted(set(selected) - set(SKILL_SPECS))
    if unknown:
        raise SkillBootstrapError(f"未知 skill: {', '.join(unknown)}")
    return selected


def skill_target_dir(skill_name: str) -> Path:
    return SKILLS_DIR / skill_name


def required_files(skill_name: str) -> list[str]:
    return list(SKILL_SPECS[skill_name]["required_files"])


def required_files_missing(skill_name: str, target: Path) -> list[str]:
    return [relative for relative in required_files(skill_name) if not (target / relative).exists()]


def is_git_checkout(target: Path) -> bool:
    return (target / ".git").exists()


def git_output(target: Path, *args: str) -> str:
    git_bin = _require_git()
    completed = _run_command([git_bin, "-C", str(target), *args], check=True)
    return (completed.stdout or "").strip()


def git_commit(target: Path) -> str:
    if not is_git_checkout(target):
        return ""
    try:
        return git_output(target, "rev-parse", "HEAD")
    except SkillBootstrapError:
        return ""


def git_branch(target: Path) -> str:
    if not is_git_checkout(target):
        return ""
    try:
        return git_output(target, "rev-parse", "--abbrev-ref", "HEAD")
    except SkillBootstrapError:
        return ""


def git_dirty(target: Path) -> bool:
    if not is_git_checkout(target):
        return False
    try:
        output = git_output(target, "status", "--short")
    except SkillBootstrapError:
        return True
    return bool(output.strip())


def git_remote_url(target: Path) -> str:
    if not is_git_checkout(target):
        return ""
    try:
        return git_output(target, "remote", "get-url", "origin")
    except SkillBootstrapError:
        return ""


def backup_skill_dir(target: Path) -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backup = BACKUP_DIR / f"{target.name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    shutil.move(str(target), str(backup))
    return backup


def clone_skill(skill_name: str, target: Path) -> None:
    git_bin = _require_git()
    spec = SKILL_SPECS[skill_name]
    target.parent.mkdir(parents=True, exist_ok=True)
    command = [
        git_bin,
        "clone",
        "--depth",
        "1",
        "--branch",
        str(spec["branch"]),
        str(spec["repo"]),
        str(target),
    ]
    _run_command(command, check=True, timeout_s=git_timeout_s())


def update_skill_checkout(skill_name: str, target: Path) -> str:
    git_bin = _require_git()
    spec = SKILL_SPECS[skill_name]
    before = git_commit(target)
    fetch = _run_command(
        [git_bin, "-C", str(target), "fetch", "--depth", "1", "origin", str(spec["branch"])],
        check=True,
        timeout_s=git_timeout_s(),
    )
    fetched_head = (fetch.stdout or "").strip()
    if not fetched_head:
        try:
            fetched_head = git_output(target, "rev-parse", "FETCH_HEAD")
        except SkillBootstrapError:
            fetched_head = ""
    if before and fetched_head and before == fetched_head:
        return "already_current"
    _run_command(
        [git_bin, "-C", str(target), "merge", "--ff-only", "FETCH_HEAD"],
        check=True,
    )
    after = git_commit(target)
    return "updated" if after and after != before else "already_current"


def collect_skill_status(selected: list[str] | None = None) -> dict[str, Any]:
    skills: list[dict[str, Any]] = []
    for skill_name in target_skill_names(selected):
        target = skill_target_dir(skill_name)
        missing = required_files_missing(skill_name, target) if target.exists() else required_files(skill_name)
        skills.append(
            {
                "name": skill_name,
                "path": str(target),
                "repo": SKILL_SPECS[skill_name]["repo"],
                "branch": SKILL_SPECS[skill_name]["branch"],
                "exists": target.exists(),
                "git_managed": is_git_checkout(target),
                "dirty": git_dirty(target) if target.exists() else False,
                "valid": not missing,
                "missing_files": missing,
                "commit": git_commit(target) if target.exists() else "",
                "git_branch": git_branch(target) if target.exists() else "",
                "remote_url": git_remote_url(target) if target.exists() else "",
            }
        )
    return {
        "updated_at": _timestamp(),
        "mode": "status",
        "skills": skills,
    }


def ensure_skills(
    *,
    selected: list[str] | None = None,
    refresh: bool = False,
    log: Any = None,
) -> dict[str, Any]:
    report = {
        "updated_at": _timestamp(),
        "mode": "refresh" if refresh else "ensure",
        "skills": [],
    }
    for skill_name in target_skill_names(selected):
        target = skill_target_dir(skill_name)
        info: dict[str, Any] = {
            "name": skill_name,
            "path": str(target),
            "repo": SKILL_SPECS[skill_name]["repo"],
            "branch": SKILL_SPECS[skill_name]["branch"],
            "action": "",
            "ok": False,
            "message": "",
            "backup_path": "",
        }
        try:
            if not target.exists():
                _log(log, "info", f"[skill-bootstrap] 缺少 {skill_name}，开始从 Git 下载")
                clone_skill(skill_name, target)
                info["action"] = "cloned"
            elif not is_git_checkout(target):
                missing = required_files_missing(skill_name, target)
                if missing:
                    backup = backup_skill_dir(target)
                    try:
                        clone_skill(skill_name, target)
                    except Exception:
                        shutil.move(str(backup), str(target))
                        raise
                    info["action"] = "recloned_missing_non_git"
                    info["backup_path"] = str(backup)
                elif refresh:
                    backup = backup_skill_dir(target)
                    try:
                        clone_skill(skill_name, target)
                    except Exception:
                        shutil.move(str(backup), str(target))
                        raise
                    info["action"] = "converted_non_git_to_git"
                    info["backup_path"] = str(backup)
                else:
                    info["action"] = "using_existing_non_git"
            else:
                missing = required_files_missing(skill_name, target)
                if missing and git_dirty(target):
                    raise SkillBootstrapError(
                        f"{skill_name} 缺少关键文件且本地存在未提交改动，已停止自动更新：{', '.join(missing)}"
                    )
                if refresh:
                    if git_dirty(target):
                        info["action"] = "dirty_skip"
                        info["message"] = "检测到本地未提交改动，跳过自动更新"
                    else:
                        try:
                            info["action"] = update_skill_checkout(skill_name, target)
                        except Exception as exc:  # pylint: disable=broad-except
                            info["action"] = "refresh_failed_using_existing_git"
                            info["message"] = f"远端刷新失败，继续使用当前版本：{exc}"
                else:
                    info["action"] = "using_existing_git"

            missing_after = required_files_missing(skill_name, target)
            if missing_after:
                raise SkillBootstrapError(f"{skill_name} 仍缺少关键文件：{', '.join(missing_after)}")

            info["ok"] = True
            if not info["message"]:
                info["message"] = "ready"
            info["commit"] = git_commit(target)
            info["git_branch"] = git_branch(target)
            info["git_managed"] = is_git_checkout(target)
            info["dirty"] = git_dirty(target) if target.exists() else False
            info["remote_url"] = git_remote_url(target)
            _log(
                log,
                "info",
                f"[skill-bootstrap] {skill_name}: {info['action']} commit={info['commit'] or 'n/a'}",
            )
        except Exception as exc:  # pylint: disable=broad-except
            info["ok"] = False
            info["message"] = str(exc)
            info["commit"] = git_commit(target) if target.exists() else ""
            info["git_branch"] = git_branch(target) if target.exists() else ""
            info["git_managed"] = is_git_checkout(target) if target.exists() else False
            info["dirty"] = git_dirty(target) if target.exists() and is_git_checkout(target) else False
            info["remote_url"] = git_remote_url(target) if target.exists() else ""
            _log(log, "warn", f"[skill-bootstrap] {skill_name}: {info['message']}")
        report["skills"].append(info)

    write_bootstrap_state(report)
    return report


def report_has_errors(report: dict[str, Any]) -> bool:
    return any(not bool(item.get("ok")) for item in report.get("skills", []))


def format_report(report: dict[str, Any]) -> str:
    lines = [
        f"mode={report.get('mode', '')}",
        f"updated_at={report.get('updated_at', '')}",
    ]
    for item in report.get("skills", []):
        state = item.get("ok")
        if state is None:
            state = item.get("valid")
        lines.append(
            " | ".join(
                [
                    str(item.get("name", "")),
                    "OK" if state else "FAIL",
                    str(item.get("action", "")),
                    str(item.get("commit", "") or "n/a"),
                    str(item.get("message", "")),
                ]
            )
        )
    return "\n".join(lines)


def ensure_runtime_skills(log: Any = None) -> dict[str, Any]:
    refresh = _truthy(os.environ.get(REFRESH_ENV))
    if _RUNTIME_CACHE["ensured"] and (not refresh or _RUNTIME_CACHE["refreshed"]):
        return dict(_RUNTIME_CACHE["report"])

    report = ensure_skills(refresh=refresh, log=log)
    _RUNTIME_CACHE["ensured"] = True
    _RUNTIME_CACHE["refreshed"] = refresh
    _RUNTIME_CACHE["report"] = report
    if report_has_errors(report):
        details = "; ".join(
            f"{item.get('name')}: {item.get('message')}"
            for item in report.get("skills", [])
            if not item.get("ok")
        )
        raise SkillBootstrapError(f"外部 Codex skills 未准备完成：{details}")
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bootstrap external Codex skills used by mars-moon")
    sub = parser.add_subparsers(dest="command", required=True)

    status = sub.add_parser("status", help="查看当前外部 skill 状态")
    status.add_argument("--skill", action="append", dest="skills", default=[], choices=available_skill_names())
    status.add_argument("--json", action="store_true")

    ensure = sub.add_parser("ensure", help="缺失时自动安装外部 skill")
    ensure.add_argument("--skill", action="append", dest="skills", default=[], choices=available_skill_names())
    ensure.add_argument("--json", action="store_true")

    refresh = sub.add_parser("refresh", help="刷新外部 skill 到 Git 远端最新版本")
    refresh.add_argument("--skill", action="append", dest="skills", default=[], choices=available_skill_names())
    refresh.add_argument("--json", action="store_true")

    return parser


def main() -> None:
    args = build_parser().parse_args()
    selected = args.skills or None
    if args.command == "status":
        report = collect_skill_status(selected)
    elif args.command == "ensure":
        report = ensure_skills(selected=selected, refresh=False)
    elif args.command == "refresh":
        report = ensure_skills(selected=selected, refresh=True)
    else:
        raise SystemExit(f"Unsupported command: {args.command}")

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(format_report(report))
    if report_has_errors(report) and args.command != "status":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
