from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from cybergym_mini_runner.agent import AgentRunConfig, run_agent  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a local CyberGym baseline agent loop.")
    parser.add_argument("--case-dir", type=Path, required=True)
    parser.add_argument("--model", type=str, default=None)
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--max-steps", type=int, default=50)
    parser.add_argument("--timeout-seconds", type=int, default=1800)
    parser.add_argument("--shell-timeout", type=int, default=30)
    parser.add_argument("--max-json-retries", type=int, default=3)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--extra-body-json", default=None, help="JSON object passed as OpenAI extra_body.")
    parser.add_argument("--enable-thinking", action="store_true", help="Shortcut for --extra-body-json '{\"enable_thinking\":true}'.")
    parser.add_argument("--reasoning-effort", default=None, help="OpenAI-compatible reasoning_effort value.")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level.upper()), format="%(asctime)s %(levelname)s %(message)s")
    model = args.model
    if not model:
        import os

        model = os.environ.get("MODEL")
    if not model:
        raise SystemExit("--model or MODEL is required")
    extra_body = None
    if args.extra_body_json:
        extra_body = json.loads(args.extra_body_json)
        if not isinstance(extra_body, dict):
            raise SystemExit("--extra-body-json must decode to a JSON object")
    if args.enable_thinking:
        extra_body = {**(extra_body or {}), "enable_thinking": True}

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    run_dir = args.run_dir or (args.case_dir / "agent_runs" / f"{model.replace('/', '_')}_{timestamp}")
    report = run_agent(
        AgentRunConfig(
            case_dir=args.case_dir,
            run_dir=run_dir,
            model=model,
            max_steps=args.max_steps,
            timeout_seconds=args.timeout_seconds,
            shell_timeout=args.shell_timeout,
            max_json_retries=args.max_json_retries,
            temperature=args.temperature,
            extra_body=extra_body,
            reasoning_effort=args.reasoning_effort,
        )
    )
    print(f"final_report: {run_dir / 'final_report.json'}")
    print(report)


if __name__ == "__main__":
    main()
