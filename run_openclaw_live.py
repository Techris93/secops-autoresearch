"""
One-command local OpenClaw live pipeline runner.

Runs:
1) export_real_openclaw_native.py
2) ingest_openclaw.py
3) openclaw_prepare.py
4) evaluate_openclaw.py --mode live
5) openclaw_findings.py

Usage:
    python run_openclaw_live.py
    python run_openclaw_live.py --skip-export
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from typing import List


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
NATIVE_DIR = os.path.join(ROOT_DIR, "data", "openclaw", "native")
RAW_AUDIT = os.path.join(ROOT_DIR, "data", "openclaw", "raw", "audit.jsonl")
LABELED_OUT = os.path.join(ROOT_DIR, "data", "openclaw", "replay", "labeled", "current.json")
UNLABELED_OUT = os.path.join(ROOT_DIR, "data", "openclaw", "replay", "unlabeled", "current.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run local OpenClaw live pipeline")
    parser.add_argument("--skip-export", action="store_true", help="Skip native export from ~/.openclaw")
    parser.add_argument("--verbose", action="store_true", help="Pass --verbose to evaluate_openclaw.py")
    return parser.parse_args()


def run_step(args: List[str]) -> None:
    print("\n$ " + " ".join(args))
    subprocess.run(args, cwd=ROOT_DIR, check=True)


def main() -> int:
    args = parse_args()

    if not args.skip_export:
        run_step([sys.executable, "export_real_openclaw_native.py"])

    run_step(
        [
            sys.executable,
            "ingest_openclaw.py",
            "--input-root",
            NATIVE_DIR,
            "--output",
            RAW_AUDIT,
            "--stats",
        ]
    )

    run_step(
        [
            sys.executable,
            "openclaw_prepare.py",
            "--input",
            RAW_AUDIT,
            "--output",
            LABELED_OUT,
            "--unlabeled-output",
            UNLABELED_OUT,
            "--stats",
        ]
    )

    eval_cmd = [
        sys.executable,
        "evaluate_openclaw.py",
        "--labeled",
        LABELED_OUT,
        "--unlabeled",
        UNLABELED_OUT,
        "--mode",
        "live",
    ]
    if args.verbose:
        eval_cmd.append("--verbose")
    run_step(eval_cmd)

    run_step([sys.executable, "openclaw_findings.py", "--input", LABELED_OUT])

    print("\nLive OpenClaw pipeline completed.")
    print(f"Replay input: {LABELED_OUT}")
    print("Use 'python soc_store.py list' to inspect the findings store.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
