"""
Router per lo scheduler prezzi: /scheduler/*.
"""

from fastapi import APIRouter

import app_state

router = APIRouter()


@router.post("/scheduler/start")
async def start_price_scheduler():
    """Avvia il sistema di schedulazione"""
    try:
        print("⏰ Avvio sistema di schedulazione...")

        result = await app_state.price_scheduler.start_scheduler()

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

@router.post("/scheduler/stop")
async def stop_price_scheduler():
    """Ferma il sistema di schedulazione"""
    try:
        print("🛑 Fermata sistema di schedulazione...")

        result = await app_state.price_scheduler.stop_scheduler()

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

@router.get("/scheduler/stats")
async def get_scheduler_statistics():
    """Ottiene statistiche del scheduler"""
    try:
        print("📈 Caricamento statistiche scheduler...")

        result = await app_state.price_scheduler.get_scheduler_stats()

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

@router.post("/scheduler/force-check/{product_id}")
async def force_check_product(product_id: int):
    """Forza controllo immediato di un prodotto"""
    try:
        print(f"🔍 Controllo forzato prodotto {product_id}...")

        result = await app_state.price_scheduler.force_check_product(product_id)

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
