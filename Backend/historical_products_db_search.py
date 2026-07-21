#!/usr/bin/env python3

"""
Historical Products DB - Search Mixin
=====================================

Mixin con i metodi di ricerca/query prodotti storici.
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


class _SearchMixin:
    """Metodi di ricerca prodotti storici"""

    async def search_historical_products(self, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Ricerca prodotti storici con filtri

        ARGS:
        - filters: Dizionario con filtri (product_name, site, date, brand)

        RETURNS:
        - Dict con prodotti trovati e statistiche
        """
        try:
            if not filters:
                filters = {}

            with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                cursor = conn.cursor()

                # Costruisci query con filtri
                query = "SELECT * FROM products WHERE 1=1"
                params = []

                if filters.get('product_name'):
                    query += " AND name LIKE ?"
                    params.append(f"%{filters['product_name']}%")

                if filters.get('site'):
                    query += " AND source LIKE ?"
                    params.append(f"%{filters['site']}%")

                # NUOVO FILTRO: sources (lista di domini)
                if filters.get('sources') and isinstance(filters['sources'], list):
                    # 🆕 GESTIONE DOMINI: Supporta sia con che senza www.
                    expanded_sources = []
                    for domain in filters['sources']:
                        # Aggiungi il dominio originale
                        expanded_sources.append(domain)
                        # Aggiungi anche la versione con www. se non presente
                        if not domain.startswith('www.'):
                            expanded_sources.append(f"www.{domain}")
                        # Aggiungi anche la versione senza www. se presente
                        elif domain.startswith('www.'):
                            expanded_sources.append(domain[4:])

                    # Rimuovi duplicati mantenendo l'ordine
                    unique_sources = list(dict.fromkeys(expanded_sources))

                    sources_placeholders = ','.join(['?' for _ in unique_sources])
                    query += f" AND source IN ({sources_placeholders})"
                    params.extend(unique_sources)

                    # 🆕 DEBUG: Mostra il filtro applicato
                    logger.info(f"🎯 FILTRO SOURCES APPLICATO:")
                    logger.info(f"  Domini richiesti originali: {filters['sources']}")
                    logger.info(f"  Domini espansi: {unique_sources}")
                    logger.info(f"  Query generata: {query}")
                    logger.info(f"  Parametri: {params}")

                if filters.get('brand'):
                    query += " AND brand LIKE ?"
                    params.append(f"%{filters['brand']}%")

                if filters.get('date'):
                    # Filtra per data specifica
                    date_str = filters['date']
                    query += " AND DATE(extraction_date) = ?"
                    params.append(date_str)

                # Ordina per data più recente
                query += " ORDER BY extraction_date DESC"

                # Parametri di ricerca
                limit = filters.get('limit', 1000)
                query += f" LIMIT {limit}"

                cursor.execute(query, params)
                rows = cursor.fetchall()

                # 🆕 DEBUG: Mostra i risultati della query
                logger.info(f"🔍 RISULTATI QUERY DATABASE:")
                logger.info(f"  Query eseguita: {query}")
                logger.info(f"  Parametri usati: {params}")
                logger.info(f"  Righe trovate: {len(rows)}")

                # Converti in dizionari
                products = []
                for row in rows:
                    product = {
                        'id': row[0],
                        'name': row[1],
                        'price': row[2],
                        'brand': row[3],
                        'url': row[4],
                        'source': row[5],
                        'source_url': row[6],
                        'extraction_date': row[7],
                        'session_id': row[8],
                        'metadata': json.loads(row[9]) if row[9] else {},
                        'validation_score': row[10],
                        'is_available': bool(row[11])
                    }
                    products.append(product)

                # 🆕 DEBUG: Mostra i primi 5 prodotti trovati
                logger.info(f"📦 PRIMI 5 PRODOTTI TROVATI:")
                for i, product in enumerate(products[:5]):
                    logger.info(f"  Prodotto {i+1}:")
                    logger.info(f"    Nome: '{product.get('name', 'N/A')}'")
                    logger.info(f"    Source: '{product.get('source', 'N/A')}'")
                    logger.info(f"    Source URL: '{product.get('source_url', 'N/A')}'")

                # Calcola statistiche ricerca
                total_found = len(products)
                unique_sites = len(set(p['source'] for p in products))
                date_range = self._get_date_range(products)

                # 🆕 DEBUG: Mostra tutti i valori source disponibili
                all_sources = set(p['source'] for p in products)
                logger.info(f"🌐 VALORI SOURCE DISPONIBILI:")
                logger.info(f"  Source unici trovati: {sorted(all_sources)}")
                logger.info(f"  Conteggio per source:")
                source_counts = {}
                for p in products:
                    source = p.get('source', 'N/A')
                    source_counts[source] = source_counts.get(source, 0) + 1
                for source, count in sorted(source_counts.items()):
                    logger.info(f"    - {source}: {count} prodotti")

                return {
                    "success": True,
                    "products": products,
                    "statistics": {
                        "total_found": total_found,
                        "unique_sites": unique_sites,
                        "date_range": date_range,
                        "filters_applied": filters
                    }
                }

        except Exception as e:
            logger.error(f"❌ Errore ricerca prodotti storici: {e}")
            return {
                "success": False,
                "error": str(e),
                "products": [],
                "statistics": {}
            }
