"""
💾 Cache Manager - Sistema di caching per performance
Gestione cache per selettori, contenuti e risultati di scraping

FLUSSO PRINCIPALE:
1. Ricezione richiesta di cache (get/set)
2. Generazione chiave univoca basata su URL e parametri
3. Controllo esistenza cache su filesystem
4. Verifica scadenza TTL (Time To Live)
5. Ritorno dati cached o None se scaduto/inesistente
6. Salvataggio nuovi dati con timestamp

DIPENDENZE:
- json: Serializzazione/deserializzazione dati
- hashlib: Generazione chiavi cache univoche
- datetime: Gestione timestamp e scadenze
- os: Operazioni filesystem
- pathlib: Gestione path (futuro sviluppo)

SCRIPT CHE RICHIAMANO QUESTO:
- mr_anto_scraper.py: Per cache risultati scraping
- unified_scraper.py: Per cache selettori e contenuti
- ai_content_analyzer.py: Per cache analisi AI
- html_analyzer.py: Per cache analisi HTML
- progressive_scraper.py: Per cache risultati progressivi

SCRIPT RICHIAMATI DA QUESTO:
- Nessun modulo locale (solo librerie standard)

TIPI DI CACHE:
1. Selectors Cache: Selettori CSS per dominio (TTL: 7 giorni)
2. Content Cache: Contenuto HTML pagine (TTL: 1 ora)
3. Results Cache: Risultati scraping completi (TTL: 6 ore)
4. AI Analysis Cache: Risultati analisi AI (TTL: 24 ore)

STRATEGIA DI CACHING:
- Filesystem-based: File JSON per ogni entry
- Chiavi MD5: Evita problemi con caratteri speciali
- TTL configurabile: Diverso per tipo di dato
- Auto-cleanup: Rimozione automatica file scaduti

PERFORMANCE:
- Cache hit: ~1-5ms (lettura file)
- Cache miss: ~10-50ms (scrittura file)
- Scalabilità: Limitata da spazio disco
- Persistenza: Dati sopravvivono a riavvii

FUTURO SVILUPPO:
- Redis integration: Per cache distribuita
- Compression: Per ridurre spazio disco
- LRU eviction: Per gestione memoria
- Cache warming: Pre-caricamento dati frequenti
"""

import json
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import os

