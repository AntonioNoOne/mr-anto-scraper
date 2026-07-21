#!/usr/bin/env python3

"""
Google Search Integration - DuckDuckGo mixin
============================================

Contiene i metodi relativi alla ricerca DuckDuckGo e alla gestione dei
banner cookie. Estratto da google_search_integration.py per rispettare il
limite di lunghezza dei file. Nessuna modifica di logica: solo spostamento.
"""

import re
import random
import logging
from typing import Dict, List, Any
from urllib.parse import quote_plus

# Import Playwright per browser automation
from playwright.async_api import async_playwright

# Import per parsing HTML
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class _DuckDuckGoMixin:
    """Metodi di ricerca DuckDuckGo e gestione banner cookie."""

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
