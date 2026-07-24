# CLAUDE.md — mr-anto-scraper (Jusper)

## Regole di lavoro (contratto) — LEGGERE SEMPRE

Il contratto completo è in `AGENTS.md` + `docs/AI_ASSISTANT_WORKSPACE.md`.
Claude Code carica in automatico solo questo file, quindi i punti chiave sono
ripetuti qui e vanno seguiti sempre:

- **Spike prima di implementare** qualsiasi cosa non banale o incerta (nuova
  integrazione, API sconosciuta, comportamento che può fallire in più modi):
  prova throwaway (scratchpad/script temp) che dimostra l'approccio sulla
  realtà PRIMA di toccare il codice del progetto. Mai implementare per
  assunzione o sul happy path.
- **Test prima di dire "fatto"**: scrivi/adegua i test del comportamento
  toccato, eseguili, riporta l'output vero. Non è "fatto" finché i test non
  passano (o spieghi perché non se ne applica nessuno).
- **File length guard NON gira senza commit.** Gli hook Git (`.githooks`)
  scattano solo su commit/push. Dopo modifiche sostanziali lancia tu
  `python scripts/check_file_length.py`. Limiti: warn 800 righe, block 1000
  (`config/guard.json`). Sopra soglia: estrai in moduli, non gonfiare il file.
- **Prima di proporre un'architettura**, leggi `docs/memory/02_failed_graveyard.md`:
  se l'approccio è lì, non riproporlo.
- Chiusura lavoro significativo: `python scripts/agent_finish.py` (o
  `write_checkpoint.py`) + `git status --short`.

## Serena MCP — USARE SEMPRE

Serena è configurato a livello **globale** (scope user, `~/.claude.json` →
`mcpServers.serena`), quindi è disponibile in **ogni** progetto senza file
locali. Questo repo NON tiene un `.mcp.json` (rimosso per evitare il doppione).

**Regola operativa:** per navigare ed editare il codice usa **sempre** gli
strumenti simbolici di Serena invece di leggere file interi o fare grep bruto:
- ricerca simboli: `find_symbol`
- riferimenti: `find_references`
- edit chirurgico: `replace_symbol_body`, `insert_after_symbol`,
  `insert_before_symbol`
Se ti ritrovi a dumpare interi file o a fare ricerche testuali larghe, fermati e
passa a Serena. Riduce i token e rende gli edit precisi.

All'apertura del progetto, se Serena non è già attivo su questa cartella:
attiva il progetto (`activate_project` / "attiva Serena su questo progetto").

### Se manca / va riconfigurato
Prerequisiti: `git` + `uv`/`uvx` (installato in `~/.local/bin`).

Config globale (una volta, vale per tutti i progetti) — editare
`~/.claude.json`, chiave top-level `mcpServers`:
```json
{
  "mcpServers": {
    "serena": {
      "command": "C:/Users/anto_/.local/bin/uvx.exe",
      "args": ["--from", "git+https://github.com/oraios/serena", "serena", "start-mcp-server", "--context", "claude-code"]
    }
  }
}
```
Nota: `claude mcp add ... -- uvx --from ...` da PowerShell fallisce (il parser
mangia `--from`; e PS 5.1 rompe il JSON di `add-json`). Editare il file è la via
affidabile. Path assoluto di `uvx` così risolve anche se il PATH non è aggiornato.

Dopo la modifica: riavvia Claude Code, poi `/mcp` deve mostrare `serena ✓`.
Primo avvio: `uvx` scarica+builda Serena (~1 min), poi resta in cache.

Per-progetto (alternativa portabile per il team): mettere lo stesso blocco in un
`.mcp.json` nella root (usare `"command": "uvx"` bare + aggiungere
`"--project", "."` agli args). Il template `_ai-project-template` lo ha già.
