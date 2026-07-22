#!/usr/bin/env python3
"""
Main API Server per MR Scraper
Integra il fast_ai_extractor ottimizzato con l'UI
"""

# Forza UTF-8 su stdout/stderr: evita crash 'charmap' su console Windows (cp1252)
# quando il codice stampa emoji. No-op se lo stream non supporta reconfigure.
import sys
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import asyncio
import json
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv

# Carica le variabili d'ambiente dal file env.local
try:
    # Prova prima il percorso relativo (quando eseguito da start.py)
    load_dotenv("env.local")
    print("✅ Variabili d'ambiente caricate da env.local")
except Exception as e:
    try:
        # Prova il percorso assoluto (quando eseguito direttamente)
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        env_path = os.path.join(current_dir, "env.local")
        load_dotenv(env_path)
        print(f"✅ Variabili d'ambiente caricate da {env_path}")
    except Exception as e2:
        print(f"⚠️ Errore caricamento env.local: {e2}")
        print("💡 Verifica che il file env.local esista nella directory Backend")

# Import del nostro sistema ottimizzato
from fast_ai_extractor import FastAIExtractor
from ai_product_comparator import AIProductComparator
from chat_ai_manager import ChatAIManager
from selector_database import SelectorDatabase
from google_search_integration import GoogleSearchIntegration
from historical_products_db import HistoricalProductsDB
from price_monitor import PriceMonitor
from price_scheduler import PriceScheduler

# Stato condiviso e router
import app_state
from routers import (
    extraction,
    comparison,
    chat,
    selectors,
    monitoring,
    scheduler,
    history,
    url_monitor,
)

app = FastAPI(
    title="MR Scraper API",
    version="2.0.0",
    description="Sistema di scraping universale con AI ottimizzato"
)

# CORS middleware per permettere richieste dal frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In produzione, specificare domini specifici
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (Frontend)
try:
    # Prova diversi percorsi per trovare la directory Frontend
    frontend_paths = [
        "../Frontend",  # Quando eseguito da start.py
        "Frontend",     # Quando eseguito direttamente da Backend/
        "../../Frontend"  # Fallback
    ]

    frontend_mounted = False
    for path in frontend_paths:
        try:
            if os.path.exists(path):
                app.mount("/static", StaticFiles(directory=path), name="static")
                print(f"✅ Frontend servito da: {path}")
                frontend_mounted = True
                break
        except Exception as e:
            print(f"⚠️ Tentativo fallito per {path}: {e}")
            continue

    if not frontend_mounted:
        print("❌ Nessun percorso Frontend valido trovato")
        print("🔍 Percorsi provati:", frontend_paths)
        print("🔍 Directory corrente:", os.getcwd())
        print("🔍 Contenuto directory:", os.listdir("."))

except Exception as e:
    print(f"❌ Errore configurazione file statici: {e}")
    print("🔍 Directory corrente:", os.getcwd())

# ==========================================
# INFRA / STATIC ENDPOINTS
# ==========================================

from fastapi.responses import FileResponse

@app.get("/")
async def root():
    """Serve il frontend HTML"""
    try:
        # Serve il file index.html con percorso assoluto
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        frontend_path = os.path.join(current_dir, "..", "Frontend", "index.html")
        return FileResponse(frontend_path)
    except FileNotFoundError:
            return {
                "name": "MR Scraper API",
                "version": "2.0.0",
                "description": "Sistema di scraping universale con AI ottimizzato",
                "features": [
                    "Scraping generico multi-URL",
                    "Sistema AI universale",
                    "Chunking intelligente",
                    "Fallback automatico",
                    "Support immobili ed e-commerce"
                ],
                "endpoints": {
                    "fast-extract": "POST /fast-extract - Estrazione singola URL",
                    "fast-extract-multiple": "POST /fast-extract-multiple - Estrazione multipla URL",
                    "compare-products": "POST /compare-products - Confronto prodotti simili",
                    "health": "GET /health - Health check"
                }
            }

