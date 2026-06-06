from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass
class StepRecord:
    step: int
    thought: str
    action: str
    observation: str
    timestamp: str
    command: str | None = None
    path: str | None = None
    exit_code: int | None = None


@dataclass
class FinalReport:
    task_id: str
    model: str
    success: bool
    submitted_poc: bool
    steps: int
    timeout: bool
    failure_type: str


class TrajectoryWriter:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, record: StepRecord) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
