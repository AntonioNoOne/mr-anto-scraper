# Scripts

Operational scripts installed by AgentsLab Guard:

| Script | Purpose |
| --- | --- |
| `agent_start.py` | Prints repository status and bounded context before agent work |
| `agent_finish.py` | Runs the guard and writes the end-of-session checkpoint |
| `check_file_length.py` | Compatibility shim for `apg check --only file-length` |
| `project_guard.py` | Compatibility shim for `apg check` |
| `write_checkpoint.py` | Writes compact status, journal and archive checkpoints |
| `install_guard_hooks.ps1` | Installs Git hooks on Windows |
| `install_guard_hooks.sh` | Installs Git hooks on Linux and macOS |

The check logic is owned by the installed `agentslab-guard` package. Do not
fork it into this repository; customize policy in `config/guard.json`.
