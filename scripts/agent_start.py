"""Agent start hook: print the context an assistant should read first."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Sequence


DEFAULT_READS = (
    "AGENTS.md",
    "docs/AI_ASSISTANT_WORKSPACE.md",
    "checkpoint.md",
    "docs/status/current.md",
    "agent.md",
)


def _run(root: Path, args: list[str]) -> str:
    try:
        result = subprocess.run(args, cwd=root, text=True, capture_output=True, check=False)
    except Exception as exc:
        return f"not-run: {exc}"
    output = (result.stdout or "") + (result.stderr or "")
    return output.strip() or f"exit={result.returncode}"


def _preview(path: Path, max_chars: int) -> str:
    if not path.exists():
        return "missing"
    text = path.read_text(encoding="utf-8", errors="ignore").strip()
    if len(text) > max_chars:
        return text[:max_chars].rstrip() + "\n...truncated..."
    return text or "(empty)"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Print start-of-agent context and guard status.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--max-chars", type=int, default=1600)
    parser.add_argument("--skip-guard", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root).resolve()
    print("# Agent Start Hook")
    print("")
    print("Read these files first:")
    for rel in DEFAULT_READS:
        print(f"- {rel}")
    print("")
    print("## Git Status")
    print(_run(root, ["git", "status", "--short"]))
    print("")
    if not args.skip_guard:
        print("## Project Guard")
        print(_run(root, [sys.executable, "scripts/project_guard.py", "--report-only"]))
        print("")
    for rel in DEFAULT_READS:
        print(f"## {rel}")
        print(_preview(root / rel, args.max_chars))
        print("")
    print("Start rule: understand current state before editing. Do not skip the final hook.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
