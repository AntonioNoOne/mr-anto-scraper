#!/usr/bin/env python3

"""
Google Search Integration - Sistema di ricerca venditori alternativi
==================================================================

Sistema per trovare automaticamente venditori alternativi di prodotti
usando Google Search e Google Shopping. Integra con il sistema principale
per fornire confronti più completi.

FLUSSO PRINCIPALE:
1. Riceve prodotto da analizzare
2. Genera query di ricerca ottimizzate
3. Cerca su Google Shopping (Playwright per bypassare blocchi)
4. Estrae risultati sponsorizzati e organici
5. Filtra e valida risultati
6. Restituisce venditori alternativi

DIPENDENZE:
- playwright: Per browser automation e bypass blocchi
- beautifulsoup4: Per parsing HTML
- fast_ai_extractor: Per estrazione prodotti dai risultati
- ai_product_comparator: Per confronto prodotti trovati
- typing: Type hints per documentazione
- json: Serializzazione risultati
- logging: Sistema di log per debugging

SCRIPT CHE RICHIAMANO QUESTO:
- main.py: Endpoint /google-search
- fast_ai_extractor.py: Per ricerca alternativa
- ai_product_comparator.py: Per confronti completi

SCRIPT RICHIAMATI DA QUESTO:
- fast_ai_extractor.py: Per estrazione da URL trovati
- ai_product_comparator.py: Per confronto prodotti

STRUTTURA RISULTATI:
- Lista venditori alternativi trovati
- Prezzi e disponibilità
- Score di rilevanza
- URL diretti ai prodotti
- Metadati ricerca (query usata, timestamp)

FUNZIONALITÀ PRINCIPALI:
- search_alternative_vendors(): Ricerca principale
- generate_search_queries(): Genera query ottimizzate
- search_google_shopping(): Ricerca Google Shopping (Playwright)
- extract_product_info(): Estrae info da risultati
- validate_results(): Valida e filtra risultati
- get_price_comparison(): Confronto prezzi completo

WORKFLOW RICERCA:
1. Riceve prodotto con nome, brand, prezzo
2. Genera query di ricerca intelligenti
3. Cerca su Google Shopping (Playwright per bypass blocchi)
4. Estrae risultati sponsorizzati e organici
5. Valida e filtra risultati rilevanti
6. Confronta prezzi con prodotto originale
7. Restituisce lista venditori alternativi

PERFORMANCE:
- Ricerca Google: ~5-15 secondi per query
- Estrazione prodotti: ~3-8 secondi per sito
- Scalabilità: Ottimizzato per 5-10 risultati
- Rate limiting: Rispetta limiti Google
- Caching: Risultati salvati per riuso

VALIDAZIONE:
- Controllo formato dati input
- Verifica prezzi validi
- Validazione URL trovati
- Controllo rilevanza risultati
- Filtro duplicati e spam

FUTURO SVILUPPO:
- Google Shopping API: Per risultati più precisi
- Machine learning: Per migliorare query
- Cache intelligente: Per performance
- Analisi competitor: Per strategie prezzo
- Notifiche automatiche: Per nuove offerte

CONFIGURAZIONE:
- User-Agent: Browser realistico
- Headers: Per evitare blocchi
- Timeout: Gestione timeout
- Retry: Tentativi multipli
- Proxy: Support proxy (opzionale)

NOTA STRUTTURA (refactor lunghezza file):
I metodi della classe sono suddivisi in mixin in moduli separati per
rispettare il limite di lunghezza dei file. Comportamento invariato:
- google_search_duckduckgo.py  -> _DuckDuckGoMixin (DuckDuckGo + cookie)
- google_search_bing.py        -> _BingMixin (Bing + e-commerce diretto)
- google_search_parsing.py     -> _ParsingMixin (parsing/prezzi/titoli)
- google_search_validation.py  -> _ValidationMixin (validazione/confronto)
"""

import asyncio
import json
import re
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging
import urllib
from urllib.parse import quote_plus, urlparse
import random
import base64
import os

# Import Playwright per browser automation
from playwright.async_api import async_playwright

# Import per parsing HTML
from bs4 import BeautifulSoup

# Import del nostro sistema
from fast_ai_extractor import FastAIExtractor
from ai_product_comparator import AIProductComparator