@app.get("/static/css/styles.css")
async def serve_css():
    """Serve il file CSS"""
    try:
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        css_path = os.path.join(current_dir, "..", "Frontend", "css", "styles.css")
        return FileResponse(css_path, media_type="text/css")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="CSS file not found")

@app.get("/static/js/config.js")
async def serve_config_js():
    """Serve il file config.js"""
    try:
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, "..", "Frontend", "js", "config.js")
        return FileResponse(config_path, media_type="application/javascript")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="config.js not found")

@app.get("/static/js/api.js")
async def serve_api_js():
    """Serve il file api.js"""
    try:
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        api_path = os.path.join(current_dir, "..", "Frontend", "js", "api.js")
        return FileResponse(api_path, media_type="application/javascript")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="api.js not found")

@app.get("/static/js/store.js")
async def serve_store_js():
    """Serve il file store.js"""
    try:
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        store_path = os.path.join(current_dir, "..", "Frontend", "js", "store.js")
        return FileResponse(store_path, media_type="application/javascript")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="store.js not found")

@app.get("/static/js/charts.js")
async def serve_charts_js():
    """Serve il file charts.js"""
    try:
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        charts_path = os.path.join(current_dir, "..", "Frontend", "js", "charts.js")
        return FileResponse(charts_path, media_type="application/javascript")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="charts.js not found")

@app.get("/static/js/actions.js")
async def serve_actions_js():
    """Serve il file actions.js"""
    try:
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        actions_path = os.path.join(current_dir, "..", "Frontend", "js", "actions.js")
        return FileResponse(actions_path, media_type="application/javascript")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="actions.js not found")

