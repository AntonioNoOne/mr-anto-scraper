# Jusper — AI E-commerce Scraper

**Jusper** (ex Mr. Anto Scraper) è un web scraper per e-commerce con analisi AI:
estrae prodotti e prezzi da qualsiasi pagina, cerca venditori alternativi,
confronta i prezzi e monitora le variazioni nel tempo. Backend FastAPI (Python),
frontend Vue 3, deploy su Render via Docker.

## Cosa fa

- **Estrazione prodotti** da URL singole o multiple (nome, prezzo, brand, specifiche).
- **Ricerca venditori** alternativi per un prodotto e arricchimento con i prezzi reali.
- **Confronto prezzi** semantico tra prodotti simili di siti diversi.
- **Monitoraggio prezzi** con check periodici e alert al superamento di una soglia.
- **Storico prodotti** con dashboard, statistiche ed export CSV/JSON.
- **Chat AI** integrata sui dati raccolti.

## Stack

- **Backend**: FastAPI + Uvicorn, Pydantic. Fetch pagine con **Crawl4AI**
  (browser Chromium + stealth) e Playwright; ricerca con la libreria **ddgs**
  (ex duckduckgo-search) e fallback Bing/browser; parsing HTML con BeautifulSoup.
- **AI cloud**: **Gemini** (default `gemini-2.5-flash`) e **OpenAI**
  (default `gpt-4o-mini`). Selezione via env `AI_PROVIDER` (`auto` | `gemini` |
  `openai`); in `auto` prova prima OpenAI poi Gemini come fallback. Le API sono
  chiamate via **HTTP diretto** (`requests`/`aiohttp`) — nessun SDK.
- **Frontend**: Vue 3 (options API, template inline in `index.html`). Asset
  self-hosted in `Frontend/vendor/` (Vue, axios, Chart.js, Font Awesome), **nessun
  CDN**. Tailwind CSS v2 buildato e purgato in locale.
- **Persistenza**: SQLite in `data/database/` (storico prodotti, selettori).
- **Deploy**: Render (Docker, immagine `playwright/python`).

## Prerequisiti

- Python 3.12+ e Chromium via Playwright.
- Chiavi AI (almeno una tra OpenAI e Gemini) per estrazione/chat.
- Node.js solo se vuoi ri-buildare il CSS Tailwind / ri-scaricare i vendor.

## Configurazione

Le chiavi stanno in `Backend/env.local` (gitignored). Copia il template e inserisci
le tue chiavi:

```bash
cp Backend/env.local.example Backend/env.local
```

Variabili principali (vedi `env.local.example`):

- `AI_PROVIDER` — `auto` (default) | `gemini` | `openai`
- `OPENAI_API_KEY`, `OPENAI_MODEL` (default `gpt-4o-mini`)
- `GEMINI_API_KEY`, `GEMINI_MODEL` (default `gemini-2.5-flash`)
- opzionale: `JINA_API_KEY` (fallback Jina Reader)

## Esecuzione in locale

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
playwright install chromium
cd Backend
uvicorn main:app --host 127.0.0.1 --port 8010
```

Apri `http://127.0.0.1:8010/`. Docs API su `/docs`, health su `/health`.

Su Windows serve la console in UTF-8: `main.py` riconfigura già `stdout`/`stderr`.

### Ri-build del frontend (opzionale)

Necessario solo se modifichi le classi Tailwind o i pacchetti vendored:

```bash
cd Frontend
npm install
npm run build        # scarica i vendor + builda css/tailwind.build.css
# oppure singolarmente: npm run vendor | npm run build:css
```

## Deploy

Deploy ufficiale su **Render** (Docker) tramite `render.yaml` + `Dockerfile`
(base `mcr.microsoft.com/playwright/python`, che fornisce il Chromium riusato anche
da Crawl4AI). Variabili d'ambiente su Render: `OPENAI_API_KEY`, `GEMINI_API_KEY`
(opz. `JINA_API_KEY`). Un keep-alive via GitHub Actions
(`.github/workflows/keep-alive.yml`) mitiga il cold start del free tier.

Procedura completa, limiti del free tier e troubleshooting: vedi **`DEPLOY.md`**.

## API in breve

Circa 47 endpoint, esposti da `Backend/main.py` (infra/static) e dai router in
`Backend/routers/`. Alcuni esempi:

- `POST /fast-extract`, `POST /fast-extract-multiple` — estrazione
- `POST /compare-products`, `POST /compare-prices` — confronto
- `POST /google-search`, `GET /google-search-results` — ricerca venditori
- `GET /monitoring/products`, `POST /monitoring/check-prices`, `GET /monitoring/alerts`
- `GET /historical-products`, `GET /historical-products/export?format=csv|json`
- `POST /chat`, `GET /chat/models`
- `GET /health`

Elenco completo in `PROJECT_STRUCTURE.md` e su `/docs`.

## Struttura

Panoramica dettagliata di cartelle, pipeline e routing in **`PROJECT_STRUCTURE.md`**.
