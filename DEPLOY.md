# Deploy — MR Anto Scraper

Deploy ufficiale: **Render** (Docker). Live: `https://mr-anto-scraper.onrender.com`

## Prerequisiti
- Account Render (free)
- Repo GitHub: `https://github.com/AntonioNoOne/mr-anto-scraper`
- API keys: `OPENAI_API_KEY`, `GEMINI_API_KEY` (mai committate)

## Deploy da `render.yaml` (automatico)
1. [render.com](https://render.com) → login con GitHub
2. **New +** → **Web Service** → connetti il repo `mr-anto-scraper`
3. Render rileva `render.yaml` (env: `docker`, usa il `Dockerfile`)
4. **Environment** → aggiungi le variabili (vedi sotto) → **Create Web Service**

Build e start sono definiti da `render.yaml` + `Dockerfile` — non serve configurarli a mano.

## Variabili d'ambiente (dashboard Render → Environment)
| Key | Note |
|-----|------|
| `OPENAI_API_KEY` | richiesta per estrazione/chat AI |
| `GEMINI_API_KEY` | provider AI alternativo |

Locale: copia le stesse in `Backend/env.local` (già in `.gitignore`, non committare).

## Test post-deploy
- Frontend: `https://mr-anto-scraper.onrender.com/`
- Health: `https://mr-anto-scraper.onrender.com/health`
- API docs: `https://mr-anto-scraper.onrender.com/docs`

## Free tier — limiti e note
- **Sleep dopo ~15 min** di inattività → primo accesso richiede ~30-50s (cold start).
  Vedi `render.yaml` per l'eventuale keep-alive / healthcheck.
- **RAM 512 MB**: al limite per Playwright/Chromium. Se crasha in scraping pesante,
  valuta il piano a pagamento (più RAM).
- **CPU 0.1 vCPU**: scraping può essere lento.

## Deploy locale (dev)
```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
playwright install chromium
cd Backend
uvicorn main:app --host 127.0.0.1 --port 8010
```
Poi apri `http://127.0.0.1:8010/`.
