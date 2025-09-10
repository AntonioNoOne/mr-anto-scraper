#!/usr/bin/env python3
"""
Main API Server per MR Scraper
Integra il fast_ai_extractor ottimizzato con l'UI
"""


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

# Configurazione globale del browser
browser_config = {
    "mode": "stealth",
    "timeout": 60,
    "human_delay": 2.0,
    "user_agent": "auto",
    "proxy": None
}

# Flag globale per fermare lo scraping
scraping_stop_flag = {"stop": False}

# ==========================================
# MODELS
# ==========================================

class ExtractRequest(BaseModel):
    url: str

class MultipleExtractRequest(BaseModel):
    urls: List[str]

class ExtractResponse(BaseModel):
    success: bool
    products: List[dict] = []
    error: Optional[str] = None
    total_found: int = 0
    containers_found: int = 0
    container_selector: Optional[str] = None
    url: Optional[str] = None

class MultipleExtractResponse(BaseModel):
    success: bool
    results: List[ExtractResponse] = []
    total_sites: int = 0
    total_products: int = 0
    errors: List[str] = []

class CompareRequest(BaseModel):
    results: List[dict]  # Risultati da comparare
    sources: Optional[List[str]] = None  # Domini selezionati per il confronto (es: ['amazon.it', 'mediaworld.it'])

class ComparePricesRequest(BaseModel):
    products: List[dict]  # Prodotti estratti da confrontare

class BrowserConfigRequest(BaseModel):
    mode: str  # 'normal', 'stealth', 'visible'
    timeout: int = 60
    human_delay: float = 2.0
    user_agent: str = 'auto'
    proxy: Optional[str] = None

class CompareResponse(BaseModel):
    success: bool
    matches: List[dict] = []
    statistics: dict = {}
    total_sites: int = 0
    total_products: int = 0
    comparable_products: int = 0
    error: Optional[str] = None

class ChatMessage(BaseModel):
    role: str  # "user" o "assistant"
    content: str
    timestamp: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    model: str = "openai"  # "openai", "ollama", "gemini"
    conversation_history: List[ChatMessage] = []
    context_data: Optional[dict] = None  # Contesto completo dell'applicazione

class ChatResponse(BaseModel):
    success: bool
    response: str
    model_used: str
    error: Optional[str] = None

# ==========================================
# GLOBAL EXTRACTOR INSTANCE
# ==========================================

# Variabili globali per le istanze (inizializzate in startup_event)
extractor = None
ai_comparator = None
chat_manager = None
selector_db = None
google_search = None
historical_db = None
price_monitor = None
price_scheduler = None

# ==========================================
# ENDPOINTS
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

@app.post("/fast-extract", response_model=ExtractResponse)
async def fast_extract(request: ExtractRequest):
    """
    Endpoint per estrazione singola URL
    """
    try:
        # Reset del flag di stop
        scraping_stop_flag["stop"] = False
        
        print(f"🚀 Fast Extract - URL: {request.url}")
        
        # Usa la configurazione browser globale aggiornata
        global browser_config
        
        # Se non c'è configurazione globale, usa default stealth
        if 'browser_config' not in globals() or not browser_config:
            browser_config = {
                'mode': 'stealth',  # Default stealth come richiesto
                'timeout': 60,
                'human_delay': 2.0,
                'user_agent': 'auto',
                'proxy': ''
            }
        
        print(f"⚙️ Configurazione browser globale: {browser_config}")
        print(f"🌐 Modalità selezionata: {browser_config.get('mode', 'N/A')}")
        print(f"⏱️ Timeout: {browser_config.get('timeout', 'N/A')}s")
        print(f"🕐 Delay umano: {browser_config.get('human_delay', 'N/A')}s")
        
        # Passa la configurazione del browser all'estrattore con flag di stop
        result = await extractor.extract_products_fast(
            request.url, 
            browser_config=browser_config,
            stop_flag=scraping_stop_flag
        )
        
        if result['success']:
            print(f"✅ Successo: {len(result['products'])} prodotti estratti")
            
            # Salva risultati per debugging
            await save_extraction_result(request.url, result)
            
            # Salva prodotti nel database storico con timestamp reali
            try:
                db_result = await historical_db.save_extracted_products(
                    url=request.url,
                    products=result['products'],
                    session_id=None,  # Generato automaticamente
                    extraction_method="fast_ai_extractor",
                    container_selector=result.get('container_selector'),
                    start_time=result.get('start_time'),
                    end_time=result.get('end_time'),
                    duration=result.get('duration')
                )
                print(f"💾 Salvati {db_result.get('saved_count', 0)} prodotti nel database storico")
            except Exception as e:
                print(f"⚠️ Errore salvataggio database storico: {e}")
            
            return ExtractResponse(
                success=True,
                products=result['products'],
                total_found=result['total_found'],
                containers_found=result.get('containers_found', 0),
                container_selector=result.get('container_selector', 'N/A'),
                url=request.url
            )
        else:
            print(f"❌ Errore: {result.get('error')}")
            return ExtractResponse(
                success=False,
                error=result.get('error', 'Errore sconosciuto'),
                url=request.url
            )
            
    except Exception as e:
        print(f"❌ Eccezione API: {e}")
        return ExtractResponse(
            success=False,
            error=f"Errore interno: {str(e)}",
            url=request.url
        )

