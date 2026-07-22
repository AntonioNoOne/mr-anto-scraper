"""Router: URL periodici (scansioni schedulate di pagine salvate)."""

from fastapi import APIRouter
import app_state

router = APIRouter()


@router.get("/monitored-urls")
async def list_monitored_urls():
    return await app_state.url_monitor.list_urls()


@router.post("/monitored-urls")
async def add_monitored_url(request: dict):
    url = (request.get("url") or "").strip()
    if not url.startswith("http"):
        return {"success": False, "error": "URL non valido (deve iniziare con http)"}
    return await app_state.url_monitor.add_url(
        url=url,
        label=request.get("label", ""),
        frequency_hours=request.get("frequency_hours", 24),
    )


@router.delete("/monitored-urls/{url_id}")
async def remove_monitored_url(url_id: int):
    return await app_state.url_monitor.remove_url(url_id)


@router.post("/monitored-urls/{url_id}/scan-now")
async def scan_monitored_url_now(url_id: int):
    return await app_state.url_monitor.scan_url_now(
        url_id, app_state.extractor, app_state.historical_db
    )
