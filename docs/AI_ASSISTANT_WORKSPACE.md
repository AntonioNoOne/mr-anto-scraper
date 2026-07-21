# AI Assistant Workspace

This repository is shared by human developers and AI coding assistants.

## Source Of Truth

- `AGENTS.md`: root rules for every assistant.
- `docs/PROJECT_GUARD.md`: guard/checkpoint policy.
- `config/guard.json`: thresholds, required files and exclusions.
- `checkpoint.md`: latest operational handoff.
- `agent.md`: bounded project journal.

## Start Checklist

Run before substantial edits:

```bash
python scripts/agent_start.py
git status --short
apg check --report-only
apg check --only file-length --report-only
```

Read the latest state:

```text
checkpoint.md
agent.md
docs/status/current.md
```

## Development Rules

- Keep source files small enough to review.
- Extract new behavior when a file approaches the warning threshold.
- Do not add new logic to files above the hard limit.
- Prefer small, focused commits.
- Keep checkpoint/journal useful but compact.
- Do not write secrets into docs, logs or checkpoints.

## Closeout Checklist

Before handing off:

```bash
python scripts/agent_finish.py --title "short title" --summary "what changed" --next "next action"
git status --short
```
