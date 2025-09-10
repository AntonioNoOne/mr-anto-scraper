# 🧹 MR Scraper - Struttura Progetto Pulita

## 📁 Struttura Principale

```
mr.-anto-scraper/
├── start.py                    # 🚀 Avvio server principale
├── requirements.txt            # 📦 Dipendenze Python
├── env.local                   # 🔑 API Keys (Backend/)
├── README.md                   # 📖 Documentazione principale
├── PROJECT_STRUCTURE.md        # 📋 Documentazione struttura
├── Frontend/
│   └── index.html             # 🎨 UI principale con chat AI
└── Backend/
    ├── main.py                # 🌐 Server FastAPI principale
    ├── fast_ai_extractor.py   # ⚡ Sistema estrazione principale
    ├── ai_content_analyzer.py # 🤖 AI per analisi contenuti
    ├── ai_product_comparator.py # 🧠 AI per confronto prodotti
    ├── google_search_integration.py # 🔍 Ricerca venditori alternativi
    ├── chat_ai_manager.py     # 💬 Gestione chat AI
    ├── product_comparator.py  # 🔄 Confronto prodotti (fallback)
    ├── selector_database.py   # 🗄️ Database selettori ottimali
    ├── selector_database.json # 💾 File database selettori
    ├── env.local              # 🔑 API Keys
    └── future_implementations/ # 🔮 Script per implementazioni future
        ├── price_monitor.py
        ├── price_scheduler.py
        ├── google_price_finder.py
        ├── google_vision_finder.py
        ├── cache_manager.py
```

## 🗂️ Cartella "vecchio/"

Contiene file obsoleti organizzati per categoria:

### obsolete_scrapers/
- `mr_anto_scraper.py` - Sostituito da main.py + fast_ai_extractor.py
- `html_extractor_improved.py` - Sostituito da fast_ai_extractor.py
- `progressive_scraper.py` - Sostituito da fast_ai_extractor.py
- `html_analyzer.py` - Sostituito da ai_content_analyzer.py
- `llm_enhanced_analyzer.py` - Sostituito da ai_content_analyzer.py
- `llm_scraper_bridge.py` - Sostituito da fast_ai_extractor.py
- `price_extractor.py` - Funzionalità integrata in fast_ai_extractor.py
- `playwright_selector_finder.py` - Funzionalità integrata
- `utils.py` - Funzionalità integrate nei moduli principali

### node_js/
- `package.json` - Progetto Node.js non necessario
- `package-lock.json` - Dipendenze Node.js
- `node_modules/` - Moduli Node.js
- `install_llm_scraper.py` - Installazione Node.js
- `llm_scraper_scripts/` - Script Node.js

### debug/
- `test_import.py` - File di test temporaneo
- `ai_content_analyzer_backup.py` - Backup precedente

## 🎯 File Essenziali

### Core System
- **`start.py`** - Avvia il server con uvicorn
- **`Backend/main.py`** - Server FastAPI con tutti gli endpoint
- **`Backend/fast_ai_extractor.py`** - Sistema di estrazione intelligente
- **`Backend/ai_content_analyzer.py`** - AI per analisi contenuti
- **`Backend/ai_product_comparator.py`** - AI per confronto prodotti semantico
- **`Backend/google_search_integration.py`** - Ricerca venditori alternativi
- **`Backend/chat_ai_manager.py`** - Gestione chat con OpenAI/Gemini/Ollama
- **`Backend/product_comparator.py`** - Confronto prodotti testuale (fallback)
- **`Backend/selector_database.py`** - Database selettori ottimali

### Frontend
- **`Frontend/index.html`** - UI completa con chat AI integrata

### Configurazione
- **`requirements.txt`** - Dipendenze Python
- **`Backend/env.local`** - API keys per OpenAI, Gemini, etc.

## 🗄️ Database Selettori (FASE 1 ✅)

### Funzionalità Implementate:
- ✅ **Salvataggio automatico** selettori che funzionano bene
- ✅ **Riutilizzo intelligente** selettori salvati per siti noti
- ✅ **Sistema di approvazione** manuale per selettori
- ✅ **Tracking performance** e success rate
- ✅ **Fallback automatico** a selettori generici
- ✅ **API endpoints** per gestione selettori