@app.get("/api")
async def api_info():
    """Endpoint con informazioni API"""
    return {
        "name": "MR Scraper API",
        "version": "2.0.0",
        "description": "Sistema di scraping universale con AI ottimizzato",
        "features": [
            "Scraping generico multi-URL",
            "Sistema AI universale",
            "Chunking intelligente",
            "Fallback automatico",
            "Support immobili ed e-commerce"
        ],
        "endpoints": {
            "fast-extract": "POST /fast-extract - Estrazione singola URL",
            "fast-extract-multiple": "POST /fast-extract-multiple - Estrazione multipla URL",
            "compare-products": "POST /compare-products - Confronto prodotti simili",
            "compare-prices": "POST /compare-prices - Confronto prezzi da dati salvati",
            "health": "GET /health - Health check"
        }
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "mr-scraper-api",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/debug/static-files")
async def debug_static_files():
    """Debug endpoint per verificare i file statici"""
    try:
        import os
        current_dir = os.getcwd()

        # Prova diversi percorsi
        frontend_paths = [
            "../Frontend",
            "Frontend",
            "../../Frontend"
        ]

        debug_info = {
            "current_directory": current_dir,
            "current_directory_contents": os.listdir("."),
            "frontend_paths": {},
            "static_files_mounted": False
        }

        for path in frontend_paths:
            try:
                if os.path.exists(path):
                    debug_info["frontend_paths"][path] = {
                        "exists": True,
                        "contents": os.listdir(path),
                        "js_contents": os.listdir(os.path.join(path, "js")) if os.path.exists(os.path.join(path, "js")) else "N/A"
                    }
                else:
                    debug_info["frontend_paths"][path] = {"exists": False}
            except Exception as e:
                debug_info["frontend_paths"][path] = {"error": str(e)}

        # Verifica se i file statici sono montati
        try:
            from fastapi.staticfiles import StaticFiles
            debug_info["static_files_mounted"] = True
        except:
            debug_info["static_files_mounted"] = False

        return debug_info

    except Exception as e:
        return {
            "error": str(e),
            "current_directory": os.getcwd() if 'os' in locals() else "N/A"
        }

# ==========================================
# REGISTRAZIONE ROUTER
# ==========================================

for _router in (
    extraction.router,
    comparison.router,
    chat.router,
    selectors.router,
    monitoring.router,
    scheduler.router,
    history.router,
    url_monitor.router,
):
    app.include_router(_router)

# ==========================================
# STARTUP
# ==========================================

@app.on_event("startup")
async def startup_event():
    """Inizializzazione all'avvio"""
    print("🚀 MR Scraper API v2.0.0 - Avvio completato")

    # Inizializza le istanze globali (single source of truth: app_state)
    print("🔧 Inizializzazione componenti...")
    app_state.extractor = FastAIExtractor()
    app_state.ai_comparator = AIProductComparator()
    app_state.chat_manager = ChatAIManager()
    app_state.selector_db = SelectorDatabase()
    app_state.google_search = GoogleSearchIntegration()
    app_state.historical_db = HistoricalProductsDB()
    app_state.price_monitor = PriceMonitor()
    app_state.price_scheduler = PriceScheduler(app_state.price_monitor)
    from url_monitor import UrlMonitor
    app_state.url_monitor = UrlMonitor()
    # Loop scansioni periodiche URL (usa getter per accedere ai singleton correnti)
    app_state.url_monitor.start_loop(lambda: app_state.extractor, lambda: app_state.historical_db)
    print("✅ Componenti inizializzati")

    # Seed demo: se il DB e' vuoto (es. Render effimero dopo un restart) inserisce
    # prodotti dimostrativi cosi' l'app e' sempre mostrabile. Gli scan reali si
    # aggiungono a questi.
    try:
        from seed_demo import seed_if_empty
        await seed_if_empty(app_state.historical_db)
    except Exception as e:
        print(f"⚠️ Seed demo non riuscito: {e}")

    # Avvia automaticamente il sistema di schedulazione
    try:
        print("⏰ Avvio automatico sistema di schedulazione...")
        scheduler_result = await app_state.price_scheduler.start_scheduler()
        if scheduler_result['success']:
            print(f"✅ Scheduler avviato automaticamente con {scheduler_result['active_tasks']} task")
        else:
            print(f"⚠️ Errore avvio automatico scheduler: {scheduler_result.get('error')}")
    except Exception as e:
        print(f"⚠️ Errore avvio automatico scheduler: {e}")
    print("🔧 Features attive:")
    print("   • Sistema AI universale")
    print("   • Chunking intelligente")
    print("   • Fallback automatico")
    print("   • Support multi-sito")
    print("   • Chat AI integrata")
    print("📍 Endpoints disponibili:")
    print("   • POST /fast-extract - Estrazione singola")
    print("   • POST /fast-extract-multiple - Estrazione multipla")
    print("   • POST /compare-products - Confronto prodotti AI")
    print("   • POST /compare-prices - Confronto prezzi da dati salvati")
    print("   • POST /test-ai-comparator - Test sistema AI")
    print("   • POST /google-search - Ricerca venditori alternativi")
    print("   • GET /historical-products - Ricerca prodotti storici")
    print("   • GET /dashboard-stats - Statistiche dashboard")
    print("   • GET /site-statistics - Statistiche siti")
    print("   • POST /monitoring/add-product - Aggiungi prodotto al monitoring")
    print("   • GET /monitoring/products - Lista prodotti monitorati")
    print("   • GET /monitoring/alerts - Alert prezzi")
    print("   • POST /monitoring/check-prices - Controllo forzato prezzi")
    print("   • POST /scheduler/start - Avvia scheduler")
    print("   • GET /scheduler/stats - Statistiche scheduler")
    print("   • POST /chat - Chat con AI (OpenAI, Ollama, Gemini)")
    print("   • GET /chat/models - Modelli AI disponibili")
    print("   • GET /selectors/stats - Statistiche selettori")
    print("   • GET /selectors/pending - Selettori in attesa")
    print("   • POST /selectors/approve/{domain} - Approva selettori")
    print("   • DELETE /selectors/{domain} - Elimina selettori")
    print("   • GET /health - Health check")

if __name__ == "__main__":
    import uvicorn
    import os

    # Per Railway/Render
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0" if os.environ.get("RAILWAY_ENVIRONMENT") else "127.0.0.1"

    print("🌐 Avvio server...")
    uvicorn.run(app, host=host, port=port, reload=not os.environ.get("RAILWAY_ENVIRONMENT"))
