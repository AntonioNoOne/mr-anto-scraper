"""Write a compact project checkpoint and bounded journal entry."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Sequence


def _load_config(root: Path, path: str) -> dict:
    config_path = Path(path)
    if not config_path.is_absolute():
        config_path = root / config_path
    if not config_path.exists():
        return {}
    return json.loads(config_path.read_text(encoding="utf-8"))


def _checkpoint_config(config: dict) -> dict:
    return config.get("checkpoint", {}) if isinstance(config, dict) else {}


def _git(root: Path, args: list[str]) -> list[str]:
    try:
        result = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=False)
    except Exception:
        return []
    if result.returncode != 0:
        return []
    return [line for line in (result.stdout or "").splitlines() if line.strip()]


def _changed_files(root: Path) -> list[str]:
    return _git(root, ["status", "--short"])


def _last_commit(root: Path) -> str:
    lines = _git(root, ["log", "-1", "--date=short", "--pretty=format:%h | %ad | %s"])
    return lines[0] if lines else "no commits found"


def _diff_stat(root: Path) -> str:
    lines = _git(root, ["diff", "--stat"])
    return "\n".join(lines) if lines else "no unstaged diff stat"


def _file_length_status(root: Path) -> str:
    script = root / "scripts" / "check_file_length.py"
    if not script.exists():
        return "not-run: missing scripts/check_file_length.py"
    result = subprocess.run(
        [sys.executable, str(script), "--root", str(root), "--report-only"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    lines = ((result.stdout or "") + (result.stderr or "")).strip().splitlines()
    return lines[-1] if lines else f"exit={result.returncode}"


def _slug(value: str) -> str:
    text = value.lower().replace(" ", "-")
    return "".join(ch for ch in text if ch.isalnum() or ch in "-_.").strip("-") or "checkpoint"


def _build_text(
    now: datetime,
    title: str,
    goal: str,
    summary: list[str],
    decisions: list[str],
    open_items: list[str],
    next_step: str,
    files: list[str],
    last_commit: str,
    diff_stat: str,
    file_length_status: str,
) -> str:
    lines = [
        "# Checkpoint",
        "",
        f"### {now.strftime('%Y-%m-%d %H:%M')} | {title}",
        "",
        f"- goal: {goal or 'not specified'}",
    ]
    lines.extend(f"- done: {item}" for item in (summary or ["not specified"]))
    lines.extend(f"- decision: {item}" for item in decisions)
    lines.extend(f"- open: {item}" for item in open_items)
    lines.append(f"- next: {next_step or 'not specified'}")
    lines.append(f"- file length guard: {file_length_status}")
    lines.append(f"- last commit: {last_commit}")
    if files:
        lines.append("")
        lines.append("## Files")
        lines.extend(f"- {item}" for item in files)
    lines.extend(["", "## Diff Summary", "", "```text", diff_stat, "```", ""])
    return "\n".join(lines)


def _write_current(path: Path, now: datetime, title: str, summary: list[str], next_step: str, file_length_status: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# Current Status",
                "",
                f"Updated: {now.strftime('%Y-%m-%d %H:%M')}",
                "",
                f"- latest checkpoint: {title}",
                *[f"- done: {item}" for item in summary[:5]],
                f"- next: {next_step or 'not specified'}",
                f"- file length guard: {file_length_status}",
                "",
                "Start a new session by reading:",
                "",
                "1. `AGENTS.md`",
                "2. `checkpoint.md`",
                "3. `agent.md`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _update_journal(path: Path, entry: str, limit: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8") if path.exists() else "# Agent Journal\n"
    sections = [part.strip() for part in existing.split("\n### ") if part.strip()]
    header = sections[0] if sections and not sections[0].startswith("20") else "# Agent Journal"
    old_entries = [f"### {part}" for part in sections[1:]] if sections and not sections[0].startswith("20") else [f"### {part}" for part in sections]
    rendered = [header.rstrip(), "", entry.strip(), ""]
    rendered.extend(old_entries[: max(0, limit - 1)])
    path.write_text("\n".join(rendered).rstrip() + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Write project checkpoint and journal.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--config", default="config/guard.json")
    parser.add_argument("--title", required=True)
    parser.add_argument("--goal", default="")
    parser.add_argument("--summary", action="append", default=[])
    parser.add_argument("--decision", action="append", default=[])
    parser.add_argument("--open-item", action="append", default=[])
    parser.add_argument("--next", dest="next_step", default="")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root).resolve()
    config = _checkpoint_config(_load_config(root, args.config))
    latest = root / config.get("latest", "checkpoint.md")
    journal = root / config.get("journal", "agent.md")
    current = root / config.get("current", "docs/status/current.md")
    last_checkpoint = root / config.get("last_checkpoint", "docs/status/last-checkpoint.md")
    archive_dir = root / config.get("archive_dir", "docs/archive/checkpoints")
    journal_limit = int(config.get("journal_entries", 30))

    now = datetime.now()
    changed = _changed_files(root)
    last_commit = _last_commit(root)
    diff_stat = _diff_stat(root)
    file_length_status = _file_length_status(root)
    text = _build_text(
        now,
        args.title,
        args.goal,
        args.summary,
        args.decision,
        args.open_item,
        args.next_step,
        changed,
        last_commit,
        diff_stat,
        file_length_status,
    )
    archive_dir.mkdir(parents=True, exist_ok=True)
    archive_path = archive_dir / f"{now.strftime('%Y-%m-%d-%H%M')}-{_slug(args.title)}.md"
    for path in (latest, last_checkpoint, archive_path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    _write_current(current, now, args.title, args.summary, args.next_step, file_length_status)
    _update_journal(journal, text, journal_limit)

    payload = {
        "checkpoint": str(latest),
        "last_checkpoint": str(last_checkpoint),
        "archive": str(archive_path),
        "journal": str(journal),
        "current": str(current),
        "file_length_status": file_length_status,
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"Checkpoint updated: {latest}")
        print(f"Journal updated: {journal}")
        print(f"Archive written: {archive_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
