"""
Router per la Chat AI: /chat, /chat/models, /chat/test, /chat/keys.
"""

import os

from fastapi import APIRouter

import app_state
from models import ChatRequest, ChatResponse

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
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
        response = await app_state.chat_manager.send_message(
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

@router.get("/chat/models")
async def get_available_models():
    """Restituisce i modelli AI disponibili"""
    try:
        models = app_state.chat_manager.get_available_models()
        return {
            "success": True,
            "models": models
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@router.get("/chat/test")
async def test_ai_connections():
    """Testa le connessioni alle API AI"""
    try:
        test_results = {}

        # Test OpenAI
        try:
            result = await app_state.chat_manager.send_message("Test di connessione", "openai", [])
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
            result = await app_state.chat_manager.send_message("Test di connessione", "gemini", [])
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
            result = await app_state.chat_manager.send_message("Test di connessione", "ollama", [])
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

@router.get("/chat/keys")
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
                    "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini")
                },
                "gemini": {
                    "configured": bool(gemini_key),
                    "key_preview": gemini_key[:10] + "..." if gemini_key else "Non configurata",
                    "model": os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
                }
            }
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