@app.post("/fast-extract-multiple", response_model=MultipleExtractResponse)
async def fast_extract_multiple(request: MultipleExtractRequest):
    """
    Endpoint per estrazione multipla URL
    Processa ogni URL sequenzialmente per evitare sovraccarico
    """
    try:
        # Reset del flag di stop
        scraping_stop_flag["stop"] = False
        
        print(f"🚀 Fast Extract Multiple - {len(request.urls)} URLs")
        
        results = []
        errors = []
        total_products = 0
        
        for i, url in enumerate(request.urls, 1):
            # Controlla se deve fermarsi
            if scraping_stop_flag["stop"]:
                print(f"🛑 Estrazione multipla fermata dall'utente")
                break
                
            print(f"📍 Processando URL {i}/{len(request.urls)}: {url}")
            
            try:
                result = await extractor.extract_products_fast(
                    url, 
                    browser_config=browser_config,
                    stop_flag=scraping_stop_flag
                )
                
                if result['success']:
                    products_count = len(result['products'])
                    total_products += products_count
                    print(f"✅ URL {i}: {products_count} prodotti estratti")
                    
                    # Salva risultati con timestamp reali
                    await save_extraction_result(url, result)
                    
                    # Salva anche nel database storico
                    try:
                        db_result = await historical_db.save_extracted_products(
                            url=url,
                            products=result['products'],
                            session_id=None,
                            extraction_method="fast_ai_extractor",
                            container_selector=result.get('container_selector'),
                            start_time=result.get('start_time'),
                            end_time=result.get('end_time'),
                            duration=result.get('duration')
                        )
                        print(f"💾 URL {i}: Salvati {db_result.get('saved_count', 0)} prodotti nel database storico")
                    except Exception as e:
                        print(f"⚠️ Errore salvataggio database storico per {url}: {e}")
                    
                    results.append(ExtractResponse(
                        success=True,
                        products=result['products'],
                        total_found=result['total_found'],
                        containers_found=result.get('containers_found', 0),
                        container_selector=result.get('container_selector', 'N/A'),
                        url=url
                    ))
                else:
                    error_msg = result.get('error', 'Errore sconosciuto')
                    print(f"❌ URL {i}: {error_msg}")
                    errors.append(f"{url}: {error_msg}")
                    
                    results.append(ExtractResponse(
                        success=False,
                        error=error_msg,
                        url=url
                    ))
                    
            except Exception as e:
                error_msg = f"Errore interno: {str(e)}"
                print(f"❌ URL {i}: {error_msg}")
                errors.append(f"{url}: {error_msg}")
                
                results.append(ExtractResponse(
                    success=False,
                    error=error_msg,
                    url=url
                ))
        
        success_count = sum(1 for r in results if r.success)
        print(f"🎯 Completato: {success_count}/{len(request.urls)} successi, {total_products} prodotti totali")
        
        return MultipleExtractResponse(
            success=success_count > 0,
            results=results,
            total_sites=len(request.urls),
            total_products=total_products,
            errors=errors
        )
        
    except Exception as e:
        print(f"❌ Errore multiplo: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/stop-scraping")
async def stop_scraping():
    """
    Endpoint per fermare lo scraping in corso
    """
    try:
        print("🛑 Richiesta di stop scraping ricevuta")
        scraping_stop_flag["stop"] = True
        return {"success": True, "message": "Stop richiesto per lo scraping"}
    except Exception as e:
        print(f"❌ Errore richiesta stop: {e}")
        return {"success": False, "error": str(e)}

@app.post("/compare-products", response_model=CompareResponse)
async def compare_products(request: CompareRequest):
    """
    Endpoint per confronto prodotti da risultati multipli
    Usa AI per analisi semantica e trova prodotti simili
    """
    try:
        print(f"🔍 Compare Products - {len(request.results)} risultati da confrontare")
        
        # DEBUG COMPLETO: Mostra TUTTO quello che arriva nella richiesta
        print("🔍 DEBUG - CONTENUTO COMPLETO RICHIESTA:")
        print(f"  Tipo richiesta: {type(request)}")
        print(f"  Attributi richiesta: {dir(request)}")
        print(f"  Sources presente: {hasattr(request, 'sources')}")
        if hasattr(request, 'sources'):
            print(f"  Sources valore: {request.sources}")
        print(f"  Results count: {len(request.results)}")
        
        for i, result in enumerate(request.results):
            print(f"  Risultato {i+1}:")
            print(f"    Success: {result.get('success')}")
            print(f"    URL: {result.get('url')}")
            print(f"    Products count: {len(result.get('products', []))}")
            if result.get('products'):
                print(f"    Primi 3 prodotti:")
                for j, product in enumerate(result.get('products', [])[:3]):
                    print(f"      Prodotto {j+1}: {product.get('name', 'N/A')} - {product.get('price', 'N/A')}")
        
        # STRATEGIA FILTRATA: Carica SOLO i prodotti dei domini selezionati
        print("🔄 Caricamento prodotti FILTRATI per domini selezionati...")
        
        # Estrai domini selezionati dal frontend
        selected_domains = request.sources if request.sources else []
        
        if selected_domains:
            print(f"🎯 DOMINI SELEZIONATI DAL FRONTEND: {selected_domains}")
            
            # Usa direttamente historical_db con filtro sources
            try:
                print(f"🎯 Filtro domini applicato: {selected_domains}")
                
                filters = {'limit': 10000, 'sources': selected_domains}
                db_result = await historical_db.search_historical_products(filters)
                
                if db_result.get('success') and db_result.get('products'):
                    all_products = db_result['products']
                    print(f"✅ Caricati {len(all_products)} prodotti FILTRATI per domini selezionati")
                    
                    # Debug: mostra i primi 5 prodotti per verifica
                    print("🔍 DEBUG - PRIMI 5 PRODOTTI FILTRATI:")
                    for i, product in enumerate(all_products[:5]):
                        print(f"  Prodotto {i+1}:")
                        print(f"    Nome: '{product.get('name', 'N/A')}'")
                        print(f"    Source: '{product.get('source', 'N/A')}'")
                        print(f"    Source URL: '{product.get('source_url', 'N/A')}'")
                        print(f"    Site: '{product.get('site', 'N/A')}'")
                else:
                    print(f"❌ Errore caricamento database filtrato: {db_result.get('error')}")
                    all_products = []
                    
            except Exception as e:
                print(f"❌ Errore caricamento database filtrato: {e}")
                all_products = []
        else:
            print("🌍 Nessun dominio selezionato, confronto TUTTI i prodotti")
            
            # Carica tutti i prodotti dal database senza filtri
            try:
                filters = {'limit': 10000}  # Carica tutti i prodotti
                db_result = await historical_db.search_historical_products(filters)
                
                if db_result.get('success') and db_result.get('products'):
                    all_products = db_result['products']
                    print(f"✅ Caricati {len(all_products)} prodotti dal database")
                    
                    # Debug: mostra i primi 5 prodotti
                    print("🔍 DEBUG - PRIMI 5 PRODOTTI DAL DATABASE:")
                    for i, product in enumerate(all_products[:5]):
                        print(f"  Prodotto {i+1}:")
                        print(f"    Nome: '{product.get('name', 'N/A')}'")
                        print(f"    Prezzo: '{product.get('price', 'N/A')}'")
                        print(f"    Brand: '{product.get('brand', 'N/A')}'")
                        print(f"    Source: '{product.get('source', 'N/A')}'")
                    
                else:
                    print(f"❌ Errore caricamento database: {db_result.get('error')}")
                    all_products = []
                    
            except Exception as e:
                print(f"❌ Errore caricamento database: {e}")
                all_products = []
        
        if not all_products:
            return CompareResponse(
                success=False,
                error="Nessun prodotto trovato nel database per il confronto"
            )
        
        print(f"🛍️ Totale prodotti caricati dal database: {len(all_products)}")
        
        # DEBUG: Mostra cosa viene passato all'AI comparator
        print("🔍 DEBUG - DATI PASSATI ALL'AI COMPARATOR:")
        print(f"  Prodotti totali: {len(all_products)}")
        print(f"  Domini selezionati: {selected_domains}")
        print(f"  Primi 5 prodotti per verifica:")
        for i, product in enumerate(all_products[:5]):
            print(f"    Prodotto {i+1}: {product.get('name', 'N/A')} da {product.get('source', 'N/A')}")
        
        # Usa il nuovo sistema AI per confronto con filtraggio domini
        result = await ai_comparator.compare_products_ai(all_products, selected_domains)
        
        if result['success']:
            print(f"✅ Confronto AI completato: {len(result['matches'])} gruppi trovati")
            
            return CompareResponse(
                success=True,
                matches=result['matches'],
                statistics=result['statistics'],
                total_sites=result['total_sites'],
                total_products=result['total_products'],
                comparable_products=result['comparable_products']
            )
        else:
            print(f"❌ Confronto AI fallito: {result.get('error')}")
            return CompareResponse(
                success=False,
                error=result.get('error', 'Errore confronto AI sconosciuto')
            )
            
    except Exception as e:
        print(f"❌ Errore confronto: {e}")
        return CompareResponse(
            success=False,
            error=f"Errore interno: {str(e)}"
        )

