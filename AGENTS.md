# Project Agent Rules

Read `docs/AI_ASSISTANT_WORKSPACE.md` before editing. These rules apply to
Codex, Cursor, Claude, Gemini and any other coding assistant.

## File Length Guard

Before editing an existing source file, check whether it is near the project
size limit.

- Warning threshold: 800 lines by default.
- Hard limit: 1000 lines by default.
- If a file is over the warning threshold, prefer extracting new behavior into
  a nearby module.
- If a file is over the hard limit, do not add new logic to it. Only route to
  extracted modules, remove code, or make the smallest compatibility edit.
- Use `apg check --only file-length --report-only` before and after substantial
  coding work.
- Use `apg check --strict` before commit/push. The scripts under `scripts/`
  remain compatibility shims for environments that call the old paths.

Thresholds and exclusions live in `config/guard.json`.

The Git hooks only run on commit/push. Do NOT rely on them as your only guard:
run `python scripts/check_file_length.py` (or `apg check --only file-length
--report-only`) yourself after substantial edits, because work that is not
committed never triggers the hooks and oversized files stay invisible.

## Spikes And Tests

- For any non-trivial or uncertain change (new integration, unfamiliar API,
  behavior that can fail in several ways), do a small **spike first**: a
  throwaway probe (in the scratchpad or a temp script) that proves the approach
  works against reality BEFORE editing project code. Do not implement on
  assumption or the happy path.
- Write or adjust **tests for the touched behavior before declaring the work
  done**, run them, and report the real output. A change is not "done" until its
  tests pass — or you state explicitly why no test applies.
- Prefer verifying against reality (real call, real data, real run) over
  believing it should work.

## Checkpoint And Journal

Keep project continuity in three files:

- `checkpoint.md`: latest operational handoff.
- `agent.md`: bounded project journal / daily notes.
- `docs/status/current.md`: compact status for a new chat or teammate.

Close meaningful work with:

```bash
python scripts/write_checkpoint.py --title "short title" --summary "what changed" --next "next action"
```

Do not store secrets, customer payloads, API keys or private tokens in
checkpoint/journal files.

## Agent Lifecycle Hooks

These are operational hooks for AI work sessions, separate from Git hooks.

At the beginning of a session, run:

```bash
python scripts/agent_start.py
```

This prints current status, latest checkpoint, journal preview, git status and
non-blocking guard output.

At the end of a meaningful session, run:

```bash
python scripts/agent_finish.py --title "short title" --summary "what changed" --next "next action"
```

This runs the project guard and writes the checkpoint/journal handoff. Do not
finish substantial work without either running this command or explaining why it
could not run.

## Git Hooks

Enable the packaged hooks with:

```bash
git config core.hooksPath .githooks
```

The hooks run the project guard and file length guard before commit/push.

## Project Memory

Two files track accumulated learning across sessions:

- `docs/memory/01_implemented.md`: approaches that succeeded.
- `docs/memory/02_failed_graveyard.md`: approaches that failed.

**Before proposing any architecture or approach**, read `docs/memory/02_failed_graveyard.md`.
If the approach appears there, do NOT propose it — acknowledge the known failure and suggest an alternative.

Log new learnings with:

```bash
apg log --success -m "What worked and why"
apg log --fail -m "What failed and the root cause"
```

## Agent Closeout Checklist

Before saying work is complete:

1. Run focused tests for touched behavior.
2. Run `apg check`.
3. Run `apg check --only file-length --report-only`.
4. Update checkpoint with `scripts/write_checkpoint.py`.
5. Check `git status --short`.
6. If a macro-task is done, log it: `apg log --success -m "..."`.
