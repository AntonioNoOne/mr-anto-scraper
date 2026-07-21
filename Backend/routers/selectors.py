"""
Router per il database selettori: /selectors/*.
"""

from fastapi import APIRouter

import app_state

router = APIRouter()


@router.get("/selectors/stats")
async def get_selector_stats():
    """Ottiene statistiche del database selettori"""
    try:
        stats = await app_state.selector_db.get_stats()
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@router.get("/selectors/pending")
async def get_pending_selectors():
    """Ottiene selettori in attesa di approvazione"""
    try:
        pending = await app_state.selector_db.get_pending_approvals()
        return {
            "success": True,
            "pending_selectors": pending
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@router.post("/selectors/approve/{domain}")
async def approve_selectors(domain: str):
    """Approva selettori per un dominio"""
    try:
        success = await app_state.selector_db.approve_selectors(domain, approved_by="user")
        return {
            "success": success,
            "message": f"Selettori per {domain} {'approvati' if success else 'non trovati'}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@router.delete("/selectors/{domain}")
async def delete_selectors(domain: str):
    """Elimina selettori per un dominio"""
    try:
        success = await app_state.selector_db.delete_selectors(domain)
        return {
            "success": success,
            "message": f"Selettori per {domain} {'eliminati' if success else 'non trovati'}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
