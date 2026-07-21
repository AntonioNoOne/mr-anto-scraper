"""Repository shim for the installed Agent Project Guard CLI."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def resolve_command() -> list[str]:
    command = shutil.which("apg") or shutil.which("apg.exe")
    if command:
        return [command]
    user_scripts = Path.home() / "AppData" / "Roaming" / "Python" / f"Python{sys.version_info.major}{sys.version_info.minor}" / "Scripts" / "apg.exe"
    if user_scripts.exists():
        return [str(user_scripts)]
    try:
        import agentslab_guard  # noqa: F401
        return [sys.executable, "-m", "agentslab_guard.cli"]
    except ImportError:
        return []


def main() -> int:
    cmd_prefix = resolve_command()
    if not cmd_prefix:
        print("agentslab-guard is not installed. Install it with pipx or pip.", file=sys.stderr)
        return 2
    root = Path(__file__).resolve().parents[1]
    return subprocess.call([*cmd_prefix, "check", "--target", str(root), *sys.argv[1:]])


if __name__ == "__main__":
    raise SystemExit(main())
