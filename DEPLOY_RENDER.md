# 🆓 Deploy GRATUITO su Render

## Perché Render?
- ✅ **GRATUITO** (750 ore/mese)
- ✅ **Supporta Playwright** (essenziale per il tuo scraper)
- ✅ **Deploy automatico** da GitHub
- ✅ **SSL automatico**
- ✅ **Nessun costo nascosto**

## Passi per il Deploy

### 1. Preparazione
```bash
# Nel terminale
cd C:\Users\anto_\Desktop\AIDev\MR_Scraper\mr.-anto-scraper

# Inizializza git
git init
git add .
git commit -m "Initial commit"

# Crea repository su GitHub
# Vai su github.com → New repository
git remote add origin https://github.com/tuo-username/mr-anto-scraper.git
git push -u origin main
```

### 2. Deploy su Render
1. Vai su [render.com](https://render.com)
2. Clicca "Get Started" → "Sign up with GitHub"
3. Clicca "New" → "Web Service"
4. Connetti il tuo repository GitHub
5. Render rileverà automaticamente il `render.yaml`

### 3. Configurazione
- **Name**: mr-anto-scraper
- **Environment**: Python 3
- **Build Command**: `cd Backend && pip install -r requirements.txt && playwright install`
- **Start Command**: `cd Backend && uvicorn main:app --host 0.0.0.0 --port $PORT`

### 4. Variabili d'Ambiente
Nel dashboard Render, vai su "Environment" e aggiungi:
```
OPENAI_API_KEY=la_tua_chiave_openai
GEMINI_API_KEY=la_tua_chiave_gemini
BROWSERBASE_API_KEY=la_tua_chiave_browserbase
BROWSERBASE_PROJECT_ID=il_tuo_project_id
```

### 5. Deploy
Clicca "Create Web Service" e aspetta il deploy!

## Risultato
Il tuo sistema sarà disponibile su: `https://mr-anto-scraper.onrender.com`

## Costi
- **GRATUITO** per 750 ore/mese
- **$7/mese** se superi le ore gratuite (raramente necessario)

## Condivisione
Condividi semplicemente l'URL con i tuoi colleghi!
