# 🚀 Deploy su Railway - Guida Completa

## 1. Preparazione
```bash
# Assicurati di essere nella directory del progetto
cd C:\Users\anto_\Desktop\AIDev\MR_Scraper\mr.-anto-scraper

# Inizializza git se non l'hai già fatto
git init
git add .
git commit -m "Initial commit"
```

## 2. Deploy su Railway
1. Vai su [railway.app](https://railway.app)
2. Clicca "Login" e accedi con GitHub
3. Clicca "New Project" → "Deploy from GitHub repo"
4. Seleziona il tuo repository
5. Railway rileverà automaticamente il `railway.json`

## 3. Configurazione Variabili d'Ambiente
Nel dashboard Railway, vai su "Variables" e aggiungi:
```
OPENAI_API_KEY=la_tua_chiave_openai
GEMINI_API_KEY=la_tua_chiave_gemini
BROWSERBASE_API_KEY=la_tua_chiave_browserbase
BROWSERBASE_PROJECT_ID=il_tuo_project_id
```

## 4. Deploy Automatico
Railway farà il deploy automaticamente e ti darà un URL pubblico!

## 5. Test
Il tuo sistema sarà disponibile su: `https://tuo-progetto.railway.app`

## Costi
- **GRATUITO** per i primi 500 ore/mese
- **$5/mese** per il piano Pro (se necessario)
