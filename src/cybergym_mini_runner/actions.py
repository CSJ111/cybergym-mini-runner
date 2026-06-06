from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class ActionName(StrEnum):
    SHELL = "shell"
    READ_FILE = "read_file"
    WRITE_FILE = "write_file"
    SUBMIT_POC = "submit_poc"
    FINISH = "finish"


@dataclass(frozen=True)
class AgentAction:
    thought: str
    action: ActionName
    command: str | None = None
    path: str | None = None
    content: str | None = None
    poc_path: str | None = None
    reason: str | None = None


class ActionParseError(ValueError):
    pass


def parse_action(raw: str) -> AgentAction:
    candidate = raw.strip()
    try:
        data = json.loads(candidate)
    except json.JSONDecodeError as exc:
        extracted = extract_json_object(candidate)
        if extracted is None:
            raise ActionParseError(f"malformed JSON: {exc.msg}") from exc
        try:
            data = json.loads(extracted)
        except json.JSONDecodeError as second_exc:
            repaired = escape_control_chars_in_strings(extracted)
            try:
                data = json.loads(repaired)
            except json.JSONDecodeError:
                raise ActionParseError(f"malformed JSON: {second_exc.msg}") from second_exc

    if not isinstance(data, dict):
        raise ActionParseError("top-level response must be a JSON object")

    thought = data.get("thought")
    action = data.get("action")
    if not isinstance(thought, str) or not thought.strip():
        raise ActionParseError("field 'thought' must be a non-empty string")
    if action not in {item.value for item in ActionName}:
        raise ActionParseError(f"unsupported action: {action!r}")

    def optional_str(name: str) -> str | None:
        value = data.get(name)
        if value is None:
            return None
        if not isinstance(value, str):
            raise ActionParseError(f"field '{name}' must be a string")
        return value

    parsed = AgentAction(
        thought=thought,
        action=ActionName(action),
        command=optional_str("command"),
        path=optional_str("path"),
        content=optional_str("content"),
        poc_path=optional_str("poc_path") or optional_str("path"),
        reason=optional_str("reason"),
    )
    validate_action(parsed)
    return parsed


def extract_json_object(text: str) -> str | None:
    fenced = text.strip()
    if fenced.startswith("```"):
        lines = fenced.splitlines()
        if len(lines) >= 3 and lines[-1].strip() == "```":
            fenced = "\n".join(lines[1:-1]).strip()
            if fenced.startswith("json"):
                fenced = fenced[4:].strip()
            try:
                json.loads(fenced)
                return fenced
            except json.JSONDecodeError:
                pass

    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    return None


def escape_control_chars_in_strings(text: str) -> str:
    out: list[str] = []
    in_string = False
    escaped = False
    for char in text:
        if in_string:
            if escaped:
                escaped = False
                out.append(char)
            elif char == "\\":
                escaped = True
                out.append(char)
            elif char == '"':
                in_string = False
                out.append(char)
            elif char == "\n":
                out.append("\\n")
            elif char == "\r":
                out.append("\\r")
            elif char == "\t":
                out.append("\\t")
            else:
                out.append(char)
            continue
        if char == '"':
            in_string = True
        out.append(char)
    return "".join(out)


def validate_action(action: AgentAction) -> None:
    if action.action == ActionName.SHELL and not action.command:
        raise ActionParseError("shell action requires 'command'")
    if action.action == ActionName.READ_FILE and not action.path:
        raise ActionParseError("read_file action requires 'path'")
    if action.action == ActionName.WRITE_FILE:
        if not action.path:
            raise ActionParseError("write_file action requires 'path'")
        if action.content is None:
            raise ActionParseError("write_file action requires 'content'")
    if action.action == ActionName.SUBMIT_POC and not action.poc_path:
        raise ActionParseError("submit_poc action requires 'poc_path' or 'path'")


def action_to_public_dict(action: AgentAction) -> dict[str, Any]:
    data: dict[str, Any] = {"thought": action.thought, "action": action.action.value}
    for key in ("command", "path", "content", "poc_path", "reason"):
        value = getattr(action, key)
        if value is not None:
            data[key] = value
    if "content" in data and len(data["content"]) > 200:
        data["content"] = data["content"][:200] + "...<truncated>"
    return data