@app.post("/compare-prices", response_model=CompareResponse)
async def compare_prices(request: ComparePricesRequest):
    """Confronta prezzi dai dati estratti salvati"""
    try:
        print(f"💰 Confronto prezzi da {len(request.products)} prodotti...")
        
        if not request.products:
            return CompareResponse(
                success=False,
                error="Nessun prodotto fornito per il confronto"
            )
        
        # Usa il comparatore per trovare match
        matches = ai_comparator.find_matches(request.products)
        
        # Calcola statistiche
        total_sites = len(set(p.get('source', p.get('source_url', 'Unknown')) for p in request.products))
        total_products = len(request.products)
        comparable_products = len(matches)
        
        statistics = {
            "total_sites": total_sites,
            "total_products": total_products,
            "comparable_products": comparable_products,
            "match_percentage": round((comparable_products / total_products * 100), 2) if total_products > 0 else 0,
            "price_range": {
                "min": min([float(p.get('price', '0').replace('€', '').replace(',', '.')) for p in request.products if p.get('price')], default=0),
                "max": max([float(p.get('price', '0').replace('€', '').replace(',', '.')) for p in request.products if p.get('price')], default=0)
            }
        }
        
        return CompareResponse(
            success=True,
            matches=matches,
            statistics=statistics,
            total_sites=total_sites,
            total_products=total_products,
            comparable_products=comparable_products
        )
        
    except Exception as e:
        print(f"❌ Errore confronto prezzi: {str(e)}")
        return CompareResponse(
            success=False,
            error=f"Errore durante il confronto prezzi: {str(e)}"
        )

