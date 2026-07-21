#!/usr/bin/env python3

"""
Historical Products DB - Stats Mixin
====================================

Mixin con i metodi di statistiche/aggregazioni per dashboard, siti,
sessioni recenti, categorie e performance.
Estratto da historical_products_db.py tramite split meccanico (nessuna
modifica di logica/SQL).
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class _StatsMixin:
    """Metodi di statistiche e aggregazioni"""

    async def get_dashboard_stats(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Ottiene statistiche per la dashboard con calcoli più accurati"""
        try:
            # Se non è richiesto il refresh, prova a usare le statistiche in cache
            if not force_refresh:
                cached_stats = self._get_cached_dashboard_stats()
                if cached_stats:
                    return {
                        "success": True,
                        "stats": cached_stats,
                        "cached": True
                    }

            with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                cursor = conn.cursor()

                # Statistiche generali più accurate
                cursor.execute("SELECT COUNT(*) FROM products")
                total_products = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(DISTINCT source) FROM products")
                total_sites = cursor.fetchone()[0]

                # Prodotti aggiunti oggi
                cursor.execute("SELECT COUNT(*) FROM products WHERE DATE(extraction_date) = DATE('now')")
                products_today = cursor.fetchone()[0]

                # Sessioni di estrazione oggi
                cursor.execute("SELECT COUNT(*) FROM extraction_sessions WHERE DATE(start_time) = DATE('now')")
                extractions_today = cursor.fetchone()[0]

                # Calcolo precisione AI basata su success rate delle estrazioni
                cursor.execute("""
                    SELECT
                        COUNT(*) as total_sessions,
                        SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_sessions
                    FROM extraction_sessions
                    WHERE start_time >= DATE('now', '-7 days')
                """)
                ai_stats = cursor.fetchone()
                total_sessions = ai_stats[0] if ai_stats[0] else 0
                successful_sessions = ai_stats[1] if ai_stats[1] else 0
                ai_accuracy = round((successful_sessions / total_sessions * 100) if total_sessions > 0 else 0, 1)

                # Siti attivi (con estrazioni negli ultimi 7 giorni)
                cursor.execute("""
                    SELECT COUNT(DISTINCT source)
                    FROM extraction_sessions
                    WHERE start_time >= DATE('now', '-7 days') AND success = 1
                """)
                active_sites = cursor.fetchone()[0]

                # Tempo medio di risposta (usa duration se disponibile, altrimenti calcola)
                cursor.execute("""
                    SELECT AVG(
                        CASE
                            WHEN duration IS NOT NULL THEN
                                CAST(REPLACE(REPLACE(duration, 's', ''), 'ms', '') AS REAL)
                            ELSE
                                (julianday(end_time) - julianday(start_time)) * 24 * 60 * 60 * 1000
                        END
                    ) as avg_response_time
                    FROM extraction_sessions
                    WHERE (end_time IS NOT NULL AND start_time IS NOT NULL) OR duration IS NOT NULL
                    AND success = 1
                    AND start_time >= DATE('now', '-7 days')
                """)
                avg_response_result = cursor.fetchone()
                avg_response_time = round(avg_response_result[0] if avg_response_result[0] else 0)

                # Calcolo uptime basato su sessioni di successo vs totali
                cursor.execute("""
                    SELECT
                        COUNT(*) as total_attempts,
                        SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_attempts
                    FROM extraction_sessions
                    WHERE start_time >= DATE('now', '-24 hours')
                """)
                uptime_stats = cursor.fetchone()
                total_attempts = uptime_stats[0] if uptime_stats[0] else 0
                successful_attempts = uptime_stats[1] if uptime_stats[1] else 0
                uptime = round((successful_attempts / total_attempts * 100) if total_attempts > 0 else 100, 1)

                # Top siti per numero prodotti
                cursor.execute("""
                    SELECT source, COUNT(*) as count
                    FROM products
                    GROUP BY source
                    ORDER BY count DESC
                    LIMIT 5
                """)
                top_sites = [{"site": row[0], "count": row[1]} for row in cursor.fetchall()]

                # Statistiche ultimi 7 giorni per grafici
                cursor.execute("""
                    SELECT DATE(extraction_date) as date, COUNT(*) as count
                    FROM products
                    WHERE extraction_date >= DATE('now', '-7 days')
                    GROUP BY DATE(extraction_date)
                    ORDER BY date DESC
                """)
                weekly_stats = [{"date": row[0], "count": row[1]} for row in cursor.fetchall()]

                # Statistiche per macro reparti (categorie o source)
                cursor.execute("PRAGMA table_info(products)")
                columns = [col[1] for col in cursor.fetchall()]

                if 'category' in columns:
                    cursor.execute("""
                        SELECT
                            COALESCE(category, 'Generale') as category,
                            COUNT(*) as count,
                            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM products), 2) as percentage
                        FROM products
                        GROUP BY COALESCE(category, 'Generale')
                        ORDER BY count DESC
                        LIMIT 8
                    """)
                else:
                    # Usa source come categoria (per database esistenti)
                    cursor.execute("""
                        SELECT
                            COALESCE(source, 'Sconosciuto') as category,
                            COUNT(*) as count,
                            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM products), 2) as percentage
                        FROM products
                        GROUP BY COALESCE(source, 'Sconosciuto')
                        ORDER BY count DESC
                        LIMIT 8
                    """)

                category_stats = []
                for row in cursor.fetchall():
                    category_stats.append({
                        'category': row[0],
                        'count': row[1],
                        'percentage': row[2] or 0
                    })

                # Aggiorna statistiche dashboard con calcoli più accurati
                stats = {
                    "total_products": total_products,
                    "new_products_today": products_today,
                    "extractions_today": extractions_today,
                    "total_sites": total_sites,
                    "sites_monitored": total_sites,
                    "active_sites": active_sites,
                    "ai_accuracy": ai_accuracy,
                    "ai_model": "GPT-4 Turbo",  # Modello AI utilizzato
                    "avg_response_time": avg_response_time,
                    "uptime": uptime,
                    "top_sites": top_sites,
                    "weekly_stats": weekly_stats,
                    "category_stats": category_stats,
                    "last_update": datetime.now().isoformat()
                }

                # Salva statistiche per cache
                self._save_dashboard_stats(stats)

                return {
                    "success": True,
                    "stats": stats,
                    "cached": False
                }

        except Exception as e:
            logger.error(f"❌ Errore statistiche dashboard: {e}")
            return {
                "success": False,
                "error": str(e),
                "stats": {}
            }

    async def get_site_statistics(self, site: str = None) -> Dict[str, Any]:
        """Ottiene statistiche per sito specifico o tutti i siti"""
        try:
            with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                cursor = conn.cursor()

                if site:
                    # Statistiche per sito specifico
                    cursor.execute("""
                        SELECT * FROM site_statistics WHERE site = ?
                    """, (site,))
                    row = cursor.fetchone()

                    if row:
                        return {
                            "success": True,
                            "site": site,
                            "statistics": {
                                "total_extractions": row[1],
                                "total_products": row[2],
                                "last_extraction": row[3],
                                "success_rate": row[4],
                                "avg_products_per_extraction": row[5]
                            }
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"Sito {site} non trovato"
                        }
                else:
                    # Statistiche per tutti i siti
                    cursor.execute("SELECT * FROM site_statistics ORDER BY total_products DESC")
                    rows = cursor.fetchall()

                    sites_stats = []
                    for row in rows:
                        sites_stats.append({
                            "site": row[0],
                            "total_extractions": row[1],
                            "total_products": row[2],
                            "last_extraction": row[3],
                            "success_rate": row[4],
                            "avg_products_per_extraction": row[5]
                        })

                    return {
                        "success": True,
                        "sites": sites_stats
                    }

        except Exception as e:
            logger.error(f"❌ Errore statistiche sito: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_recent_extraction_sessions(self, limit: int = 10) -> Dict[str, Any]:
        """Ottiene le sessioni di estrazione recenti per la dashboard con dettagli completi"""
        try:
            with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                cursor = conn.cursor()

                # Carica sessioni recenti con informazioni più dettagliate
                cursor.execute("""
                    SELECT
                        es.id,
                        es.url,
                        es.start_time,
                        es.end_time,
                        es.products_found,
                        es.success,
                        es.extraction_method,
                        es.error_message,
                        es.session_type,
                        es.source,
                        es.total_pages,
                        es.pages_processed,
                        es.duration
                    FROM extraction_sessions es
                    ORDER BY es.start_time DESC
                    LIMIT ?
                """, (limit,))

                sessions = []
                for row in cursor.fetchall():
                    # Usa durata dal database se disponibile, altrimenti calcola
                    duration = row[12]  # Campo duration dal database
                    start_time = row[2]
                    end_time = row[3]
                    if not duration and start_time and end_time:
                        try:
                            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                            duration_seconds = (end_dt - start_dt).total_seconds()
                            if duration_seconds < 60:
                                duration = f"{duration_seconds:.1f}s"
                            elif duration_seconds < 3600:
                                duration = f"{duration_seconds/60:.1f}m"
                            else:
                                duration = f"{duration_seconds/3600:.1f}h"
                        except:
                            duration = "N/A"

                    # Estrai nome del sito dall'URL
                    site_name = "Sito sconosciuto"
                    if row[1]:  # URL
                        try:
                            from urllib.parse import urlparse
                            parsed_url = urlparse(row[1])
                            site_name = parsed_url.netloc.replace('www.', '') if parsed_url.netloc else "URL invalido"
                        except:
                            site_name = "URL invalido"

                    # Determina tipo di attività
                    session_type = row[8] or 'extraction'
                    if session_type == 'extraction':
                        activity_type = 'scrape'
                        icon = 'fas fa-spider'
                        if row[4] and row[4] > 0:  # products_found
                            description = f"Scraping completato su {site_name}: {row[4]} prodotti estratti"
                        else:
                            description = f"Scraping su {site_name} - Nessun prodotto trovato"
                    elif session_type == 'comparison':
                        activity_type = 'analysis'
                        icon = 'fas fa-balance-scale'
                        description = f"Confronto prodotti completato su {site_name}"
                    elif session_type == 'update':
                        activity_type = 'update'
                        icon = 'fas fa-sync-alt'
                        description = f"Aggiornamento prezzi su {site_name}"
                    else:
                        activity_type = 'other'
                        icon = 'fas fa-cog'
                        description = f"Attività {session_type} su {site_name}"

                    # Aggiungi dettagli aggiuntivi
                    additional_info = []
                    if row[10] and row[11]:  # total_pages e pages_processed
                        additional_info.append(f"Pagine: {row[11]}/{row[10]}")
                    if duration:
                        additional_info.append(f"Durata: {duration}")
                    if row[7]:  # error_message
                        additional_info.append(f"Errore: {row[7][:50]}...")

                    # Crea descrizione completa
                    if additional_info:
                        description += f" ({', '.join(additional_info)})"

                    session = {
                        'id': row[0],
                        'url': row[1],
                        'start_time': row[2],
                        'end_time': row[3],
                        'products_found': row[4],
                        'success': bool(row[5]),
                        'extraction_method': row[6],
                        'error_message': row[7],
                        'session_type': session_type,
                        'source': row[9] or site_name,
                        'total_pages': row[10],
                        'pages_processed': row[11],
                        'duration': duration,
                        'site_name': site_name,
                        'activity_type': activity_type,
                        'icon': icon,
                        'description': description,
                        'additional_info': additional_info
                    }

                    # AGGIUNGI LA SESSIONE ALL'ARRAY (BUG CORRETTO!)
                    sessions.append(session)

                return {
                    "success": True,
                    "sessions": sessions
                }

        except Exception as e:
            logger.error(f"❌ Errore caricamento sessioni recenti: {e}")
            return {
                "success": False,
                "error": str(e),
                "sessions": []
            }

    async def get_product_categories_stats(self) -> Dict[str, Any]:
        """Ottiene statistiche per categoria per la dashboard"""
        try:
            with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                cursor = conn.cursor()

                # Prima controlla se la colonna category esiste
                cursor.execute("PRAGMA table_info(products)")
                columns = [col[1] for col in cursor.fetchall()]

                if 'category' in columns:
                    # Se la colonna esiste, usa la query originale
                    cursor.execute("""
                        SELECT
                            COALESCE(category, 'Generale') as category,
                            COUNT(*) as count,
                            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM products), 2) as percentage
                        FROM products
                        GROUP BY COALESCE(category, 'Generale')
                        ORDER BY count DESC
                        LIMIT 10
                    """)
                else:
                    # Se la colonna non esiste, usa source come alternativa
                    cursor.execute("""
                        SELECT
                            COALESCE(source, 'Sconosciuto') as category,
                            COUNT(*) as count,
                            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM products), 2) as percentage
                        FROM products
                        GROUP BY COALESCE(source, 'Sconosciuto')
                        ORDER BY count DESC
                        LIMIT 10
                    """)

                categories = []
                for row in cursor.fetchall():
                    category = {
                        'category': row[0],
                        'count': row[1],
                        'percentage': row[2] or 0
                    }
                    categories.append(category)

                return {
                    "success": True,
                    "categories": categories
                }

        except Exception as e:
            logger.error(f"❌ Errore caricamento statistiche categorie: {e}")
            return {
                "success": False,
                "error": str(e),
                "categories": []
            }

    async def get_sites_performance_stats(self) -> Dict[str, Any]:
        """Ottiene statistiche delle performance per sito per la dashboard"""
        try:
            with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                cursor = conn.cursor()

                # Carica statistiche performance per sito (ultimi 7 giorni)
                cursor.execute("""
                    SELECT
                        COALESCE(es.source, 'Sito sconosciuto') as site,
                        COUNT(*) as total_sessions,
                        SUM(CASE WHEN es.success = 1 THEN 1 ELSE 0 END) as successful_sessions,
                        ROUND(
                            SUM(CASE WHEN es.success = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1
                        ) as success_rate,
                        ROUND(AVG(es.products_found), 1) as avg_products,
                        ROUND(AVG(
                            CASE
                                WHEN es.duration IS NOT NULL THEN
                                    CAST(REPLACE(REPLACE(es.duration, 's', ''), 'ms', '') AS REAL)
                                ELSE
                                    (julianday(es.end_time) - julianday(es.start_time)) * 24 * 60 * 60 * 1000
                            END
                        )) as avg_response_time
                    FROM extraction_sessions es
                    WHERE es.start_time >= DATE('now', '-7 days')
                    AND es.source IS NOT NULL
                    GROUP BY es.source
                    ORDER BY success_rate DESC, avg_products DESC
                    LIMIT 10
                """)

                sites = []
                for row in cursor.fetchall():
                    site = {
                        'site': row[0],
                        'total_sessions': row[1],
                        'successful_sessions': row[2],
                        'success_rate': row[3] or 0,
                        'avg_products': row[4] or 0,
                        'avg_response_time': row[5] or 0
                    }
                    sites.append(site)

                # Se non ci sono dati, crea dati di esempio
                if not sites:
                    sites = [
                        {
                            'site': 'Nessun sito scansionato',
                            'total_sessions': 0,
                            'successful_sessions': 0,
                            'success_rate': 0,
                            'avg_products': 0,
                            'avg_response_time': 0
                        }
                    ]

                return {
                    "success": True,
                    "sites": sites
                }

        except Exception as e:
            logger.error(f"❌ Errore caricamento statistiche performance sito: {e}")
            return {
                "success": False,
                "error": str(e),
                "sites": []
            }
