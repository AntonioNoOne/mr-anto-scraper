"""
Price Monitor System - Sistema completo di monitoraggio prezzi e competitor analysis

FLUSSO PRINCIPALE:
1. PriceMonitorCore -> Gestisce la logica principale del monitoraggio
2. PriceMonitorDB -> Gestisce tutte le operazioni database
3. Integrazione con scraping_logic.py per il recupero prezzi
4. Integrazione con price_scheduler.py per monitoraggio automatico

DIPENDENZE:
- sqlite3: Database locale per storage dati
- asyncio: Per operazioni asincrone (futuro sviluppo)
- datetime: Gestione timestamp e date
- dataclasses: Modelli dati strutturati
- logging: Sistema di log per debugging

SCRIPT CHE RICHIAMANO QUESTO:
- price_scheduler.py: Per monitoraggio automatico
- scraping_logic.py: Per integrazione con sistema scraping
- unified_scraper.py: Per recupero prezzi competitor
- test_system.py: Per testing del sistema

SCRIPT RICHIAMATI DA QUESTO:
- Nessuno (è un modulo indipendente)
"""

import sqlite3
import json
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Product:
    """
    Modello per prodotto da monitorare
    
    UTILIZZO:
    - Rappresenta un prodotto da tracciare nei competitor
    - Contiene keywords per matching automatico
    - Target price per alert automatici
    """
    id: Optional[int] = None
    name: str = ""
    brand: str = ""
    model: str = ""
    category: str = ""
    keywords: str = ""  # Parole chiave per matching
    target_price: float = 0.0  # Prezzo target per alert
    created_at: Optional[str] = None
    active: bool = True

@dataclass
class CompetitorSite:
    """
    Modello per sito competitor
    
    UTILIZZO:
    - Rappresenta un sito e-commerce da monitorare
    - Contiene info su metodo di scraping da utilizzare
    - Tracking dell'ultimo controllo effettuato
    """
    id: Optional[int] = None
    name: str = ""
    domain: str = ""
    base_url: str = ""
    scraping_method: str = "text_first"  # text_first, smart, selectors
    active: bool = True
    last_check: Optional[str] = None

@dataclass
class ProductMapping:
    """
    Mapping prodotto -> URL specifico su sito competitor
    
    UTILIZZO:
    - Collega un prodotto a un URL specifico su un sito
    - Permette override di selettori per siti specifici
    - Gestisce mapping attivo/inattivo
    """
    id: Optional[int] = None
    product_id: int = 0
    site_id: int = 0
    product_url: str = ""
    selector_overrides: str = "{}"  # JSON con selettori specifici
    active: bool = True

@dataclass
class PriceHistory:
    """
    Storico prezzi
    
    UTILIZZO:
    - Traccia tutti i prezzi rilevati nel tempo
    - Contiene info su disponibilità prodotto
    - Raw data per analisi avanzate
    """
    id: Optional[int] = None
    product_id: int = 0
    site_id: int = 0
    price: float = 0.0
    availability: str = "unknown"  # available, out_of_stock, unknown
    timestamp: Optional[str] = None
    raw_data: str = "{}"  # JSON con dati completi del prodotto

@dataclass
class PriceAlert:
    """
    Alert configurati
    
    UTILIZZO:
    - Configurazione alert automatici
    - Diversi tipi di notifica (prezzo, disponibilità)
    - Metodi di notifica (dashboard, email, telegram)
    """
    id: Optional[int] = None
    product_id: int = 0
    alert_type: str = "price_drop"  # price_drop, price_rise, availability, competitor_lower
    threshold: float = 0.0
    notification_method: str = "dashboard"  # dashboard, email, telegram
    active: bool = True
    created_at: Optional[str] = None