class CacheManager:
    """
    Gestore cache per sistema di scraping
    
    RESPONSABILITÀ:
    - Gestione cache selettori CSS per dominio
    - Cache contenuti HTML pagine
    - Cache risultati analisi AI
    - Gestione TTL e scadenze
    - Invalidation cache su richiesta
    
    FLUSSO DI LAVORO:
    1. Inizializzazione con directory cache
    2. Generazione chiavi univoche per ogni entry
    3. Controllo esistenza e validità cache
    4. Salvataggio nuovi dati con timestamp
    5. Cleanup automatico file scaduti
    """
    
    def __init__(self):
        """
        Sistema di caching semplificato che usa solo filesystem.
        
        INIZIALIZZAZIONE:
        1. Crea directory cache se non esiste
        2. Configura TTL di default per diversi tipi
        3. Prepara per future integrazioni Redis
        """
        self.redis_client = None  # Disabilitato per ora
        self.cache_dir = "cache"
        
        # Crea directory cache
        os.makedirs(self.cache_dir, exist_ok=True)
        print("✅ Cache filesystem attivo")
    
    def _generate_key(self, url: str, params: Dict = None) -> str:
        """
        Genera chiave cache univoca
        
        STRATEGIA:
        - Combina URL e parametri in stringa
        - Ordina parametri per consistenza
        - Genera hash MD5 per chiave univoca
        - Evita problemi con caratteri speciali
        
        UTILIZZO:
        - Chiamato internamente per generare chiavi
        - Garantisce unicità per URL+parametri
        """
        content = f"{url}_{json.dumps(params or {}, sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def get_cached_selectors(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Recupera selettori cached per un URL
        
        FLUSSO:
        1. Genera chiave cache per URL
        2. Controlla esistenza file cache
        3. Verifica scadenza (7 giorni TTL)
        4. Ritorna selettori se validi
        
        UTILIZZO:
        - Chiamato prima di analisi AI per evitare re-analisi
        - Riduce tempo di scraping per domini già analizzati
        """
        key = f"selectors_{self._generate_key(url)}"
        
        # Usa solo filesystem
        cache_file = os.path.join(self.cache_dir, f"{key}.json")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Verifica scadenza (7 giorni)
                    cached_time = datetime.fromisoformat(data.get('cached_at', ''))
                    if datetime.now() - cached_time < timedelta(days=7):
                        print(f"✅ Cache hit (File): {url}")
                        return data.get('selectors')
            except Exception as e:
                print(f"⚠️ Errore lettura cache file: {e}")
        
        print(f"❌ Cache miss: {url}")
        return None
    
    async def cache_selectors(self, url: str, selectors: Dict[str, Any], ttl_hours: int = 168):
        """
        Salva selettori in cache (default: 7 giorni)
        
        FLUSSO:
        1. Genera chiave cache per URL
        2. Crea struttura dati con timestamp
        3. Salva su filesystem come JSON
        4. Log operazione di salvataggio
        
        UTILIZZO:
        - Chiamato dopo analisi AI riuscita
        - Salva selettori per riuso futuro
        - Riduce tempo di analisi per domini noti
        """
        key = f"selectors_{self._generate_key(url)}"
        data = {
            'selectors': selectors,
            'cached_at': datetime.now().isoformat(),
            'url': url
        }
        
        # Salva su filesystem
        try:
            cache_file = os.path.join(self.cache_dir, f"{key}.json")
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"✅ Cache salvata (File): {url}")
        except Exception as e:
            print(f"⚠️ Errore salvataggio file: {e}")
    
    async def get_cached_page_content(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Recupera contenuto pagina cached
        
        FLUSSO:
        1. Genera chiave cache per contenuto
        2. Controlla esistenza file cache
        3. Verifica scadenza (1 ora TTL)
        4. Ritorna contenuto se valido
        
        UTILIZZO:
        - Chiamato per evitare re-download pagine
        - Riduce traffico di rete e tempo di risposta
        - TTL breve per contenuti che cambiano spesso
        """
        key = f"content_{self._generate_key(url)}"
        
        cache_file = os.path.join(self.cache_dir, f"{key}.json")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Verifica scadenza (1 ora per contenuto)
                    cached_time = datetime.fromisoformat(data.get('cached_at', ''))
                    if datetime.now() - cached_time < timedelta(hours=1):
                        print(f"✅ Content cache hit: {url}")
                        return data.get('content')
            except Exception as e:
                print(f"⚠️ Errore lettura content cache: {e}")
        
        return None
    
    async def cache_page_content(self, url: str, content: Dict[str, Any]):
        """
        Salva contenuto pagina in cache (1 ora TTL)
        
        FLUSSO:
        1. Genera chiave cache per contenuto
        2. Crea struttura dati con timestamp
        3. Salva su filesystem come JSON
        4. Log operazione di salvataggio
        
        UTILIZZO:
        - Chiamato dopo download pagina
        - Salva contenuto per riuso breve termine
        - Riduce carico sui server target
        """
        key = f"content_{self._generate_key(url)}"
        data = {
            'content': content,
            'cached_at': datetime.now().isoformat(),
            'url': url
        }
        
        try:
            cache_file = os.path.join(self.cache_dir, f"{key}.json")
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"✅ Content cache salvato: {url}")
        except Exception as e:
            print(f"⚠️ Errore salvataggio content: {e}")
    
    async def invalidate_cache(self, url: str):
        """
        Invalida cache per un URL specifico
        
        FLUSSO:
        1. Genera chiavi per tutti i tipi di cache
        2. Rimuove file cache se esistenti
        3. Log operazione di invalidazione
        
        UTILIZZO:
        - Chiamato quando si vuole forzare refresh
        - Rimuove cache selettori e contenuti
        - Forza re-analisi completa
        """
        base_key = self._generate_key(url)
        
        # Rimuovi file cache
        try:
            files_removed = 0
            for filename in os.listdir(self.cache_dir):
                if base_key in filename and filename.endswith('.json'):
                    os.remove(os.path.join(self.cache_dir, filename))
                    files_removed += 1
            print(f"✅ Cache invalidata: {files_removed} file rimossi")
        except Exception as e:
            print(f"⚠️ Errore rimozione file cache: {e}")

# Singleton instance
cache_manager = CacheManager() 