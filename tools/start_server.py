from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cybergym_mini_runner.cybergym_adapter import discover_paths, start_server  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Start the official CyberGym PoC server.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8666)
    parser.add_argument("--log-dir", type=Path, default=Path("./runs/server_poc"))
    parser.add_argument("--db-path", type=Path, default=Path("./runs/server_poc/poc.db"))
    parser.add_argument("--binary-dir", type=Path, default=None)
    parser.add_argument("--cybergym-root", type=Path, default=None)
    parser.add_argument("--data-dir", type=Path, default=None)
    parser.add_argument("--mask-map", type=Path, default=None)
    args = parser.parse_args()

    paths = discover_paths(args.cybergym_root, args.data_dir, args.mask_map)
    start_server(
        paths=paths,
        host=args.host,
        port=args.port,
        log_dir=args.log_dir,
        db_path=args.db_path,
        binary_dir=args.binary_dir,
    )


if __name__ == "__main__":
    main()
