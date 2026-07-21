# Struttura del progetto — Jusper

Documento di architettura. Per uso/installazione vedi `README.md`, per il deploy
vedi `DEPLOY.md`.

## Layout radice

```
mr-anto-scraper/
├── Backend/                 # API FastAPI + logica scraping/AI
├── Frontend/                # SPA Vue 3 (asset self-hosted, no CDN)
├── data/
│   ├── database/            # SQLite: historical_products.db, selector_database.db
│   └── api_extracts/        # estrazioni salvate (JSON)
├── config/guard.json        # regole del project guard
├── scripts/                 # tooling guard/checkpoint (project_guard.py, ...)
├── .githooks/               # hook git che eseguono il guard
├── .github/workflows/       # keep-alive.yml (anti cold-start Render)
├── docs/                    # documentazione interna
├── Dockerfile, render.yaml  # deploy Render (Docker)
├── requirements.txt         # dipendenze Python (Backend/requirements.txt vi rimanda)
├── start.py                 # launcher alternativo (uvicorn)
└── README.md, DEPLOY.md, PROJECT_STRUCTURE.md
```

I file sorgente sono tenuti sotto ~900 righe: il **project guard**
(`config/guard.json` + `scripts/` + hook in `.githooks/`) blocca i file oltre 1000
righe e verifica la presenza di file/sezioni richiesti. Per questo i moduli grandi
sono divisi in mixin/router (vedi sotto).

## Backend/

### Entry point e infrastruttura

- **`main.py`** — costruisce l'app FastAPI, configura CORS e `StaticFiles`, monta il
  frontend, definisce gli endpoint infrastrutturali (`/`, `/health`, `/api`,
  `/debug/static-files`, static JS/CSS) e include tutti i router. Nello `startup`
  istanzia i componenti in `app_state` e avvia lo scheduler prezzi. Riconfigura
  `stdout`/`stderr` in UTF-8 (fix console Windows).
- **`app_state.py`** — stato condiviso (single source of truth): istanze di
  extractor, comparator, chat manager, selector DB, google search, historical DB,
  price monitor, price scheduler. I router leggono da qui.
- **`models.py`** — modelli Pydantic di request/response (es. `ExtractResponse`,
  `CompareResponse`, `ChatResponse`).
- **`env.local`** (gitignored) / **`env.local.example`** — configurazione ambiente.

### Router (`Backend/routers/`)

Ogni router raggruppa endpoint per area; `main.py` li include tutti.

- **`extraction.py`** — `POST /fast-extract`, `POST /fast-extract-multiple`,
  `POST /stop-scraping`
- **`comparison.py`** — `POST /compare-products`, `POST /compare-prices`,
  `POST /test-ai-comparator`
- **`chat.py`** — `POST /chat`, `GET /chat/models`, `GET /chat/test`, `GET /chat/keys`
- **`selectors.py`** — `GET /selectors/stats`, `GET /selectors/pending`,
  `POST /selectors/approve/{domain}`, `DELETE /selectors/{domain}`
- **`monitoring.py`** — `POST /monitoring/add-product`, `GET /monitoring/products`,
  `GET /monitoring/price-history/{product_id}`, `GET /monitoring/alerts`,
  `POST /monitoring/alerts/{alert_id}/read`, `DELETE /monitoring/products/{product_id}`,
  `POST /monitoring/check-prices`, `GET /monitoring/stats`
- **`scheduler.py`** — `POST /scheduler/start`, `POST /scheduler/stop`,
  `GET /scheduler/stats`, `POST /scheduler/force-check/{product_id}`
- **`history.py`** — `GET /historical-products`,
  `GET /historical-products/export` (`?format=csv|json`), `GET /dashboard-stats`,
  `GET /site-statistics`, `POST /google-search`, `GET /google-search-results`,
  `GET /extraction-sessions/recent`, `GET /products/categories/stats`,
  `GET /sites/performance/stats`, `POST` e `GET /api/browser-config`

### Pipeline di estrazione

Composta da `fast_ai_extractor.py` (classe `FastAIExtractor`) più i mixin:

- `fast_ai_extractor_config.py` — costanti (liste anti-bot, args browser)
- `fast_ai_extractor_extraction.py` — `_extract_single_attempt` (browser custom con
  selettori dal DB)
- `fast_ai_extractor_ai.py` — `_extract_via_crawl4ai` (fetcher primario) e
  `_extract_via_jina_reader` (fallback cloud)
- `fast_ai_extractor_parsing.py` — `_ai_parse_products`: chunking del markdown +
  chiamate AI in parallelo (`asyncio.gather`); il prompt inferisce brand/model/specs
  dal nome e distingue real-estate vs e-commerce con match a parola intera
- `fast_ai_extractor_selectorflow.py` — flusso di selezione/salvataggio selettori

Ordine dei fetcher (in `fast_ai_extractor.py`):