@app.post("/chat", response_model=ChatResponse)
async def chat_with_ai(request: ChatRequest):
    """Chat con AI (OpenAI, Ollama, Gemini)"""
    try:
        # Importa i moduli necessari
        from google_search_integration import google_search
        
        # Ottieni il contesto attuale dell'applicazione
        context_parts = []
        
        # 1. Contesto Google Search (dal backend)
        google_results = []
        if hasattr(google_search, 'last_results') and google_search.last_results:
            google_results = google_search.last_results
            context_parts.append("🔍 CONTESTO GOOGLE SEARCH (Backend):")
            for i, result in enumerate(google_results[:5], 1):  # Limita a 5 risultati
                context_parts.append(f"  {i}. {result.get('name', 'N/A')} - {result.get('price', 'N/A')} - {result.get('source', 'N/A')}")
        
        # 4. Statistiche Generali
        try:
            from historical_products_db import historical_db
            if historical_db:
                stats = historical_db.get_dashboard_statistics()
                if stats:
                    context_parts.append(f"\n📈 STATISTICHE GENERALI:")
                    context_parts.append(f"  Prodotti totali nel database: {stats.get('total_products', 0)}")
                    context_parts.append(f"  Siti monitorati: {stats.get('total_sites', 0)}")
                    context_parts.append(f"  Ultima estrazione: {stats.get('last_extraction', 'N/A')}")
        except Exception as e:
            print(f"⚠️ Errore nel recupero statistiche: {e}")
        
        # Costruisci il messaggio potenziato con tutto il contesto
        enhanced_message = request.message
        
        # Aggiungi istruzioni specifiche per l'analisi
        if "analizza" in request.message.lower() or "trova" in request.message.lower() or "migliori" in request.message.lower():
            enhanced_message = f"""
{request.message}

ISTRUZIONI SPECIFICHE:
- Analizza i dati forniti nel contesto
- Identifica i migliori prezzi e le migliori offerte
- Fornisci raccomandazioni specifiche basate sui dati reali
- Ordina i risultati per convenienza
- Calcola risparmi potenziali
- Suggerisci il miglior acquisto

"""
        
        # Aggiungi il contesto dal frontend se disponibile
        print(f"🔍 DEBUG: Context data ricevuto: {request.context_data}")
        if request.context_data:
            context_parts.append(f"\n📱 CONTESTO FRONTEND:")
            context_parts.append(f"  Sezione attuale: {request.context_data.get('current_section', 'N/A')}")
            
            # Contesto Scraping dal frontend
            if request.context_data.get('scraping_results'):
                scraping = request.context_data['scraping_results']
                context_parts.append(f"  📊 SCRAPING GENERICO:")
                context_parts.append(f"    Siti scrapati: {scraping.get('sites_count', 0)}")
                context_parts.append(f"    Prodotti totali: {scraping.get('total_products', 0)}")
                
                # Aggiungi dettagli dei siti
                if scraping.get('sites'):
                    context_parts.append(f"    Dettagli siti:")
                    for site in scraping['sites'][:3]:  # Primi 3 siti
                        site_name = site.get('url', 'N/A').split('/')[2] if site.get('url') else 'N/A'
                        context_parts.append(f"      • {site_name}: {site.get('products_count', 0)} prodotti")
                    
                    # Aggiungi prodotti di esempio
                    for site in scraping['sites'][:2]:  # Primi 2 siti
                        if site.get('sample_products'):
                            site_name = site.get('url', 'N/A').split('/')[2] if site.get('url') else 'N/A'
                            context_parts.append(f"      Prodotti {site_name}:")
                            for product in site['sample_products']:
                                context_parts.append(f"        - {product.get('name', 'N/A')} - {product.get('price', 'N/A')}")
            
            # Contesto Confronto dal frontend
            if request.context_data.get('comparison_results'):
                comparison = request.context_data['comparison_results']
                context_parts.append(f"  ⚖️ CONFRONTO PRODOTTI:")
                context_parts.append(f"    Gruppi confrontabili: {comparison.get('comparable_products', 0)}")
                context_parts.append(f"    Prodotti totali: {comparison.get('total_products', 0)}")
                context_parts.append(f"    Match trovati: {comparison.get('matches_count', 0)}")
                
                # Aggiungi match di esempio
                if comparison.get('sample_matches'):
                    context_parts.append(f"    Match principali:")
                    for match in comparison['sample_matches']:
                        context_parts.append(f"      • {match.get('name', 'N/A')} - Risparmio: €{match.get('savings', 0)}")
            
            # Contesto Google Search dal frontend
            if request.context_data.get('google_search'):
                google = request.context_data['google_search']
                context_parts.append(f"  🔍 GOOGLE SEARCH (Frontend):")
                context_parts.append(f"    Risultati trovati: {google.get('results_count', 0)}")
                
                # Aggiungi risultati di esempio
                if google.get('sample_results'):
                    context_parts.append(f"    Risultati principali:")
                    for result in google['sample_results'][:3]:
                        context_parts.append(f"      • {result.get('name', 'N/A')} - {result.get('price', 'N/A')} - {result.get('source', 'N/A')}")
            
            # Contesto Monitoring dal frontend
            if request.context_data.get('monitoring'):
                monitoring = request.context_data['monitoring']
                context_parts.append(f"  📋 MONITORING:")
                context_parts.append(f"    Prodotti selezionati: {monitoring.get('selected_products_count', 0)}")
                if monitoring.get('monitoring_config'):
                    config = monitoring['monitoring_config']
                    context_parts.append(f"    Frequenza: {config.get('frequency', 'N/A')}")
                    context_parts.append(f"    Soglia prezzo: €{config.get('priceThreshold', 0)}")
            
            # Statistiche Dashboard dal frontend
            if request.context_data.get('dashboard_stats'):
                stats = request.context_data['dashboard_stats']
                context_parts.append(f"  📈 STATISTICHE DASHBOARD:")
                context_parts.append(f"    Prodotti totali: {stats.get('total_products', 0)}")
                context_parts.append(f"    Siti monitorati: {stats.get('sites_monitored', 0)}")
                context_parts.append(f"    Nuovi oggi: {stats.get('new_products_today', 0)}")
        
        if context_parts:
            enhanced_message = f"{request.message}\n\n{'='*50}\nCONTESTO ATTUALE DELL'APPLICAZIONE:\n{'='*50}\n" + "\n".join(context_parts) + f"\n{'='*50}\n"
            
            # Aggiungi istruzioni specifiche per l'analisi dei dati
            if "analizza" in request.message.lower() or "trova" in request.message.lower() or "migliori" in request.message.lower():
                enhanced_message += f"""

ANALISI RICHIESTA:
- Hai richiesto di analizzare i risultati e trovare i migliori prezzi
- Usa i dati forniti nel contesto sopra per fornire una risposta specifica
- Ordina i risultati per convenienza (prezzo più basso)
- Calcola i risparmi potenziali
- Suggerisci il miglior acquisto basato sui dati reali
- Non essere generico, usa i dati specifici forniti

"""
        
        # Converti ChatMessage in dizionari per il chat_manager
        conversation_history = []
        if request.conversation_history:
            for msg in request.conversation_history:
                conversation_history.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        # Chiama la Chat AI con il messaggio potenziato
        response = await chat_manager.send_message(
            message=enhanced_message,
            model=request.model,
            conversation_history=conversation_history
        )
        
        return response
        
    except Exception as e:
        print(f"❌ Errore chat AI: {e}")
        return ChatResponse(
            success=False,
            response="",
            model_used=request.model,
            error=str(e)
        )

