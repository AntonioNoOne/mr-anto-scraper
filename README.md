# 🚀 Jusper - AI-Powered E-commerce Scraper

**Jusper** (ex Mr. Anto Scraper) è un sistema avanzato di web scraping per e-commerce con analisi AI integrata, dashboard in tempo reale e **il nuovo sistema AI-Assisted per scraping guidato**.

## 🤖 **NUOVO**: AI-Assisted Scraper

**Sistema rivoluzionario** che utilizza l'AI per guidarti nel processo di scraping!

### 🎯 Come Funziona:
1. **📍 Inserisci URL** → L'AI analizza automaticamente la pagina
2. **🧠 Analisi Intelligente** → "Cosa vuoi scrapare? Ho trovato questi elementi..."
3. **⚙️ Schema Personalizzato** → Definisci cosa estrarre in formato JSON
4. **✅ Validazione & Estrazione** → Risultati automatici con export!

### 🌟 Caratteristiche AI-Assisted:
- **Analisi AI automatica** del contenuto delle pagine web
- **Suggerimenti intelligenti** su cosa si può estrarre
- **Validazione schema** in tempo reale
- **Interfaccia step-by-step** intuitiva
- **Export automatico** in JSON/CSV

### 🚀 Accesso Rapido:
- **Interfaccia AI-Assisted**: Apri `Frontend/ai-assisted-scraper.html`
- **Test del Sistema**: `python Backend/test_ai_assisted.py`

## ✨ Caratteristiche Principali

- 🤖 **Analisi AI Avanzata** - Supporto per Gemini, GPT-4 e analisi locale
- 🔗 **LLM Scraper Integration** - Integrazione con [llm-scraper](https://github.com/mishushakov/llm-scraper) per scraping avanzato
- 📊 **Dashboard in Tempo Reale** - Statistiche live e metriche di performance  
- 🎯 **Scraping Intelligente** - Estrazione automatica di prodotti e prezzi
- 💾 **Persistenza Dati** - Salvataggio automatico in database SQLite
- 🔄 **Modalità Batch** - Elaborazione di URL multipli
- 📱 **UI Moderna** - Interfaccia Vue.js responsive e intuitiva
- 🚀 **Architettura Asincrona** - Performance ottimizzate con async/await
- ⚖️ **Sistema di Confronto Avanzato** - Confronto intelligente tra prodotti di siti diversi
- 🌐 **Filtri Dinamici** - Selezione multipla di domini per confronti mirati

## 🛠️ Installazione Rapida

### 1. Clona il Repository
```bash
git clone https://github.com/tuo-username/jusper.git
cd jusper
```

### 2. Installa le Dipendenze
```bash
pip install -r requirements.txt
```

### 3. Configura le Variabili d'Ambiente
```bash
# Copia il file di esempio
cp Backend/env.local Backend/env.local.backup

# Modifica Backend/env.local con le tue API keys
```

### 4. Avvia il Server
```bash
python start.py
```

Apri http://localhost:8000 nel browser! 🎉

## 🚀 Deploy su Railway (Hosting Gratuito)

### Deploy con Un Click
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/jusper)

