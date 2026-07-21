#!/usr/bin/env python3

"""
Historical Products DB - Helpers Mixin
======================================

Mixin con i metodi di supporto: aggiornamento statistiche sito/dashboard,
fingerprint prodotto, cache statistiche, range date, pulizia dati vecchi ed
export.
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


class _HelpersMixin:
    """Metodi di supporto per statistiche, cache e manutenzione"""

    def _update_site_statistics(self, url: str, products_count: int, success: bool):
        """Aggiorna statistiche per sito (metodo legacy per compatibilità)"""
        try:
            site = urlparse(url).netloc

            # Gestione robusta delle connessioni con retry
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                        cursor = conn.cursor()
                        self._update_site_statistics_with_connection(cursor, url, products_count, success)
                        conn.commit()
                        break  # Successo, esci dal loop retry

                except sqlite3.OperationalError as e:
                    if "database is locked" in str(e) and attempt < max_retries - 1:
                        logger.warning(f"⚠️ Database bloccato, tentativo {attempt + 1}/{max_retries}, riprovo...")
                        import time
                        time.sleep(1)  # Attendi 1 secondo prima di riprovare
                        continue
                    else:
                        raise

                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"⚠️ Errore tentativo {attempt + 1}/{max_retries}: {e}, riprovo...")
                        import time
                        time.sleep(1)
                        continue
                    else:
                        raise

        except Exception as e:
            logger.error(f"❌ Errore aggiornamento statistiche sito dopo {max_retries} tentativi: {e}")

    def _update_site_statistics_with_connection(self, cursor, url: str, products_count: int, success: bool):
        """Aggiorna statistiche per sito usando una connessione esistente"""
        try:
            site = urlparse(url).netloc

            # Controlla se sito esiste
            cursor.execute("SELECT * FROM site_statistics WHERE site = ?", (site,))
            row = cursor.fetchone()

            if row:
                # Aggiorna statistiche esistenti
                total_extractions = row[1] + 1
                total_products = row[2] + products_count
                success_count = row[1] * row[4] + (1 if success else 0)
                success_rate = success_count / total_extractions
                avg_products = total_products / total_extractions

                cursor.execute("""
                    UPDATE site_statistics
                    SET total_extractions = ?, total_products = ?, last_extraction = ?,
                        success_rate = ?, avg_products_per_extraction = ?, updated_at = ?
                    WHERE site = ?
                """, (total_extractions, total_products, datetime.now(),
                      success_rate, avg_products, datetime.now(), site))
            else:
                # Crea nuove statistiche
                cursor.execute("""
                    INSERT INTO site_statistics
                    (site, total_extractions, total_products, last_extraction, success_rate, avg_products_per_extraction)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (site, 1, products_count, datetime.now(),
                      1.0 if success else 0.0, products_count))

        except Exception as e:
            logger.error(f"❌ Errore aggiornamento statistiche sito: {e}")

    def _update_dashboard_stats(self):
        """Aggiorna statistiche dashboard (metodo legacy per compatibilità)"""
        try:
            with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                cursor = conn.cursor()
                self._update_dashboard_stats_with_connection(cursor)
                conn.commit()

        except Exception as e:
            logger.error(f"❌ Errore aggiornamento statistiche dashboard: {e}")

    def _create_product_fingerprint(self, product: Dict[str, Any]) -> str:
        """
        Crea un fingerprint univoco per il prodotto basato su caratteristiche multiple

        ARGS:
        - product: Dizionario prodotto con tutti i campi

        RETURNS:
        - String hash univoco per identificazione prodotto
        """
        try:
            import hashlib

            # Campi chiave per identificazione univoca
            key_fields = [
                product.get('name', ''),
                product.get('brand', ''),
                product.get('model', ''),
                product.get('category', ''),
                product.get('weight', ''),
                product.get('description', '')[:100] if product.get('description') else '',  # Primi 100 caratteri
            ]

            # Normalizza e rimuovi campi vuoti
            key_fields = [str(field).strip().lower() for field in key_fields if field]

            # Crea stringa combinata
            combined_string = "|".join(key_fields)

            # Genera hash SHA-256
            fingerprint = hashlib.sha256(combined_string.encode('utf-8')).hexdigest()[:16]

            logger.debug(f"🔍 Fingerprint creato per {product.get('name', 'Unknown')}: {fingerprint}")
            logger.debug(f"   Campi chiave: {key_fields}")

            return fingerprint

        except Exception as e:
            logger.error(f"❌ Errore creazione fingerprint per {product.get('name', 'Unknown')}: {e}")
            # Fallback: usa nome + brand
            fallback_string = f"{product.get('name', '')}|{product.get('brand', '')}"
            return hashlib.sha256(fallback_string.encode('utf-8')).hexdigest()[:16]

    def _update_dashboard_stats_with_connection(self, cursor):
        """Aggiorna statistiche dashboard usando una connessione esistente"""
        try:
            # Calcola statistiche
            cursor.execute("SELECT COUNT(*) FROM products")
            total_products = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(DISTINCT source) FROM products")
            total_sites = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM extraction_sessions WHERE DATE(start_time) = DATE('now')")
            extractions_today = cursor.fetchone()[0]

            # Salva statistiche
            stats_to_save = [
                ("total_products", str(total_products)),
                ("total_sites", str(total_sites)),
                ("extractions_today", str(extractions_today)),
                ("last_update", datetime.now().isoformat())
            ]

            for stat_name, stat_value in stats_to_save:
                cursor.execute("""
                    INSERT INTO dashboard_stats (stat_name, stat_value)
                    VALUES (?, ?)
                """, (stat_name, stat_value))

        except Exception as e:
            logger.error(f"❌ Errore aggiornamento statistiche dashboard: {e}")

    def _save_dashboard_stats(self, stats: Dict[str, Any]):
        """Salva statistiche dashboard per cache"""
        try:
            with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                cursor = conn.cursor()

                # Pulisci statistiche vecchie (mantieni solo ultime 100)
                cursor.execute("DELETE FROM dashboard_stats WHERE id NOT IN (SELECT id FROM dashboard_stats ORDER BY timestamp DESC LIMIT 100)")

                # Salva nuove statistiche
                for stat_name, stat_value in stats.items():
                    if isinstance(stat_value, (dict, list)):
                        stat_value = json.dumps(stat_value)
                    else:
                        stat_value = str(stat_value)

                    cursor.execute("""
                        INSERT INTO dashboard_stats (stat_name, stat_value)
                        VALUES (?, ?)
                    """, (stat_name, stat_value))

                conn.commit()

        except Exception as e:
            logger.error(f"❌ Errore salvataggio statistiche dashboard: {e}")

    def _get_cached_dashboard_stats(self) -> Optional[Dict[str, Any]]:
        """Ottiene statistiche dashboard dalla cache se disponibili e recenti"""
        try:
            with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                cursor = conn.cursor()

                # Controlla se ci sono statistiche recenti (ultimi 5 minuti)
                cursor.execute("""
                    SELECT stat_name, stat_value
                    FROM dashboard_stats
                    WHERE timestamp >= datetime('now', '-5 minutes')
                    ORDER BY timestamp DESC
                """)

                rows = cursor.fetchall()
                if not rows:
                    return None

                # Ricostruisci le statistiche dalla cache
                cached_stats = {}
                for row in rows:
                    stat_name = row[0]
                    stat_value = row[1]

                    # Converti i valori al tipo corretto
                    if stat_name in ['total_products', 'new_products_today', 'extractions_today',
                                   'total_sites', 'sites_monitored', 'active_sites', 'total_pages', 'pages_processed']:
                        try:
                            cached_stats[stat_name] = int(stat_value)
                        except:
                            cached_stats[stat_name] = 0
                    elif stat_name in ['ai_accuracy', 'uptime']:
                        try:
                            cached_stats[stat_name] = float(stat_value)
                        except:
                            cached_stats[stat_name] = 0.0
                    elif stat_name in ['avg_response_time']:
                        try:
                            cached_stats[stat_name] = int(float(stat_value))
                        except:
                            cached_stats[stat_name] = 0
                    else:
                        cached_stats[stat_name] = stat_value

                # Controlla se abbiamo tutte le statistiche necessarie
                required_stats = ['total_products', 'new_products_today', 'extractions_today',
                                'total_sites', 'sites_monitored', 'active_sites', 'ai_accuracy',
                                'ai_model', 'avg_response_time', 'uptime']

                if all(stat in cached_stats for stat in required_stats):
                    logger.info("✅ Statistiche dashboard caricate dalla cache")
                    return cached_stats
                else:
                    logger.info("⚠️ Cache statistiche incomplete, ricalcolo necessario")
                    return None

        except Exception as e:
            logger.error(f"❌ Errore lettura cache statistiche: {e}")
            return None

    def _get_date_range(self, products: List[Dict[str, Any]]) -> Dict[str, str]:
        """Calcola range date per prodotti"""
        try:
            if not products:
                return {"start": None, "end": None}

            dates = [p['extraction_date'] for p in products if p['extraction_date']]
            if not dates:
                return {"start": None, "end": None}

            return {
                "start": min(dates),
                "end": max(dates)
            }

        except Exception as e:
            logger.error(f"❌ Errore calcolo range date: {e}")
            return {"start": None, "end": None}

    async def cleanup_old_data(self, days_to_keep: int = 90):
        """Pulisce dati vecchi dal database"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)

            with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                cursor = conn.cursor()

                # Conta record da eliminare
                cursor.execute("SELECT COUNT(*) FROM products WHERE extraction_date < ?", (cutoff_date,))
                products_to_delete = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM extraction_sessions WHERE start_time < ?", (cutoff_date,))
                sessions_to_delete = cursor.fetchone()[0]

                # Elimina dati vecchi
                cursor.execute("DELETE FROM products WHERE extraction_date < ?", (cutoff_date,))
                cursor.execute("DELETE FROM extraction_sessions WHERE start_time < ?", (cutoff_date,))

                conn.commit()

                logger.info(f"🧹 Pulizia completata: eliminati {products_to_delete} prodotti e {sessions_to_delete} sessioni")

                return {
                    "success": True,
                    "products_deleted": products_to_delete,
                    "sessions_deleted": sessions_to_delete
                }

        except Exception as e:
            logger.error(f"❌ Errore pulizia dati: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def export_data(self, format: str = "json") -> Dict[str, Any]:
        """Export dati per backup"""
        try:
            with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                cursor = conn.cursor()

                # Esporta prodotti
                cursor.execute("SELECT * FROM products ORDER BY extraction_date DESC LIMIT 1000")
                products = cursor.fetchall()

                # Esporta sessioni
                cursor.execute("SELECT * FROM extraction_sessions ORDER BY start_time DESC LIMIT 100")
                sessions = cursor.fetchall()

                # Esporta statistiche
                cursor.execute("SELECT * FROM site_statistics")
                site_stats = cursor.fetchall()

                export_data = {
                    "export_date": datetime.now().isoformat(),
                    "products_count": len(products),
                    "sessions_count": len(sessions),
                    "sites_count": len(site_stats),
                    "products": products,
                    "sessions": sessions,
                    "site_statistics": site_stats
                }

                return {
                    "success": True,
                    "data": export_data,
                    "format": format
                }

        except Exception as e:
            logger.error(f"❌ Errore export dati: {e}")
            return {
                "success": False,
                "error": str(e)
            }