# Import dei mixin con i metodi estratti (refactor lunghezza file)
from google_search_duckduckgo import _DuckDuckGoMixin
from google_search_bing import _BingMixin
from google_search_parsing import _ParsingMixin
from google_search_validation import _ValidationMixin

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GoogleSearchIntegration(_DuckDuckGoMixin, _BingMixin, _ParsingMixin, _ValidationMixin):
    """Sistema di ricerca Google intelligente per venditori alternativi"""

    def __init__(self):
        # Configurazione
        self.max_results = 50  # Numero massimo di risultati da mostrare
        self.max_products_per_site = 25  # Numero massimo di prodotti per sito (aumentato)
        self.timeout = 60
        self.last_results = []  # Salva gli ultimi risultati per Chat AI

        # User agents per evitare rilevamento bot (migliorati per Render)
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            # User agents più recenti per Render
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]

        # Configurazione per produzione (browser invisibile ma non headless)
        self.production_mode = True  # Cambia a False per sviluppo

        # 🚀 RENDER FIX: Forza headless=True su Render
        self.render_mode = os.environ.get('RENDER', '').lower() == 'true'

        logger.info("🔧 Google Search Integration inizializzato")
        logger.info(f"   • Max risultati: {self.max_results}")
        logger.info(f"   • Timeout: {self.timeout}s")
        logger.info(f"   • Modalità produzione: {self.production_mode}")

        # Inizializza componenti
        self.fast_extractor = FastAIExtractor()
        self.ai_comparator = AIProductComparator()

    async def search_alternative_vendors(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ricerca venditori alternativi usando Google Shopping (Playwright per bypass blocchi)
        """
        try:
            logger.info(f"🔍 Ricerca venditori alternativi per: {product_data.get('name', 'Unknown')}")

            # Valida dati input
            if not self._validate_product_data(product_data):
                return {
                    "success": False,
                    "error": "Dati prodotto non validi",
                    "alternative_vendors": [],
                    "total_results_found": 0
                }

            # Genera query di ricerca
            search_queries = self._generate_search_queries(product_data)
            logger.info(f"🔍 Query generate: {search_queries}")

            # FASE 1: Ricerca venditori alternativi (Playwright per bypass blocchi)
            all_results = []
            for query in search_queries[:2]:  # Max 2 query per evitare blocchi
                logger.info(f"🔍 DEBUG: Iniziando ricerca per query: '{query}'")
                shopping_results = await self._search_google_shopping_playwright(query)
                logger.info(f"🛒 Risultati venditori alternativi per '{query}': {len(shopping_results)}")

                # DEBUG: Log dettagliato dei risultati
                logger.info(f"🛒 DEBUG: === RISULTATI RICEVUTI DA _search_google_shopping_playwright ===")
                for i, result in enumerate(shopping_results):
                    logger.info(f"🛒 DEBUG: Risultato {i+1}: {result.get('name', 'N/A')[:50]} - {result.get('source', 'N/A')} - {result.get('price', 'N/A')}")
                logger.info(f"🛒 DEBUG: === FINE RISULTATI RICEVUTI ===")

                all_results.extend(shopping_results)
                logger.info(f"🔍 DEBUG: Totale risultati accumulati: {len(all_results)}")

                # Delay tra query
                await asyncio.sleep(3)

            # Se non abbiamo risultati, fermati qui
            if not all_results:
                logger.warning("❌ Nessun risultato trovato, ricerca terminata")
                return {
                    "success": True,
                    "original_product": product_data,
                    "alternative_vendors": [],
                    "comparison_results": {},
                    "search_queries": search_queries,
                    "total_results_found": 0,
                    "validated_results": [],
                    "extracted_products": [],
                    "timestamp": datetime.now().isoformat(),
                    "message": "Nessun venditore alternativo trovato"
                }

            # FASE 2: Valida e filtra risultati
            logger.info(f"🔍 DEBUG: === INIZIO VALIDAZIONE ===")
            logger.info(f"🔍 DEBUG: Risultati da validare: {len(all_results)}")
            validated_results = self._validate_and_filter_results(all_results, product_data)
            logger.info(f"✅ Risultati validati: {len(validated_results)}")
            logger.info(f"🔍 DEBUG: === FINE VALIDAZIONE ===")

            # FASE 2.5: arricchimento prezzi dalle pagine venditore (i prezzi non
            # sono negli snippet di ricerca). Fetch dei top risultati con Crawl4AI.
            validated_results = await self._enrich_prices_from_pages(validated_results, max_pages=6)

            logger.info(f"🔍 DEBUG: Riepilogo risultati:")
            logger.info(f"🔍 DEBUG: - Totale trovati: {len(all_results)}")
            logger.info(f"🔍 DEBUG: - Validati: {len(validated_results)}")
            logger.info(f"🔍 DEBUG: - Limite massimo: {self.max_results}")

            # Debug dettagliato per ogni risultato validato
            for i, result in enumerate(validated_results):
                score = result.get('validation_score', 0)
                logger.info(f"🔍 DEBUG: Risultato {i+1}: '{result.get('name', 'N/A')[:50]}' - Score: {score}")

            logger.info(f"🔍 DEBUG: Scores finali: {[r.get('validation_score', 0) for r in validated_results]}")

            # Se non abbiamo risultati validi, fermati qui
            if not validated_results:
                logger.warning("❌ Nessun risultato valido, ricerca terminata")
                return {
                    "success": True,
                    "original_product": product_data,
                    "alternative_vendors": [],
                    "comparison_results": {},
                    "search_queries": search_queries,
                    "total_results_found": len(all_results),
                    "validated_results": [],
                    "extracted_products": [],
                    "timestamp": datetime.now().isoformat(),
                    "message": "Nessun venditore alternativo valido trovato"
                }

            # FASE 3: Formatta risultati finali
            alternative_vendors = self._format_alternative_vendors(validated_results)

            # FASE 4: Confronta prezzi
            comparison_results = await self._compare_prices(product_data, validated_results)

            # Salva gli ultimi risultati per Chat AI
            self.last_results = alternative_vendors

            logger.info(f"✅ Ricerca completata: {len(alternative_vendors)} venditori trovati")

            return {
                "success": True,
                "original_product": product_data,
                "alternative_vendors": alternative_vendors,
                "comparison_results": comparison_results,
                "search_queries": search_queries,
                "total_results_found": len(all_results),
                "validated_results": validated_results,
                "extracted_products": validated_results,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Errore ricerca venditori alternativi: {e}")
            return {
                "success": False,
                "error": str(e),
                "alternative_vendors": [],
                "total_results_found": 0
            }

    def _validate_product_data(self, product_data: Dict[str, Any]) -> bool:
        """Valida i dati del prodotto"""
        if not product_data:
            return False

        # Richiede almeno il nome del prodotto
        if not product_data.get('name'):
            return False

        return True

    def _generate_search_queries(self, product_data: Dict[str, Any]) -> List[str]:
        """Genera query di ricerca ottimizzate"""
        name = product_data.get('name', '').strip()
        brand = product_data.get('brand', '').strip()

        queries = []

        # Query base con nome prodotto
        if name:
            queries.append(name)
            queries.append(f'"{name}"')

        # Query con brand se disponibile
        if brand and brand.lower() not in name.lower():
            queries.append(f'"{brand} {name}"')

        # Rimuovi duplicati e limita
        unique_queries = list(dict.fromkeys(queries))
        return unique_queries[:2]  # Max 2 query per evitare blocchi

    async def _search_google_shopping_playwright(self, query: str) -> List[Dict[str, Any]]:
        """Ricerca su motori di ricerca alternativi usando Playwright per bypassare blocchi"""
        results = []

        try:
            logger.info(f"🔍 Ricerca venditori alternativi con Playwright: {query}")

            # STRATEGIA 1: DuckDuckGo via libreria ddgs (veloce, no browser, no blocchi)
            logger.info("🦆 === STRATEGIA 1: DuckDuckGo (ddgs) ===")
            results = await self._try_duckduckgo_ddgs(query)
            logger.info(f"🦆 Risultati DuckDuckGo (ddgs): {len(results)}")

            # STRATEGIA 2 (fallback): SPA shopping DuckDuckGo via browser
            if not results:
                logger.info("🦆 === STRATEGIA 2: DuckDuckGo Shopping (browser) ===")
                results = await self._try_duckduckgo_shopping(query)
                logger.info(f"🦆 Risultati DuckDuckGo (browser): {len(results)}")

            # Se non abbiamo risultati, STRATEGIA 3: Prova Bing Shopping
            if not results:
                logger.info("🔄 === STRATEGIA 3: Bing Shopping ===")
                results = await self._try_bing_shopping(query)
                logger.info(f"🔍 Risultati Bing: {len(results)}")

            # Se ancora niente, STRATEGIA 3: Prova ricerca diretta sui siti e-commerce
            if not results:
                logger.info("🔄 === STRATEGIA 3: Ricerca diretta e-commerce ===")
                results = await self._try_direct_ecommerce_search(query)
                logger.info(f"🛒 Risultati ricerca diretta: {len(results)}")

            logger.info(f"✅ Ricerca completata. Totale risultati: {len(results)}")
            return results

        except Exception as e:
            logger.error(f"❌ Errore ricerca venditori alternativi per '{query}': {e}")
            # In caso di errore, ritorna lista vuota
            return []

# Istanza globale
google_search = GoogleSearchIntegration()

# Funzione standalone per compatibilità
async def search_alternative_vendors(product_data: Dict[str, Any]) -> Dict[str, Any]:
    """Funzione standalone per ricerca venditori alternativi"""
    return await google_search.search_alternative_vendors(product_data)
