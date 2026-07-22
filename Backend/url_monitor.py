"""
URL Monitor - scansioni periodiche di URL salvati (es. pagine categoria).

A differenza del monitoraggio per-prodotto (variazione prezzo di un item), qui
si salvano URL da RI-SCANSIONARE a intervalli: ogni scansione ri-estrae tutti i
prodotti della pagina e li salva nel DB storico. Un loop in background controlla
gli URL "scaduti" e li rilancia.
"""

import asyncio
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class UrlMonitor:
    def __init__(self, db_path: str = "data/database/url_monitor.db"):
        self.db_path = db_path
        self._ensure_dir()
        self._init_db()
        self._loop_task = None

    def _ensure_dir(self):
        import os
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS monitored_urls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL UNIQUE,
                    label TEXT,
                    frequency_hours INTEGER DEFAULT 24,
                    last_scan TEXT,
                    last_count INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT (datetime('now'))
                )
            """)
            conn.commit()

    async def add_url(self, url: str, label: str = "", frequency_hours: int = 24) -> Dict[str, Any]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                cur.execute(
                    "INSERT OR IGNORE INTO monitored_urls (url, label, frequency_hours) VALUES (?,?,?)",
                    (url, label or url, int(frequency_hours)),
                )
                conn.commit()
                if cur.rowcount == 0:
                    return {"success": False, "error": "URL già presente"}
                return {"success": True, "id": cur.lastrowid}
        except Exception as e:
            logger.error(f"❌ add_url: {e}")
            return {"success": False, "error": str(e)}

    async def list_urls(self) -> Dict[str, Any]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    "SELECT * FROM monitored_urls ORDER BY created_at DESC"
                ).fetchall()
                return {"success": True, "urls": [dict(r) for r in rows]}
        except Exception as e:
            return {"success": False, "error": str(e), "urls": []}

    async def remove_url(self, url_id: int) -> Dict[str, Any]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM monitored_urls WHERE id = ?", (url_id,))
                conn.commit()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _get_due(self) -> List[Dict[str, Any]]:
        """URL attivi mai scansionati o scaduti (ora - last_scan >= frequency)."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM monitored_urls WHERE is_active = 1").fetchall()
        due = []
        now = datetime.now()
        for r in rows:
            r = dict(r)
            if not r.get("last_scan"):
                due.append(r)
                continue
            try:
                last = datetime.fromisoformat(r["last_scan"])
                if now - last >= timedelta(hours=r.get("frequency_hours", 24)):
                    due.append(r)
            except Exception:
                due.append(r)
        return due

    def _mark_scanned(self, url_id: int, count: int):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE monitored_urls SET last_scan = ?, last_count = ? WHERE id = ?",
                (datetime.now().isoformat(), count, url_id),
            )
            conn.commit()

    async def scan_url_now(self, url_id: int, extractor, historical_db) -> Dict[str, Any]:
        """Ri-scansiona un URL specifico ora e salva i prodotti."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM monitored_urls WHERE id = ?", (url_id,)).fetchone()
        if not row:
            return {"success": False, "error": "URL non trovato"}
        return await self._scan_one(dict(row), extractor, historical_db)

    async def _scan_one(self, row: Dict[str, Any], extractor, historical_db) -> Dict[str, Any]:
        url = row["url"]
        try:
            logger.info(f"🔁 URL periodico: scansione {url}")
            result = await extractor.extract_products_fast(url)
            products = result.get("products", []) if result and result.get("success") else []
            if products and historical_db:
                await historical_db.save_extracted_products(
                    url=url, products=products, session_id=None,
                    extraction_method="url_monitor",
                )
            self._mark_scanned(row["id"], len(products))
            return {"success": True, "count": len(products)}
        except Exception as e:
            logger.error(f"❌ scan_one {url}: {e}")
            self._mark_scanned(row["id"], 0)
            return {"success": False, "error": str(e)}

    async def _loop(self, extractor_getter, db_getter, interval_seconds: int = 900):
        """Loop: ogni `interval` controlla gli URL scaduti e li scansiona (in serie)."""
        logger.info("🔁 URL monitor loop avviato")
        while True:
            try:
                due = await self._get_due()
                if due:
                    logger.info(f"🔁 URL periodici scaduti: {len(due)}")
                for row in due:
                    ext, db = extractor_getter(), db_getter()
                    if ext:
                        await self._scan_one(row, ext, db)
                    await asyncio.sleep(2)
            except Exception as e:
                logger.error(f"❌ URL monitor loop: {e}")
            await asyncio.sleep(interval_seconds)

    def start_loop(self, extractor_getter, db_getter):
        if self._loop_task is None:
            self._loop_task = asyncio.create_task(self._loop(extractor_getter, db_getter))