### Endpoints Selettori:
- `GET /selectors/stats` - Statistiche database selettori
- `GET /selectors/pending` - Selettori in attesa approvazione
- `POST /selectors/approve/{domain}` - Approva selettori per dominio
- `DELETE /selectors/{domain}` - Elimina selettori per dominio

### Flusso di Lavoro:
1. **Prima estrazione**: Usa selettori generici e salva quelli che funzionano
2. **Estrazioni successive**: Usa selettori salvati per velocità e accuratezza
3. **Approvazione manuale**: Utente può approvare selettori salvati
4. **Tracking performance**: Sistema monitora success rate dei selettori

## 🧠 AI Product Comparator (FASE 2 ✅)

### Funzionalità Implementate:
- ✅ **Analisi semantica AI** per confronto prodotti
- ✅ **Normalizzazione intelligente** nomi, prezzi, brand
- ✅ **Clustering automatico** prodotti simili
- ✅ **Calcolo statistiche prezzo** avanzate
- ✅ **Fallback testuale** se AI non disponibile
- ✅ **Score di similarità** 0-1 per ogni gruppo
- ✅ **Differenze prezzo** e opportunità di risparmio

### Caratteristiche Avanzate:
- **Analisi AI diretta**: Per gruppi piccoli (≤20 prodotti)
- **Analisi AI per gruppi**: Per grandi dataset con merge intelligente
- **Normalizzazione robusta**: Gestione separatori decimali, valute, stop words
- **Statistiche dettagliate**: Min/max/avg prezzo, varianza, differenze percentuali
- **Opportunità di risparmio**: Calcolo automatico potenziali risparmi

### Vantaggi vs Sistema Testuale:
- 🎯 **Accuratezza superiore**: Identifica prodotti simili anche con nomi diversi
- 🧠 **Comprensione semantica**: Capisce sinonimi e variazioni linguistiche
- 📊 **Analisi più ricca**: Statistiche prezzo e clustering intelligente
- 🔄 **Fallback robusto**: Sistema testuale come backup

## 🔍 Google Search Integration (FASE 3 ✅)

### Funzionalità Implementate:
- ✅ **Ricerca automatica** venditori alternativi
- ✅ **Query intelligenti** generate automaticamente
- ✅ **Ricerca Google Shopping** per prezzi diretti
- ✅ **Ricerca Google Web** per siti e-commerce
- ✅ **Validazione risultati** con score di rilevanza
- ✅ **Estrazione prodotti** dai siti trovati
- ✅ **Confronto prezzi** con prodotto originale
- ✅ **Identificazione migliori offerte**

### Caratteristiche Avanzate:
- **Generazione query ottimizzate**: Basate su nome, brand, prezzo
- **Ricerca multi-fonte**: Google Shopping + Google Web
- **Filtro siti e-commerce**: Solo siti di vendita validi
- **Score di validazione**: Rilevanza risultati 0-1
- **Estrazione automatica**: Usa fast_ai_extractor sui siti trovati
- **Confronto AI**: Usa ai_product_comparator per analisi semantica
- **Identificazione offerte**: Trova automaticamente le migliori offerte

### Vantaggi:
- 🔍 **Scoperta automatica**: Trova venditori non considerati
- 📊 **Confronti completi**: Analisi prezzo più ampia
- 🎯 **Offerte migliori**: Identifica automaticamente i migliori prezzi
- 🧠 **Analisi intelligente**: Usa AI per confronti semantici
- ⚡ **Performance ottimizzate**: Rate limiting e caching

## 🔮 Future Implementations

Script pronti per implementazioni future:

- **`price_monitor.py`** - Monitoraggio prezzi nel tempo
- **`price_scheduler.py`** - Schedulazione controlli prezzi
- **`google_price_finder.py`** - Ricerca prezzi su Google
- **`google_vision_finder.py`** - Analisi immagini con Google Vision
- **`cache_manager.py`** - Gestione cache per performance

## 🚀 Avvio Progetto

```bash
# Avvio normale
python start.py

# Avvio senza browser
python start.py --no-browser

# Avvio con auto-reload (sviluppo)
python start.py --reload

# Avvio su porta specifica
python start.py --port 8080
```

## 🌐 Endpoints API

### Estrazione e Confronto
- `POST /fast-extract` - Estrazione singola URL
- `POST /fast-extract-multiple` - Estrazione multipla URL
- `POST /compare-products` - Confronto prodotti AI semantico
- `POST /compare-prices` - Confronto prezzi da dati salvati
- `POST /test-ai-comparator` - Test sistema AI
- `POST /google-search` - Ricerca venditori alternativi

