#!/usr/bin/env python3

"""
Historical Products DB - Save Mixin
===================================

Mixin con i metodi di salvataggio/inserimento prodotti e pulizia duplicati.
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


class _SaveMixin:
    """Metodi di salvataggio prodotti e pulizia duplicati"""

    async def save_extracted_products(self, url: str, products: List[Dict[str, Any]],
                                    session_id: str = None, extraction_method: str = "fast_ai_extractor",
                                    container_selector: str = None, start_time: str = None,
                                    end_time: str = None, duration: str = None) -> Dict[str, Any]:
        """
        Salva prodotti estratti nel database

        ARGS:
        - url: URL da cui sono stati estratti i prodotti
        - products: Lista prodotti estratti
        - session_id: ID sessione estrazione
        - extraction_method: Metodo di estrazione usato
        - container_selector: Selettore container usato
        - start_time: Timestamp inizio estrazione (ISO string)
        - end_time: Timestamp fine estrazione (ISO string)
        - duration: Durata calcolata dell'estrazione

        RETURNS:
        - Dict con risultato operazione
        """
        try:
            if not session_id:
                session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(url) % 10000}"

            # Gestione robusta delle connessioni con retry
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                        cursor = conn.cursor()

                        # Salva sessione estrazione con timestamp reali
                        actual_start_time = start_time if start_time else datetime.now().isoformat()
                        actual_end_time = end_time if end_time else datetime.now().isoformat()

                        cursor.execute("""
                            INSERT INTO extraction_sessions
                            (id, url, start_time, end_time, products_found, success, extraction_method, container_selector, duration)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            session_id, url, actual_start_time, actual_end_time,
                            len(products), True, extraction_method, container_selector, duration
                        ))

                        # Salva ogni prodotto
                        saved_count = 0
                        seen_products = set()  # Per evitare duplicati nella stessa sessione

                        for product in products:
                            try:
                                # Normalizza dati prodotto
                                name = product.get('name', '').strip()
                                price = product.get('price', '').strip()
                                brand = product.get('brand', '').strip()
                                product_url = product.get('url', '').strip()
                                source = product.get('source', '').strip()
                                source_url = product.get('source_url', '').strip()

                                # Estrai dominio come source se non presente
                                if not source and source_url:
                                    source = urlparse(source_url).netloc
                                elif not source and url:
                                    source = urlparse(url).netloc

                                # Assicurati che source_url sia sempre popolato
                                if not source_url and url:
                                    source_url = url

                                # Se ancora non abbiamo source, estrailo dall'URL
                                if not source:
                                    source = urlparse(url).netloc if url else 'Unknown'

                                # 🚀 CONTROLLO DUPPLICATI INTELLIGENTE: Identificazione univoca robusta
                                try:
                                    # Crea ID univoco del prodotto basato su caratteristiche multiple
                                    product_fingerprint = self._create_product_fingerprint(product)

                                    # Cerca prodotti simili nel database usando fingerprint + source
                                    cursor.execute("""
                                        SELECT id, name, price, brand, source, extraction_date, metadata
                                        FROM products
                                        WHERE source = ? AND product_fingerprint = ?
                                        ORDER BY extraction_date DESC
                                        LIMIT 1
                                    """, (source, product_fingerprint))

                                    existing_product = cursor.execute("""
                                        SELECT id, name, price, brand, source, extraction_date, metadata
                                        FROM products
                                        WHERE source = ? AND product_fingerprint = ?
                                        ORDER BY extraction_date DESC
                                        LIMIT 1
                                    """, (source, product_fingerprint)).fetchone()

                                    if existing_product:
                                        existing_price = existing_product[2]
                                        existing_date = existing_product[5]
                                        existing_metadata = existing_product[6]

                                        # Se il prezzo è cambiato, aggiorna il prodotto esistente
                                        if existing_price != price:
                                            logger.info(f"🔄 Prezzo cambiato per {name} su {source}: {existing_price} → {price}")

                                            # Aggiorna prezzo e data
                                            cursor.execute("""
                                                UPDATE products
                                                SET price = ?, extraction_date = ?, session_id = ?
                                                WHERE id = ?
                                            """, (price, datetime.now(), session_id, existing_product[0]))

                                            saved_count += 1
                                            logger.debug(f"✅ Prodotto aggiornato: {name} su {source} (prezzo: {existing_price} → {price})")
                                            continue
                                        else:
                                            # Prodotto identico già esistente nello stesso sito, salta
                                            logger.debug(f"⏭️ Prodotto duplicato saltato (stesso sito): {name} su {source} (prezzo: {price})")
                                            continue

                                except Exception as dedup_error:
                                    logger.warning(f"⚠️ Errore controllo duplicati per {name}: {dedup_error}")
                                    # Continua con il salvataggio normale

                                # Crea chiave unica per evitare duplicati nella stessa sessione
                                product_key = f"{source}_{name}_{brand}_{price}"
                                if product_key in seen_products:
                                    logger.debug(f"⏭️ Prodotto duplicato saltato nella sessione: {name} su {source}")
                                    continue
                                seen_products.add(product_key)

                                # Metadata aggiuntivi - Semplificato per debug
                                try:
                                    metadata = {
                                        'original_data': product,
                                        'extraction_method': extraction_method or 'unknown',
                                        'container_selector': container_selector or 'unknown',
                                        'session_id': session_id or 'unknown'
                                    }

                                    cursor.execute("""
                                        INSERT INTO products
                                        (name, price, brand, url, source, source_url, session_id, metadata, validation_score, product_fingerprint)
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    """, (
                                        name, price, brand, product_url, source, source_url,
                                        session_id, json.dumps(metadata), product.get('validation_score', 0.0), product_fingerprint
                                    ))

                                    saved_count += 1
                                    logger.debug(f"✅ Prodotto salvato: {name} su {source}")

                                except Exception as metadata_error:
                                    logger.error(f"❌ Errore metadata per {name}: {metadata_error}")
                                    # Fallback: salva senza metadata
                                    try:
                                        cursor.execute("""
                                            INSERT INTO products
                                            (name, price, brand, url, source, source_url, session_id, metadata, validation_score, product_fingerprint)
                                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                        """, (
                                            name, price, brand, product_url, source, source_url,
                                            session_id, '{}', product.get('validation_score', 0.0), product_fingerprint
                                        ))
                                        saved_count += 1
                                        logger.debug(f"✅ Prodotto salvato (fallback): {name} su {source}")
                                    except Exception as fallback_error:
                                        logger.error(f"❌ Errore fallback per {name}: {fallback_error}")
                                        continue

                            except Exception as e:
                                logger.warning(f"⚠️ Errore salvataggio prodotto: {e}")
                                continue

                        # Aggiorna statistiche sito (usando la stessa connessione)
                        self._update_site_statistics_with_connection(cursor, url, len(products), True)

                        # Aggiorna statistiche dashboard (usando la stessa connessione)
                        self._update_dashboard_stats_with_connection(cursor)

                        conn.commit()

                        logger.info(f"✅ Salvati {saved_count}/{len(products)} prodotti per {url}")

                        return {
                            "success": True,
                            "saved_count": saved_count,
                            "total_products": len(products),
                            "session_id": session_id
                        }

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
            logger.error(f"❌ Errore salvataggio prodotti dopo {max_retries} tentativi: {e}")
            return {
                "success": False,
                "error": str(e),
                "saved_count": 0
            }

    async def clean_duplicate_products(self) -> Dict[str, Any]:
        """Pulisce i prodotti duplicati dal database"""
        try:
            with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                cursor = conn.cursor()

                # Trova prodotti duplicati SOLO all'interno dello stesso sito (stesso nome, brand e source)
                cursor.execute("""
                    SELECT source, name, brand, COUNT(*) as count,
                           GROUP_CONCAT(id) as ids,
                           GROUP_CONCAT(price) as prices,
                           GROUP_CONCAT(extraction_date) as dates
                    FROM products
                    GROUP BY source, name, brand
                    HAVING COUNT(*) > 1
                    ORDER BY count DESC
                """)

                duplicates = cursor.fetchall()
                total_duplicates = sum(row[3] for row in duplicates)
                cleaned_count = 0

                logger.info(f"🧹 Trovati {len(duplicates)} gruppi di duplicati ({total_duplicates} prodotti totali)")
                logger.info("📋 NOTA: Elimino duplicati SOLO all'interno dello stesso sito")
                logger.info("🔒 Prodotti su siti diversi (es. Amazon vs MediaWorld) rimangono separati")

                for duplicate in duplicates:
                    source, name, brand, count, ids, prices, dates = duplicate

                    if count > 1:
                        # Prendi solo il prodotto più recente
                        id_list = [int(x) for x in ids.split(',')]
                        price_list = prices.split(',')
                        date_list = dates.split(',')

                        # Trova l'indice del prodotto più recente
                        latest_index = 0
                        latest_date = date_list[0]

                        for i, date_str in enumerate(date_list):
                            try:
                                current_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                                latest_date_obj = datetime.fromisoformat(latest_date.replace('Z', '+00:00'))

                                if current_date > latest_date_obj:
                                    latest_index = i
                                    latest_date = date_str
                            except:
                                continue

                        # Mantieni solo il prodotto più recente, elimina gli altri
                        ids_to_delete = [id_list[i] for i in range(len(id_list)) if i != latest_index]

                        if ids_to_delete:
                            placeholders = ','.join(['?' for _ in ids_to_delete])
                            cursor.execute(f"DELETE FROM products WHERE id IN ({placeholders})", ids_to_delete)
                            cleaned_count += len(ids_to_delete)

                            logger.info(f"🧹 Eliminati {len(ids_to_delete)} duplicati per {name} su {source}")

                conn.commit()

                logger.info(f"✅ Pulizia completata: eliminati {cleaned_count} prodotti duplicati")

                return {
                    "success": True,
                    "duplicates_found": len(duplicates),
                    "total_duplicates": total_duplicates,
                    "cleaned_count": cleaned_count
                }

        except Exception as e:
            logger.error(f"❌ Errore pulizia duplicati: {e}")
            return {
                "success": False,
                "error": str(e)
            }
