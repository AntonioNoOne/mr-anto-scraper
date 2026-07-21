"""Agent finish hook: run guards and write a checkpoint."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Sequence


def _run(root: Path, args: list[str], *, check: bool) -> int:
    print(f"$ {' '.join(args)}")
    result = subprocess.run(args, cwd=root, text=True, check=False)
    if check and result.returncode != 0:
        raise SystemExit(result.returncode)
    return result.returncode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run end-of-agent checks and write checkpoint.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--title", required=True)
    parser.add_argument("--goal", default="")
    parser.add_argument("--summary", action="append", required=True)
    parser.add_argument("--decision", action="append", default=[])
    parser.add_argument("--open-item", action="append", default=[])
    parser.add_argument("--next", dest="next_step", default="")
    parser.add_argument("--allow-guard-failure", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root).resolve()
    print("# Agent Finish Hook")
    print("")
    _run(root, [sys.executable, "scripts/project_guard.py"], check=not args.allow_guard_failure)
    print("")
    checkpoint_cmd = [
        sys.executable,
        "scripts/write_checkpoint.py",
        "--title",
        args.title,
    ]
    if args.goal:
        checkpoint_cmd.extend(["--goal", args.goal])
    for item in args.summary:
        checkpoint_cmd.extend(["--summary", item])
    for item in args.decision:
        checkpoint_cmd.extend(["--decision", item])
    for item in args.open_item:
        checkpoint_cmd.extend(["--open-item", item])
    if args.next_step:
        checkpoint_cmd.extend(["--next", args.next_step])
    _run(root, checkpoint_cmd, check=True)
    print("")
    print("Finish rule: report tests/guards/checkpoint path to the human.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
