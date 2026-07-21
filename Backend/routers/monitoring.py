"""
Router per il monitoring prezzi: /monitoring/*.
"""

from fastapi import APIRouter

import app_state

router = APIRouter()


@router.post("/monitoring/add-product")
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

        # add_product_to_scheduler aggiunge al monitoring E crea il task schedulato
        # in un'unica operazione (evita il doppio inserimento che prima faceva
        # fallire la registrazione del task -> total_tasks restava 0).
        result = await app_state.price_scheduler.add_product_to_scheduler(request)

        if result.get('success'):
            print(f"✅ Prodotto aggiunto a monitoring + scheduler: {result.get('product_id')}")
        else:
            print(f"❌ Errore aggiunta: {result.get('error')}")
        return result

    except Exception as e:
        print(f"❌ Errore aggiunta prodotto al monitoring: {e}")
        return {
            "success": False,
            "error": f"Errore interno: {str(e)}"
        }

@router.get("/monitoring/products")
async def get_monitored_products():
    """Ottiene lista prodotti monitorati"""
    try:
        print("📋 Caricamento prodotti monitorati...")

        result = await app_state.price_monitor.get_monitored_products(active_only=True)

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

@router.get("/monitoring/price-history/{product_id}")
async def get_product_price_history(product_id: int, days: int = 30):
    """Ottiene storico prezzi per un prodotto"""
    try:
        print(f"📈 Caricamento storico prezzi per prodotto {product_id}...")

        result = await app_state.price_monitor.get_price_history(product_id, days)

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

@router.get("/monitoring/alerts")
async def get_price_alerts(unread_only: bool = False, limit: int = 50):
    """Ottiene alert generati"""
    try:
        print(f"🔔 Caricamento alert (unread_only={unread_only})...")

        result = await app_state.price_monitor.get_price_alerts(unread_only, limit)

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

@router.post("/monitoring/alerts/{alert_id}/read")
async def mark_alert_as_read(alert_id: int):
    """Segna un alert come letto"""
    try:
        print(f"✅ Marcatura alert {alert_id} come letto...")

        result = await app_state.price_monitor.mark_alert_as_read(alert_id)

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

@router.delete("/monitoring/products/{product_id}")
async def remove_product_from_monitoring(product_id: int):
    """Rimuove prodotto dal monitoring"""
    try:
        print(f"🗑️ Rimozione prodotto {product_id} dal monitoring...")

        result = await app_state.price_monitor.remove_from_monitoring(product_id)

        if result['success']:
            # Rimuovi anche dal scheduler
            await app_state.price_scheduler.remove_product_from_scheduler(product_id)

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

@router.post("/monitoring/check-prices")
async def check_all_prices():
    """Forza controllo prezzi per tutti i prodotti"""
    try:
        print("🔍 Controllo forzato prezzi per tutti i prodotti...")

        result = await app_state.price_monitor.check_price_changes()

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

@router.get("/monitoring/stats")
async def get_monitoring_statistics():
    """Ottiene statistiche del monitoring"""
    try:
        print("📊 Caricamento statistiche monitoring...")

        result = await app_state.price_monitor.get_monitoring_stats()

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
