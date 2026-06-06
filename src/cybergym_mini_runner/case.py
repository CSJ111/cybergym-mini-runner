from __future__ import annotations

import json
import shutil
import tarfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CaseInfo:
    case_dir: Path
    task_id: str
    readme: str
    description: str
    workspace: Path


def load_case(case_dir: Path, run_dir: Path) -> CaseInfo:
    case_dir = case_dir.resolve()
    if not case_dir.is_dir():
        raise FileNotFoundError(f"case directory not found: {case_dir}")
    readme = _read_optional(case_dir / "README.md")
    description = _read_optional(case_dir / "description.txt")
    task_id = _task_id_from_case(case_dir, readme)
    workspace = (run_dir / "workspace").resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    _prepare_workspace(case_dir, workspace)
    return CaseInfo(case_dir=case_dir, task_id=task_id, readme=readme, description=description, workspace=workspace)


def _read_optional(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""


def _task_id_from_case(case_dir: Path, readme: str) -> str:
    meta_path = case_dir / "case_meta.json"
    if meta_path.is_file():
        payload = json.loads(meta_path.read_text(encoding="utf-8"))
        if isinstance(payload.get("task_id"), str):
            return payload["task_id"]
    for line in readme.splitlines():
        if "task_id" in line.lower() and ":" in line:
            return line.split(":", 1)[1].strip()
    name = case_dir.name
    if "_" in name:
        family, ident = name.split("_", 1)
        if family in {"arvo", "oss-fuzz", "oss-fuzz-latest"}:
            return f"{family}:{ident}"
    return name


def _prepare_workspace(case_dir: Path, workspace: Path) -> None:
    archive = case_dir / "repo-vul.tar.gz"
    if archive.is_file() and not any(workspace.iterdir()):
        with tarfile.open(archive, "r:gz") as tar:
            _safe_extract(tar, workspace)
    for name in ("README.md", "description.txt"):
        src = case_dir / name
        if src.is_file():
            shutil.copy2(src, workspace / name)


def _safe_extract(tar: tarfile.TarFile, destination: Path) -> None:
    dest = destination.resolve()
    for member in tar.getmembers():
        target = (dest / member.name).resolve()
        if not str(target).startswith(str(dest)):
            raise RuntimeError(f"unsafe tar member path: {member.name}")
    tar.extractall(dest)