@app.get("/chat/models")
async def get_available_models():
    """Restituisce i modelli AI disponibili"""
    try:
        models = chat_manager.get_available_models()
        return {
            "success": True,
            "models": models
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/chat/test")
async def test_ai_connections():
    """Testa le connessioni alle API AI"""
    try:
        test_results = {}
        
        # Test OpenAI
        try:
            result = await chat_manager.send_message("Test di connessione", "openai", [])
            test_results["openai"] = {
                "success": result["success"],
                "error": result.get("error", "Nessun errore")
            }
        except Exception as e:
            test_results["openai"] = {
                "success": False,
                "error": str(e)
            }
        
        # Test Gemini
        try:
            result = await chat_manager.send_message("Test di connessione", "gemini", [])
            test_results["gemini"] = {
                "success": result["success"],
                "error": result.get("error", "Nessun errore")
            }
        except Exception as e:
            test_results["gemini"] = {
                "success": False,
                "error": str(e)
            }
        
        # Test Ollama
        try:
            result = await chat_manager.send_message("Test di connessione", "ollama", [])
            test_results["ollama"] = {
                "success": result["success"],
                "error": result.get("error", "Nessun errore")
            }
        except Exception as e:
            test_results["ollama"] = {
                "success": False,
                "error": str(e)
            }
        
        return {
            "success": True,
            "test_results": test_results
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/chat/keys")
async def check_api_keys():
    """Verifica le API keys configurate"""
    try:
        # Carica le configurazioni
        openai_key = os.getenv("OPENAI_API_KEY")
        gemini_key = os.getenv("GEMINI_API_KEY")
        
        return {
            "success": True,
            "keys": {
                "openai": {
                    "configured": bool(openai_key),
                    "key_preview": openai_key[:10] + "..." if openai_key else "Non configurata",
                    "model": os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
                },
                "gemini": {
                    "configured": bool(gemini_key),
                    "key_preview": gemini_key[:10] + "..." if gemini_key else "Non configurata",
                    "model": os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
                }
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# ==========================================
# SELECTOR DATABASE ENDPOINTS
# ==========================================

@app.get("/selectors/stats")
async def get_selector_stats():
    """Ottiene statistiche del database selettori"""
    try:
        stats = await selector_db.get_stats()
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/selectors/pending")
async def get_pending_selectors():
    """Ottiene selettori in attesa di approvazione"""
    try:
        pending = await selector_db.get_pending_approvals()
        return {
            "success": True,
            "pending_selectors": pending
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/selectors/approve/{domain}")
async def approve_selectors(domain: str):
    """Approva selettori per un dominio"""
    try:
        success = await selector_db.approve_selectors(domain, approved_by="user")
        return {
            "success": success,
            "message": f"Selettori per {domain} {'approvati' if success else 'non trovati'}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.delete("/selectors/{domain}")
async def delete_selectors(domain: str):
    """Elimina selettori per un dominio"""
    try:
        success = await selector_db.delete_selectors(domain)
        return {
            "success": success,
            "message": f"Selettori per {domain} {'eliminati' if success else 'non trovati'}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/test-ai-comparator")
async def test_ai_comparison():
    """Test del sistema AI Product Comparator"""
    try:
        # Dati di test
        test_products = [
            {
                'name': 'iPhone 15 Pro 128GB Titanio Naturale',
                'price': '1.199,00€',
                'brand': 'Apple',
                'source': 'amazon.it'
            },
            {
                'name': 'Apple iPhone 15 Pro 128GB Titanio Naturale',
                'price': '1.189,00€',
                'brand': 'Apple',
                'source': 'mediaworld.it'
            },
            {
                'name': 'Samsung Galaxy S24 Ultra 256GB Titanio Grigio',
                'price': '1.399,00€',
                'brand': 'Samsung',
                'source': 'unieuro.it'
            },
            {
                'name': 'Samsung Galaxy S24 Ultra 256GB Titanio Grigio',
                'price': '1.379,00€',
                'brand': 'Samsung',
                'source': 'amazon.it'
            }
        ]
        
        print("🧪 Test AI Product Comparator...")
        result = await ai_comparator.compare_products_ai(test_products)
        
        return {
            "success": True,
            "test_result": result,
            "message": f"Test completato: {len(result.get('matches', []))} gruppi trovati"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/historical-products")
async def search_historical_products(
    product_name: str = None,
    site: str = None,
    date: str = None,
    brand: str = None,
    sources: str = None,  # 🆕 Supporto per filtraggio domini
    limit: int = 1000
):
    """Ricerca prodotti storici dal database"""
    try:
        print(f"🔍 Ricerca prodotti storici - Filtri: {product_name}, {site}, {date}, sources={sources}")
        
        filters = {}
        if product_name:
            filters['product_name'] = product_name
        if site:
            filters['site'] = site
        if date:
            filters['date'] = date
        if brand:
            filters['brand'] = brand
        if sources:  # 🆕 Gestione filtraggio domini
            # Converte stringa comma-separated in lista
            sources_list = [s.strip() for s in sources.split(',') if s.strip()]
            filters['sources'] = sources_list
            print(f"🎯 Filtro domini applicato: {sources_list}")
        if limit:
            filters['limit'] = limit
        
        result = await historical_db.search_historical_products(filters)
        
        if result['success']:
            print(f"✅ Ricerca completata: {len(result.get('products', []))} prodotti trovati")
            return result
        else:
            print(f"❌ Ricerca fallita: {result.get('error')}")
            return {
                "success": False,
                "error": result.get('error', 'Errore ricerca sconosciuto'),
                "products": [],
                "statistics": {}
            }
            
    except Exception as e:
        print(f"❌ Errore ricerca prodotti storici: {e}")
        return {
            "success": False,
            "error": f"Errore interno: {str(e)}",
            "products": [],
            "statistics": {}
        }



@app.get("/dashboard-stats")
async def get_dashboard_statistics():
    """Ottiene statistiche dashboard dal database"""
    try:
        print("📊 Caricamento statistiche dashboard...")
        
        result = await historical_db.get_dashboard_stats()
        
        if result['success']:
            print(f"✅ Statistiche caricate: {result['stats'].get('total_products', 0)} prodotti totali")
            return result
        else:
            print(f"❌ Errore caricamento statistiche: {result.get('error')}")
            return {
                "success": False,
                "error": result.get('error', 'Errore caricamento statistiche'),
                "stats": {}
            }
            
    except Exception as e:
        print(f"❌ Errore statistiche dashboard: {e}")
        return {
            "success": False,
            "error": f"Errore interno: {str(e)}",
            "stats": {}
        }

# ==========================================
# PRICE MONITORING ENDPOINTS
# ==========================================

@app.post("/monitoring/add-product")
async def add_product_to_monitoring(request: dict):
    """Aggiunge prodotto al monitoring prezzi"""
    try:
        print(f"💰 Aggiunta prodotto al monitoring: {request.get('name', 'Unknown')}")
        
        # Valida dati input
        required_fields = ['name', 'url', 'price', 'source']
        for field in required_fields:
            if field not in request:
                return {
                    "success": False,
                    "error": f"Campo mancante: {field}"
                }
        
        # Aggiungi al monitoring
        result = await price_monitor.add_product_to_monitoring(
            product_data=request,
            alert_threshold=request.get('alert_threshold', 5.0),
            check_frequency=request.get('check_frequency', 24)
        )
        
        if result['success']:
            # Aggiungi anche al scheduler
            await price_scheduler.add_product_to_scheduler(request)
            
            print(f"✅ Prodotto aggiunto al monitoring: {result['product_id']}")
            return result
        else:
            print(f"❌ Errore aggiunta al monitoring: {result.get('error')}")
            return result
            
    except Exception as e:
        print(f"❌ Errore aggiunta prodotto al monitoring: {e}")
        return {
            "success": False,
            "error": f"Errore interno: {str(e)}"
        }

@app.get("/monitoring/products")
async def get_monitored_products():
    """Ottiene lista prodotti monitorati"""
    try:
        print("📋 Caricamento prodotti monitorati...")
        
        result = await price_monitor.get_monitored_products(active_only=True)
        
        if result['success']:
            print(f"✅ Caricati {len(result['products'])} prodotti monitorati")
            return result
        else:
            print(f"❌ Errore caricamento: {result.get('error')}")
            return result
            
    except Exception as e:
        print(f"❌ Errore prodotti monitorati: {e}")
        return {
            "success": False,
            "error": f"Errore interno: {str(e)}"
        }

@app.get("/monitoring/price-history/{product_id}")
async def get_product_price_history(product_id: int, days: int = 30):
    """Ottiene storico prezzi per un prodotto"""
    try:
        print(f"📈 Caricamento storico prezzi per prodotto {product_id}...")
        
        result = await price_monitor.get_price_history(product_id, days)
        
        if result['success']:
            print(f"✅ Caricati {len(result['history'])} record storici")
            return result
        else:
            print(f"❌ Errore caricamento storico: {result.get('error')}")
            return result
            
    except Exception as e:
        print(f"❌ Errore storico prezzi: {e}")
        return {
            "success": False,
            "error": f"Errore interno: {str(e)}"
        }

@app.get("/monitoring/alerts")
async def get_price_alerts(unread_only: bool = False, limit: int = 50):
    """Ottiene alert generati"""
    try:
        print(f"🔔 Caricamento alert (unread_only={unread_only})...")
        
        result = await price_monitor.get_price_alerts(unread_only, limit)
        
        if result['success']:
            print(f"✅ Caricati {len(result['alerts'])} alert")
            return result
        else:
            print(f"❌ Errore caricamento alert: {result.get('error')}")
            return result
            
    except Exception as e:
        print(f"❌ Errore alert: {e}")
        return {
            "success": False,
            "error": f"Errore interno: {str(e)}"
        }

@app.post("/monitoring/alerts/{alert_id}/read")
async def mark_alert_as_read(alert_id: int):
    """Segna un alert come letto"""
    try:
        print(f"✅ Marcatura alert {alert_id} come letto...")
        
        result = await price_monitor.mark_alert_as_read(alert_id)
        
        if result['success']:
            print(f"✅ Alert {alert_id} marcato come letto")
            return result
        else:
            print(f"❌ Errore marcatura: {result.get('error')}")
            return result
            
    except Exception as e:
        print(f"❌ Errore marcatura alert: {e}")
        return {
            "success": False,
            "error": f"Errore interno: {str(e)}"
        }

@app.delete("/monitoring/products/{product_id}")
async def remove_product_from_monitoring(product_id: int):
    """Rimuove prodotto dal monitoring"""
    try:
        print(f"🗑️ Rimozione prodotto {product_id} dal monitoring...")
        
        result = await price_monitor.remove_from_monitoring(product_id)
        
        if result['success']:
            # Rimuovi anche dal scheduler
            await price_scheduler.remove_product_from_scheduler(product_id)
            
            print(f"✅ Prodotto {product_id} rimosso dal monitoring")
            return result
        else:
            print(f"❌ Errore rimozione: {result.get('error')}")
            return result
            
    except Exception as e:
        print(f"❌ Errore rimozione prodotto: {e}")
        return {
            "success": False,
            "error": f"Errore interno: {str(e)}"
        }

@app.post("/monitoring/check-prices")
async def check_all_prices():
    """Forza controllo prezzi per tutti i prodotti"""
    try:
        print("🔍 Controllo forzato prezzi per tutti i prodotti...")
        
        result = await price_monitor.check_price_changes()
        
        if result['success']:
            print(f"✅ Controllo completato: {result['products_checked']} prodotti, {result['alerts_generated']} alert")
            return result
        else:
            print(f"❌ Errore controllo: {result.get('error')}")
            return result
            
    except Exception as e:
        print(f"❌ Errore controllo prezzi: {e}")
        return {
            "success": False,
            "error": f"Errore interno: {str(e)}"
        }

@app.get("/monitoring/stats")
async def get_monitoring_statistics():
    """Ottiene statistiche del monitoring"""
    try:
        print("📊 Caricamento statistiche monitoring...")
        
        result = await price_monitor.get_monitoring_stats()
        
        if result['success']:
            print(f"✅ Statistiche monitoring caricate")
            return result
        else:
            print(f"❌ Errore statistiche: {result.get('error')}")
            return result
            
    except Exception as e:
        print(f"❌ Errore statistiche monitoring: {e}")
        return {
            "success": False,
            "error": f"Errore interno: {str(e)}"
        }

# ==========================================
# SCHEDULER ENDPOINTS
# ==========================================

@app.post("/scheduler/start")
async def start_price_scheduler():
    """Avvia il sistema di schedulazione"""
    try:
        print("⏰ Avvio sistema di schedulazione...")
        
        result = await price_scheduler.start_scheduler()
        
        if result['success']:
            print(f"✅ Scheduler avviato con {result['active_tasks']} task")
            return result
        else:
            print(f"❌ Errore avvio scheduler: {result.get('error')}")
            return result
            
    except Exception as e:
        print(f"❌ Errore avvio scheduler: {e}")
        return {
            "success": False,
            "error": f"Errore interno: {str(e)}"
        }

@app.post("/scheduler/stop")
async def stop_price_scheduler():
    """Ferma il sistema di schedulazione"""
    try:
        print("🛑 Fermata sistema di schedulazione...")
        
        result = await price_scheduler.stop_scheduler()
        
        if result['success']:
            print(f"✅ Scheduler fermato (uptime: {result['uptime_seconds']:.1f}s)")
            return result
        else:
            print(f"❌ Errore fermata scheduler: {result.get('error')}")
            return result
            
    except Exception as e:
        print(f"❌ Errore fermata scheduler: {e}")
        return {
            "success": False,
            "error": f"Errore interno: {str(e)}"
        }

@app.get("/scheduler/stats")
async def get_scheduler_statistics():
    """Ottiene statistiche del scheduler"""
    try:
        print("📈 Caricamento statistiche scheduler...")
        
        result = await price_scheduler.get_scheduler_stats()
        
        if result['success']:
            print(f"✅ Statistiche scheduler caricate")
            return result
        else:
            print(f"❌ Errore statistiche scheduler: {result.get('error')}")
            return result
            
    except Exception as e:
        print(f"❌ Errore statistiche scheduler: {e}")
        return {
            "success": False,
            "error": f"Errore interno: {str(e)}"
        }

@app.post("/scheduler/force-check/{product_id}")
async def force_check_product(product_id: int):
    """Forza controllo immediato di un prodotto"""
    try:
        print(f"🔍 Controllo forzato prodotto {product_id}...")
        
        result = await price_scheduler.force_check_product(product_id)
        
        if result['success']:
            print(f"✅ Controllo forzato completato")
            return result
        else:
            print(f"❌ Errore controllo forzato: {result.get('error')}")
            return result
            
    except Exception as e:
        print(f"❌ Errore controllo forzato: {e}")
        return {
            "success": False,
            "error": f"Errore interno: {str(e)}"
        }

@app.get("/site-statistics")
async def get_site_statistics(site: str = None):
    """Ottiene statistiche per sito specifico o tutti i siti"""
    try:
        print(f"📈 Caricamento statistiche sito: {site or 'tutti'}")
        
        result = await historical_db.get_site_statistics(site)
        
        if result['success']:
            print(f"✅ Statistiche sito caricate")
            return result
        else:
            print(f"❌ Errore statistiche sito: {result.get('error')}")
            return {
                "success": False,
                "error": result.get('error', 'Errore caricamento statistiche sito')
            }
            
    except Exception as e:
        print(f"❌ Errore statistiche sito: {e}")
        return {
            "success": False,
            "error": f"Errore interno: {str(e)}"
        }

@app.post("/google-search")
async def search_alternative_vendors(request: dict):
    """Ricerca venditori alternativi usando Google Search"""
    try:
        print(f"🔍 Google Search - Ricerca venditori alternativi")
        print(f"📥 Request ricevuta: {request}")
        
        # Valida dati input - i dati vengono inviati direttamente
        if not request.get('name'):
            return {
                "success": False,
                "error": "Dati prodotto mancanti"
            }
        
        product_data = request
        print(f"📦 Dati prodotto: {product_data}")
        
        # Ricerca venditori alternativi
        result = await google_search.search_alternative_vendors(product_data)
        
        if result['success']:
            print(f"✅ Ricerca completata: {len(result.get('alternative_vendors', []))} venditori trovati")
            
            return {
                "success": True,
                "original_product": result['original_product'],
                "alternative_vendors": result['alternative_vendors'],
                "comparison_results": result['comparison_results'],
                "search_queries": result['search_queries'],
                "total_results_found": result['total_results_found'],
                "validated_results": result['validated_results'],
                "extracted_products": result['extracted_products'],
                "timestamp": result['timestamp']
            }
        else:
            print(f"❌ Ricerca fallita: {result.get('error')}")
            return {
                "success": False,
                "error": result.get('error', 'Errore ricerca sconosciuto')
            }
            
    except Exception as e:
        print(f"❌ Errore ricerca Google: {e}")
        return {
            "success": False,
            "error": f"Errore interno: {str(e)}"
        }

# Endpoint per ottenere risultati di Google Search per Chat AI
@app.get("/google-search-results")
async def get_google_search_results():
    """Restituisce gli ultimi risultati di Google Search per la Chat AI"""
    try:
        # Importa il modulo di Google Search
        from google_search_integration import google_search
        
        # Restituisce gli ultimi risultati se disponibili
        if hasattr(google_search, 'last_results'):
            return {
                "success": True,
                "results": google_search.last_results,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "results": [],
                "message": "Nessun risultato di ricerca disponibile"
            }
    except Exception as e:
        return {
            "success": False,
            "results": [],
            "error": str(e)
        }

@app.get("/extraction-sessions/recent")
async def get_recent_extraction_sessions():
    """Ottiene le sessioni di estrazione recenti per la dashboard"""
    try:
        print("📋 Caricamento sessioni estrazione recenti...")
        
        result = await historical_db.get_recent_extraction_sessions(limit=10)
        
        if result['success']:
            print(f"✅ Caricate {len(result['sessions'])} sessioni recenti")
            return result
        else:
            print(f"❌ Errore caricamento sessioni: {result.get('error')}")
            return result
            
    except Exception as e:
        print(f"❌ Errore sessioni recenti: {e}")
        return {
            "success": False,
            "error": f"Errore interno: {str(e)}",
            "sessions": []
        }

@app.get("/products/categories/stats")
async def get_product_categories_stats():
    """Ottiene statistiche per categoria per la dashboard"""
    try:
        print("📊 Caricamento statistiche categorie...")
        
        result = await historical_db.get_product_categories_stats()
        
        if result['success']:
            print(f"✅ Caricate statistiche per {len(result['categories'])} categorie")
            return result
        else:
            print(f"❌ Errore caricamento categorie: {result.get('error')}")
            return result
            
    except Exception as e:
        print(f"❌ Errore statistiche categorie: {e}")
        return {
            "success": False,
            "error": f"Errore interno: {str(e)}",
            "categories": []
        }

@app.get("/sites/performance/stats")
async def get_sites_performance_stats():
    """Ottiene statistiche delle performance per sito per la dashboard"""
    try:
        print("📊 Caricamento statistiche performance per sito...")
        
        result = await historical_db.get_sites_performance_stats()
        
        if result['success']:
            print(f"✅ Caricate statistiche performance per {len(result['sites'])} siti")
            return result
        else:
            print(f"❌ Errore caricamento performance sito: {result.get('error')}")
            return result
            
    except Exception as e:
        print(f"❌ Errore statistiche performance sito: {e}")
        return {
            "success": False,
            "error": f"Errore interno: {str(e)}",
            "sites": []
        }

# Endpoint per la configurazione del browser
@app.post("/api/browser-config")
async def update_browser_config(config: BrowserConfigRequest):
    """Aggiorna la configurazione del browser per lo scraping"""
    try:
        print(f"⚙️ Aggiornamento configurazione browser: {config.mode}")
        print(f"📋 Configurazione completa ricevuta: {config}")
        
        # Salva la configurazione globalmente
        global browser_config
        browser_config = {
            "mode": config.mode,
            "timeout": config.timeout,
            "human_delay": config.human_delay,
            "user_agent": config.user_agent,
            "proxy": config.proxy
        }
        
        print(f"✅ Configurazione browser aggiornata globalmente: {browser_config}")
        
        return {
            "success": True,
            "message": "Configurazione browser aggiornata",
            "config": browser_config,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Errore aggiornamento configurazione browser: {e}")
        return {
            "success": False,
            "error": f"Errore interno: {str(e)}"
        }

# Endpoint per ottenere la configurazione corrente del browser
@app.get("/api/browser-config")
async def get_browser_config():
    """Restituisce la configurazione corrente del browser"""
    try:
        global browser_config
        return {
            "success": True,
            "config": browser_config if 'browser_config' in globals() else {
                "mode": "stealth",
                "timeout": 60,
                "human_delay": 2.0,
                "user_agent": "auto",
                "proxy": None
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# ==========================================
# UTILITY FUNCTIONS
# ==========================================

async def save_extraction_result(url: str, result: dict):
    """Salva i risultati dell'estrazione per debugging"""
    try:
        # Crea directory se non esiste
        os.makedirs("../data/api_extracts", exist_ok=True)
        
        # Nome file basato su URL e timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = url.replace('https://', '').replace('http://', '').replace('/', '_').replace('?', '_').replace('=', '_').replace('&', '_')
        filepath = f"../data/api_extracts/{filename}_{timestamp}.json"
        
        # Salva risultato
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                "url": url,
                "timestamp": datetime.now().isoformat(),
                "result": result
            }, f, indent=2, ensure_ascii=False)
            
        print(f"💾 Risultato salvato: {filepath}")
        
    except Exception as e:
        print(f"⚠️ Errore salvataggio: {e}")

# ==========================================
# STARTUP
# ==========================================

@app.on_event("startup")
async def startup_event():
    """Inizializzazione all'avvio"""
    global extractor, ai_comparator, chat_manager, selector_db, google_search, historical_db, price_monitor, price_scheduler
    
    print("🚀 MR Scraper API v2.0.0 - Avvio completato")
    
    # Inizializza le istanze globali
    print("🔧 Inizializzazione componenti...")
    extractor = FastAIExtractor()
    ai_comparator = AIProductComparator()
    chat_manager = ChatAIManager()
    selector_db = SelectorDatabase()
    google_search = GoogleSearchIntegration()
    historical_db = HistoricalProductsDB()
    price_monitor = PriceMonitor()
    price_scheduler = PriceScheduler(price_monitor)
    print("✅ Componenti inizializzati")
    
    # Avvia automaticamente il sistema di schedulazione
    try:
        print("⏰ Avvio automatico sistema di schedulazione...")
        scheduler_result = await price_scheduler.start_scheduler()
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