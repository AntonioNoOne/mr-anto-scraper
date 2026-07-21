#!/usr/bin/env python3

"""
Google Search Integration - Bing / e-commerce diretto mixin
===========================================================

Contiene i metodi relativi alla ricerca Bing Shopping e alla ricerca
diretta sui siti e-commerce. Estratto da google_search_integration.py per
rispettare il limite di lunghezza dei file. Nessuna modifica di logica:
solo spostamento.
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


class _BingMixin:
    """Metodi di ricerca Bing Shopping e ricerca diretta e-commerce."""

    async def _try_bing_shopping(self, query: str) -> List[Dict[str, Any]]:
        """Prova Bing Shopping"""
        results = []  # Inizializza results all'inizio
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
                            price_text = "Prezzo non disponibile"
                            price_numeric = 0

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
                                # Controlla duplicati prima di aggiungere
                                is_duplicate = False
                                for existing in results:
                                    if (existing['name'].lower() == title.lower() and
                                        abs(existing['price_numeric'] - price_numeric) < 0.01):
                                        is_duplicate = True
                                        logger.info(f"🔍 DEBUG: Duplicato saltato: {title}")
                                        break

                                if not is_duplicate:
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
