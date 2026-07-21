# Project Guard

## Guard Policy

The project guard keeps the codebase reviewable and the project history
recoverable between sessions.

Default thresholds:

- warn at 800 lines;
- block above 1000 lines.

Configure thresholds and exclusions in `config/guard.json`.

The installed `apg` package is the single implementation used by every
repository. The scripts copied into a repository are compatibility shims, not
independent guard implementations.

When a file crosses the warning threshold, prefer one of these actions:

- extract a focused module;
- split UI/components/services;
- move data/config out of code;
- reduce duplication.

When a file crosses the hard limit, do not add feature logic to that file.

## Checkpoint Policy

Use checkpoints as a compact handoff, not as raw logs.

At the start of agent work:

```bash
python scripts/agent_start.py
```

At the end of meaningful work:

```bash
python scripts/agent_finish.py --title "image matching spike" --summary "Testato OpenCV similarity" --next "Validare su 10 screenshot reali"
```

The finish hook runs guards, then updates:

- `checkpoint.md`;
- `docs/status/last-checkpoint.md`;
- `docs/status/current.md`;
- `agent.md`;
- `docs/archive/checkpoints/<timestamp>.md`.

If you only need to write a checkpoint manually, use:

```bash
python scripts/write_checkpoint.py --title "short title" --summary "what changed"
```

## Hook Setup

Enable hooks:

```bash
apg install-hooks --target .
```

Run the complete guard manually:

```bash
apg check --target .
```

Hooks:

- `pre-commit`: runs the repository shim for `apg check`;
- `pre-push`: runs the repository shim for `apg check --only file-length`.

## Cursor Setup

Cursor reads:

- `.cursorrules`;
- `.cursor/rules/guard-checkpoint.mdc`.

If the project already has Cursor rules, merge the guard rules manually.

## Codex Setup

Codex reads `AGENTS.md`. Keep `CODEX.md` as a short adapter note.

For every substantial task, Codex should:

1. read `AGENTS.md`;
2. run `python scripts/agent_start.py`;
3. implement scoped changes;
4. run `python scripts/agent_finish.py --title "..." --summary "..."`;
5. leave `git status --short` clean or explain what remains.
