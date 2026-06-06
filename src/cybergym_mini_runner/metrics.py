from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


def load_reports(path: Path) -> list[dict[str, Any]]:
    if path.is_file():
        return [json.loads(path.read_text(encoding="utf-8"))]
    reports = []
    for report_path in sorted(path.rglob("final_report.json")):
        reports.append(json.loads(report_path.read_text(encoding="utf-8")))
    return reports


def summarize_reports(reports: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(reports)
    if total == 0:
        return {
            "total": 0,
            "pass@1": 0.0,
            "submission_rate": 0.0,
            "timeout_rate": 0.0,
            "average_steps": 0.0,
            "failure_distribution": {},
        }
    successes = sum(1 for item in reports if item.get("success") is True)
    submitted = sum(1 for item in reports if item.get("submitted_poc") is True)
    timed_out = sum(1 for item in reports if item.get("timeout") is True)
    steps = [int(item.get("steps", 0)) for item in reports]
    failures = Counter(str(item.get("failure_type", "unknown")) for item in reports if item.get("success") is not True)
    return {
        "total": total,
        "pass@1": successes / total,
        "submission_rate": submitted / total,
        "timeout_rate": timed_out / total,
        "average_steps": sum(steps) / total,
        "failure_distribution": dict(sorted(failures.items())),
    }
