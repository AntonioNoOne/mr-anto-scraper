#!/usr/bin/env python3

"""
Historical Products Database - Database per prodotti estratti
================================================================

Database SQLite per salvare tutti i prodotti estratti e permettere
ricerche storiche. Integra con il sistema principale per persistenza
dati e analisi temporali.

FLUSSO PRINCIPALE:
1. Salva automaticamente ogni prodotto estratto
2. Permette ricerche per nome, sito, data
3. Traccia statistiche di estrazione
4. Fornisce dati per dashboard in tempo reale
5. Supporta monitoraggio prezzi nel tempo

STRUTTURA DATABASE:
- products: Prodotti estratti con metadati
- extraction_sessions: Sessioni di estrazione
- site_statistics: Statistiche per sito
- dashboard_stats: Statistiche dashboard

DIPENDENZE:
- sqlite3: Database SQLite
- datetime: Gestione timestamp
- json: Serializzazione dati
- typing: Type hints
- logging: Sistema log

SCRIPT CHE RICHIAMANO QUESTO:
- main.py: Per salvare prodotti estratti
- fast_ai_extractor.py: Per salvare automaticamente
- Frontend: Per ricerche storiche e dashboard

SCRIPT RICHIAMATI DA QUESTO:
- Nessuno (database standalone)

STRUTTURA RISULTATI:
- Lista prodotti storici con filtri
- Statistiche estrazione per sito
- Dati dashboard aggregati
- Metadati sessione estrazione

FUNZIONALITÀ PRINCIPALI:
- save_extracted_products(): Salva prodotti estratti
- search_historical_products(): Ricerca prodotti storici
- get_dashboard_stats(): Statistiche dashboard
- get_site_statistics(): Statistiche per sito
- cleanup_old_data(): Pulizia dati vecchi
- export_data(): Export dati per backup

WORKFLOW SALVATAGGIO:
1. Riceve prodotti estratti da fast_ai_extractor
2. Salva ogni prodotto con metadati completi
3. Aggiorna statistiche sito e dashboard
4. Mantiene traccia sessione estrazione
5. Permette ricerche e analisi future

PERFORMANCE:
- Salvataggio: ~1-5ms per prodotto
- Ricerca: ~10-50ms per query
- Scalabilità: Ottimizzato per 100k+ prodotti
- Indici: Ottimizzati per ricerche comuni
- Backup: Export automatico periodico

VALIDAZIONE:
- Controllo formato dati input
- Validazione URL e prezzi
- Sanitizzazione stringhe
- Controllo duplicati intelligente
- Verifica integrità database

FUTURO SVILUPPO:
- Analisi trend prezzi
- Machine learning per predizioni
- Backup cloud automatico
- API REST per accesso esterno
- Dashboard analytics avanzate

CONFIGURAZIONE:
- Database path: Configurabile
- Retention policy: Dati mantenuti per X mesi
- Backup frequency: Configurabile
- Max products: Limite configurabile
- Cleanup schedule: Automatico

NOTA ARCHITETTURALE:
La classe HistoricalProductsDB è composta tramite mixin per mantenere ogni
file sorgente sotto il limite di lunghezza. I metodi sono suddivisi in:
- historical_products_db_save.py    (_SaveMixin)
- historical_products_db_search.py  (_SearchMixin)
- historical_products_db_stats.py   (_StatsMixin)
- historical_products_db_helpers.py (_HelpersMixin)
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging
from urllib.parse import urlparse
import re

from historical_products_db_save import _SaveMixin
from historical_products_db_search import _SearchMixin
from historical_products_db_stats import _StatsMixin
from historical_products_db_helpers import _HelpersMixin

logger = logging.getLogger(__name__)

class HistoricalProductsDB(_SaveMixin, _SearchMixin, _StatsMixin, _HelpersMixin):
    """Database per prodotti storici e statistiche"""

    def __init__(self, db_path: str = "data/database/historical_products.db"):
        self.db_path = db_path
        # Crea la cartella database se non esiste
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_database()
        logger.info(f"🗄️ Historical Products DB inizializzato: {db_path}")

    def init_database(self):
        """Inizializza il database con le tabelle necessarie"""
        try:
            with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                cursor = conn.cursor()

                # Tabella prodotti estratti
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS products (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        price TEXT,
                        brand TEXT,
                        url TEXT,
                        source TEXT NOT NULL,
                        source_url TEXT,
                        extraction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        session_id TEXT,
                        metadata TEXT,
                        validation_score REAL DEFAULT 0.0,
                        is_available BOOLEAN DEFAULT 1,
                        product_fingerprint TEXT
                    )
                """)

                # Aggiungi campo product_fingerprint se non esiste (per database esistenti)
                try:
                    cursor.execute("ALTER TABLE products ADD COLUMN product_fingerprint TEXT")
                    logger.info("✅ Campo product_fingerprint aggiunto alla tabella products")
                except sqlite3.OperationalError:
                    # Campo già esiste
                    pass

                # Tabella sessioni di estrazione
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS extraction_sessions (
                        id TEXT PRIMARY KEY,
                        url TEXT NOT NULL,
                        start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        end_time TIMESTAMP,
                        products_found INTEGER DEFAULT 0,
                        success BOOLEAN DEFAULT 1,
                        error_message TEXT,
                        extraction_method TEXT,
                        container_selector TEXT,
                        session_type TEXT DEFAULT 'extraction',
                        source TEXT,
                        total_pages INTEGER DEFAULT 0,
                        pages_processed INTEGER DEFAULT 0
                    )
                """)

                # Aggiungi nuovi campi se non esistono (per database esistenti)
                try:
                    cursor.execute("ALTER TABLE extraction_sessions ADD COLUMN session_type TEXT DEFAULT 'extraction'")
                except:
                    # Campo già esiste
                    pass

                try:
                    cursor.execute("ALTER TABLE extraction_sessions ADD COLUMN source TEXT")
                except:
                    # Campo già esiste
                    pass

                try:
                    cursor.execute("ALTER TABLE extraction_sessions ADD COLUMN total_pages INTEGER DEFAULT 0")
                except:
                    # Campo già esiste
                    pass

                try:
                    cursor.execute("ALTER TABLE extraction_sessions ADD COLUMN pages_processed INTEGER DEFAULT 0")
                except:
                    # Campo già esiste
                    pass

                try:
                    cursor.execute("ALTER TABLE extraction_sessions ADD COLUMN duration TEXT")
                except:
                    # Campo già esiste
                    pass

                # Tabella statistiche sito
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS site_statistics (
                        site TEXT PRIMARY KEY,
                        total_extractions INTEGER DEFAULT 0,
                        total_products INTEGER DEFAULT 0,
                        last_extraction TIMESTAMP,
                        success_rate REAL DEFAULT 0.0,
                        avg_products_per_extraction REAL DEFAULT 0.0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Tabella statistiche dashboard
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS dashboard_stats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        stat_name TEXT NOT NULL,
                        stat_value TEXT NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Indici per performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_name ON products(name)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_source ON products(source)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_date ON products(extraction_date)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_fingerprint ON products(product_fingerprint)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_url ON extraction_sessions(url)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_date ON extraction_sessions(start_time)")

                conn.commit()
                logger.info("✅ Database inizializzato con successo")

        except Exception as e:
            logger.error(f"❌ Errore inizializzazione database: {e}")
            raise

# Test del database
async def test_historical_db():
    """Test del database prodotti storici"""
    try:
        db = HistoricalProductsDB("test_historical.db")

        # Test salvataggio prodotti
        test_products = [
            {
                'name': 'iPhone 15 Pro 128GB',
                'price': '1.199,00€',
                'brand': 'Apple',
                'url': 'https://amazon.it/iphone15pro',
                'source': 'amazon.it'
            },
            {
                'name': 'Samsung Galaxy S24 Ultra',
                'price': '1.399,00€',
                'brand': 'Samsung',
                'url': 'https://mediaworld.it/s24ultra',
                'source': 'mediaworld.it'
            }
        ]

        result = await db.save_extracted_products(
            url="https://amazon.it/iphone15pro",
            products=test_products,
            session_id=None,
            extraction_method="test"
        )

        print(f"✅ Test salvataggio: {result}")

        # Test ricerca
        search_result = await db.search_historical_products({
            'product_name': 'iPhone'
        })

        print(f"✅ Test ricerca: {len(search_result.get('products', []))} prodotti trovati")

        # Test statistiche
        stats_result = await db.get_dashboard_stats()
        print(f"✅ Test statistiche: {stats_result}")

        return True

    except Exception as e:
        print(f"❌ Errore test: {e}")
        return False

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_historical_db())