### Chat AI
- `POST /chat` - Chat con AI
- `GET /chat/models` - Modelli AI disponibili
- `GET /chat/test` - Test connessioni AI
- `GET /chat/keys` - Status API keys

### Database Selettori
- `GET /selectors/stats` - Statistiche selettori
- `GET /selectors/pending` - Selettori in attesa
- `POST /selectors/approve/{domain}` - Approva selettori
- `DELETE /selectors/{domain}` - Elimina selettori

### Utility
- `GET /health` - Health check
- `GET /` - Pagina principale
- `GET /api` - Info API

## ✅ Implementazioni Completate

### FASE 1: Database Selettori ✅
- ✅ Integrato `selector_database.py` nel sistema principale
- ✅ Modificato `fast_ai_extractor.py` per usare selettori salvati
- ✅ Aggiunto sistema di fallback a selettori generici
- ✅ Implementato salvataggio automatico selettori funzionanti
- ✅ Aggiunto tracking performance e success rate
- ✅ Creati endpoint API per gestione selettori
- ✅ Sistema di approvazione manuale selettori

### FASE 2: AI Product Comparator ✅
- ✅ Creato `ai_product_comparator.py` con analisi semantica AI
- ✅ Integrato con `ai_content_analyzer.py` e `chat_ai_manager.py`
- ✅ Modificato endpoint `/compare-products` per usare AI
- ✅ Implementato sistema di normalizzazione intelligente
- ✅ Aggiunto clustering automatico prodotti simili
- ✅ Calcolo statistiche prezzo avanzate
- ✅ Sistema di fallback al confronto testuale
- ✅ Endpoint di test `/test-ai-comparator`

### FASE 3: Google Search Integration ✅
- ✅ Creato `google_search_integration.py` per ricerca venditori alternativi
- ✅ Integrato con `fast_ai_extractor.py` e `ai_product_comparator.py`
- ✅ Implementato generazione query di ricerca intelligenti
- ✅ Aggiunto ricerca Google Shopping e Google Web
- ✅ Sistema di validazione risultati con score di rilevanza
- ✅ Estrazione automatica prodotti dai siti trovati
- ✅ Confronto prezzi con AI Product Comparator
- ✅ Identificazione automatica migliori offerte
- ✅ Endpoint `/google-search` per ricerca venditori alternativi

### Vantaggi Ottenuti:
- 🚀 **Performance migliorata**: Estrazione più veloce per siti noti
- 🎯 **Accuratezza aumentata**: Selettori ottimizzati per ogni sito
- 🧠 **Intelligenza semantica**: Confronto prodotti con AI
- 🔍 **Scoperta automatica**: Trova venditori alternativi automaticamente
- 📊 **Apprendimento continuo**: Sistema migliora con l'uso
- 🔧 **Gestione flessibile**: Approvazione e modifica selettori
- 📈 **Monitoraggio avanzato**: Statistiche performance e prezzi
- 💰 **Risparmio automatico**: Identifica le migliori offerte

## 🎯 Prossimi Passi

### FASE 4: Price Monitoring & Scheduling (IN CORSO)
- [ ] Integrare `price_monitor.py` e `price_scheduler.py`
- [ ] Database storico prezzi con SQLite
- [ ] Sistema di alert e notifiche email
- [ ] Dashboard monitoraggi in tempo reale
- [ ] Schedulazione automatica controlli prezzi
- [ ] Analisi trend prezzi nel tempo

### FASE 5: Advanced Analytics
- [ ] Analisi competitor e strategie prezzo
- [ ] Predizione variazioni prezzo con ML
- [ ] Dashboard analytics avanzate
- [ ] Report automatici e export dati
- [ ] Integrazione con Google Vision per analisi immagini

## 📊 Statistiche Progetto

- **File essenziali**: 9 file core
- **File obsoleti**: 9 file spostati in vecchio/
- **Script future**: 5 script pronti per implementazione
- **Endpoint API**: 17+ endpoint disponibili
- **Database**: 1 database selettori attivo
- **Sistemi AI**: 4 sistemi AI integrati (estrazione, confronto, chat, ricerca)
- **Funzionalità**: Estrazione, confronto AI, chat AI, database selettori, ricerca Google 