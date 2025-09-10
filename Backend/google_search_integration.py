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

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GoogleSearchIntegration:
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
            
            # STRATEGIA 1: Prova DuckDuckGo Shopping (Google rimosso per blocchi persistenti)
            logger.info("🦆 === STRATEGIA 1: DuckDuckGo Shopping ===")
            results = await self._try_duckduckgo_shopping(query)
            logger.info(f"🦆 Risultati DuckDuckGo: {len(results)}")
            
            # Se non abbiamo risultati, STRATEGIA 2: Prova Bing Shopping
            if not results:
                logger.info("🔄 === STRATEGIA 2: Bing Shopping ===")
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



    async def _handle_cookie_banners(self, page):
        """Gestisce i banner cookie invece di confonderli con captcha"""
        try:
            logger.info("🍪 Gestione banner cookie...")
            
            # Attesa per caricamento banner
            await page.wait_for_timeout(2000)
            
            # Selettori comuni per banner cookie
            cookie_selectors = [
                
                # Generici
                'button:has-text("Accept all")',
                'button:has-text("Accept All")',
                'button:has-text("Accetta tutto")',
                'button:has-text("I agree")',
                'button:has-text("OK")',
                'button:has-text("Got it")',
                'button:has-text("Continue")',
                'button:has-text("Proceed")',
                'button:has-text("Allow all")',
                'button:has-text("Consenti tutto")',
                'button[data-testid*="accept"]',
                'button[data-testid*="cookie"]',
                'button[class*="accept"]',
                'button[class*="cookie"]',
                'button[id*="accept"]',
                'button[id*="cookie"]',
                'div[role="button"]:has-text("Accept")',
                'div[role="button"]:has-text("Accetta")',
                # Bing specific selectors
                '[id*="cookie"] button',
                '[class*="cookie"] button',
                '[data-testid*="cookie"] button',
                '[aria-label*="cookie"] button'
            ]
            
            for selector in cookie_selectors:
                try:
                    # Cerca elemento banner cookie
                    cookie_element = await page.query_selector(selector)
                    if cookie_element:
                        logger.info(f"✅ Trovato banner cookie: {selector}")
                        
                        # Clicca il banner
                        await cookie_element.click()
                        logger.info("✅ Cliccato banner cookie")
                        
                        # Attesa per chiusura banner
                        await page.wait_for_timeout(2000)
                        break
                    
                except Exception as e:
                    logger.debug(f"⚠️ Errore con selettore cookie {selector}: {e}")
                    continue
            
            # Prova anche a cercare banner generici
            try:
                # Cerca qualsiasi pulsante che potrebbe essere per i cookie
                buttons = await page.query_selector_all('button')
                for button in buttons[:10]:  # Controlla i primi 10 pulsanti
                    try:
                        button_text = await button.text_content()
                        if button_text and any(word in button_text.lower() for word in ['accept', 'accetta', 'ok', 'continue', 'proceed', 'allow', 'consenti']):
                            logger.info(f"✅ Trovato pulsante cookie generico: {button_text}")
                            await button.click()
                            logger.info("✅ Cliccato pulsante cookie generico")
                            await page.wait_for_timeout(2000)
                            break
                    except:
                        continue
            except Exception as e:
                logger.debug(f"⚠️ Errore ricerca pulsanti cookie generici: {e}")
            
            logger.info("🍪 Gestione banner cookie completata")
            
            # Tentativo specifico per Bing
            try:
                # Cerca banner cookie specifici di Bing
                bing_cookie_selectors = [
                    'button[aria-label*="Accept"]',
                    'button[aria-label*="Accept all"]',
                    'button[aria-label*="I agree"]',
                    'button[aria-label*="OK"]',
                    'button[aria-label*="Continue"]',
                    'button[aria-label*="Got it"]',
                    'button[aria-label*="Proceed"]',
                    'button[aria-label*="Allow all"]',
                    'button[aria-label*="Consenti tutto"]',
                    'button[aria-label*="Accetta tutto"]',
                    'button[aria-label*="Accetta"]'
                ]
                
                for selector in bing_cookie_selectors:
                    try:
                        element = await page.query_selector(selector)
                        if element:
                            logger.info(f"✅ Trovato banner cookie Bing: {selector}")
                            await element.click()
                            logger.info("✅ Cliccato banner cookie Bing")
                            await page.wait_for_timeout(2000)
                            break
                    except:
                        continue
            except Exception as e:
                logger.debug(f"⚠️ Errore gestione cookie Bing specifici: {e}")
            
        except Exception as e:
            logger.error(f"❌ Errore gestione banner cookie: {e}")

    async def _try_duckduckgo_shopping(self, query: str) -> List[Dict[str, Any]]:
        """Prova DuckDuckGo Shopping (meno restrittivo)"""
        try:
            logger.info(f"🦆 Ricerca DuckDuckGo Shopping: {query}")

            # URL DuckDuckGo Shopping
            encoded_query = quote_plus(query)
            url = f"https://duckduckgo.com/?q={encoded_query}+shopping&t=h_&iax=shopping&ia=shopping"
            logger.info(f"🦆 DEBUG: URL DuckDuckGo: {url}")

            logger.info("🦆 DEBUG: === APERTURA BROWSER DUCKDUCKGO ===")
            async with async_playwright() as p:
                # Configurazione browser per produzione (invisibile ma non headless)
                if self.production_mode:
                    # Modalità produzione: browser invisibile ma non headless
                    browser = await p.chromium.launch(
                        headless=self.render_mode,  # Headless su Render, visibile in produzione normale
                        args=[
                            '--no-sandbox',
                            '--disable-blink-features=AutomationControlled',
                            '--disable-web-security',
                            '--disable-features=VizDisplayCompositor',
                            '--disable-dev-shm-usage',
                            '--disable-gpu',
                            '--no-first-run',
                            '--no-default-browser-check',
                            '--disable-default-apps',
                            '--disable-extensions',
                            '--disable-plugins',
                            '--disable-images',
                            '--window-size=1,1',  # Finestra minima
                            '--window-position=9999,9999',  # Fuori schermo
                            '--user-agent=' + random.choice(self.user_agents)
                        ]
                    )
                else:
                    # Modalità sviluppo: browser visibile
                    browser = await p.chromium.launch(
                        headless=False,
                        args=[
                            '--no-sandbox',
                            '--disable-blink-features=AutomationControlled',
                            '--disable-web-security',
                            '--disable-features=VizDisplayCompositor',
                            '--disable-dev-shm-usage',
                            '--disable-gpu',
                            '--no-first-run',
                            '--no-default-browser-check',
                            '--disable-default-apps',
                            '--disable-extensions',
                            '--disable-plugins',
                            '--disable-images',
                            '--user-agent=' + random.choice(self.user_agents)
                        ]
                    )
                logger.info("🦆 DEBUG: Browser DuckDuckGo aperto")

                page = await browser.new_page()
                
                # Aggiungi headers anti-detection per Render
                await page.set_extra_http_headers({
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'it-IT,it;q=0.9,en;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Cache-Control': 'max-age=0'
                })
                
                # Imposta viewport più realistico
                await page.set_viewport_size({"width": 1366, "height": 768})
                
                # Aggiungi comportamento umano
                await page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined,
                    });
                """)
                
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                
                # Delay random per simulare comportamento umano su Render
                if self.render_mode:
                    delay = random.uniform(5, 8)  # 5-8 secondi su Render per evitare anti-bot
                    logger.info(f"🦆 DEBUG: Delay anti-bot su Render: {delay:.1f}s")
                else:
                    delay = random.uniform(2, 4)  # 2-4 secondi in locale
                
                await page.wait_for_timeout(int(delay * 1000))

                # Gestione banner cookie
                await self._handle_cookie_banners(page)

                # DEBUG: Simula scroll umano per caricare più contenuti
                logger.info("🦆 DEBUG: Iniziando scroll per caricare contenuti...")
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight/3)")
                await page.wait_for_timeout(3000)
                logger.info("🦆 DEBUG: Scroll 1/3 completato")

                await page.evaluate("window.scrollTo(0, document.body.scrollHeight*2/3)")
                await page.wait_for_timeout(2000)
                logger.info("🦆 DEBUG: Scroll 2/3 completato")

                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(2000)
                logger.info("🦆 DEBUG: Scroll completo")

                # Estrai risultati DuckDuckGo
                html_content = await page.content()
                logger.info(f"🦆 DEBUG: HTML estratto, lunghezza: {len(html_content)} caratteri")
                soup = BeautifulSoup(html_content, 'html.parser')

            results = []

            # DEBUG: Log della struttura HTML per capire cosa c'è
            logger.info(f"🦆 DEBUG: Analizzando HTML DuckDuckGo...")

            # Cerca risultati con selettori più generici
            all_links = soup.find_all('a', href=True)
            logger.info(f"🦆 DEBUG: Trovati {len(all_links)} link totali")

            # DEBUG: Log di TUTTI i link per capire la struttura (versione compatta)
            logger.info("🦆 DEBUG: === LISTA COMPLETA DEI LINK ===")
            for i, link in enumerate(all_links):
                href = link.get('href', '')
                text = link.get_text(strip=True)
                if text and href:
                    # Accorcia link e testo per log più puliti
                    short_href = href[:80] + "..." if len(href) > 80 else href
                    short_text = text[:50] + "..." if len(text) > 50 else text
                    logger.info(f"🦆 DEBUG: Link {i+1}: '{short_text}' -> {short_href}")

            logger.info("🦆 DEBUG: === FINE LISTA LINK ===")

            # Cerca anche div e span che potrebbero contenere prodotti
            all_divs = soup.find_all('div')
            all_spans = soup.find_all('span')
            logger.info(f"🦆 DEBUG: Trovati {len(all_divs)} div e {len(all_spans)} span")

            # Cerca elementi che potrebbero essere prodotti
            product_elements = []

            # 1. Cerca link che puntano a siti e-commerce
            for link in all_links:
                href = link.get('href', '')
                text = link.get_text(strip=True)

                # Miglioramento: cerca link che puntano a siti e-commerce reali
                if any(site in href.lower() for site in ['amazon', 'mediaworld', 'unieuro', 'carrefour', 'conad', 'ebay', 'shop', 'store', 'buy', 'product']):
                    product_elements.append(('link', link))
                    logger.info(f"🦆 DEBUG: Link shopping trovato: {text[:50]} -> {href}")

            # 2. Cerca div che contengono prezzi
            logger.info("🦆 DEBUG: === CERCANDO DIV CON PREZZI ===")
            for div in all_divs:
                text = div.get_text(strip=True)
                if '€' in text and len(text) > 20 and len(text) < 200:
                    product_elements.append(('div', div))
                    logger.info(f"🦆 DEBUG: Div con prezzo trovato: {text[:100]}")

            # 3. Cerca span che contengono prezzi
            logger.info("🦆 DEBUG: === CERCANDO SPAN CON PREZZI ===")
            for span in all_spans:
                text = span.get_text(strip=True)
                if '€' in text and len(text) > 10 and len(text) < 100:
                    product_elements.append(('span', span))
                    logger.info(f"🦆 DEBUG: Span con prezzo trovato: {text[:50]}")

            logger.info(f"🦆 DEBUG: === TROVATI {len(product_elements)} ELEMENTI POTENZIALI ===")
            logger.info(f"🦆 DEBUG: Limite prodotti per sito: {self.max_products_per_site}")

            # Estrai informazioni da tutti gli elementi trovati
            elements_to_process = min(len(product_elements), self.max_products_per_site)
            logger.info(f"🦆 DEBUG: Processando {elements_to_process} elementi su {len(product_elements)} trovati")
            
            for element_type, element in product_elements[:self.max_products_per_site]:  # Limita risultati
                try:
                    if element_type == 'link':
                        title = element.get_text(strip=True)
                        url = element.get('href')

                        # Miglioramento: cerca URL reali dei prodotti
                        if url.startswith('/'):
                            # URL relativo, cerca di costruire URL completo
                            if 'amazon' in url.lower():
                                url = f"https://www.amazon.it{url}"
                            elif 'mediaworld' in url.lower():
                                url = f"https://www.mediaworld.it{url}"
                            elif 'unieuro' in url.lower():
                                url = f"https://www.unieuro.it{url}"
                            else:
                                url = f"https://duckduckgo.com{url}"

                        # 1. Usa direttamente gli URL di tracking DuckDuckGo (funzionano!)
                        if url and ('duckduckgo.com/y.js' in url or 'links.duckduckgo.com' in url):
                            # NON decodificare! Gli URL di tracking funzionano direttamente
                            logger.info(f"🦆 DEBUG: === URL TRACKING DUCKDUCKGO TROVATO ===")
                            logger.info(f"🦆 DEBUG: URL ORIGINALE: {url}")
                            logger.info(f"🦆 DEBUG: LUNGHEZZA: {len(url)}")
                            logger.info(f"🦆 DEBUG: CONTIENE 'spld': {'spld' in url}")
                            logger.info(f"🦆 DEBUG: CONTIENE 'uddg': {'uddg' in url}")
                            logger.info(f"🦆 DEBUG: === FINE DEBUG URL ===")
                            # L'URL rimane così com'è - DuckDuckGo lo decodificherà automaticamente
                        
                        # 2. Gestisci URL relativi (che iniziano con '/')
                        elif url and url.startswith('/'):
                            # Un link relativo su DuckDuckGo non è un prodotto, lo saltiamo
                            logger.info(f"🦆 DEBUG: Trovato URL relativo, lo scarto: {url}")
                            continue

                        # Miglioramento: estrai prezzo dal titolo se presente
                        price_text = "Prezzo non disponibile"
                        
                        # DEBUG: Log del testo completo per capire cosa contiene
                        logger.info(f"🦆 DEBUG: === ESTRAZIONE PREZZO ===")
                        logger.info(f"🦆 DEBUG: Titolo completo: '{title}'")
                        
                        # Pattern più robusti per prezzi
                        price_patterns = [
                            r'(\d+[.,]\d+)\s*€',  # €123,45
                            r'€\s*(\d+[.,]\d+)',  # € 123,45
                            r'(\d+)\s*€',         # 123€
                            r'€\s*(\d+)',         # € 123
                            r'(\d+[.,]\d+)\s*EUR', # 123,45 EUR
                            r'EUR\s*(\d+[.,]\d+)'  # EUR 123,45
                        ]
                        
                        # Prova prima nel titolo
                        for i, pattern in enumerate(price_patterns):
                            price_match = re.search(pattern, title, re.IGNORECASE)
                            if price_match:
                                price_text = f"€{price_match.group(1)}"
                                logger.info(f"🦆 DEBUG: ✅ Prezzo estratto dal titolo con pattern {i+1}: '{price_match.group(0)}' -> {price_text}")
                                break
                            else:
                                logger.info(f"🦆 DEBUG: ❌ Pattern {i+1} non trovato nel titolo")
                        
                        # Se non trovato nel titolo, prova nel parent
                        if price_text == "Prezzo non disponibile":
                            parent = element.parent
                            if parent:
                                parent_text = parent.get_text()
                                logger.info(f"🦆 DEBUG: Cercando prezzo nel parent, testo: '{parent_text[:100]}...'")
                                
                                for i, pattern in enumerate(price_patterns):
                                    price_match = re.search(pattern, parent_text, re.IGNORECASE)
                                    if price_match:
                                        price_text = f"€{price_match.group(1)}"
                                        logger.info(f"🦆 DEBUG: ✅ Prezzo estratto dal parent con pattern {i+1}: '{price_match.group(0)}' -> {price_text}")
                                        break
                                    else:
                                        logger.info(f"🦆 DEBUG: ❌ Pattern {i+1} non trovato nel parent")
                        
                        logger.info(f"🦆 DEBUG: Prezzo finale estratto: '{price_text}'")
                        logger.info(f"🦆 DEBUG: === FINE ESTRAZIONE PREZZO ===")

                        if title and url and len(title) > 10:  # Filtra titoli troppo corti
                            title = self._clean_product_title(title)  # Pulisci il titolo
                            results.append({
                                'name': title,
                                'price': price_text,
                                'price_numeric': self._extract_price_from_text(price_text),
                                'url': url,
                                'site': self._extract_site_from_url(url),
                                'description': f"Risultato DuckDuckGo per {query}",
                                'source': 'duckduckgo_shopping',
                                'query': query,
                                'validation_score': 0.7
                            })
                            logger.info(f"🦆 DEBUG: === RISULTATO AGGIUNTO ===")
                            logger.info(f"🦆 DEBUG: Titolo: {title[:50]}")
                            logger.info(f"🦆 DEBUG: URL SALVATO: {url}")
                            logger.info(f"🦆 DEBUG: LUNGHEZZA URL: {len(url)}")
                            logger.info(f"🦆 DEBUG: === FINE RISULTATO ===")

                    elif element_type in ['div', 'span']:
                        text = element.get_text(strip=True)

                        # Miglioramento: estrai prezzo e titolo dal testo
                        price_match = re.search(r'(\d+[.,]\d+)\s*€', text)
                        if price_match:
                            price_text = f"€{price_match.group(1)}"

                            # Cerca un titolo nel testo (prima del prezzo)
                            lines = text.split('\n')
                            title = ""
                            for line in lines:
                                if '€' not in line and len(line.strip()) > 10:
                                    title = line.strip()
                                    break

                            if not title:
                                title = text[:50]  # Usa i primi 50 caratteri come titolo

                            title = self._clean_product_title(title)  # Pulisci il titolo

                            # Miglioramento: cerca un link associato a questo elemento
                            url = f"https://duckduckgo.com/?q={quote_plus(query)}"

                            # Cerca un link nelle vicinanze
                            parent = element.parent
                            if parent:
                                nearby_link = parent.find('a', href=True)
                                if nearby_link:
                                    url = nearby_link.get('href')
                                    if url.startswith('/'):
                                        url = f"https://duckduckgo.com{url}"

                            results.append({
                                'name': title,
                                'price': price_text,
                                'price_numeric': self._extract_price_from_text(price_text),
                                'url': url,
                                'site': self._extract_site_from_url(url),
                                'description': f"Risultato DuckDuckGo per {query}",
                                'source': 'duckduckgo_shopping',
                                'query': query,
                                'validation_score': 0.6
                            })
                            logger.info(f"🦆 DEBUG: Aggiunto risultato {element_type}: {title[:50]} -> {url}")

                except Exception as e:
                    logger.error(f"🦆 DEBUG: Errore estrazione {element_type}: {e}")
                continue

            logger.info("🦆 DEBUG: === CHIUSURA BROWSER DUCKDUCKGO ===")
            await browser.close()
            logger.info("🦆 DEBUG: Browser DuckDuckGo chiuso")

            logger.info(f"🦆 DEBUG: === RISULTATI FINALI DUCKDUCKGO ===")
            for i, result in enumerate(results):
                logger.info(f"🦆 DEBUG: === RISULTATO FINALE {i+1} ===")
                logger.info(f"🦆 DEBUG: Nome: {result.get('name', 'N/A')[:50]}")
                logger.info(f"🦆 DEBUG: Prezzo: {result.get('price', 'N/A')}")
                logger.info(f"🦆 DEBUG: URL FINALE: {result.get('url', 'N/A')}")
                logger.info(f"🦆 DEBUG: Lunghezza URL: {len(result.get('url', ''))}")
                logger.info(f"🦆 DEBUG: === FINE RISULTATO {i+1} ===")
            logger.info(f"🦆 DEBUG: === FINE RISULTATI DUCKDUCKGO ===")
            logger.info(f"🦆 Risultati DuckDuckGo: {len(results)}")
            logger.info(f"🦆 DEBUG: Risultati finali DuckDuckGo:")
            for i, result in enumerate(results):
                name = result.get('name', 'N/A')[:40] + "..." if len(result.get('name', '')) > 40 else result.get('name', 'N/A')
                price = result.get('price', 'N/A')
                site = result.get('site', 'N/A')
                logger.info(f"🦆 DEBUG: Risultato {i+1}: {name} - {price} - {site}")
            return results

        except Exception as e:
            logger.error(f"❌ Errore DuckDuckGo Shopping: {e}")
            return []
    
    async def _try_bing_shopping(self, query: str) -> List[Dict[str, Any]]:
        """Prova Bing Shopping"""
        try:
            logger.info(f"🔍 Ricerca Bing Shopping: {query}")

            # URL Bing Shopping
            encoded_query = quote_plus(query)
            url = f"https://www.bing.com/shop?q={encoded_query}&setlang=it-IT"

            logger.info(f"🔍 DEBUG: URL Bing: {url}")

            logger.info("🔍 DEBUG: === APERTURA BROWSER BING ===")
            async with async_playwright() as p:
                # Configurazione browser per produzione (invisibile ma non headless)
                if self.production_mode:
                    # Modalità produzione: browser invisibile ma non headless
                    browser = await p.chromium.launch(
                        headless=self.render_mode,  # Headless su Render, visibile in produzione normale
                        args=[
                            '--no-sandbox',
                            '--disable-blink-features=AutomationControlled',
                            '--disable-web-security',
                            '--disable-features=VizDisplayCompositor',
                            '--disable-dev-shm-usage',
                            '--disable-gpu',
                            '--no-first-run',
                            '--no-default-browser-check',
                            '--disable-default-apps',
                            '--disable-extensions',
                            '--disable-plugins',
                            '--disable-images',
                            '--window-size=1,1',  # Finestra minima
                            '--window-position=9999,9999',  # Fuori schermo
                            '--user-agent=' + random.choice(self.user_agents)
                        ]
                    )
                else:
                    # Modalità sviluppo: browser visibile
                    browser = await p.chromium.launch(
                        headless=False,
                        args=[
                            '--no-sandbox',
                            '--disable-blink-features=AutomationControlled',
                            '--disable-web-security',
                            '--disable-features=VizDisplayCompositor',
                            '--disable-dev-shm-usage',
                            '--disable-gpu',
                            '--no-first-run',
                            '--no-default-browser-check',
                            '--disable-default-apps',
                            '--disable-extensions',
                            '--disable-plugins',
                            '--disable-images',
                            '--user-agent=' + random.choice(self.user_agents)
                        ]
                    )
                logger.info("🔍 DEBUG: Browser Bing aperto")

                page = await browser.new_page()
                
                # Imposta viewport più realistico
                await page.set_viewport_size({"width": 1366, "height": 768})
                
                # Aggiungi comportamento umano
                await page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined,
                    });
                """)
                
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                await page.wait_for_timeout(8000)  # Più tempo per caricare contenuti dinamici

                # Gestione banner cookie
                await self._handle_cookie_banners(page)

                # DEBUG: Simula scroll umano per caricare più contenuti
                logger.info("🔍 DEBUG: Iniziando scroll per caricare contenuti Bing...")
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight/3)")
                await page.wait_for_timeout(2000)
                logger.info("🔍 DEBUG: Scroll Bing 1/3 completato")

                await page.evaluate("window.scrollTo(0, document.body.scrollHeight*2/3)")
                await page.wait_for_timeout(2000)
                logger.info("🔍 DEBUG: Scroll Bing 2/3 completato")

                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(2000)
                logger.info("🔍 DEBUG: Scroll Bing completo")

                # Estrai risultati Bing
                html_content = await page.content()
                logger.info(f"🔍 DEBUG: HTML Bing estratto, lunghezza: {len(html_content)} caratteri")
                soup = BeautifulSoup(html_content, 'html.parser')

                results = []

                # DEBUG: Log della struttura HTML per capire cosa c'è
                logger.info(f"🔍 DEBUG: Analizzando HTML Bing...")

                # Cerca risultati con selettori più generici
                all_links = soup.find_all('a', href=True)
                logger.info(f"🔍 DEBUG: Trovati {len(all_links)} link totali Bing")

                # DEBUG: Log di TUTTI i link per capire la struttura
                logger.info("🔍 DEBUG: === LISTA COMPLETA DEI LINK BING ===")
                for i, link in enumerate(all_links):
                    href = link.get('href', '')
                    text = link.get_text(strip=True)
                    if text and href:
                        logger.info(f"🔍 DEBUG: Link Bing {i+1}: '{text[:100]}' -> {href}")

                logger.info("🔍 DEBUG: === FINE LISTA LINK BING ===")

                # Cerca anche div e span che potrebbero contenere prodotti
                all_divs = soup.find_all('div')
                all_spans = soup.find_all('span')
                logger.info(f"🔍 DEBUG: Trovati {len(all_divs)} div e {len(all_spans)} span Bing")

                # Cerca elementi che potrebbero essere prodotti
                product_elements = []

                # 1. Cerca link che puntano a siti e-commerce
                for link in all_links:
                    href = link.get('href', '')
                    text = link.get_text(strip=True)

                    # Miglioramento: cerca link che puntano a siti e-commerce reali
                    if any(site in href.lower() for site in ['amazon', 'mediaworld', 'unieuro', 'carrefour', 'conad', 'ebay', 'shop', 'store', 'buy', 'product']):
                        product_elements.append(('link', link))
                        logger.info(f"🔍 DEBUG: Link shopping Bing trovato: {text[:50]} -> {href}")

                # 2. Cerca div che contengono prezzi
                logger.info("🔍 DEBUG: === CERCANDO DIV CON PREZZI BING ===")
                for div in all_divs:
                    text = div.get_text(strip=True)
                    if '€' in text and len(text) > 20 and len(text) < 200:
                        product_elements.append(('div', div))
                        logger.info(f"🔍 DEBUG: Div con prezzo Bing trovato: {text[:100]}")

                # 3. Cerca span che contengono prezzi
                logger.info("🔍 DEBUG: === CERCANDO SPAN CON PREZZI BING ===")
                for span in all_spans:
                    text = span.get_text(strip=True)
                    if '€' in text and len(text) > 10 and len(text) < 100:
                        product_elements.append(('span', span))
                        logger.info(f"🔍 DEBUG: Span con prezzo Bing trovato: {text[:50]}")
                
                # 4. NUOVO: Cerca elementi con prezzi usando regex
                logger.info("🔍 DEBUG: === CERCANDO ELEMENTI CON PREZZI REGEX ===")
                import re
                price_pattern = r'€\s*\d+[.,]\d+'
                all_elements = soup.find_all(text=re.compile(price_pattern))
                logger.info(f"🔍 DEBUG: Trovati {len(all_elements)} elementi con prezzi in €")
                
                for i, element in enumerate(all_elements[:20]):
                    parent = element.parent
                    if parent:
                        text = parent.get_text(strip=True)
                        if len(text) > 20 and len(text) < 300:
                            product_elements.append(('price_element', parent))
                            logger.info(f"🔍 DEBUG: Elemento con prezzo {i+1}: {text[:100]}")

            logger.info(f"🔍 DEBUG: === TROVATI {len(product_elements)} ELEMENTI POTENZIALI BING ===")
            logger.info(f"🔍 DEBUG: Limite prodotti per sito: {self.max_products_per_site}")

            # Estrai informazioni da tutti gli elementi trovati
            elements_to_process = min(len(product_elements), self.max_products_per_site)
            logger.info(f"🔍 DEBUG: Processando {elements_to_process} elementi su {len(product_elements)} trovati")
            
            # PRIORITÀ: Processa prima elementi con prezzi, poi link
            elements_with_prices = [e for e in product_elements if e[0] in ['div', 'span', 'price_element']]
            link_elements = [e for e in product_elements if e[0] == 'link']
            
            # Combina: prima elementi con prezzi, poi link
            prioritized_elements = elements_with_prices + link_elements
            
            logger.info(f"🔍 DEBUG: Elementi con prezzi: {len(elements_with_prices)}, Link: {len(link_elements)}")
            
            for element_type, element in prioritized_elements[:self.max_products_per_site]:  # Limita risultati
                try:
                        if element_type == 'link':
                            title = element.get_text(strip=True)
                            url = element.get('href')

                            # Miglioramento: cerca URL reali dei prodotti
                            if url.startswith('/'):
                                # URL relativo, cerca di costruire URL completo
                                if 'amazon' in url.lower():
                                    url = f"https://www.amazon.it{url}"
                                elif 'mediaworld' in url.lower():
                                    url = f"https://www.mediaworld.it{url}"
                                elif 'unieuro' in url.lower():
                                    url = f"https://www.unieuro.it{url}"
                                else:
                                    url = f"https://www.bing.com{url}"

                            # Cerca il prezzo nel testo del link o nei parent
                            price_text = "Prezzo non disponibile"
                            parent = element.parent
                            if parent:
                                price_match = re.search(r'€\s*(\d+[.,]\d+)', parent.get_text())
                                if price_match:
                                    price_text = f"€{price_match.group(1)}"

                            if title and url and len(title) > 10:  # Filtra titoli troppo corti
                                results.append({
                                    'name': title,
                                    'price': price_text,
                                    'price_numeric': self._extract_price_from_text(price_text),
                                    'url': url,
                                    'site': self._extract_site_from_url(url),
                                    'description': f"Risultato Bing per {query}",
                                    'source': 'bing_shopping',
                                    'query': query,
                                    'validation_score': 0.7
                                })
                                logger.info(f"🔍 DEBUG: Aggiunto risultato link Bing: {title[:50]} -> {url}")

                        elif element_type in ['div', 'span', 'price_element']:
                            text = element.get_text(strip=True)

                            # Cerca prezzo nel testo (FIX: usa pattern che funziona)
                            # Pattern 1: numero seguito da € (FUNZIONA - 10/10 match)
                            price_match = re.search(r'(\d+[.,]\d+)\s*€', text)
                            if price_match:
                                price_text = f"€{price_match.group(1)}"
                                price_numeric = self._extract_price_from_text(price_text)
                                logger.info(f"🔍 DEBUG: Prezzo estratto: {price_text} -> {price_numeric}")
                            else:
                                # Pattern 2: € seguito da numero (fallback)
                                price_match = re.search(r'€\s*(\d+[.,]\d+)', text)
                                if price_match:
                                    price_text = f"€{price_match.group(1)}"
                                    price_numeric = self._extract_price_from_text(price_text)
                                    logger.info(f"🔍 DEBUG: Prezzo fallback: {price_text} -> {price_numeric}")
                                else:
                                    # Pattern 3: numeri con virgole/punti (fallback finale)
                                    price_match = re.search(r'(\d{1,3}[.,]\d{2})', text)
                                    if price_match:
                                        price_text = f"€{price_match.group(1)}"
                                        price_numeric = self._extract_price_from_text(price_text)
                                        logger.info(f"🔍 DEBUG: Prezzo finale: {price_text} -> {price_numeric}")
                                    else:
                                        logger.info(f"🔍 DEBUG: Nessun prezzo trovato in: {text[:100]}")
                                        continue

                                # Cerca un titolo nel testo (prima del prezzo)
                                # FIX: estrai titolo prima del pattern "numero €"
                                title = ""
                                
                                # Cerca titolo prima del prezzo usando il pattern corretto
                                price_pattern = r'(\d+[.,]\d+)\s*€'
                                price_match = re.search(price_pattern, text)
                                if price_match:
                                    # Estrai tutto prima del prezzo
                                    title_part = text[:price_match.start()].strip()
                                    if title_part and len(title_part) > 10:
                                        title = title_part
                                
                                # Fallback: cerca per righe
                                if not title:
                                    lines = text.split('\n')
                                    for line in lines:
                                        if '€' not in line and len(line.strip()) > 10:
                                            title = line.strip()
                                            break
                                
                                # Fallback finale: usa la prima parte del testo
                                if not title:
                                    title = text.split('€')[0].strip()[:100]
                                    if not title:
                                        title = f"Prodotto {query}"
                                
                                # Pulizia titolo per rimuovere caratteri indesiderati
                                title = re.sub(r'[^\w\s\-\(\)\[\]\.]', ' ', title)
                                title = re.sub(r'\s+', ' ', title).strip()
                                if len(title) > 100:
                                    title = title[:100] + "..."
                                
                                # Cerca link prodotto nell'elemento
                                product_link = element.find('a', href=True)
                                url = f"https://www.bing.com/shop?q={quote_plus(query)}"
                                if product_link:
                                    href = product_link.get('href', '')
                                    if href and not href.startswith('javascript:'):
                                        if href.startswith('/'):
                                            url = f"https://www.bing.com{href}"
                                        elif href.startswith('http'):
                                            url = href
                                
                                # Solo aggiungi se ha un prezzo valido
                                if price_numeric > 0:
                                    results.append({
                                        'name': title,
                                        'price': price_text,
                                        'price_numeric': price_numeric,
                                        'url': url,
                                        'site': self._extract_site_from_url(url),
                                        'description': f"Risultato Bing per {query}",
                                        'source': 'bing_shopping',
                                        'query': query,
                                        'validation_score': 0.8 if price_numeric > 0 else 0.6
                                    })
                                    logger.info(f"🔍 DEBUG: Aggiunto risultato {element_type} Bing: {title[:50]} - {price_text} - {url}")
                                else:
                                    logger.info(f"🔍 DEBUG: Saltato {element_type} Bing: prezzo non valido ({price_text})")

                except Exception as e:
                    logger.error(f"🔍 DEBUG: Errore estrazione {element_type} Bing: {e}")
                    continue

            logger.info("🔍 DEBUG: === CHIUSURA BROWSER BING ===")
            await browser.close()
            logger.info("🔍 DEBUG: Browser Bing chiuso")

            logger.info(f"🔍 DEBUG: === RISULTATI FINALI BING ===")
            for i, result in enumerate(results):
                logger.info(f"🔍 DEBUG: Risultato finale Bing {i+1}: {result.get('name', 'N/A')[:50]} - {result.get('price', 'N/A')} - {result.get('url', 'N/A')}")
            logger.info(f"🔍 DEBUG: === FINE RISULTATI BING ===")
            logger.info(f"🔍 Risultati Bing: {len(results)}")
            logger.info(f"🔍 DEBUG: Risultati finali Bing:")
            for i, result in enumerate(results):
                name = result.get('name', 'N/A')[:40] + "..." if len(result.get('name', '')) > 40 else result.get('name', 'N/A')
                price = result.get('price', 'N/A')
                site = result.get('site', 'N/A')
                logger.info(f"🔍 DEBUG: Risultato {i+1}: {name} - {price} - {site}")
            return results

        except Exception as e:
            logger.error(f"❌ Errore Bing Shopping: {e}")
            return []

    async def _try_direct_ecommerce_search(self, query: str) -> List[Dict[str, Any]]:
        """Ricerca diretta sui siti e-commerce principali"""
        try:
            logger.info(f"🛍️ Ricerca diretta e-commerce: {query}")

            results = []

            # Lista siti e-commerce da provare (espansa)
            ecommerce_sites = [
                {
                    'name': 'Amazon',
                    'url': f'https://www.amazon.it/s?k={quote_plus(query)}',
                    'search_selector': 'h2 a[href*="/dp/"], [data-component-type="s-search-result"]',
                    'price_selector': 'span.a-price-whole, .a-price-range'
                },
                {
                    'name': 'MediaWorld',
                    'url': f'https://www.mediaworld.it/search?q={quote_plus(query)}',
                    'search_selector': 'a[href*="/p/"], .product-item',
                    'price_selector': '.price, .current-price'
                },
                {
                    'name': 'Unieuro',
                    'url': f'https://www.unieuro.it/search?q={quote_plus(query)}',
                    'search_selector': 'a[href*="/p/"], .product-item',
                    'price_selector': '.price, .current-price'
                },
                {
                    'name': 'Euronics',
                    'url': f'https://www.euronics.it/search?q={quote_plus(query)}',
                    'search_selector': 'a[href*="/p/"], .product-item',
                    'price_selector': '.price, .current-price'
                },
                {
                    'name': 'Trony',
                    'url': f'https://www.trony.it/search?q={quote_plus(query)}',
                    'search_selector': 'a[href*="/p/"], .product-item',
                    'price_selector': '.price, .current-price'
                }
            ]

            async with async_playwright() as p:
                # Configurazione browser per produzione (invisibile ma non headless)
                if self.production_mode:
                    # Modalità produzione: browser invisibile ma non headless
                    browser = await p.chromium.launch(
                        headless=self.render_mode,  # Headless su Render, visibile in produzione normale
                        args=[
                            '--no-sandbox',
                            '--disable-blink-features=AutomationControlled',
                            '--disable-web-security',
                            '--disable-features=VizDisplayCompositor',
                            '--disable-dev-shm-usage',
                            '--disable-gpu',
                            '--no-first-run',
                            '--no-default-browser-check',
                            '--disable-default-apps',
                            '--disable-extensions',
                            '--disable-plugins',
                            '--disable-images',
                            '--window-size=1,1',  # Finestra minima
                            '--window-position=9999,9999',  # Fuori schermo
                            '--user-agent=' + random.choice(self.user_agents)
                        ]
                    )
                else:
                    # Modalità sviluppo: browser visibile
                    browser = await p.chromium.launch(
                        headless=False,
                        args=[
                            '--no-sandbox',
                            '--disable-blink-features=AutomationControlled',
                            '--disable-web-security',
                            '--disable-features=VizDisplayCompositor',
                            '--disable-dev-shm-usage',
                            '--disable-gpu',
                            '--no-first-run',
                            '--no-default-browser-check',
                            '--disable-default-apps',
                            '--disable-extensions',
                            '--disable-plugins',
                            '--disable-images',
                            '--user-agent=' + random.choice(self.user_agents)
                        ]
                    )

                for site in ecommerce_sites[:2]:  # Prova solo i primi 2 siti
                    try:
                        page = await browser.new_page()
                        await page.goto(site['url'], wait_until="domcontentloaded", timeout=30000)
                        await page.wait_for_timeout(3000)

                        # Estrai risultati
                        html_content = await page.content()
                        soup = BeautifulSoup(html_content, 'html.parser')

                        # Cerca prodotti
                        product_links = soup.select(site['search_selector'])

                        for link in product_links[:3]:  # Max 3 prodotti per sito
                            try:
                                title = link.get_text(strip=True)
                                url = link.get('href', '')

                                if not url.startswith('http'):
                                    url = 'https://' + site['name'].lower() + '.it' + url

                                results.append({
                                    'name': title,
                                    'price': 'Prezzo non disponibile',
                                    'price_numeric': 0,
                                    'url': url,
                                    'site': site['name'],
                                    'description': f"Prodotto {site['name']} per {query}",
                                    'source': f'direct_{site["name"].lower()}',
                                    'query': query,
                                    'validation_score': 0.5
                                })
                            except Exception as e:
                                continue

                        await page.close()

                    except Exception as e:
                        logger.error(f"❌ Errore ricerca {site['name']}: {e}")
                        continue

                await browser.close()
                logger.info(f"🛍️ Risultati e-commerce diretti: {len(results)}")
                return results

        except Exception as e:
            logger.error(f"❌ Errore ricerca e-commerce diretta: {e}")
            return []



   
    def _extract_shopping_results(self, soup: BeautifulSoup, query: str) -> List[Dict[str, Any]]:
        """Estrae risultati da Google Shopping HTML"""
        results = []
        try:
            # Strategia 1: Cerca risultati sponsorizzati (sponsored ads)
            sponsored_items = soup.find_all('div', class_=['pla-unit', 'sh-dgr__content', 'sh-dlr__product-result'])
            logger.info(f"🛒 Trovati {len(sponsored_items)} elementi sponsorizzati")
            for item in sponsored_items[:10]:  # Max 10 risultati
                try:
                    result = self._extract_shopping_item(item, query)
                    if result:
                        results.append(result)
                except Exception as e:
                    logger.debug(f"⚠️ Errore estrazione item sponsorizzato: {e}")
                    continue

            # Strategia 2: Cerca risultati organici
            organic_items = soup.find_all('div', class_=['sh-dgr__content', 'pla-unit'])
            logger.info(f"🛒 Trovati {len(organic_items)} elementi organici")
            for item in organic_items[:10]:  # Max 10 risultati
                try:
                    result = self._extract_shopping_item(item, query)
                    if result and result not in results:
                        results.append(result)
                except Exception as e:
                    logger.debug(f"⚠️ Errore estrazione item organico: {e}")
                    continue

            # Strategia 3: Cerca qualsiasi link con prezzi
            price_links = soup.find_all('a', href=True)
            for link in price_links[:20]:  # Max 20 link
                try:
                    href = link.get('href', '')
                    if 'url=' in href and any(site in href.lower() for site in ['amazon', 'ebay', 'mediaworld', 'unieuro']):
                        result = self._extract_link_result(link, query)
                        if result and result not in results:
                            results.append(result)
                except Exception as e:
                    logger.debug(f"⚠️ Errore estrazione link: {e}")
                    continue

        except Exception as e:
            logger.error(f"❌ Errore estrazione risultati shopping: {e}")

        return results

    def _extract_shopping_item(self, item, query: str) -> Optional[Dict[str, Any]]:
        """Estrae dati da un item Google Shopping"""
        try:
            # Titolo prodotto
            title_elem = item.find(['h3', 'h4', 'a', 'span'], class_=['shntl', 'sh-dlr__product-title'])
            title = title_elem.get_text(strip=True) if title_elem else ""
            title = self._clean_product_title(title)  # Pulisci il titolo

            # Prezzo
            price_elem = item.find(string=re.compile(r'€\s*\d+'))
            if not price_elem:
                price_elem = item.find(['span', 'div'], string=re.compile(r'\d+[.,]\d+'))

            price_text = price_elem.strip() if price_elem else ""
            price = self._extract_price_from_text(price_text)

            # URL e sito
            link_elem = item.find('a', href=True)
            url = link_elem['href'] if link_elem else ""

            if url.startswith('/url?q='):
                # Decodifica URL Google
                url = url.split('/url?q=')[1].split('&')[0]

            site = self._extract_site_from_url(url)

            # Descrizione
            desc_elem = item.find(['div', 'span'], class_=['aULzUe', 'sh-dlr__product-snippet'])
            description = desc_elem.get_text(strip=True) if desc_elem else ""

            if title and url and site:
                return {
                    'name': title,
                    'price': price_text if price_text else "Prezzo non disponibile",
                    'price_numeric': price,
                    'url': url,
                    'site': site,
                    'description': description,
                    'source': 'google_shopping',
                    'query': query,
                    'validation_score': 0.8
                }

        except Exception as e:
            logger.debug(f"⚠️ Errore estrazione shopping item: {e}")
            return None

    def _extract_link_result(self, link, query: str) -> Optional[Dict[str, Any]]:
        """Estrae dati da un link generico"""
        try:
            title = link.get_text(strip=True)
            title = self._clean_product_title(title)  # Pulisci il titolo
            url = link.get('href', '')

            # Filtra risultati che sono chiaramente filtri o non prodotti
            filter_keywords = [
                'fino a', 'oltre', 'prezzo', 'filtra', 'filtro', 'categoria', 'marca',
                'venditore', 'confronta', 'visualizza', 'accedi', 'elenco', 'collezioni',
                'preferenze', 'desideri', 'ordina', 'sort', 'filter', 'price range',
                'confronta i prezzi', 'visualizza lista', 'prezzo decrescente', 'prezzo crescente'
            ]
            
            title_lower = title.lower()
            if any(keyword in title_lower for keyword in filter_keywords):
                return None  # Salta questo risultato
            
            # Verifica che il titolo sia abbastanza lungo (non solo "€" o numeri)
            if len(title) < 5 or title.isdigit() or title in ['€', '€0', '€0,00']:
                return None

            if url.startswith('/url?q='):
                url = url.split('/url?q=')[1].split('&')[0]

            site = self._extract_site_from_url(url)

            if title and url and site:
                return {
                    'name': title,
                    'price': "Prezzo non disponibile",
                    'price_numeric': 0,
                    'url': url,
                    'site': site,
                    'description': f"Risultato per {query}",
                    'source': 'google_shopping_link',
                    'query': query,
                    'validation_score': 0.6
                }

        except Exception as e:
            logger.debug(f"⚠️ Errore estrazione link result: {e}")
            return None
    
    def _extract_price_from_text(self, price_text: str) -> float:
        """Estrae prezzo numerico dal testo"""
        try:
            if not price_text or price_text == "Prezzo non disponibile":
                logger.info(f"🦆 DEBUG: Prezzo vuoto o non disponibile, ritorno 0.0")
                return 0.0
            
            logger.info(f"🦆 DEBUG: === CONVERSIONE PREZZO NUMERICO ===")
            logger.info(f"🦆 DEBUG: Prezzo input: '{price_text}'")
            
            # Cerca pattern di prezzo con regex
            import re
            price_pattern = r'€\s*(\d+[.,]\d+)'
            match = re.search(price_pattern, str(price_text))
            if match:
                price_clean = match.group(1)
                logger.info(f"🦆 DEBUG: Prezzo estratto con regex: '{price_clean}'")
            else:
                # Fallback: rimuovi simboli di valuta e spazi
                price_clean = re.sub(r'[€$£\s]', '', str(price_text))
                logger.info(f"🦆 DEBUG: Dopo rimozione simboli: '{price_clean}'")
            
            # Gestisci virgole e punti decimali (formato italiano)
            if ',' in price_clean and '.' in price_clean:
                # Se ha entrambi, la virgola è il separatore delle migliaia
                price_clean = price_clean.replace('.', '').replace(',', '.')
                logger.info(f"🦆 DEBUG: Virgola e punto -> virgola migliaia: '{price_clean}'")
            elif ',' in price_clean:
                # Se ha solo virgola, potrebbe essere decimale o migliaia
                if price_clean.count(',') == 1 and len(price_clean.split(',')[1]) <= 2:
                    # Probabilmente decimale (es: 123,45)
                    price_clean = price_clean.replace(',', '.')
                    logger.info(f"🦆 DEBUG: Virgola decimale -> punto: '{price_clean}'")
                else:
                    # Probabilmente migliaia (es: 1,234,567)
                    price_clean = price_clean.replace(',', '')
                    logger.info(f"🦆 DEBUG: Virgola migliaia rimossa: '{price_clean}'")
            
            # Estrai solo numeri e punto decimale
            price_match = re.search(r'[\d.]+', price_clean)
            if price_match:
                price_float = float(price_match.group())
                
                # FILTRO PREZZI MALFORMATI (basato su pattern specifici)
                price_str = str(price_float)
                
                # Pattern 1: Troppi zeri iniziali (es: 093385,72 -> 93385.72)
                if price_str.startswith('0') and len(price_str) > 4:
                    # Rimuovi zeri iniziali e ricalcola
                    price_clean_fixed = price_str.lstrip('0')
                    if price_clean_fixed and price_clean_fixed != '.':
                        try:
                            price_float_fixed = float(price_clean_fixed)
                            logger.info(f"🦆 DEBUG: 🔧 Prezzo corretto da {price_float}€ a {price_float_fixed}€")
                            price_float = price_float_fixed
                        except:
                            pass
                
                # Pattern 2: Prezzi con troppe cifre decimali (es: 123.456789)
                if '.' in price_str:
                    decimal_part = price_str.split('.')[1]
                    if len(decimal_part) > 2:  # Più di 2 decimali
                        # Arrotonda a 2 decimali
                        price_float = round(price_float, 2)
                        logger.info(f"🦆 DEBUG: 🔧 Prezzo arrotondato a 2 decimali: {price_float}€")
                
                # Pattern 3: Prezzi con formato strano (es: 123456.789 -> 123456.79)
                if price_float > 0 and price_float < 1:  # Prezzi sotto 1€ sono sospetti per molti prodotti
                    # Controlla se è un errore di parsing (es: 0.123456 -> 123.456)
                    if len(price_str) > 6 and price_str.startswith('0.'):
                        # Potrebbe essere un errore di parsing, prova a moltiplicare per 1000
                        potential_price = price_float * 1000
                        if 1 <= potential_price <= 10000:  # Range ragionevole
                            logger.info(f"🦆 DEBUG: 🔧 Prezzo corretto da {price_float}€ a {potential_price}€")
                            price_float = potential_price
                
                # Pattern 4: Controlla formato prezzi secondo standard 
                # Formati validi: 0,87 | 255,00 | 255.000,00 | 3490.000,00
                
                # Pattern 5: Controlla formato decimali (sempre 2 cifre max)
                if '.' in price_str:
                    decimal_part = price_str.split('.')[1]
                    if len(decimal_part) > 2:  # Più di 2 decimali
                        # Arrotonda a 2 decimali
                        price_float = round(price_float, 2)
                        logger.info(f"🦆 DEBUG: 🔧 Prezzo arrotondato a 2 decimali: {price_float}€")
                
                # Pattern 6: Controlla se prezzo alto non è arrotondato al migliaio
                if price_float >= 1000:
                    integer_part = int(price_float)
                    # Se ha più di 3 cifre, dovrebbe essere arrotondato al migliaio
                    if integer_part % 1000 != 0:  # Non è arrotondato al migliaio
                        # Arrotonda al migliaio più vicino
                        price_float = round(integer_part / 1000) * 1000
                        logger.info(f"🦆 DEBUG: 🔧 Prezzo arrotondato al migliaio: {price_float}€")
                
                # Pattern 7: Scarta prezzi con formato strano (es: 4372869.01)
                # I prezzi alti dovrebbero essere sempre arrotondati al migliaio
                if price_float > 100000:
                    integer_part = int(price_float)
                    # Se non è arrotondato al migliaio, è sospetto
                    if integer_part % 1000 != 0:
                        logger.info(f"🦆 DEBUG: ❌ Prezzo alto non arrotondato al migliaio scartato: {price_float}€")
                        logger.info(f"🦆 DEBUG: === FINE CONVERSIONE PREZZO (NON ARROTONDATO) ===")
                        return 0.0
                
                # Pattern 8: Scarta prezzi con troppe cifre intere (es: 4369729,00)
                # I prezzi sopra 100k dovrebbero avere max 6 cifre intere
                if price_float > 100000:
                    integer_part = int(price_float)
                    integer_str = str(integer_part)
                    if len(integer_str) > 6:  # Più di 6 cifre intere
                        logger.info(f"🦆 DEBUG: ❌ Prezzo con troppe cifre intere scartato: {price_float}€ ({len(integer_str)} cifre)")
                        logger.info(f"🦆 DEBUG: === FINE CONVERSIONE PREZZO (TROPPE CIFRE) ===")
                        return 0.0
                
                # Pattern 9: Scarta prezzi con zero iniziale (es: 044,80)
                if price_float > 0 and price_float < 1000:
                    price_str = str(price_float)
                    if price_str.startswith('0') and len(price_str) > 3:
                        logger.info(f"🦆 DEBUG: ❌ Prezzo con zero iniziale scartato: {price_float}€")
                        logger.info(f"🦆 DEBUG: === FINE CONVERSIONE PREZZO (ZERO INIZIALE) ===")
                        return 0.0
                
                logger.info(f"🦆 DEBUG: ✅ Prezzo convertito e validato: '{price_text}' -> {price_float}")
                logger.info(f"🦆 DEBUG: === FINE CONVERSIONE PREZZO ===")
                return price_float
            else:
                logger.info(f"🦆 DEBUG: ❌ Nessun numero trovato in '{price_clean}'")
                logger.info(f"🦆 DEBUG: === FINE CONVERSIONE PREZZO ===")
                return 0.0
            
        except Exception as e:
            logger.error(f"❌ Errore estrazione prezzo '{price_text}': {e}")
            logger.info(f"🦆 DEBUG: === FINE CONVERSIONE PREZZO (ERRORE) ===")
            return 0.0

    def _extract_site_from_url(self, url: str) -> str:
        """Estrae il nome del sito dall'URL"""
        try:
            if not url:
                return "Sconosciuto"
            
            # Gestisci URL di tracking DuckDuckGo
            if 'links.duckduckgo.com' in url:
                return "DuckDuckGo"
            
            # Gestisci URL di Bing
            if 'bing.com' in url:
                return "Bing"
            
            # Estrai dominio
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Mappa domini a nomi più descrittivi
            site_mapping = {
                'www.amazon.it': 'Amazon',
                'amazon.it': 'Amazon',
                'www.mediaworld.it': 'MediaWorld',
                'mediaworld.it': 'MediaWorld',
                'www.unieuro.it': 'Unieuro',
                'unieuro.it': 'Unieuro',
                'www.carrefour.it': 'Carrefour',
                'carrefour.it': 'Carrefour',
                'www.conad.it': 'Conad',
                'conad.it': 'Conad',
                'www.ebay.it': 'eBay',
                'ebay.it': 'eBay',
                'www.comparor.com': 'Comparor',
                'comparor.com': 'Comparor',
                'www.delupe.it': 'Delupe',
                'delupe.it': 'Delupe',
                'www.prezzoforte.com': 'PrezzoForte',
                'prezzoforte.com': 'PrezzoForte',
                'www.awin1.com': 'Awin',
                'awin1.com': 'Awin'
            }
            
            # Rimuovi www. se presente per il mapping
            domain_clean = domain.replace('www.', '')
            
            if domain_clean in site_mapping:
                return site_mapping[domain_clean]
            
            # Se non è mappato, usa il dominio principale
            if '.' in domain:
                return domain.split('.')[-2].title()
            
            return domain.title()
        except Exception as e:
            logger.debug(f"⚠️ Errore estrazione sito da '{url}': {e}")
            return "Sconosciuto"
    
    def _clean_product_title(self, title: str) -> str:
        """Pulisce e normalizza il titolo del prodotto"""
        if not title:
            return ""
        
        try:
            # Rimuovi caratteri speciali e spazi multipli
            cleaned = re.sub(r'\s+', ' ', title.strip())
            
            # Rimuovi parti comuni che rendono i titoli confusi
            patterns_to_remove = [
                r'Risultato DuckDuckGo per\s+["\']?[^"\']*["\']?',
                r'Risultato\s+[A-Za-z]+\s+per\s+["\']?[^"\']*["\']?',
                r'Fonte:\s*',
                r'Prezzo:\s*€?\d+[.,]\d+',
                r'Score:\s*[A-Za-z%]+',
                r'Clicca\s*$',
                r'https?://[^\s]+',
                r'www\.[^\s]+',
                r'\.it\s*$',
                r'\.com\s*$',
                r'\.net\s*$',
                r'\.org\s*$',
                # Rimuovi prezzi dal titolo
                r'€\s*\d+[.,]\d+\s*€?[A-Za-z\s]*$',
                r'\d+[.,]\d+\s*€\s*[A-Za-z\s]*$',
                r'€\s*\d+[.,]\d+[A-Za-z\s]*$',
                r'\d+[.,]\d+\s*€?[A-Za-z\s]*$',
                # Rimuovi parti finali con prezzi
                r'\s+\d+[.,]\d+\s*€\s*[A-Za-z\s]*$',
                r'\s+€\s*\d+[.,]\d+\s*[A-Za-z\s]*$'
            ]
            
            for pattern in patterns_to_remove:
                cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
            
            # Rimuovi spazi extra e caratteri strani
            cleaned = re.sub(r'\s+', ' ', cleaned.strip())
            cleaned = re.sub(r'[^\w\s\-.,()€$%]', '', cleaned)
            
            # Limita la lunghezza
            if len(cleaned) > 80:
                cleaned = cleaned[:77] + "..."
            
            return cleaned
            
        except Exception as e:
            logger.debug(f"⚠️ Errore pulizia titolo: {e}")
            return title[:80] if len(title) > 80 else title

    def _validate_and_filter_results(self, results: List[Dict[str, Any]], original_product: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Valida e filtra i risultati"""
        validated = []
        
        logger.info(f"🔍 DEBUG: === INIZIO VALIDAZIONE DETTAGLIATA ===")
        logger.info(f"🔍 DEBUG: Risultati da validare: {len(results)}")
        
        # Rimuovi duplicati prima della validazione
        seen_titles = set()
        unique_results = []
        
        for result in results:
            title_normalized = result.get('name', '').lower().strip()
            if title_normalized not in seen_titles and len(title_normalized) >= 3:
                seen_titles.add(title_normalized)
                unique_results.append(result)
        
        logger.info(f"🔍 DEBUG: Risultati unici dopo rimozione duplicati: {len(unique_results)}")
        
        for i, result in enumerate(unique_results):
            try:
                logger.info(f"🔍 DEBUG: Validando risultato {i+1}: {result.get('name', 'N/A')[:50]}")
                
                url = result.get('url', '')
                if not url:
                    logger.info(f"🔍 DEBUG: Risultato {i+1} scartato - URL vuoto")
                    continue
                
                # Valida URL
                if not self._is_valid_url(url):
                    logger.info(f"🔍 DEBUG: Risultato {i+1} scartato - URL non valido: {url}")
                    continue
                
                # Calcola score di validazione
                score = self._calculate_validation_score(result, original_product)
                logger.info(f"🔍 DEBUG: Risultato {i+1} - Score: {score}")
                
                if score >= 0.20:  # Soglia ridotta per includere più risultati validi
                    result['validation_score'] = score
                    validated.append(result)
                    logger.info(f"🔍 DEBUG: Risultato {i+1} VALIDATO - Score: {score} - Titolo: {result.get('name', 'N/A')[:50]}")
                else:
                    logger.info(f"🔍 DEBUG: Risultato {i+1} scartato - Score troppo basso: {score}")
                
            except Exception as e:
                logger.error(f"❌ Errore validazione risultato {i+1}: {e}")
                continue
        
        # Ordina per score
        validated.sort(key=lambda x: x.get('validation_score', 0), reverse=True)
        
        logger.info(f"🔍 DEBUG: === FINE VALIDAZIONE DETTAGLIATA ===")
        logger.info(f"🔍 DEBUG: Risultati validati: {len(validated)}")
        
        return validated[:self.max_results]

    def _is_valid_url(self, url: str) -> bool:
        """Verifica se l'URL è valido"""
        try:
            parsed = urlparse(url)
            return bool(parsed.scheme and parsed.netloc)
        except:
            return False

    def _calculate_validation_score(self, result: Dict[str, Any], original_product: Dict[str, Any]) -> float:
        """Calcola score di validazione per un risultato - SOLO VICINANZA AL TESTO"""
        score = 0.0
        
        try:
            title = result.get('name', '').lower()
            description = result.get('description', '').lower()
            
            logger.info(f"🔍 DEBUG: Calcolo score per: {title[:50]}")
            logger.info(f"🔍 DEBUG: Prodotto originale: {original_product.get('name', 'N/A')[:50]}")
            
            # Score SOLO per rilevanza del contenuto (vicinanza al testo)
            product_name = original_product.get('name', '').lower()
            logger.info(f"🔍 DEBUG: Product name: '{product_name}'")
            
            if product_name:
                # Cerca parole chiave nel titolo o descrizione (includi numeri ma scarta articoli)
                product_words = []
                for word in product_name.split():
                    word = word.strip()
                    if len(word) > 0:
                        # Includi numeri (anche se corti)
                        if word.isdigit() or word.replace('.', '').replace(',', '').isdigit():
                            product_words.append(word)
                        # Includi parole normali (ma scarta articoli comuni)
                        elif len(word) > 2 and word.lower() not in ['il', 'la', 'lo', 'gli', 'le', 'un', 'una', 'uno', 'di', 'da', 'in', 'con', 'su', 'per', 'tra', 'fra', 'e', 'o', 'ma', 'se', 'che', 'chi', 'cosa', 'dove', 'quando', 'come', 'perché']:
                            product_words.append(word)
                logger.info(f"🔍 DEBUG: Product words: {product_words}")
                
                matches = 0
                for word in product_words:
                    # LOGICA MIGLIORATA - Riconosce varianti delle parole
                    title_words = title.lower().split()
                    description_words = description.lower().split()
                    
                    word_lower = word.lower()
                    
                    # Controlla se la parola è presente nel TITOLO (esatta o come parte di una parola)
                    title_match = False
                    
                    # 1. Cerca parola esatta
                    exact_match = any(w.strip('.,!?;:()[]{}"\'-') == word_lower for w in title_words)
                    
                    # 2. Cerca parola come parte di altre parole (es: "128" in "128GB")
                    partial_match = any(word_lower in w.strip('.,!?;:()[]{}"\'-') for w in title_words)
                    
                    # 3. Cerca varianti comuni (es: "128" -> "128gb", "128 gb", "128GB")
                    variant_matches = []
                    if word_lower.isdigit():
                        # Per numeri, cerca varianti con unità comuni
                        variants = [word_lower, word_lower + 'gb', word_lower + ' gb', word_lower + 'gb', word_lower + 'tb', word_lower + ' tb']
                        for variant in variants:
                            if any(variant in w.strip('.,!?;:()[]{}"\'-') for w in title_words):
                                variant_matches.append(variant)
                    else:
                        # Per parole, cerca varianti con suffissi comuni
                        variants = [word_lower, word_lower + 's', word_lower + 'es', word_lower + 'ing']
                        for variant in variants:
                            if any(variant in w.strip('.,!?;:()[]{}"\'-') for w in title_words):
                                variant_matches.append(variant)
                    
                    title_match = exact_match or partial_match or len(variant_matches) > 0
                    
                    # DEBUG: Log dettagliato per capire i match
                    logger.info(f"🔍 DEBUG: Cercando '{word_lower}' in titolo: {title_words[:10]}")
                    logger.info(f"🔍 DEBUG: Match esatto: {exact_match}")
                    logger.info(f"🔍 DEBUG: Match parziale: {partial_match}")
                    logger.info(f"🔍 DEBUG: Varianti trovate: {variant_matches}")
                    
                    if title_match:
                        matching_words = [w for w in title_words if word_lower in w.strip('.,!?;:()[]{}"\'-')]
                        logger.info(f"🔍 DEBUG: ✅ MATCH TITOLO: '{word_lower}' trovata come: {matching_words}")
                    else:
                        logger.info(f"🔍 DEBUG: ❌ PAROLA '{word_lower}' NON trovata nel titolo")
                    
                    if title_match:
                        matches += 1
                        logger.info(f"🔍 DEBUG: Parola '{word}' trovata in titolo (esatta/parziale/variante)")
                    else:
                        logger.info(f"🔍 DEBUG: Parola '{word}' NON trovata in titolo")
                
                # LOGICA COMPLETAMENTE NUOVA - FORZA AGGIORNAMENTO
                logger.info(f"🔍 DEBUG: *** NUOVA LOGICA ATTIVA *** Matches trovati: {matches}")
                
                # LOGICA CON PENALIZZAZIONE - Solo risultati con TUTTE le parole sono validi
                total_words = len(product_words)
                logger.info(f"🔍 DEBUG: *** LOGICA PENALIZZANTE *** Trovate {matches}/{total_words} parole")
                
                if matches == total_words:
                    # TUTTE le parole trovate = Score alto
                    if total_words == 1:
                        score = 0.60  # Una parola, ma è l'unica richiesta
                    elif total_words == 2:
                        score = 0.80  # Due parole, entrambe trovate
                    else:
                        score = 0.90  # Tre o più parole, tutte trovate
                    logger.info(f"🔍 DEBUG: *** TUTTE LE PAROLE TROVATE *** Score: {score} ({matches}/{total_words})")
                elif matches > 0:
                    # PENALIZZAZIONE RIDOTTA - Solo alcune parole trovate
                    penalty_score = (matches / total_words) * 0.50  # Max 50% se manca qualche parola
                    score = penalty_score
                    logger.info(f"🔍 DEBUG: *** PENALIZZAZIONE APPLICATA *** Score: {score} ({matches}/{total_words} parole)")
                    logger.info(f"🔍 DEBUG: *** PAROLE MANCANTI *** Mancano {total_words - matches} parole su {total_words}")
                else:
                    # Nessuna parola trovata = Score ZERO
                    score = 0.0
                    logger.info(f"🔍 DEBUG: *** NESSUNA PAROLA TROVATA *** Score: 0.0")
            else:
                logger.warning(f"🔍 DEBUG: Product name vuoto! Original product: {original_product}")
                score = 0.0  # Score ZERO se non c'è nome prodotto
            
            # RIMOSSO BONUS PER TITOLO LUNGO - Punteggio basato solo sulle parole trovate
            logger.info(f"🔍 DEBUG: Nessun bonus aggiuntivo - punteggio basato solo su parole trovate")
            
        except Exception as e:
            logger.error(f"❌ Errore calcolo score: {e}")
        
        logger.info(f"🔍 DEBUG: Score finale: {score}")
        return min(score, 1.0)

    def _format_alternative_vendors(self, validated_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Formatta i venditori alternativi per la UI"""
        vendors = []
        
        for result in validated_results:
            validation_score = result.get('validation_score', 0)
            
            # NON troncare URL - gli URL di tracking DuckDuckGo sono lunghi ma funzionanti
            url = result.get('url', '#')
            
            vendor = {
                'name': result.get('name', 'Prodotto'),
                'price': result.get('price', 'Prezzo non disponibile'),
                'description': result.get('description', ''),
                'url': url,
                'brand': result.get('brand', ''),
                'source': result.get('site', 'Venditore'),
                'validation_score': validation_score
            }
            
            logger.info(f"🔍 DEBUG: Vendor '{vendor['name'][:30]}' - Score: {validation_score}")
            vendors.append(vendor)
        
        # Ordina per score di validazione
        vendors.sort(key=lambda x: x.get('validation_score', 0), reverse=True)
        
        return vendors

    async def _compare_prices(self, original_product: Dict[str, Any], alternative_products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Confronta prezzi tra prodotto originale e alternative"""
        try:
            original_price = self._normalize_price(original_product.get('price', '0'))
            
            if original_price <= 0:
                return {
                    "price_comparison": "Impossibile confrontare prezzi",
                    "best_deal": None,
                    "price_range": None
                }
            
            # Analizza prezzi alternativi
            valid_prices = []
            for product in alternative_products:
                price = product.get('price_numeric', 0)
                if price > 0:
                    valid_prices.append(price)
                    product['normalized_price'] = price
            
            if not valid_prices:
                return {
                    "price_comparison": "Nessun prezzo alternativo valido",
                    "best_deal": None,
                    "price_range": None
                }
            
            # Calcola statistiche
            min_price = min(valid_prices)
            max_price = max(valid_prices)
            avg_price = sum(valid_prices) / len(valid_prices)
            
            # Trova miglior affare
            best_deal = None
            if min_price < original_price:
                best_deal = {
                    "savings": original_price - min_price,
                    "savings_percentage": ((original_price - min_price) / original_price) * 100,
                    "price": min_price
                }
            
            return {
                "price_comparison": "Confronto completato",
                "original_price": original_price,
                "min_alternative_price": min_price,
                "max_alternative_price": max_price,
                "average_alternative_price": avg_price,
                "best_deal": best_deal,
                "total_alternatives": len(valid_prices)
            }
            
        except Exception as e:
            logger.error(f"❌ Errore confronto prezzi: {e}")
            return {
                "price_comparison": f"Errore confronto: {str(e)}",
                "best_deal": None,
                "price_range": None
            }

    def _normalize_price(self, price: str) -> float:
        """Normalizza il prezzo in formato numerico"""
        try:
            if not price:
                return 0.0
            
            # Rimuovi simboli di valuta e spazi
            price_clean = re.sub(r'[€$£\s]', '', str(price))
            
            # Gestisci virgole e punti decimali
            price_clean = price_clean.replace(',', '.')
            
            # Estrai solo numeri e punto decimale
            price_match = re.search(r'[\d.]+', price_clean)
            if price_match:
                return float(price_match.group())
            
            return 0.0
            
        except Exception as e:
            logger.error(f"❌ Errore normalizzazione prezzo '{price}': {e}")
            return 0.0

# Istanza globale
google_search = GoogleSearchIntegration()

# Funzione standalone per compatibilità
async def search_alternative_vendors(product_data: Dict[str, Any]) -> Dict[str, Any]:
    """Funzione standalone per ricerca venditori alternativi"""
    return await google_search.search_alternative_vendors(product_data)
