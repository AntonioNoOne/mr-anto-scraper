"""
Router per l'estrazione prodotti: /fast-extract, /fast-extract-multiple, /stop-scraping.
"""

import json
import os
from datetime import datetime

from fastapi import APIRouter, HTTPException

import app_state
from models import (
    ExtractRequest,
    MultipleExtractRequest,
    ExtractResponse,
    MultipleExtractResponse,
)

router = APIRouter()

# Flag globale per fermare lo scraping
scraping_stop_flag = {"stop": False}


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


@router.post("/fast-extract", response_model=ExtractResponse)
async def fast_extract(request: ExtractRequest):
    """
    Endpoint per estrazione singola URL
    """
    try:
        # Reset del flag di stop
        scraping_stop_flag["stop"] = False

        print(f"🚀 Fast Extract - URL: {request.url}")

        # Usa la configurazione browser globale aggiornata
        # Se non c'è configurazione globale, usa default stealth
        if not app_state.browser_config:
            app_state.browser_config = {
                'mode': 'stealth',  # Default stealth come richiesto
                'timeout': 60,
                'human_delay': 2.0,
                'user_agent': 'auto',
                'proxy': ''
            }
        browser_config = app_state.browser_config

        print(f"⚙️ Configurazione browser globale: {browser_config}")
        print(f"🌐 Modalità selezionata: {browser_config.get('mode', 'N/A')}")
        print(f"⏱️ Timeout: {browser_config.get('timeout', 'N/A')}s")
        print(f"🕐 Delay umano: {browser_config.get('human_delay', 'N/A')}s")

        # Passa la configurazione del browser all'estrattore con flag di stop
        result = await app_state.extractor.extract_products_fast(
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
                db_result = await app_state.historical_db.save_extracted_products(
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
                url=request.url,
                extraction_method=result.get('extraction_method')
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

@router.post("/fast-extract-multiple", response_model=MultipleExtractResponse)
async def fast_extract_multiple(request: MultipleExtractRequest):
    """
    Endpoint per estrazione multipla URL
    Processa ogni URL sequenzialmente per evitare sovraccarico
    """
    try:
        # Reset del flag di stop
        scraping_stop_flag["stop"] = False

        print(f"🚀 Fast Extract Multiple - {len(request.urls)} URLs")

        browser_config = app_state.browser_config
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
                result = await app_state.extractor.extract_products_fast(
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
                        db_result = await app_state.historical_db.save_extracted_products(
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

@router.post("/stop-scraping")
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
