from __future__ import annotations

import os
import re
from pathlib import Path


class SafetyError(RuntimeError):
    pass


DENIED_COMMAND_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\b(sudo|su|doas)\b",
        r"\b(nmap|masscan|zmap|hping3|nping|ettercap|mitmproxy)\b",
        r"\b(ssh|scp|sftp|telnet|ftp|rlogin|rsync)\b",
        r"\b(curl|wget|aria2c|python\s+-m\s+http\.server)\b",
        r"\b(pip\s+install|npm\s+install|apt(-get)?\s+install|yum\s+install|dnf\s+install)\b",
        r"\b(chown|mount|umount|iptables|nft|sysctl|modprobe|insmod|rmmod)\b",
        r"\b(mkfs|fdisk|parted|dd\s+if=|shutdown|reboot|poweroff)\b",
        r"rm\s+-[^\n]*[rf][^\n]*\s+(/|\$HOME|~)",
        r":\(\)\s*\{\s*:\|:",
        r"(^|[\s;|&])cd\s+/",
        r"(/etc|/proc|/sys|/dev|/root)\b",
    )
)


def resolve_workspace_path(workspace: Path, user_path: str) -> Path:
    if "\x00" in user_path:
        raise SafetyError("path contains NUL byte")
    candidate = Path(user_path)
    if not candidate.is_absolute():
        candidate = workspace / candidate
    resolved_workspace = workspace.resolve()
    resolved = candidate.resolve()
    if os.path.commonpath([str(resolved_workspace), str(resolved)]) != str(resolved_workspace):
        raise SafetyError(f"path escapes workspace: {user_path}")
    return resolved


def validate_shell_command(command: str) -> None:
    if not command.strip():
        raise SafetyError("empty shell command")
    if len(command) > 4000:
        raise SafetyError("shell command is too long")
    for pattern in DENIED_COMMAND_PATTERNS:
        if pattern.search(command):
            raise SafetyError(f"command rejected by safety policy: {pattern.pattern}")
