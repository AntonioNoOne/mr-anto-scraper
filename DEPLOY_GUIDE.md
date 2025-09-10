# 🚀 Guida Deploy per Colleghi

## Opzione 1: Railway (RACCOMANDATO)

### 1. Preparazione
```bash
# Nel terminale, vai nella directory del progetto
cd C:\Users\anto_\Desktop\AIDev\MR_Scraper\mr.-anto-scraper

# Inizializza git
git init
git add .
git commit -m "Initial commit"

# Crea repository su GitHub
# Vai su github.com → New repository → Crea repo
git remote add origin https://github.com/tuo-username/mr-anto-scraper.git
git push -u origin main
```

### 2. Deploy su Railway
1. Vai su [railway.app](https://railway.app)
2. Login con GitHub
3. "New Project" → "Deploy from GitHub repo"
4. Seleziona il tuo repository
5. Railway farà tutto automaticamente!

### 3. Configurazione
Nel dashboard Railway:
- Vai su "Variables"
- Aggiungi le tue API keys:
  - `OPENAI_API_KEY`
  - `GEMINI_API_KEY`
  - `BROWSERBASE_API_KEY`
  - `BROWSERBASE_PROJECT_ID`

### 4. Risultato
Il tuo sistema sarà disponibile su: `https://tuo-progetto.railway.app`

## Opzione 2: Render (Alternativa)

1. Vai su [render.com](https://render.com)
2. "New" → "Web Service"
3. Connetti GitHub
4. Seleziona il repository
5. Render userà il `render.yaml` automaticamente

## Opzione 3: Vercel (Solo Frontend)

1. Vai su [vercel.com](https://vercel.com)
2. "New Project" → Importa da GitHub
3. Vercel userà il `vercel.json` automaticamente

## Costi
- **Railway**: GRATUITO (500 ore/mese)
- **Render**: GRATUITO (750 ore/mese)
- **Vercel**: GRATUITO (illimitato per frontend)

## Condivisione con Colleghi
Una volta deployato, condividi semplicemente l'URL pubblico!
