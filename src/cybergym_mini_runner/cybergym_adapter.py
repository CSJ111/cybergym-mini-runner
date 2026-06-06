from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


SUBSET_TASK_IDS = (
    "arvo:47101",
    "arvo:3938",
    "arvo:24993",
    "arvo:1065",
    "arvo:10400",
    "arvo:368",
    "oss-fuzz:42535201",
    "oss-fuzz:42535468",
    "oss-fuzz:370689421",
    "oss-fuzz:385167047",
)


@dataclass(frozen=True)
class CyberGymPaths:
    root: Path
    data_dir: Path
    mask_map: Path | None


def discover_paths(cybergym_root: Path | None, data_dir: Path | None, mask_map: Path | None) -> CyberGymPaths:
    root = cybergym_root or Path(os.environ.get("CYBERGYM_ROOT", "../cybergym"))
    root = root.resolve()
    data = data_dir or Path(os.environ.get("CYBERGYM_DATA_DIR", "../cybergym_data/data"))
    data = data.resolve()
    mask_env = os.environ.get("CYBERGYM_MASK_MAP")
    mask = mask_map or (Path(mask_env) if mask_env else None)
    mask = mask.resolve() if mask else None
    if not root.exists():
        raise FileNotFoundError(f"CyberGym root not found: {root}")
    if mask and not mask.exists():
        mask = None
    return CyberGymPaths(root=root, data_dir=data, mask_map=mask)


def python_env(root: Path) -> dict[str, str]:
    env = os.environ.copy()
    src = str((root / "src").resolve())
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = src if not existing else src + os.pathsep + existing
    return env


def generate_case(
    *,
    task_id: str,
    out_dir: Path,
    paths: CyberGymPaths,
    server: str,
    difficulty: str,
    agent_id: str | None = None,
    with_flag: bool = False,
) -> None:
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        "-m",
        "cybergym.task.gen_task",
        "--task-id",
        task_id,
        "--out-dir",
        str(out_dir),
        "--data-dir",
        str(paths.data_dir),
        "--server",
        server,
        "--difficulty",
        difficulty,
    ]
    if agent_id:
        cmd.extend(["--agent-id", agent_id])
    if paths.mask_map:
        cmd.extend(["--mask-map", str(paths.mask_map)])
    if with_flag:
        cmd.append("--with-flag")
    subprocess.run(cmd, cwd=paths.root, env=python_env(paths.root), check=True)


def start_server(
    *,
    paths: CyberGymPaths,
    host: str,
    port: int,
    log_dir: Path,
    db_path: Path,
    binary_dir: Path | None = None,
) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        "-m",
        "cybergym.server",
        "--host",
        host,
        "--port",
        str(port),
        "--log_dir",
        str(log_dir),
        "--db_path",
        str(db_path),
    ]
    if paths.mask_map:
        cmd.extend(["--mask_map_path", str(paths.mask_map)])
    if binary_dir:
        cmd.extend(["--binary_dir", str(binary_dir.resolve())])
    subprocess.run(cmd, cwd=paths.root, env=python_env(paths.root), check=True)


def sanitize_task_id(task_id: str) -> str:
    return task_id.replace(":", "_").replace("/", "_")
