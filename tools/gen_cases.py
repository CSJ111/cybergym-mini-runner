from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cybergym_mini_runner.cybergym_adapter import discover_paths, generate_case, sanitize_task_id  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate CyberGym cases using the official generator.")
    parser.add_argument("--task-ids", nargs="+", required=True)
    parser.add_argument("--difficulty", default="level1", choices=["level0", "level1", "level2", "level3"])
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--server", default="http://127.0.0.1:8666")
    parser.add_argument("--cybergym-root", type=Path, default=None)
    parser.add_argument("--data-dir", type=Path, default=None)
    parser.add_argument("--mask-map", type=Path, default=None)
    parser.add_argument("--agent-id", default=None)
    parser.add_argument("--with-flag", action="store_true")
    args = parser.parse_args()

    paths = discover_paths(args.cybergym_root, args.data_dir, args.mask_map)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    for task_id in args.task_ids:
        case_dir = args.out_dir / sanitize_task_id(task_id)
        generate_case(
            task_id=task_id,
            out_dir=case_dir,
            paths=paths,
            server=args.server,
            difficulty=args.difficulty,
            agent_id=args.agent_id,
            with_flag=args.with_flag,
        )
        (case_dir / "case_meta.json").write_text(
            json.dumps({"task_id": task_id, "difficulty": args.difficulty, "server": args.server}, indent=2) + "\n",
            encoding="utf-8",
        )
        print(case_dir)


if __name__ == "__main__":
    main()