class PriceMonitorDB:
    """
    Database manager per Price Monitor
    
    RESPONSABILITÀ:
    - Gestione completa del database SQLite
    - CRUD operations per tutti i modelli
    - Query complesse per analytics
    - Indici per performance
    
    TABELLE GESTITE:
    - products: Prodotti da monitorare
    - competitor_sites: Siti competitor
    - product_mappings: Mapping prodotto-URL
    - price_history: Storico prezzi
    - price_alerts: Configurazione alert
    """
    
    def __init__(self, db_path: str = "Backend/database/price_monitor.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """
        Inizializza database e tabelle
        
        FLUSSO:
        1. Crea directory database se non esiste
        2. Crea tutte le tabelle con schema completo
        3. Aggiunge indici per performance
        4. Log dell'inizializzazione
        """
        with sqlite3.connect(self.db_path) as conn:
            # Tabella prodotti
            conn.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    brand TEXT,
                    model TEXT,
                    category TEXT,
                    keywords TEXT,
                    target_price REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    active BOOLEAN DEFAULT 1
                )
            """)
            
            # Tabella siti competitor
            conn.execute("""
                CREATE TABLE IF NOT EXISTS competitor_sites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    domain TEXT UNIQUE NOT NULL,
                    base_url TEXT,
                    scraping_method TEXT DEFAULT 'text_first',
                    active BOOLEAN DEFAULT 1,
                    last_check TIMESTAMP
                )
            """)
            
            # Tabella mapping prodotti-siti
            conn.execute("""
                CREATE TABLE IF NOT EXISTS product_mappings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    site_id INTEGER NOT NULL,
                    product_url TEXT NOT NULL,
                    selector_overrides TEXT DEFAULT '{}',
                    active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (product_id) REFERENCES products (id),
                    FOREIGN KEY (site_id) REFERENCES competitor_sites (id),
                    UNIQUE(product_id, site_id)
                )
            """)
            
            # Tabella storico prezzi
            conn.execute("""
                CREATE TABLE IF NOT EXISTS price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    site_id INTEGER NOT NULL,
                    price REAL NOT NULL,
                    availability TEXT DEFAULT 'unknown',
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    raw_data TEXT DEFAULT '{}',
                    FOREIGN KEY (product_id) REFERENCES products (id),
                    FOREIGN KEY (site_id) REFERENCES competitor_sites (id)
                )
            """)
            
            # Tabella alert
            conn.execute("""
                CREATE TABLE IF NOT EXISTS price_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    alert_type TEXT NOT NULL,
                    threshold REAL DEFAULT 0,
                    notification_method TEXT DEFAULT 'dashboard',
                    active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products (id)
                )
            """)
            
            # Indici per performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_price_history_product_site ON price_history (product_id, site_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_price_history_timestamp ON price_history (timestamp)")
            
            conn.commit()
            logger.info("🗄️ Database Price Monitor inizializzato")

    # CRUD Prodotti
    def add_product(self, product: Product) -> int:
        """
        Aggiunge nuovo prodotto
        
        UTILIZZO:
        - Chiamato da PriceMonitorCore.add_product_to_monitor()
        - Chiamato da interfaccia utente per aggiunta manuale
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO products (name, brand, model, category, keywords, target_price)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (product.name, product.brand, product.model, product.category, product.keywords, product.target_price))
            product_id = cursor.lastrowid
            conn.commit()
            logger.info(f"✅ Prodotto aggiunto: {product.name} (ID: {product_id})")
            return product_id

    def get_products(self, active_only: bool = True) -> List[Product]:
        """
        Ottiene lista prodotti
        
        UTILIZZO:
        - Chiamato da PriceMonitorCore.get_monitoring_dashboard_data()
        - Chiamato da interfaccia per visualizzazione prodotti
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            query = "SELECT * FROM products"
            if active_only:
                query += " WHERE active = 1"
            query += " ORDER BY created_at DESC"
            
            rows = conn.execute(query).fetchall()
            return [Product(**dict(row)) for row in rows]

    def get_product(self, product_id: int) -> Optional[Product]:
        """
        Ottiene prodotto specifico
        
        UTILIZZO:
        - Chiamato per operazioni su prodotto specifico
        - Validazione esistenza prodotto
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
            return Product(**dict(row)) if row else None

    # CRUD Competitor Sites
    def add_competitor_site(self, site: CompetitorSite) -> int:
        """
        Aggiunge sito competitor
        
        UTILIZZO:
        - Chiamato da PriceMonitorCore.setup_default_competitors()
        - Chiamato da interfaccia per aggiunta siti manuale
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO competitor_sites (name, domain, base_url, scraping_method)
                VALUES (?, ?, ?, ?)
            """, (site.name, site.domain, site.base_url, site.scraping_method))
            site_id = cursor.lastrowid
            conn.commit()
            logger.info(f"🏪 Sito competitor aggiunto: {site.name} (ID: {site_id})")
            return site_id

    def get_competitor_sites(self, active_only: bool = True) -> List[CompetitorSite]:
        """
        Ottiene lista siti competitor
        
        UTILIZZO:
        - Chiamato da PriceMonitorCore.get_monitoring_dashboard_data()
        - Chiamato da scraping_logic.py per determinare siti da controllare
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            query = "SELECT * FROM competitor_sites"
            if active_only:
                query += " WHERE active = 1"
            query += " ORDER BY name"
            
            rows = conn.execute(query).fetchall()
            return [CompetitorSite(**dict(row)) for row in rows]

    # Product Mappings
    def add_product_mapping(self, mapping: ProductMapping) -> int:
        """
        Aggiunge mapping prodotto-sito
        
        UTILIZZO:
        - Chiamato da PriceMonitorCore.add_product_url_mapping()
        - Chiamato da interfaccia per configurazione manuale mapping
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT OR REPLACE INTO product_mappings 
                (product_id, site_id, product_url, selector_overrides)
                VALUES (?, ?, ?, ?)
            """, (mapping.product_id, mapping.site_id, mapping.product_url, mapping.selector_overrides))
            mapping_id = cursor.lastrowid
            conn.commit()
            logger.info(f"🔗 Mapping aggiunto: Prodotto {mapping.product_id} -> Sito {mapping.site_id}")
            return mapping_id

    def get_product_mappings(self, product_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Ottiene mappings con info complete
        
        UTILIZZO:
        - Chiamato da PriceMonitorCore.get_monitoring_dashboard_data()
        - Chiamato da scraping_logic.py per determinare URL da controllare
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            query = """
                SELECT pm.*, p.name as product_name, cs.name as site_name, cs.domain
                FROM product_mappings pm
                JOIN products p ON pm.product_id = p.id
                JOIN competitor_sites cs ON pm.site_id = cs.id
                WHERE pm.active = 1
            """
            params = ()
            if product_id:
                query += " AND pm.product_id = ?"
                params = (product_id,)
            
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]

    def delete_product_mapping(self, mapping_id: int) -> bool:
        """
        Elimina mapping prodotto-sito
        
        UTILIZZO:
        - Chiamato da interfaccia per rimozione mapping
        - Soft delete (imposta active = 0)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                UPDATE product_mappings 
                SET active = 0 
                WHERE id = ?
            """, (mapping_id,))
            
            success = cursor.rowcount > 0
            conn.commit()
            
            if success:
                logger.info(f"🗑️ Mapping eliminato: ID {mapping_id}")
            
            return success

    # Price History
    def add_price_record(self, price_record: PriceHistory) -> int:
        """
        Aggiunge record prezzo
        
        UTILIZZO:
        - Chiamato da scraping_logic.py dopo ogni scraping
        - Chiamato da unified_scraper.py per salvare risultati
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO price_history (product_id, site_id, price, availability, raw_data)
                VALUES (?, ?, ?, ?, ?)
            """, (price_record.product_id, price_record.site_id, price_record.price, 
                  price_record.availability, price_record.raw_data))
            record_id = cursor.lastrowid
            conn.commit()
            return record_id

    def get_price_history(self, product_id: int, site_id: Optional[int] = None, 
                         days_back: int = 30) -> List[Dict[str, Any]]:
        """
        Ottiene storico prezzi
        
        UTILIZZO:
        - Chiamato per analisi trend prezzi
        - Chiamato da interfaccia per grafici storici
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            query = """
                SELECT ph.*, cs.name as site_name, cs.domain
                FROM price_history ph
                JOIN competitor_sites cs ON ph.site_id = cs.id
                WHERE ph.product_id = ? AND ph.timestamp > datetime('now', '-{} days')
            """.format(days_back)
            
            params = [product_id]
            if site_id:
                query += " AND ph.site_id = ?"
                params.append(site_id)
            
            query += " ORDER BY ph.timestamp DESC"
            
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]

    def get_latest_prices(self, product_id: int) -> List[Dict[str, Any]]:
        """
        Ottiene ultimi prezzi per prodotto da tutti i siti
        
        UTILIZZO:
        - Chiamato da PriceMonitorCore.get_monitoring_dashboard_data()
        - Chiamato per confronto prezzi attuali
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            query = """
                SELECT ph.*, cs.name as site_name, cs.domain
                FROM price_history ph
                JOIN competitor_sites cs ON ph.site_id = cs.id
                WHERE ph.product_id = ? AND ph.id IN (
                    SELECT MAX(id) FROM price_history 
                    WHERE product_id = ? 
                    GROUP BY site_id
                )
                ORDER BY ph.price ASC
            """
            
            rows = conn.execute(query, (product_id, product_id)).fetchall()
            return [dict(row) for row in rows]

    # Analytics
    def get_price_stats(self, product_id: int) -> Dict[str, Any]:
        """
        Statistiche prezzi per prodotto
        
        UTILIZZO:
        - Chiamato da PriceMonitorCore.get_monitoring_dashboard_data()
        - Chiamato per dashboard analytics
        - Calcola min/max/avg e trend prezzi
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Prezzo minimo, massimo, medio
            stats_query = """
                SELECT 
                    MIN(price) as min_price,
                    MAX(price) as max_price,
                    AVG(price) as avg_price,
                    COUNT(*) as total_records
                FROM price_history 
                WHERE product_id = ? AND timestamp > datetime('now', '-30 days')
            """
            
            stats = dict(conn.execute(stats_query, (product_id,)).fetchone())
            
            # Trend ultimo vs precedente
            trend_query = """
                SELECT price, timestamp FROM price_history 
                WHERE product_id = ? 
                ORDER BY timestamp DESC 
                LIMIT 2
            """
            
            trend_rows = conn.execute(trend_query, (product_id,)).fetchall()
            
            if len(trend_rows) >= 2:
                current_price = trend_rows[0]['price']
                previous_price = trend_rows[1]['price']
                price_change = current_price - previous_price
                price_change_percent = (price_change / previous_price) * 100 if previous_price > 0 else 0
                
                stats['current_price'] = current_price
                stats['price_change'] = price_change
                stats['price_change_percent'] = round(price_change_percent, 2)
                stats['trend'] = 'down' if price_change < 0 else 'up' if price_change > 0 else 'stable'
            
            return stats

class PriceMonitorCore:
    """
    Core del sistema Price Monitor
    
    RESPONSABILITÀ:
    - Orchestrazione di tutte le operazioni del sistema
    - Setup automatico dei competitor di default
    - Gestione dashboard e analytics
    - Interfaccia principale per altri moduli
    
    FLUSSO PRINCIPALE:
    1. Inizializzazione con setup automatico competitor
    2. Gestione prodotti da monitorare
    3. Configurazione mapping prodotto-URL
    4. Fornitura dati per dashboard
    
    INTEGRAZIONI:
    - Utilizzato da price_scheduler.py per monitoraggio automatico
    - Utilizzato da scraping_logic.py per determinare cosa controllare
    - Utilizzato da interfaccia utente per operazioni CRUD
    """
    
    def __init__(self):
        self.db = PriceMonitorDB()
        logger.info("🚀 Price Monitor Core inizializzato")
    
    def setup_default_competitors(self):
        """
        Setup siti competitor di default
        
        FLUSSO:
        1. Definisce lista siti e-commerce principali italiani
        2. Aggiunge automaticamente al database
        3. Gestisce duplicati con try/catch
        
        UTILIZZO:
        - Chiamato all'inizializzazione del sistema
        - Chiamato da setup script per reset competitor
        """
        default_sites = [
            CompetitorSite(name="MediaWorld", domain="mediaworld.it", 
                          base_url="https://www.mediaworld.it", scraping_method="text_first"),
            CompetitorSite(name="Unieuro", domain="unieuro.it", 
                          base_url="https://www.unieuro.it", scraping_method="text_first"),
            CompetitorSite(name="Amazon IT", domain="amazon.it", 
                          base_url="https://www.amazon.it", scraping_method="text_first"),
            CompetitorSite(name="Euronics", domain="euronics.it", 
                          base_url="https://www.euronics.it", scraping_method="text_first")
        ]
        
        for site in default_sites:
            try:
                self.db.add_competitor_site(site)
            except sqlite3.IntegrityError:
                # Sito già esistente
                pass
    
    def add_product_to_monitor(self, name: str, brand: str = "", model: str = "", 
                              category: str = "", target_price: float = 0.0) -> int:
        """
        Aggiunge prodotto al monitoraggio
        
        FLUSSO:
        1. Genera keywords automatiche da nome/brand/modello
        2. Crea oggetto Product con tutti i dati
        3. Salva nel database
        4. Ritorna ID del prodotto creato
        
        UTILIZZO:
        - Chiamato da interfaccia utente per aggiunta prodotti
        - Chiamato da script di setup per prodotti di test
        """
        keywords = f"{name} {brand} {model}".strip().lower()
        
        product = Product(
            name=name,
            brand=brand,
            model=model,
            category=category,
            keywords=keywords,
            target_price=target_price
        )
        
        return self.db.add_product(product)
    
    def add_product_url_mapping(self, product_id: int, site_id: int, product_url: str):
        """
        Associa URL specifico a prodotto su sito competitor
        
        FLUSSO:
        1. Crea mapping prodotto-sito-URL
        2. Salva nel database
        3. Permette scraping automatico dell'URL specifico
        
        UTILIZZO:
        - Chiamato da interfaccia per configurazione manuale
        - Chiamato da script di setup per mapping di test
        """
        mapping = ProductMapping(
            product_id=product_id,
            site_id=site_id,
            product_url=product_url
        )
        
        return self.db.add_product_mapping(mapping)
    
    def get_monitoring_dashboard_data(self) -> Dict[str, Any]:
        """
        Dati per dashboard principale
        
        FLUSSO:
        1. Recupera tutti i prodotti attivi
        2. Recupera tutti i siti competitor
        3. Per ogni prodotto, ottiene:
           - Ultimi prezzi da tutti i siti
           - Statistiche prezzi (min/max/avg/trend)
           - Mapping configurati
        4. Ritorna struttura dati completa per dashboard
        
        UTILIZZO:
        - Chiamato da interfaccia web per dashboard principale
        - Chiamato da API per dati JSON
        - Chiamato da script di reporting
        """
        products = self.db.get_products()
        sites = self.db.get_competitor_sites()
        
        dashboard_data = {
            'total_products': len(products),
            'total_sites': len(sites),
            'products': [],
            'sites': [asdict(site) for site in sites]
        }
        
        for product in products:
            product_data = asdict(product)
            product_data['latest_prices'] = self.db.get_latest_prices(product.id)
            product_data['price_stats'] = self.db.get_price_stats(product.id)
            product_data['mappings'] = self.db.get_product_mappings(product.id)
            dashboard_data['products'].append(product_data)
        
        return dashboard_data

# Inizializzazione globale
# Questa istanza viene utilizzata da tutti gli altri moduli del sistema
price_monitor = PriceMonitorCore() 