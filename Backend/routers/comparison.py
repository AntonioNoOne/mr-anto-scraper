"""
Router per il confronto prodotti/prezzi: /compare-products, /compare-prices, /test-ai-comparator.
"""

from fastapi import APIRouter

import app_state
from models import CompareRequest, ComparePricesRequest, CompareResponse

router = APIRouter()


@router.post("/compare-products", response_model=CompareResponse)
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
                db_result = await app_state.historical_db.search_historical_products(filters)

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
                db_result = await app_state.historical_db.search_historical_products(filters)

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
        result = await app_state.ai_comparator.compare_products_ai(all_products, selected_domains)

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

@router.post("/compare-prices", response_model=CompareResponse)
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
        matches = app_state.ai_comparator.find_matches(request.products)

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

@router.post("/test-ai-comparator")
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
        result = await app_state.ai_comparator.compare_products_ai(test_products)

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
