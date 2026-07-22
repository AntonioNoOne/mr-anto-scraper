"""
Router per storico, statistiche, Google Search e configurazione browser:
/historical-products, /historical-products/export, /dashboard-stats,
/site-statistics, /google-search, /google-search-results,
/extraction-sessions/recent, /products/categories/stats,
/sites/performance/stats, /api/browser-config (GET/POST).
"""

import asyncio
import json
from datetime import datetime

from fastapi import APIRouter, HTTPException

import app_state
from models import BrowserConfigRequest

router = APIRouter()


@router.get("/historical-products")
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

        result = await app_state.historical_db.search_historical_products(filters)

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



@router.get("/historical-products/export")
async def export_historical_products(
    format: str = "csv",
    product_name: str = None,
    site: str = None,
    date: str = None,
    brand: str = None,
    sources: str = None,
    limit: int = 10000,
):
    """Esporta i prodotti storici (stessi filtri di /historical-products) come CSV o JSON scaricabile."""
    import csv
    import io
    from fastapi.responses import Response

    fmt = (format or "csv").lower().strip()
    if fmt not in ("csv", "json"):
        raise HTTPException(status_code=400, detail="format deve essere 'csv' o 'json'")

    filters = {"limit": limit}
    if product_name:
        filters["product_name"] = product_name
    if site:
        filters["site"] = site
    if date:
        filters["date"] = date
    if brand:
        filters["brand"] = brand
    if sources:
        filters["sources"] = [s.strip() for s in sources.split(",") if s.strip()]

    result = await app_state.historical_db.search_historical_products(filters)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Errore ricerca"))

    products = result.get("products", [])
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    if fmt == "json":
        return Response(
            content=json.dumps(products, ensure_ascii=False, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="prodotti_{ts}.json"'},
        )

    # CSV: colonne = unione ordinata delle chiavi presenti
    columns = []
    for p in products:
        for k in p.keys():
            if k not in columns:
                columns.append(k)

    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    for p in products:
        writer.writerow({k: p.get(k, "") for k in columns})

    # BOM UTF-8: Excel apre correttamente gli accenti
    return Response(
        content="﻿" + buffer.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="prodotti_{ts}.csv"'},
    )


@router.get("/dashboard-stats")
async def get_dashboard_statistics():
    """Ottiene statistiche dashboard dal database"""
    try:
        print("📊 Caricamento statistiche dashboard...")

        result = await app_state.historical_db.get_dashboard_stats()

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

@router.get("/site-statistics")
async def get_site_statistics(site: str = None):
    """Ottiene statistiche per sito specifico o tutti i siti"""
    try:
        print(f"📈 Caricamento statistiche sito: {site or 'tutti'}")

        result = await app_state.historical_db.get_site_statistics(site)

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

@router.post("/google-search")
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

        # Ricerca venditori alternativi con timeout: lo scraping browser di
        # Google/Bing/DDG può bloccarsi a lungo (anti-bot). Meglio rispondere con
        # un errore chiaro entro 60s che lasciare la UI appesa all'infinito.
        try:
            result = await asyncio.wait_for(
                app_state.google_search.search_alternative_vendors(product_data),
                timeout=150,
            )
        except asyncio.TimeoutError:
            print("⏰ Google Search: timeout 150s superato")
            return {
                "success": False,
                "error": "Ricerca troppo lenta (timeout 150s). Riprova con un nome "
                         "prodotto più specifico o usa lo scraping diretto da URL.",
            }

        if result['success']:
            print(f"✅ Ricerca completata: {len(result.get('alternative_vendors', []))} venditori trovati")

            # Salva nel DB storico i venditori CON prezzo (come fa fast-extract),
            # cosi' i risultati della ricerca sono confrontabili/monitorabili.
            try:
                vendors = result.get('alternative_vendors') or result.get('extracted_products') or []
                to_save = [v for v in vendors if v.get('price')]
                if to_save:
                    save_res = await app_state.historical_db.save_extracted_products(
                        url=f"google-search:{product_data.get('name','')}",
                        products=to_save,
                        session_id=None,
                        extraction_method="google_search",
                    )
                    print(f"💾 Google Search: salvati {save_res.get('saved_count', 0)} venditori nel DB")
            except Exception as e:
                print(f"⚠️ Errore salvataggio ricerca nel DB: {e}")

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
@router.get("/google-search-results")
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

@router.get("/extraction-sessions/recent")
async def get_recent_extraction_sessions():
    """Ottiene le sessioni di estrazione recenti per la dashboard"""
    try:
        print("📋 Caricamento sessioni estrazione recenti...")

        result = await app_state.historical_db.get_recent_extraction_sessions(limit=10)

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

@router.get("/products/categories/stats")
async def get_product_categories_stats():
    """Ottiene statistiche per categoria per la dashboard"""
    try:
        print("📊 Caricamento statistiche categorie...")

        result = await app_state.historical_db.get_product_categories_stats()

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

@router.get("/sites/performance/stats")
async def get_sites_performance_stats():
    """Ottiene statistiche delle performance per sito per la dashboard"""
    try:
        print("📊 Caricamento statistiche performance per sito...")

        result = await app_state.historical_db.get_sites_performance_stats()

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
@router.post("/api/browser-config")
async def update_browser_config(config: BrowserConfigRequest):
    """Aggiorna la configurazione del browser per lo scraping"""
    try:
        print(f"⚙️ Aggiornamento configurazione browser: {config.mode}")
        print(f"📋 Configurazione completa ricevuta: {config}")

        # Salva la configurazione globalmente
        app_state.browser_config = {
            "mode": config.mode,
            "timeout": config.timeout,
            "human_delay": config.human_delay,
            "user_agent": config.user_agent,
            "proxy": config.proxy
        }

        print(f"✅ Configurazione browser aggiornata globalmente: {app_state.browser_config}")

        return {
            "success": True,
            "message": "Configurazione browser aggiornata",
            "config": app_state.browser_config,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        print(f"❌ Errore aggiornamento configurazione browser: {e}")
        return {
            "success": False,
            "error": f"Errore interno: {str(e)}"
        }

# Endpoint per ottenere la configurazione corrente del browser
@router.get("/api/browser-config")
async def get_browser_config():
    """Restituisce la configurazione corrente del browser"""
    try:
        return {
            "success": True,
            "config": app_state.browser_config if app_state.browser_config else {
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
