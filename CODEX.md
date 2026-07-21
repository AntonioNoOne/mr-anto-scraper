# Codex Rules

Use `AGENTS.md` as the root operating guide.

Codex-specific focus:

- make scoped changes end to end;
- start sessions with `python scripts/agent_start.py`;
- respect file length guard before editing large files;
- run focused tests and `python scripts/project_guard.py`;
- finish meaningful sessions with `python scripts/agent_finish.py --title "..."`
  so checkpoint/journal stay aligned;
- avoid committing secrets or noisy generated artifacts.