### Deploy Manuale
1. Crea account su [Railway.app](https://railway.app)
2. Connetti il tuo repository GitHub
3. Configura le variabili d'ambiente:
   - `AI_PROVIDER=local` (o gemini/openai)
   - `GEMINI_API_KEY=tua_key` (se usi Gemini)
   - `OPENAI_API_KEY=tua_key` (se usi OpenAI)
4. Deploy automatico! ✨

## ⚙️ Configurazione AI

### Modalità Locale (Gratuita)
```bash
AI_PROVIDER=local
```
- ✅ Nessuna API key richiesta
- ✅ Completamente gratuito
- ✅ Privacy totale

### Modalità Gemini (Consigliata)
```bash
AI_PROVIDER=gemini
GEMINI_API_KEY=your_api_key
```
- 🚀 Analisi più precisa
- 💰 Tier gratuito generoso
- 🔗 [Ottieni API Key](https://makersuite.google.com/app/apikey)

### Modalità OpenAI
```bash
AI_PROVIDER=openai
OPENAI_API_KEY=your_api_key
```
- 🎯 Massima precisione
- 💵 A pagamento
- 🔗 [Ottieni API Key](https://platform.openai.com/api-keys)

## 📊 Dashboard Features

- **Statistiche Giornaliere** - Prodotti scansionati, accuratezza AI
- **Attività Recenti** - Log in tempo reale delle operazioni
- **Categorie Prodotti** - Classificazione automatica
- **Metriche Performance** - Tempi di risposta e ottimizzazioni
- **Reset Giornaliero** - Statistiche che si resettano ogni 24h

## 🔧 Utilizzo

### Scraping Singolo URL
1. Inserisci l'URL del sito e-commerce
2. Seleziona il provider AI
3. Clicca "Avvia Scraping"
4. Visualizza i risultati nella dashboard

### Scraping Multiplo
1. Clicca "Modalità Multipla"
2. Inserisci gli URL (uno per riga)
3. Configura le opzioni avanzate
4. Avvia l'elaborazione batch

### Confronto Prodotti Avanzato
1. **Modalità "Tutti i Prodotti"**: Confronta automaticamente tutti i prodotti di tutti i siti
2. **Modalità "Domini Specifici"**: Seleziona 2+ siti da confrontare per analisi mirata
3. **Risultati Intelligenti**: Trova prodotti simili con prezzi diversi tra siti diversi
4. **Filtri Dinamici**: Selezione multipla di domini con conteggio prodotti in tempo reale

## 🔗 LLM Scraper Integration

**Nuova integrazione** con [LLM Scraper](https://github.com/mishushakov/llm-scraper) per funzionalità avanzate di scraping!

### 🚀 Caratteristiche LLM Scraper:
- **Schema-based Extraction** - Estrazione basata su schemi Zod/JSON
- **Multiple LLM Support** - OpenAI, Anthropic, Google AI
- **Streaming Support** - Streaming di dati in tempo reale
- **Code Generation** - Generazione automatica di script Playwright
- **Multi-modal Support** - Supporto per immagini e screenshot

### 📦 Installazione Automatica:
```bash
cd Backend
python install_llm_scraper.py
```

### 📦 Installazione Manuale:
```bash
cd Backend
npm install
npx playwright install chromium
python test_llm_scraper.py
```

### 🔧 Utilizzo Rapido:
```python
from llm_scraper_bridge import scrape_with_llm_scraper

result = await scrape_with_llm_scraper(
    url="https://example.com",
    schema={"type": "object", "properties": {"products": {"type": "array"}}},
    format_type="html"
)
```

📖 **Documentazione completa**: `Backend/LLM_SCRAPER_README.md`

## 🏗️ Struttura del Progetto

```
jusper/
├── Backend/
│   ├── mr_anto_scraper.py      # API principale FastAPI
│   ├── html_analyzer.py        # Analizzatore HTML/AI asincrono
│   ├── ai_content_analyzer.py  # Analizzatore contenuto AI
│   ├── ai_product_comparator.py # Confronto intelligente prodotti con AI
│   ├── historical_products_db.py # Database prodotti storici
│   ├── llm_scraper_bridge.py   # Bridge per LLM Scraper
│   ├── test_llm_scraper.py     # Test LLM Scraper
│   ├── package.json            # Dipendenze Node.js
│   ├── selector_database.py    # Gestione selettori CSS
│   ├── unified_scraper.py      # Scraper unificato
│   ├── progressive_scraper.py  # Scraper progressivo
│   ├── price_monitor.py        # Monitoraggio prezzi
│   ├── price_extractor.py      # Estrazione prezzi
│   ├── google_price_finder.py  # Ricerca prezzi Google
│   ├── google_vision_finder.py # Ricerca con Google Vision
│   ├── playwright_selector_finder.py # Trova selettori con Playwright
│   ├── scraping_logic.py       # Logica di scraping
│   ├── utils.py                # Utilità generali
│   ├── cache_manager.py        # Gestione cache
│   ├── price_scheduler.py      # Scheduler prezzi
│   ├── env.local               # Configurazione ambiente
│   └── database/               # Database SQLite
├── Frontend/
│   ├── index.html             # UI Vue.js con sistema confronto avanzato
│   ├── css/styles.css         # Stili CSS personalizzati
│   └── js/                    # Moduli JavaScript modulari
├── data/
│   ├── cache/                 # Cache dati
│   ├── database/              # Database selettori
│   └── api_extracts/          # Estrazioni API salvate
├── docs/                      # Documentazione
├── start.py                   # Script di avvio
├── requirements.txt           # Dipendenze Python
├── Procfile                  # Configurazione deploy
└── railway.json             # Configurazione Railway
```

## 🐛 Risoluzione Problemi

### Errore "Browser has been closed"
- Assicurati che Playwright sia installato: `playwright install`
- Riavvia il server dopo cambi di configurazione

### Problemi con API Keys
- Verifica che le chiavi siano corrette in `Backend/env.local`
- Controlla i limiti di quota delle API

### Port già in uso
- Cambia porta in `start.py` o usa: `python start.py --port 8001`

## 🤝 Contribuire

1. Fork del repository
2. Crea un branch feature (`git checkout -b feature/nuova-feature`)
3. Commit delle modifiche (`git commit -am 'Aggiungi nuova feature'`)
4. Push del branch (`git push origin feature/nuova-feature`)
5. Crea una Pull Request

## 📝 Licenza

Questo progetto è distribuito sotto licenza MIT. Vedi `LICENSE` per maggiori dettagli.

## 🙏 Crediti

Sviluppato con ❤️ per la community del web scraping.

---

**⭐ Se ti piace il progetto, lascia una stella su GitHub!** 