1. **Crawl4AI** (primario) — `AsyncWebCrawler` + stealth, produce `fit_markdown`
   ripulito, poi passato al parser AI (Gemini/OpenAI).
2. **Browser custom** (fallback) — selettori dal database, `_extract_single_attempt`.
3. **Jina Reader** (fallback cloud) — `r.jina.ai`.

Moduli AI di supporto: `ai_content_analyzer.py` + mixin
(`ai_content_analyzer_providers.py` gestisce ordine provider e fallback OpenAI/Gemini
via HTTP; `_browser`, `_parsing`, `_pipeline`).

### Ricerca venditori

`google_search_integration.py` (classe `GoogleSearchIntegration`) + mixin:

- `google_search_duckduckgo.py` — **strategia 1**: libreria `ddgs` (no browser)
- `google_search_bing.py` — fallback Bing Shopping + ricerca diretta e-commerce
- `google_search_parsing.py` — parsing dei risultati
- `google_search_validation.py` — filtro domini junk (social/forum/esteri) e scoring

L'arricchimento prezzi fa fetch delle prime ~10 pagine venditore con Crawl4AI e
seleziona il prezzo con `price_utils.pick_price_near_product`.

### Monitoraggio prezzi

- `price_monitor.py` (`PriceMonitor`) — aggiunge prodotti al monitoring, esegue
  `check_price_changes`, salva alert al superamento della soglia. Il prezzo corrente
  è **reale**: `_extract_current_price` usa Crawl4AI + `pick_price_near_product`.
- `price_scheduler.py` (`PriceScheduler`) — check periodici, avviato nello startup.

### Estrazione prezzo condivisa

`price_utils.py` — `pick_price_near_product(text, name)`: tra i molti prezzi € di una
pagina sceglie quello testualmente più vicino alle keyword del nome prodotto.

### Confronto e storico

- `ai_product_comparator.py` + `ai_product_comparator_ai.py` — confronto semantico AI
  (clustering prodotti simili, statistiche prezzo, opportunità di risparmio).
- `historical_products_db.py` + mixin (`_helpers`, `_save`, `_search`, `_stats`) —
  storage SQLite dei prodotti estratti e statistiche.
- `selector_database.py` (+ `selector_database.json`, `init_selectors.py`,
  `init_default_selectors.py`) — database dei selettori CSS per dominio.
- `chat_ai_manager.py` — gestione della chat AI.

### Supporto scraping

`proxy_manager.py`, `proxy_updater.py`, `captcha_handler.py`, `backup_manager.py`,
`clean_database.py`.

### `Backend/future_implementations/`

Copie/prototipi non montati nell'app (`cache_manager.py`, `google_price_finder.py`,
`google_vision_finder.py`, e versioni precedenti di `price_monitor`/`price_scheduler`).

## Frontend/

SPA Vue 3 con template inline in `index.html` e logica modulare in `js/`. Nessun CDN:
tutti gli asset sono in `vendor/`.

```
Frontend/
├── index.html              # markup + template Vue (options API)
├── vendor/                 # asset self-hosted: vue.global.prod.js, axios.min.js,
│                           #   chart.umd.js, fontawesome/
├── css/
│   ├── styles.css          # CSS custom (responsive <1200px, sotto-tab)
│   ├── tailwind.entry.css  # sorgente Tailwind
│   └── tailwind.build.css  # output buildato/purgato (npm run build:css)
├── js/
│   ├── config.js           # configurazione (base URL API, costanti)
│   ├── api.js              # wrapper axios verso il backend
│   ├── store.js            # stato Vue
│   ├── store.methods.js    # metodi dello store
│   ├── store.init.js       # inizializzazione
│   ├── charts.js           # grafici Chart.js
│   └── actions.js          # azioni UI
├── scripts/vendor.mjs      # scarica/aggiorna i vendor (npm run vendor)
├── package.json, package-lock.json
├── tailwind.config.js, postcss.config.js
└── node_modules/           # solo per build (non servito)
```

Interfaccia: sidebar con **3 sezioni**:

- **Dashboard** — statistiche e grafici.
- **Estrazione** — sotto-tab: *Scraping URL* / *Ricerca Google* / *Confronto*.
- **Impostazioni & Monitoraggio** — sotto-tab: *Monitoraggio* / *Configurazione*.

Layout responsive. Tailwind è v2 (build locale in `tailwind.build.css`), gli stili
custom e le regole responsive stanno in `styles.css`.

## Deploy (sintesi)

`render.yaml` + `Dockerfile` costruiscono l'immagine su Render partendo da
`mcr.microsoft.com/playwright/python`; il Chromium dell'immagine è riusato anche da
Crawl4AI. Env vars su Render: `OPENAI_API_KEY`, `GEMINI_API_KEY` (opz. `JINA_API_KEY`).
Dettagli e limiti free tier in `DEPLOY.md`.
