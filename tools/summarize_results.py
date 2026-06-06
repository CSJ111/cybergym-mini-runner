from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cybergym_mini_runner.metrics import load_reports, summarize_reports  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize CyberGym mini-runner final reports.")
    parser.add_argument("path", type=Path, help="A final_report.json file or a directory containing reports.")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    summary = summarize_reports(load_reports(args.path))
    text = json.dumps(summary, indent=2, sort_keys=True)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
